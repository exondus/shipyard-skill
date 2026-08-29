# Sending, Scheduling and Deep Linking

Verified August 2026 against Expo's push service docs. Time-sensitive: the rate limits and payload ceilings below are Expo's current published figures, the receipt retention window is 24 hours, and foreground presentation defaults change in SDK 58. Re-verify at [docs.expo.dev/push-notifications/sending-notifications](https://docs.expo.dev/push-notifications/sending-notifications/) and the [FAQ](https://docs.expo.dev/push-notifications/faq/).

## Token lifecycle — the facts that dictate the schema

| Fact | Source | Consequence |
|---|---|---|
| `ExpoPushToken` survives app upgrades and never expires | [Expo FAQ](https://docs.expo.dev/push-notifications/faq/) | You cannot expire tokens on a timer; only receipts tell you a token is dead |
| On Android, reinstalling **may** change the token; on iOS it usually does not | Expo FAQ | The same physical device can produce several live tokens over time |
| Changing `applicationId` or `experienceId` changes every token | Expo FAQ | A bundle-ID change is a full re-registration event |
| A token can rotate **while the app is running** | `addPushTokenListener` | Registration is not a one-time onboarding step |
| A token identifies an install, not a person | — | One user, many tokens; one token, potentially several users over time |

## Schema

```sql
create table push_tokens (
  id            uuid primary key default gen_random_uuid(),
  token         text not null unique,           -- 'ExponentPushToken[...]'
  user_id       uuid references users(id) on delete cascade,
  device_id     text not null,                  -- stable per install
  platform      text not null check (platform in ('ios','android')),
  app_version   text,
  locale        text,                           -- for localised sends; see localization-foundation
  timezone      text,                           -- IANA, for local-time scheduling
  last_seen_at  timestamptz not null default now(),
  disabled_at   timestamptz,                    -- set on DeviceNotRegistered; never delete the row
  disabled_reason text
);
create index on push_tokens (user_id) where disabled_at is null;
```

`unique (token)` is the important constraint: registration is an upsert on the token, reassigning `user_id` when the device signs into a different account. Without it a shared tablet sends every user's notifications to whoever logged in first.

**Soft-disable, never hard-delete.** A deleted row re-registers on next launch and you lose the fact that this token was already proven dead, which produces a loop of send → `DeviceNotRegistered` → delete → re-register. Keep the row and the reason.

On sign-out, null the `user_id`; do not disable the token. The install is still valid and the next sign-in should reuse it.

`postgres-data` owns RLS: `push_tokens` is server-written and must not be readable by other users — a leaked Expo token lets anyone send notifications as you unless you enable [enhanced push security](https://expo.dev/settings/access-tokens) and require an access token on every send. Turn it on before launch; it costs one header.

## Registration on the client

```ts
async function registerPushToken() {
  if (Platform.OS === 'android') await ensureChannels();   // must precede the token call

  const s = await Notifications.getPermissionsAsync();
  const ok = s.granted || s.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL;
  if (!ok) return;                                          // onboarding-flow owns the asking

  try {
    const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId });
    await api.push.register.mutate({ token, platform: Platform.OS, deviceId, timezone, locale });
  } catch {/* offline or APNs unreachable — retry on next foreground, never block the UI */}
}
```

Call it on every cold start and on sign-in, and subscribe `addPushTokenListener` once so a mid-session rotation re-registers immediately. `getExpoPushTokenAsync` hits Expo's servers and fails offline — always wrap it. Treat iOS `PROVISIONAL` as granted for delivery, and read `ios.status` rather than the root `status`, which flattens the five iOS authorization states.

## The send path

Use [`expo-server-sdk-node`](https://github.com/expo/expo-server-sdk-node). It chunks to 100 messages, caps concurrency at six connections, gzips, throttles under the 600/second limit, and retries with exponential backoff. Writing this yourself buys nothing.

```ts
const expo = new Expo({ accessToken: process.env.EXPO_ACCESS_TOKEN });

const messages = rows
  .filter(r => Expo.isExpoPushToken(r.token))
  .map(r => ({
    to: r.token,
    title: 'Your trial ends tomorrow',
    body: `You'll be charged ${price} on ${date}. Cancel anytime in Settings.`,
    data: { url: '/settings/subscription', campaign_id: 'trial_reminder_v2' },
    channelId: 'reminders',                 // Android; must already exist on device
    categoryId: 'trial',                    // optional interactive actions
    priority: 'high',
    ttl: 60 * 60 * 12,
    badge: 1,                               // iOS only
    interruptionLevel: 'active',            // iOS only
    collapseId: `trial:${r.user_id}`,       // dedupe in transit
  }));

for (const chunk of expo.chunkPushNotificationChunks(messages)) {
  const tickets = await expo.sendPushNotificationsAsync(chunk);
  await persistTickets(chunk, tickets);     // ticket id ↔ token ↔ campaign
}
```

Message-format notes that bite:

- **`badge` is iOS-only.** Android badge counts come from the launcher and the channel, not this field. Manage the iOS count server-side or with `setBadgeCountAsync(0)` on foreground; a badge that never clears is the fastest route to an uninstall.
- **`channelId` pointing at a channel the device has not created means the notification is not displayed** — no error anywhere. Ship channels in the same release as the campaign that uses them.
- **4KiB total payload**, including `data`. Over it: receipt error `MessageTooBig`.
- **`priority: 'high'`** is APNs 10 / FCM high — wakes the device. `normal` is throttled and, on Android, may not open a network connection at all until the device leaves Doze. Use `high` for anything time-bound and `normal` for marketing, which is also the polite reading of the platforms' guidance.
- **`ttl: 0` on Android can mean never delivered** to a dozing device. Give a reminder a TTL long enough to survive a Doze window — hours, not seconds.
- **`collapseId` vs `tag`**: `collapseId` coalesces messages *in transit* on both platforms and also replaces displayed notifications on iOS; Android needs `tag` to replace an already-displayed one.
- **`contentAvailable: true`** with only `data` makes a headless background notification: it needs `enableBackgroundRemoteNotifications` on iOS plus a registered `expo-task-manager` task, delivery is not guaranteed, and Apple asks for [no more than two or three per hour](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app#overview). Prefer a normal notification message.

## Receipts — the job everyone skips

A ticket with `status: 'ok'` means **Expo accepted the message**, nothing more. The receipt, available about 15 minutes later and **purged after 24 hours**, says whether APNs/FCM accepted the handoff. Neither says the user saw it.

Run a worker: every 15 minutes, take tickets older than 15 minutes without a receipt, batch up to 1,000 IDs, `POST https://exp.host/--/api/v2/push/getReceipts`, and act on each.

| Error | Where | Action |
|---|---|---|
| `DeviceNotRegistered` | Ticket and receipt | Set `disabled_at` on that token immediately. Never send to it again. Apple and Google decide when a device counts as unregistered, on their own schedule — you cannot reproduce this by uninstalling and sending a minute later |
| `MessageTooBig` | Receipt | Payload over 4096 bytes. Trim `data`; it is almost always `data` |
| `MessageRateExceeded` | Receipt | Too many to one device. Back off exponentially for that token |
| `MismatchSenderId` | Receipt | FCM service account key and `google-services.json` come from different Firebase projects. See `setup.md` |
| `InvalidCredentials` | Receipt | Key revoked or missing. Android: re-upload the service account key. iOS: regenerate the push key with `eas credentials`; an `InvalidProviderToken` detail means regenerate the provisioning profile and rebuild too |
| `TOO_MANY_REQUESTS` | Whole request | Over 600/sec/project. Throttle; the Node SDK does this |
| `PUSH_TOO_MANY_NOTIFICATIONS` | Whole request | >100 messages in one request |
| `PUSH_TOO_MANY_RECEIPTS` | Whole request | >1000 ticket IDs in one receipt request |
| `PUSH_TOO_MANY_EXPERIENCE_IDS` | Whole request | Tokens from two Expo projects batched together. Partition by project before chunking |
| HTTP 429 / 5xx | Whole request | Transient. Exponential backoff with jitter |
| HTTP 400 | Whole request | Malformed payload. Do not retry — fix it |

A missing receipt after 15 minutes usually means an Expo-side problem, not a device problem. Log it; do not disable the token.

## Scheduling patterns

**Server-side, database-backed** — use for anything conditional on state the server owns.

```sql
create table scheduled_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  kind text not null,                       -- 'trial_reminder' | 'streak' | 'winback'
  send_at timestamptz not null,
  payload jsonb not null,
  dedupe_key text unique,                   -- e.g. 'trial_reminder:<user>:<period_end>'
  status text not null default 'pending',   -- pending | sent | cancelled | skipped
  sent_at timestamptz
);
create index on scheduled_notifications (send_at) where status = 'pending';
```

- **Trial-ending reminder.** RevenueCat emits no "trial about to end" event. On the `INITIAL_PURCHASE` webhook, read the period end and insert a row at `expiry − 24h` with a `dedupe_key`. Re-check at send time and mark `skipped` if the subscription already converted, cancelled or entered billing retry. `payments-paywalls` owns the webhook — read state from your own entitlements table, not a cached copy in the payload.
- **Streak reminder.** Compute the cohort at send time from activity, never at schedule time. A row written yesterday for a user who has already logged today damages trust.
- **Re-engagement.** A query, not a stored row: users whose `last_seen_at` crosses a boundary, excluding anyone who disabled the category, hit a frequency cap, or is inside quiet hours in their own `timezone`.

Idempotency is the whole game: unique `dedupe_key`, guarded `status` transitions, and a worker claiming rows with `for update skip locked`. A retried job that re-sends is worse than one that never sends.

**Local, client-scheduled** — the right answer when the trigger is a time the user chose and the content needs no server state.

```ts
await Notifications.scheduleNotificationAsync({
  content: { title: 'Time to log lunch', data: { url: '/log' } },
  trigger: { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour: 12, minute: 30 },
});
```

Cheaper, works offline, needs no token or permission round trip to your server, and correct for daily reminders and timers. Limits: it dies on reinstall, it does not follow the user across devices, you cannot cancel or change copy remotely, and Doze shifts its timing on Android. Cancel by identifier with `cancelScheduledNotificationAsync`, and reconcile the full set with `getAllScheduledNotificationsAsync` on launch rather than blindly re-scheduling — duplicates are the usual bug.

## Deep linking with expo-router

```tsx
// app/_layout.tsx
const ALLOWED = [/^\/log$/, /^\/settings\/subscription$/, /^\/streak\/\d+$/];

function useNotificationRouting() {
  useEffect(() => {
    const go = (n: Notifications.Notification) => {
      const url = n.request.content.data?.url;
      if (typeof url !== 'string') return;
      if (!ALLOWED.some(r => r.test(url))) return;   // untrusted input
      router.push(url);
    };
    const last = Notifications.getLastNotificationResponse();   // cold start
    if (last?.notification) { go(last.notification); Notifications.clearLastNotificationResponse(); }
    const sub = Notifications.addNotificationResponseReceivedListener(r => go(r.notification)); // warm
    return () => sub.remove();
  }, []);
}
```

- **Cold start and warm are different code paths.** `getLastNotificationResponse()` covers the launch-from-notification case; the listener covers taps while the app is alive. Handle both or terminated-state taps land on the home screen. Register the listener as early as possible — module scope on iOS — because a listener attached inside a screen misses the launch response entirely. The synchronous `getLastNotificationResponse` / `clearLastNotificationResponse` are current; the `...Async` variants are the deprecated ones. *(The published SDK reference labels the deprecation on the synchronous entries with a self-referential note — [UNVERIFIED] docs bug; the CHANGELOG and the Expo Router example both use the synchronous form.)*
- **Clear the last response after routing**, or a state change re-runs the effect and navigates again.
- **Validate before routing.** Allow-list, never `router.push(data.url)` on raw input.
- Check `response.actionIdentifier === Notifications.DEFAULT_ACTION_IDENTIFIER` to distinguish a body tap from an action-button tap when a category has actions.
- Foreground presentation: through **SDK 57** a notification arriving in the foreground is not shown unless `setNotificationHandler` says so, and a handler that does not answer within 3 seconds drops it. From **SDK 58** the default flips to shown ([receiving notifications](https://docs.expo.dev/push-notifications/receiving-notifications/)). Set the handler explicitly so the upgrade does not change behaviour under you.

## Rate limits, at a glance

| Limit | Value |
|---|---|
| Notifications per second per project | 600 |
| Messages per send request | 100 |
| Ticket IDs per receipt request | 1,000 |
| Total payload | 4,096 bytes |
| Receipt availability | ~15 min after send, purged at 24 h |
| Cost | Free — Expo charges nothing for push volume |

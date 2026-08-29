---
name: push-engagement
description: >
  Wire push notifications end to end on an Expo app — credentials, token storage, the send path,
  receipts, server-side scheduling, deep linking and the content rules that decide whether the channel
  survives. Use when adding push notifications, sending a reminder, building a trial ending reminder or
  re-engagement campaign, deciding between a local scheduled notification and a server-sent push,
  setting up an APNs key or FCM service account, deep linking
  from a notification into a screen, cleaning up dead tokens, or when someone says notifications aren't
  arriving, arrive late on Android, work in development but not in TestFlight, or open the wrong screen.
---

# Push and engagement

Push is the only channel that reaches a user who is not thinking about your app. It is also the only
one they can permanently revoke with one tap. Build it as a system with a token table, a job runner
and a preference centre — not as a `fetch` call bolted onto a button.

Three skills already depend on this one: `onboarding-flow` calls the trial-reminder push one of the
highest-leverage things in the app, `aso-growth` builds retention on it, `payments-paywalls` wants a
reminder before a trial converts. All three assume the wiring below exists.

## Decide the transport first, once

**Use the Expo push service.** It is free with no volume charge, takes an `ExpoPushToken` and hides
the APNs/FCM split, and it is the only option that keeps one code path for both platforms. Its limits
are 600 notifications/second/project, 100 messages per request, 4KiB total payload, and **no SLA**.
For a consumer app under a million sends a month that trade is correct.

Go direct to APNs/FCM only for the things Expo cannot express: Live Activity content updates (those
use a per-activity APNs token, not an Expo token), critical alerts, or an FCM feature with no field in
Expo's message format. You can mix — `getDevicePushTokenAsync()` returns the native token alongside
the Expo one. Do not migrate wholesale to "get control" you will not use.

Buy a managed platform (OneSignal, Customer.io, Braze) when you need marketer-editable campaigns,
journey builders and send-time optimisation more than you need a small bill. Roughly: OneSignal's free
tier covers unlimited mobile push, and its Growth plan starts near $19/mo plus ~$0.012 per monthly
active user — so 50k MAU is ~$620/mo. Re-verify on the vendor page; `cost-control` owns the method.

## The setup that actually breaks

Credentials, always. `references/setup.md` has both platforms end to end with the symptom each mistake
produces. The four that catch everyone:

- **Push does not work in Expo Go.** Remote push throws on Android from SDK 53 and is unavailable on
  iOS. Every test needs a development build. Local notifications still work in Expo Go, which is why
  people wrongly conclude their setup is fine.
- **On Android you must create a notification channel before requesting permission or a token.** The
  Android 13+ permission prompt will not appear until a channel exists, and a push sent to a
  `channelId` the device has never seen is silently dropped — delivered, never displayed.
- **The APNs key is account-wide, not app-scoped.** Two per Apple Developer account, it never expires,
  and revoking it kills push for every app using it. EAS generates and stores it for you; let it.
- **iOS dev builds talk to APNs sandbox, TestFlight and production talk to APNs production.** Tokens
  from one are invalid on the other. "Works on my device, silent in TestFlight" is nearly always this.

## Tokens are the data model

One row per install, not per user. A user has several devices; a device may be signed out, signed into
another account, or reinstalled. Store `(token, user_id, platform, device_id, app_version, last_seen_at,
disabled_at)` with a unique index on the token, and re-register on every cold start — tokens rotate,
and `addPushTokenListener` fires when one rotates mid-session.

Then **actually delete dead tokens**. Every send returns a ticket; every ticket ID resolves to a
receipt about 15 minutes later; a receipt with `details.error === 'DeviceNotRegistered'` means stop
sending to that token forever. Skipping the receipt job is the standard failure: the list looks
healthy, delivery quietly rots, and nothing in the dashboard says so. `references/sending.md` has the
schema, the send path, the receipt worker and the full error table.

## Server-side jobs, not client-side hope

The rule: **if the server owns the fact, the server owns the notification.**

A trial-ending reminder is server-side. RevenueCat has no "trial about to end" webhook — on
`INITIAL_PURCHASE` you read the expiry, write a row into a `scheduled_notifications` table, and a
worker sends it 24 hours out, cancelling if the subscription already converted or cancelled. A
client-scheduled version dies when the user reinstalls, changes timezone or never reopens the app,
which is precisely the user you are trying to reach. Re-engagement and any push that depends on other
users' behaviour are the same shape.

A local scheduled notification is the *better* answer when the trigger is a time the user themselves
chose and the content needs no server state — the daily reminder at 8am, a timer, a streak nudge based
on data already on the device. It fires with no network, costs nothing, and needs no token. Use it,
and note that on Android its timing is subject to Doze; it is a reminder, not an alarm.

## Deep link every notification

A notification that opens the home screen wastes the tap. Put a route in `data.url`, and handle both
paths: `getLastNotificationResponse()` at startup for the cold launch, and
`addNotificationResponseReceivedListener` for the warm one. Register the listener at module scope, not
inside a screen, or the cold-start case is lost before React mounts.

**Validate the payload before routing.** Allow-list the route against known patterns and reject
anything else. A push payload is untrusted input; `router.push(data.url)` on an unvalidated string is
a navigation-injection bug.

## Permission, platform floors, and the rules

**`onboarding-flow` owns permission priming** — the soft ask, the timing, the re-ask path, provisional
authorisation. Do not re-decide it here. What this skill adds: request the token only after the
permission resolves, treat iOS `PROVISIONAL` as granted-for-delivery (check `ios.status`, not the root
`status`), and remember badge is an iOS-only field in Expo's message format.

Android needs channels per notification *type*, not per app — `reminders`, `social`, `product` — so a
user can mute one instead of all. Channel settings are immutable after creation; only name and
description can change, so pick importance carefully the first time. iOS uses `interruptionLevel`:
`passive` for marketing, `active` by default, `time-sensitive` to break through Focus, `critical` only
with an Apple-approved entitlement you will not get.

**Store and legal constraints are hard limits, not guidance.** Apple 4.5.4: push may not be required
for the app to function, must not carry sensitive data, and may not be used for promotion or marketing
without explicit in-app opt-in *and* an in-app opt-out. Apple 5.1.2(i) and Play both forbid gating
functionality, content or rewards on enabling notifications. In the EU, the OS prompt alone is not
valid consent for marketing sends. `store-submission` has the review detail; `references/content.md`
has the preference-centre design that satisfies all of it.

## Measure it or delete it

Emit `push_token_registered`, `push_sent`, `push_delivered`, `push_opened`,
`notification_permission_changed` and `notification_preference_changed`. The three campaign events —
`push_sent`, `push_delivered`, `push_opened` — all carry `campaign_id` and `notification_type`, so the
send→open funnel breaks down without re-instrumenting. The other three are not campaign-scoped and
must not carry them: `push_token_registered` describes a device, and the two `*_changed` events
describe a state transition that may happen in Settings with no campaign involved.
`observability-analytics` owns the taxonomy, the property lists and the cardinality rules — take the
names from there rather than inventing a second convention.

Know what you cannot see: **sent ≠ delivered ≠ displayed ≠ opened.** A receipt says APNs/FCM accepted
the handoff, nothing more. You cannot observe display at all on either platform. The number that
matters is not open rate; it is retained revenue and 30-day retention for the notified cohort against
a held-out control, because the way to raise open rate is to send more, and the way to raise it a lot
is to send more than anyone wants.

## Reference files

- `references/setup.md` — packages, config, credentials both platforms, dev vs TestFlight vs production, symptom table
- `references/sending.md` — token schema, send path, receipts and `DeviceNotRegistered`, scheduling, deep linking, rate limits
- `references/content.md` — cadence, timing, segmentation, copy patterns, preference centre, store and legal constraints, measurement

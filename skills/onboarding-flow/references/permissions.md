# Permission Priming

Time-sensitive: platform permission behaviour (provisional push, ATT, Android 13+ POST_NOTIFICATIONS, photo-picker limited access) changes with OS releases, and store policy on permission gating is revised regularly. Verify against current Apple/Google documentation before shipping; the opt-in figures below are vendor-reported and dated.

## The one-shot rule

The OS permission dialog can be shown **once**. Dismiss it or deny it and the app can never present it again — recovery is only via a trip to system Settings, which almost nobody makes. Treat every OS prompt as a single, expensive, irreversible request.

Therefore: **never call the permission API directly from a screen the user did not ask for.** Every OS prompt is preceded by an in-app soft ask that you control, can A/B test, can localise, and can show again.

```
soft ask (your UI, unlimited retries)
   ├── "Not now"  → no OS prompt fired. Permission still available forever. Re-ask later.
   └── "Enable"   → fire OS prompt
                      ├── granted → done
                      └── denied  → permanently lost; only Settings deep-link remains
```

Reported lift: apps using pre-permission priming report **2–3× higher opt-in rates** than firing the cold system prompt; benchmark opt-in ~54% on iOS and ~85% on Android ([Plotline](https://www.plotline.so/blog/how-to-improve-push-notification-opt-in-rates)). **[UNVERIFIED — vendor-reported aggregate with no published methodology. The direction is well established across sources; treat the multiple as indicative, not a target.]**

## Timing rules

1. **Ask after the value is visible, not before.** The soft ask must be able to name a concrete benefit the user has already seen. Cal AI asks for notifications right after the personalised plan exists, framed as "reminders to log, streak alerts, progress check-ins" — the plan, not the capability, is the subject of the sentence ([Cal AI teardown](https://tasu.ai/library/cal-ai)).
2. **One permission per screen**, never a batched "we need these 4 things".
3. **Ask at the moment of need where one exists.** Camera at the first scan, photos at the first upload. A just-in-time ask needs less priming than a pre-emptive one because the context is self-evident.
4. **Notifications are the exception** — they have no natural moment of need, so they go in onboarding, **after the reveal screen and before the paywall**. The reason, so the rule survives editing: the soft ask must point at something concrete the user has already been shown ("we'll remind you at 8am about *this* plan"), and before the reveal there is nothing to point at. `sequence.md` orders the flow the same way; if you move the reveal, the soft ask moves with it.
5. **Treat a soft-ask "no" as "not yet".** Duolingo asks during onboarding, and asks again after the user has a streak and several completed lessons — by then the value of a reminder is obvious ([Duolingo teardown](https://tasu.ai/library/duolingo)). Rate-limit: no more than one re-ask per week, max three lifetime, and never immediately after a decline.
6. **Never ask on first launch, cold.** It is the lowest-information moment for the user and burns the one prompt.

## Copy templates

Structure every soft ask as: **what you'll get → what we'll send/use → the ask.** Name the benefit in the user's terms, name the frequency or scope to bound the anxiety, and make "Not now" a real, visible, same-weight option (not greyed, not tiny — see the dark-pattern list in `experiments.md`).

**Notifications**
> **Stay on track**
> We'll send a daily reminder at the time you chose, and a nudge if your streak is about to break. Nothing else.
> `[Turn on reminders]`  `[Not now]`

**Camera**
> **Point and log**
> We use the camera to identify your meal — photos are analysed on-device and never posted anywhere.
> `[Allow camera]`  `[Enter manually]`

Give camera and microphone soft asks a manual fallback in the secondary button. A user who declines but has a path forward stays; a dead end churns.

**Photos**
> **Add from your library**
> Pick the photos you want to use. You can choose specific photos instead of granting access to everything.
> `[Choose photos]`  `[Not now]`

On iOS prefer the limited-access photo picker (`PHPickerViewController` / `expo-image-picker` without full-library permission) — it needs no permission at all for selection. Only request full library access if you genuinely need background scanning.

**Location**
> **Local results**
> We use your location to show what's near you right now. We only check while you have the app open.
> `[Allow while using]`  `[Enter a city instead]`

Never request "Always" on the first ask. Request "While Using" first; escalate later, in context, and only if a background feature is genuinely used. An early "Always" ask is a common review rejection and a trust breaker.

**Health (HealthKit / Health Connect)**
> **Use your existing data**
> Connect Health to pull in steps and weight so you don't have to enter them twice. We read only those two, and write nothing back.
> `[Connect Health]`  `[I'll enter manually]`

Name each data type you read and each you write. Apple requires purpose strings per type and reviewers check them; HealthKit denial is also silent (the app cannot tell read-denied from no-data), so build the manual path regardless.

**Contacts**
> **Find people you know**
> We'll check which of your contacts already use [App]. We don't message anyone, and we don't upload your contacts.
> `[Find friends]`  `[Skip]`

Only make this claim if it is true. Contacts is the highest-suspicion permission; if you do upload, say so plainly. Never auto-invite.

Localise every one of these (namespace `onboarding` or `permissions`), and remember the OS purpose strings (`NSCameraUsageDescription` et al.) are localised separately via `InfoPlist.strings`, not by your JS catalogue.

## iOS provisional authorisation

`UNAuthorizationOptions.provisional` registers for notifications **without any prompt**. Notifications arrive silently in Notification Center (no banner, no sound) with inline "Keep" / "Turn Off" controls the user acts on after seeing real content.

Use it when: your notifications are genuinely valuable and self-explanatory on arrival, and you would rather earn the opt-in with a real message than a promise. It converts the decision from "will this be useful?" to "was this useful?".

Do not use it when: notifications are time-critical (no banner means no attention), or when your volume is high enough that silent delivery reads as spam and gets "Turn Off". Provisional is not a way to skip the design work; it is a different bet.

You can escalate from provisional to full authorisation later with a normal prompt — that prompt is still one-shot, so prime it the same way.

## Android specifics

- Android 13+ requires runtime `POST_NOTIFICATIONS`; below 13 notifications are granted at install. Same soft-ask discipline applies on 13+.
- Android permission dialogs allow a second ask; a second denial sets "don't ask again" permanently. `shouldShowRequestPermissionRationale()` tells you which state you are in — use it to decide between re-prompting and deep-linking to Settings.
- Android opt-in rates run far higher than iOS (~85% vs ~54%), so the cost of a mistimed ask is lower — but the ceiling is also why an unprimed ask looks fine in Android data and quietly destroys iOS revenue. Segment permission metrics by platform.

## The Settings recovery path

Once the OS prompt is denied, the only route is Settings. Show this path contextually — at the moment the missing permission blocks something — never as a nag.

```ts
import { Linking, Platform } from 'react-native';
Linking.openSettings(); // both platforms; lands on the app's settings page
```

> **Reminders are off**
> Turn on notifications in Settings and we'll nudge you at 8am, like you asked.
> `[Open Settings]`  `[Not now]`

Reference the specific thing they set up. "Enable notifications" is generic; "we'll nudge you at 8am, like you asked" recalls the commitment they made in onboarding.

After sending the user to Settings, re-check permission state on the next foreground (`AppState` change) and update the UI silently. Do not show a "did it work?" screen.

## Store rules that constrain gating

- **Apple 5.1.1(iv):** you may not require access to a permission that is not directly relevant to core functionality, and the app must remain usable if the user declines. A hard block behind a declined permission is a rejection risk. Every permission needs a fallback path or a clearly degraded-but-functional mode.
- **Purpose strings are mandatory and reviewed.** A vague `NSCameraUsageDescription` ("for app features") gets rejected. State the specific use.
- **Google Play** requires permissions be limited to what the declared functionality needs; sensitive permissions (location background, contacts, SMS) require an in-console declaration and often a video walkthrough. Background location in particular triggers a review process with real rejection rates.
- Neither store permits conditioning app functionality on a *tracking* consent (ATT) — you may not withhold features from users who decline ATT, nor incentivise granting it.

**ATT specifically:** prime it, but keep the soft ask honest and short, place it *after* the user has value (not on launch), and accept that a large share will decline. Never imply the app breaks without it. Store your own analytics identity independently of IDFA so a decline does not blind your funnel.

## Events to emit

Around every permission, emit four events. Without all four you cannot tell a copy problem from a timing problem. These names and properties are defined in `observability-analytics/references/event-spec.md`, which owns the vocabulary — use them exactly as written there.

```ts
track('permission_softask_shown',    { permission, placement, variant });
track('permission_softask_answered', { permission, accepted, placement, variant });
track('permission_prompt_requested', { permission, placement, trigger });  // only if accepted === true
track('permission_prompt_answered',  { permission, result, placement, variant });
```

`permission` is a fixed enum (`'notifications' | 'camera' | 'photos' | 'location' | 'health' | 'contacts' | 'tracking'`) — one event reused N times, never `camera_permission_viewed` as its own name, or adding a permission rewrites your history.

`accepted` is a boolean: `false` is the defer/"not now" path and means the OS prompt is **not** shown. `result` is `'granted' | 'denied' | 'provisional' | 'limited' | 'undetermined'` — `limited` matters for photos and `provisional` for notifications, so do not collapse them to a boolean. `placement` is required on all four; without it you cannot compare the same permission asked in onboarding versus at a feature gate, which is the main thing you will want to know.

Derived metrics to watch:
- **Soft-ask accept rate** — a copy/timing problem lives here.
- **OS grant rate given soft-ask accept** — should be high (70%+); if it is not, the soft ask is over-promising and users are correcting at the real dialog.
- **End-to-end opt-in** = accept rate × grant rate. This is the number to optimise, and it is what a re-ask path improves without touching either component.
- Segment all three by platform, locale and onboarding `variant`. Also log `permission_settings_opened {permission, placement}` and pair it with the subsequent `notification_permission_changed` on foreground to measure recovery, which is usually in the low single digits and worth knowing before you invest in that flow.

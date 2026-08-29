# Push Content, Cadence and Measurement

Verified August 2026. Time-sensitive: every benchmark here is vendor-reported and re-cut annually; store policy text (Apple 4.5.4, 5.1.2(i); Google Play notification and ads policies) is revised without notice; EU ePrivacy analysis of push is contested and unsettled. Re-read the primary sources before quoting a number to anyone or shipping a marketing send in the EU.

## What the evidence actually supports

| Claim | Figure | Source and caveat |
|---|---|---|
| Opt-in rates are converging across platforms | Android and iOS at "near parity" following universal Android 13+ adoption | [Airship 2026 benchmarks](https://www.airship.com/blog/your-guide-to-airships-mobile-app-push-notification-benchmarks-for-2026/), 681bn notifications, 3bn users, 15 verticals. Headline figures sit behind a form — get the report rather than quoting the older ~51% iOS / ~81% Android split, which `aso-growth` correctly flags as 2021 data |
| Priming lifts opt-in | 2–3× over a cold prompt | Widely reported, no published methodology. [UNVERIFIED] as a multiple; the direction is consistent across every source |
| Push-enabled users engage more | "lifts north of 80%" | [OneSignal 2026](https://onesignal.com/blog/onesignal-guide-push-notification-best-practices-2026/). [UNVERIFIED] — heavily selection-confounded. Users who opt in were already more engaged; treat as correlation |
| Behavioural personalisation beats merge fields | One case study: CTR <1% → 12%; a quest-based campaign +250% engagement | OneSignal 2026, single-customer case study. Directionally useful, not a forecast |
| Frequency has a ceiling | "more than a few messages per week starts to erode trust" | OneSignal 2026 |
| Volume spread is enormous within verticals | 57.3pp spread on Android, 49.6pp on iOS in food & drink | Airship 2026 — meaning: category benchmarks tell you almost nothing about *your* app |

Honest summary: personalisation, timing and relevance are supported; the multipliers are not. Treat every row above as a hypothesis and optimise against your own held-out control.

## Cadence

Set a global frequency cap in code, not in a doc, and enforce it in the send path so no campaign can bypass it.

| Category | Cap | Notes |
|---|---|---|
| Transactional (something happened to *their* data) | Uncapped | A reply, a completed export, a payment failure. Never counted against the cap |
| Reminder the user configured | Their chosen schedule | One per day maximum, at their time, cancellable in-app |
| Lifecycle (trial ending, streak at risk, winback) | 1 per user per 72 h | Deduped by `kind` |
| Marketing / product news | 1 per week, opt-in only | Requires explicit consent — see the legal section |

Global: **no more than one non-transactional notification per user per day, four per week.** Quiet hours 21:00–08:00 in the user's own timezone, which is why `push_tokens.timezone` exists in the schema (`sending.md`). A notification that wakes someone is not recovered by a good open rate.

## Timing

- **Send in the user's local time**, computed from the stored IANA timezone, not the server's. A campaign fired at "9am" server-side lands at 2am for a third of an international audience.
- **Anchor to behaviour, not the clock.** The best send time is the user's own historical active hour; the second best is the hour after the action the notification is about. Blanket-scheduled sends are the ones frequency caps exist to survive.
- **Day zero is the window that matters.** Around 55% of three-day-trial cancellations happen on day zero and 84% by day one (`onboarding-flow`, citing RevenueCat 2026), so the trial-value push belongs inside the first 24 hours, not at hour 60. `payments-paywalls` says the same.
- **The trial-ending reminder goes ~24 hours before conversion.** Earlier and it prompts a cancellation the user had not been considering; later and it arrives after the charge, which produces a refund and a one-star review instead.

## Segmentation

Three axes carry nearly all the value. Anything beyond them is usually a proxy for one of them.

1. **Lifecycle stage** — anonymous / activated / trialling / subscribed / lapsed. Lapsed users need a *lower* cap, not a higher one.
2. **Engagement recency** — active this week / dormant 7–30 days / dormant 30+. Past 60 days the honest answer is to stop sending, not escalate.
3. **Declared intent** — the goal chosen in onboarding. `onboarding-flow` captures it; echoing it back verbatim is the cheapest personalisation with the highest perceived fidelity.

Never segment on anything you could not explain to the user if they asked. That test also keeps you inside GDPR's transparency requirements.

## Copy patterns

Structure: **specific subject → concrete stake → one action.** Title ≤ 50 characters (the hook), body 14–25 words with the payload first, because both platforms truncate ([OneSignal 2026](https://onesignal.com/blog/onesignal-guide-push-notification-best-practices-2026/)). Numbers beat adjectives. No all-caps, no more than one emoji, and never an emoji doing the work of a word.

| Type | Bad | Good | Why |
|---|---|---|---|
| Trial ending | "Your trial is ending soon!" | "Trial ends tomorrow — you'll be charged £29.99/yr on 12 Sep. Cancel anytime." | Names the amount and date. Honesty here reduces refunds and chargebacks more than it reduces conversions |
| Streak at risk | "Don't lose your streak!! 🔥🔥" | "Your 14-day streak ends at midnight. One log keeps it." | States the number and the exact action. No loss-framed shouting |
| Re-engagement | "We miss you! Come back 😢" | "Your December summary is ready — 42 workouts, 3 personal bests." | Points at something that exists and is theirs. Guilt is not a value proposition |
| Reminder | "Reminder" | "8am check-in: how did you sleep?" | Echoes the schedule they set, in the words they set it in |
| Social | "You have new activity" | "Sam replied to your note about the Berlin trip." | Names the person and the object |

Localise every string through the i18n catalogue with ICU plurals — `localization-foundation` notes push copy as a commonly-missed surface. Send in the token's stored `locale`, not the account's default.

Never ship: fake urgency, invented countdowns, fabricated social proof ("3 people are looking at this"), confirmshaming, or anything that reads as a system message. `onboarding-flow` lists the line you do not cross; it applies identically here, and Google Play's [Unauthorized Use or Imitation of System Functionality](https://support.google.com/googleplay/android-developer/answer/9969861) policy makes the system-message impersonation a removal risk rather than a taste question.

## Preference centre and opt-out

Build it before the second notification type ships. It is the single highest-leverage retention feature in this skill: a user who can mute one category will not mute all of them at OS level, and an OS-level mute is unrecoverable without a trip to Settings.

Requirements:

- **One toggle per category**, matching the Android channels exactly, so the in-app switch and the system switch describe the same thing. Minimum set: Reminders, Activity, Trial and billing, News and offers.
- **Marketing off by default** — the only category that legally requires opt-in.
- **A quiet-hours control and a daily-reminder time picker.**
- **Read the OS state and show it.** If notifications are off at OS level, say so and offer `Linking.openSettings()` rather than toggles that do nothing.
- **Enforce server-side.** The preference is a row checked in the send path. A client-side filter still delivers the notification.
- **One `canSend(userId, category)` function**, called by every job.

Log preference changes as events. A spike in mutes after a campaign is the clearest signal that the campaign was wrong, and it arrives before the uninstalls do.

## Store and legal constraints

These are hard limits. Violating them costs you the app, not a metric.

**Apple 4.5.4**, verbatim from the [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/):

> Push Notifications must not be required for the app to function, and should not be used to send sensitive personal or confidential information. Push Notifications should not be used for promotions or direct marketing purposes unless customers have explicitly opted in to receive them via consent language displayed in your app's UI, and you provide a method in your app for a user to opt out from receiving such messages. Abuse of these services may result in revocation of your privileges.

**Apple 5.1.2(i)**: an app "may not require users to enable system functionalities (e.g. push notifications, location services, tracking) in order to access functionality, content, use the app, or receive monetary or other compensation, including but not limited to gift cards and codes." An "enable notifications to unlock" mechanic is a named rejection trigger — `store-submission` lists it in the 5.1.1 rejection patterns, and `onboarding-flow` designs around it.

**Google Play** prohibits notifications that mimic system functionality, ads delivered through system notifications, and notifications promoting other apps or third-party services. Notifications are permitted only in support of the app's own core features, and the sending app must be identifiable.

**EU ePrivacy.** The academic reading is that push notifications fall under Article 13(3) ("other forms of unsolicited communication") rather than the email rules, that writing to the device engages Article 5(3), and that **the OS permission prompt alone is not valid consent for marketing** because it names no purposes and offers no withdrawal path ([JIPITEC, 2025](https://www.jipitec.eu/jipitec/article/download/423/426/2178)). Practical consequence: your in-app marketing toggle *is* the consent record — store when it was granted, for what, and from where. Transactional and user-requested notifications sit under the strictly-necessary reading and do not need it. This area is unsettled; treat the strict interpretation as the design target, since it is also what Apple 4.5.4 requires.

Sensitive content: no health results, financial balances, message bodies from a private conversation, or anything you would not want on a lock screen in public. Use a neutral title plus "Open to view", and rely on iOS notification previews being user-configurable rather than assuming they are hidden.

## Measurement

Emit these through the `observability-analytics` taxonomy — `object_action`, snake case, past tense, properties carrying the variance. Add them to `docs/app/analytics-spec.md` and `lib/analytics/events.ts` before use.

```ts
track('push_token_registered', { platform, permission_status });
track('push_sent',       { notification_type, campaign_id, variant });   // server-side
track('push_delivered',  { notification_type, campaign_id });            // server-side, from receipt
track('push_opened',     { notification_type, campaign_id, action_id });  // client
track('notification_permission_changed', { from_status, to_status, source }); // OS-level grant changed
track('notification_preference_changed', { category, enabled, source });      // in-app category toggled
```

Names and properties are defined in `observability-analytics/references/event-spec.md`; use them exactly as written there.

`notification_type` and `campaign_id` are fixed enums carrying the campaign discriminators, and they appear on the four **campaign** events only — `push_sent`, `push_delivered`, `push_opened`, and `notification_type` on nothing else. Without them on all four, the send→open funnel cannot be broken down without re-instrumenting.

The other three events are not campaign-scoped and must not carry them: `push_token_registered` describes a device (`platform`, `permission_status`), and the two `*_changed` events describe a state transition (`from_status`/`to_status`/`source`, or `category`/`enabled`/`source`). Attaching a `campaign_id` to a permission change invents an attribution you did not measure — the user may have changed it in Settings days later, with no campaign involved. `category` on `notification_preference_changed` is the preference-centre category, which matches the Android channels exactly; it is deliberately not `notification_type`.

Never put the message body or a user ID in a property.

**Know the four states and what you can see:**

| State | Observable? | How |
|---|---|---|
| Sent | Yes | Your own send log plus the push ticket |
| Delivered to APNs/FCM | Yes, ~15 min later | Push receipt `status: 'ok'`. This is a **handoff** confirmation, not device delivery |
| Displayed on the device | **No** | Neither platform reports it. Anything claiming a "delivery rate" is inferring it |
| Opened | Yes | `addNotificationResponseReceivedListener` / `getLastNotificationResponse` |

Compute open rate against *sent*, state that denominator wherever the number appears, and never compare it to a vendor benchmark that used a different one.

**Attribution.** A direct open is a tap you observed. An *influenced* open is an app open within a window of a send with no tap — pick 60 minutes, write it down, keep it fixed, because changing the window silently rewrites your history. Attribute conversions only inside that window and only to direct opens; influenced-open revenue attribution always flatters the channel.

**The metric that decides whether push is working** is not open rate. It is 30-day retention and retained revenue for the notified cohort against a **held-out control that receives nothing**. Hold out 5% permanently. Without it you cannot tell a channel that creates engagement from one that merely intercepts it — and the intercepting kind looks excellent right up until the uninstalls arrive.

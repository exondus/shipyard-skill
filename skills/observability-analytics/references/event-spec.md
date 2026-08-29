# Minimum Viable Event Spec

Time-sensitive only in the vendor-integration details (RevenueCat/Stripe webhook payload shapes, PostHog identity APIs). The taxonomy rules below are conventions, not vendor requirements — they are marked where it matters.

**This file is the single source of the event vocabulary.** Other skills — `onboarding-flow`, `push-engagement`, `payments-paywalls` — *use* these names; they do not define them. Any skill needing an event this table lacks adds it **here first**, then to `lib/analytics/events.ts` and the project's `docs/app/analytics-spec.md`, in the same PR. An event emitted from a component without a row in this table is a bug, not a shortcut: it is untyped, undocumented, and invisible to whoever builds the funnel.

## Taxonomy rules

Enforce these mechanically; they are cheap to follow on day one and expensive to retrofit.

1. **`object_action`, snake_case, past tense.** `paywall_viewed`, `subscription_started`. Not `viewPaywall`, not `Paywall View`, not `PAYWALL_VIEWED`.
2. **Fixed vocabulary.** The event names are a closed set defined in one file. Adding one is a deliberate edit, not something a component does inline.
3. **Properties carry the variance, never the event name.** `paywall_viewed {variant: 'b'}` — never `paywall_b_viewed`. Name-encoded variants make every funnel a manual union and break the moment you add a third variant.
4. **One user action produces one event.** If a tap fires both `button_tapped` and `checkout_started`, your funnel double-counts and your conversion rates are wrong.
5. **No PII in properties.** No email, no name, no free text, no message bodies. These leak into a third party and into every CSV export.
6. **Bounded cardinality.** See the cardinality section.

Define the vocabulary in a typed module so the compiler enforces it:

```ts
// lib/analytics/events.ts
export const EVENTS = {
  APP_OPENED: 'app_opened',
  PAYWALL_VIEWED: 'paywall_viewed',
  // ...
} as const;

type EventName = (typeof EVENTS)[keyof typeof EVENTS];
export function track<E extends EventName>(name: E, props: PropsFor<E>) { /* ... */ }
```

Untyped `track('some_string', {...})` calls scattered through components are how taxonomies rot.

## The ~15 events

| Event | Property | Type / allowed values |
|---|---|---|
| `app_installed` | `platform` | `'ios' \| 'android'` |
| | `app_version` | string, semver |
| | `install_source` | `'organic' \| 'paid' \| 'referral' \| 'unknown'` |
| `app_opened` | `is_first_open` | boolean |
| | `days_since_install` | integer |
| | `session_number` | integer |
| `onboarding_started` | `variant` | string, fixed experiment variant set |
| `onboarding_step_viewed` | `step_index` | integer, 1..N |
| | `step_name` | enum, fixed set |
| | `variant` | string |
| `onboarding_step_completed` | `step_index` | integer, 1..N |
| | `step_name` | enum: `'intent' \| 'profile' \| 'goal' \| 'social_proof' \| 'permissions'` |
| | `variant` | string |
| `onboarding_reveal_viewed` | `variant` | string |
| | `seconds_to_reveal` | integer, from `onboarding_started` |
| | `reveal_type` | enum (`'plan' \| 'library' \| 'people' \| 'result'`) |
| `onboarding_completed` | `duration_seconds` | integer |
| | `steps_skipped` | integer |
| | `variant` | string |
| `permission_softask_shown` | `permission` | enum (`'notifications' \| 'contacts' \| 'location' \| 'camera' \| 'photos' \| 'health' \| 'tracking'`) |
| | `placement` | enum (`'onboarding_post_reveal'`, `'feature_gate'`, `'settings'`) |
| | `variant` | string |
| `permission_softask_answered` | `permission` | same enum |
| | `accepted` | boolean — `false` means the OS prompt is **not** shown |
| | `placement`, `variant` | as above |
| `permission_prompt_requested` | `permission` | same enum |
| | `placement` | enum |
| | `trigger` | enum, what caused the ask |
| `permission_prompt_answered` | `permission` | same enum |
| | `result` | enum: `'granted' \| 'denied' \| 'provisional' \| 'limited' \| 'undetermined'` |
| | `placement`, `variant` | as above |
| `permission_settings_opened` | `permission` | same enum |
| | `placement` | enum, where the re-ask path was offered |
| `signup_started` | `method` | `'apple' \| 'google' \| 'email'` |
| | `entry_point` | enum (`'onboarding'`, `'paywall'`, `'settings'`) |
| `signup_completed` | `method` | same enum |
| | `seconds_since_started` | integer |
| `activation_completed` | `time_to_activate_seconds` | integer |
| | `activation_path` | enum, how they got there |
| `paywall_viewed` | `placement` | enum (`'onboarding'`, `'feature_gate'`, `'settings'`) |
| | `variant` | string |
| | `offering_id` | string, low cardinality |
| | `trigger` | enum, what caused the show |
| `paywall_dismissed` | `placement` | enum |
| | `seconds_visible` | integer |
| | `variant` | string |
| `checkout_started` | `product_id` | string, fixed SKU set |
| | `price_band` | enum, bucketed (see below) |
| | `currency` | ISO 4217 |
| `subscription_started` | `product_id` | string |
| | `period` | `'monthly' \| 'annual' \| 'lifetime'` |
| | `is_trial` | boolean |
| | `revenue_usd` | number, normalised |
| `subscription_renewed` | `product_id`, `period` | as above |
| | `renewal_count` | integer |
| `subscription_cancelled` | `product_id` | string |
| | `days_active` | integer |
| | `cancel_reason` | enum where known, else `'unknown'` |
| `core_action_performed` | `feature` | enum, fixed set of feature names |
| | `count_today` | integer |
| `day7_retained` (derived) | `cohort_week` | date bucket, computed server-side |
| `push_token_registered` | `platform` | `'ios' \| 'android'` |
| | `permission_status` | enum, as `permission_prompt_answered.result` |
| `push_sent` *(server)* | `notification_type` | enum, fixed set (`'reminder'`, `'trial_ending'`, `'streak_risk'`, `'winback'`, `'activity'`) |
| | `campaign_id` | string, fixed low-cardinality set |
| | `variant` | string |
| `push_delivered` *(server)* | `notification_type`, `campaign_id` | as above |
| | `receipt_status` | enum (`'ok' \| 'error'`) — **handoff to APNs/FCM, not device display** |
| `push_opened` | `notification_type`, `campaign_id` | as above |
| | `action_id` | enum, which action button; `'default'` for the body tap |
| | `seconds_since_sent` | integer |
| `notification_permission_changed` | `from_status`, `to_status` | enum, as `permission_prompt_answered.result` |
| | `source` | enum (`'os' \| 'in_app'`) |
| `notification_preference_changed` | `category` | enum, matching the Android channels exactly |
| | `enabled` | boolean |
| | `source` | enum (`'in_app' \| 'os'`) |

**`activation_completed` is the one to get right.** It marks the single action that predicts retention for your product — the first note saved, first workout logged, first message sent. Everything upstream is onboarding funnel; everything downstream is engagement. If you cannot name it, the analytics spec is not finished.

`day7_retained` is derived from `app_opened` server-side or in a PostHog cohort, not emitted from the client. Clients cannot reliably know they are on day 7.

**Emit `onboarding_step_viewed` on every screen, not just `onboarding_step_completed`.** Viewed-minus-completed per `step_index` is what localises a drop-off to a specific screen; completions alone tell you people left without telling you where. One screen usually owns most of the loss.

**The permission pair exists because the OS prompt is one-shot.** `permission_softask_shown` / `permission_softask_answered` cover the in-app pre-ask; `permission_prompt_requested` / `permission_prompt_answered` cover the OS dialog. The OS prompt fires **only** when `permission_softask_answered.accepted = true`, so `permission_prompt_requested` should never exceed accepted soft-asks — if it does, some code path is calling the OS API directly and burning the one-shot prompt. The ratio you actually optimise is `permission_prompt_answered {result:'granted'}` over `permission_softask_shown`. `permission_settings_opened` covers the only recovery path once a permission is denied — pair it with the next `notification_permission_changed` to measure whether that flow is worth building at all.

**`push_delivered` means handoff, not display.** The push receipt confirms APNs/FCM accepted the payload; **neither platform reports whether a notification was displayed on the device**, so there is no `push_displayed` event and there cannot be one. Compute open rate against `push_sent` and state that denominator wherever the number appears. Any "delivery rate" is an inference.

**`notification_permission_changed` and `notification_preference_changed` are two events, not one** (an earlier draft of `push-engagement` had a single `push_disabled`). Two rather than one, because OS-level permission and in-app category preference are different states with different remedies, and because a single `*_disabled` event cannot record a **re-enable** — which is the signal that a preference centre is working.

## Cardinality rules

A property is high-cardinality if its distinct value count grows with users or time. These inflate storage cost, make breakdowns useless (thousands of rows of n=1) and are a common cause of a surprise PostHog bill.

| Bad property | Why | Bucketed replacement |
|---|---|---|
| `user_id: 'usr_8f2a...'` | Grows with users; already on the person | omit — it's the `distinct_id` |
| `price: 9.99` (raw, all currencies) | Unbounded across FX | `price_band: '5-10'` |
| `timestamp: '2026-08-29T14:03:11Z'` | Unbounded | omit — the event already has a timestamp |
| `url: '/item/abc123?ref=x'` | One value per item | `route: '/item/:id'` |
| `search_query: 'red running shoes'` | Free text, also PII risk | `query_length_band`, `result_count_band` |
| `cart_contents: [...]` | Unbounded array | `cart_item_count`, `cart_value_band` |
| `error_message: '...'` | Unbounded, belongs in Sentry | `error_code` enum |
| `screen_title: 'Hi, Dana!'` | Interpolated copy | `screen_name: 'home'` |

Rule of thumb [UNVERIFIED — a working convention, not a vendor-published threshold]: keep any breakdown property under ~50 distinct values. If it exceeds that, bucket it or move it to a person property.

## The funnel-discriminator rule

A funnel is answerable only if every step shares (a) the same `distinct_id` and (b) the **same discriminating property**. If `paywall_viewed` carries `variant` and `placement` but `subscription_started` does not, you can measure overall conversion and nothing else — not "did variant B convert better," which is the only question anyone asks. Retrofitting costs a full cycle of new data.

So: **propagate `variant`, `placement` and `offering_id` through every downstream step**, including server-emitted revenue events — carry them in the purchase context and attach them at conversion time.

Keep steps strictly ordered and non-overlapping. `onboarding_step_completed` with a `step_index` is one event used N times — correct. `step_2_completed` as its own name is not: adding a step renumbers your entire history.

## Revenue: server-side, from webhooks

**The payment platform is the source of truth for revenue; product analytics is the source of truth for behaviour.**

Client-emitted: `paywall_viewed`, `paywall_dismissed`, `checkout_started` — behavioural, and only the client knows them. Server-emitted from RevenueCat or Stripe webhooks: `subscription_started`, `subscription_renewed`, `subscription_cancelled`, plus refunds and billing-retry outcomes. Client-side purchase events are wrong four ways: they double-count on retry, miss renewals entirely (no app open required), miss refunds and chargebacks, and are trivially spoofed.

**The identity-linking requirement.** Server events must land on the same person as client events, or your funnel breaks exactly at the conversion step. Set the payment platform's user identifier to your PostHog `distinct_id` at login:

```ts
// at login, before any purchase is possible
await Purchases.logIn(user.id);      // RevenueCat appUserID
posthog.identify(user.id);           // same ID
```

Then in the webhook handler:

```ts
posthogServer.capture({
  distinctId: event.app_user_id,     // === PostHog distinct_id
  event: 'subscription_started',
  properties: {
    product_id: event.product_id,
    period: periodFrom(event),
    is_trial: event.period_type === 'TRIAL',
    revenue_usd: event.price_in_purchased_currency_usd,
    variant: storedVariantFor(event.app_user_id),   // funnel discriminator
  },
});
```

**Symptom of a broken link: paywall views look healthy, subscriptions appear in RevenueCat, and the PostHog funnel shows near-zero conversion** because the revenue events landed on anonymous or separate person records. Verify by checking that one test purchase appears on the same person as the paywall view before trusting any conversion number.

Reconcile monthly: total `revenue_usd` in analytics should be within a small margin of the payment platform's reported revenue. Divergence means dropped webhooks or identity splits, and it always grows.

## Copy-ready spec template

Copy **`assets/analytics-spec-template.md`** (in this skill) to `docs/app/analytics-spec.md` and fill it in. It carries the event table, the identity model, the client-vs-server emission split, the funnel definitions, the sampling and cost settings, and a decisions log.

That file is the project's instance of this vocabulary; this file is the vocabulary itself. Keep them in step — adding an event means editing both, plus `lib/analytics/events.ts`, in one PR.

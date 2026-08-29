# Analytics Spec — <app name>

Locked <date>. The event vocabulary is owned by the `observability-analytics` skill
(`references/event-spec.md`). This file is **this project's instance** of it.

Adding an event means editing the skill reference, this file, and `lib/analytics/events.ts`
in the same PR. An event emitted without a row here is a bug.

## Conventions

- Naming: `object_action`, snake_case, past tense.
- Variance lives in properties, never in the event name.
- One user action → one event.
- No PII. No unbounded-cardinality properties — see Cardinality.

## Activation definition

Write the aha in one sentence. The spec is not finished until this is filled in.

> The user has <X> and feels <Y>.

`activation_completed` fires when: <exact condition, in code terms>

Time-to-value target: <under N minutes, first session>

## Identity model

| Concern | Value |
|---|---|
| `distinct_id` | <server-issued user ID> |
| Set by | `posthog.identify(<id>)` at <where> |
| Anonymous phase | device ID from <screen 1 / app open>, merged on identify |
| RevenueCat `appUserID` | **same value as `distinct_id`** — set via `Purchases.logIn()` |
| Logout | `posthog.reset()` at <where> |
| Never used as identity | email, session ID, client-generated UUID |

Verify once before trusting any conversion number: make a test purchase and confirm the
paywall view and the webhook-emitted `subscription_started` land on the **same person**.

- [ ] Verified on <date> by <who>

## Events

`C` = client-emitted. `S` = server-emitted from a webhook or job — never from the client.

| Event | C/S | When it fires | Properties (type / allowed values) | Owner |
|---|---|---|---|---|
| `app_installed` | C | First launch | `platform`, `app_version`, `install_source` | |
| `app_opened` | C | Every foreground | `is_first_open`, `days_since_install`, `session_number` | |
| `onboarding_started` | C | | `variant` | |
| `onboarding_step_viewed` | C | Every screen | `step_index`, `step_name`, `variant` | |
| `onboarding_step_completed` | C | | `step_index`, `step_name`, `variant` | |
| `onboarding_reveal_viewed` | C | | `variant`, `seconds_to_reveal`, `reveal_type` | |
| `onboarding_completed` | C | | `duration_seconds`, `steps_skipped`, `variant` | |
| `permission_softask_shown` | C | In-app pre-ask | `permission`, `placement`, `variant` | |
| `permission_softask_answered` | C | | `permission`, `accepted`, `placement`, `variant` | |
| `permission_prompt_requested` | C | OS dialog shown | `permission`, `placement`, `trigger` | |
| `permission_prompt_answered` | C | | `permission`, `result`, `placement`, `variant` | |
| `signup_started` | C | | `method`, `entry_point` | |
| `signup_completed` | C | | `method`, `seconds_since_started` | |
| `activation_completed` | C | See above | `time_to_activate_seconds`, `activation_path` | |
| `paywall_viewed` | C | | `placement`, `variant`, `offering_id`, `trigger` | |
| `paywall_dismissed` | C | | `placement`, `seconds_visible`, `variant` | |
| `checkout_started` | C | | `product_id`, `price_band`, `currency` | |
| `subscription_started` | **S** | RevenueCat webhook | `product_id`, `period`, `is_trial`, `revenue_usd`, `variant` | |
| `subscription_renewed` | **S** | RevenueCat webhook | `product_id`, `period`, `renewal_count` | |
| `subscription_cancelled` | **S** | RevenueCat webhook | `product_id`, `days_active`, `cancel_reason` | |
| `core_action_performed` | C | | `feature`, `count_today` | |
| `day7_retained` | **S** | Derived, cohort | `cohort_week` | |
| `push_token_registered` | C | | `platform`, `permission_status` | |
| `push_sent` | **S** | | `notification_type`, `campaign_id`, `variant` | |
| `push_delivered` | **S** | Receipt, ~15 min | `notification_type`, `campaign_id`, `receipt_status` | |
| `push_opened` | C | | `notification_type`, `campaign_id`, `action_id`, `seconds_since_sent` | |
| `notification_permission_changed` | C | | `from_status`, `to_status`, `source` | |
| `notification_preference_changed` | C | | `category`, `enabled`, `source` | |

Delete rows this product does not have. Do not add a row without a matching entry in
`lib/analytics/events.ts`.

### Enum values used by this project

| Property | Allowed values |
|---|---|
| `step_name` | |
| `placement` | |
| `variant` | |
| `offering_id` | |
| `product_id` | |
| `feature` | |
| `notification_type` | |
| `campaign_id` | |
| `activation_path` | |
| `price_band` | |

## Server-emitted revenue

Payment platform = source of truth for **revenue**. Product analytics = source of truth for
**behaviour**. Never emit `subscription_*` from the client: it double-counts on retry, misses
renewals and refunds, and is spoofable.

| | |
|---|---|
| Webhook source | <RevenueCat / Stripe> |
| Handler path | <`apps/api/webhooks/revenuecat.ts`> |
| Signature verification | <how> |
| Idempotency key | <what> |
| Variant lookup | <how the funnel discriminator is attached at conversion> |
| Monthly reconciliation | analytics `revenue_usd` total vs platform revenue, ±<N>% |

- [ ] Reconciled on <date>, variance <N>%

## Funnel discriminators

`variant`, `placement` and `offering_id` propagate through **every** step of the onboarding
and paywall flows, including the server-emitted revenue events. A funnel whose last step
lacks the discriminator can answer overall conversion and nothing else.

## Funnels this project must answer

List the questions before building dashboards. Each must be answerable from the events above.

| # | Question | Steps | Breakdown property |
|---|---|---|---|
| 1 | Where do people drop out of onboarding? | `onboarding_started` → `onboarding_step_viewed`/`_completed` per index → `onboarding_completed` | `step_index`, `variant` |
| 2 | Does the reveal earn the permission? | `onboarding_reveal_viewed` → `permission_softask_shown` → `permission_prompt_answered{granted}` | `variant` |
| 3 | Which paywall variant converts? | `paywall_viewed` → `checkout_started` → `subscription_started` | `variant`, `placement` |
| 4 | Do activated users retain? | `activation_completed` → `day7_retained` | `activation_path` |
| 5 | Is push creating engagement or intercepting it? | `push_sent` → `push_opened` → retention vs **held-out control** | `notification_type` |
| 6 | <your question> | | |

Push open rate is computed against **`push_sent`**. Display is not observable on either
platform — there is no `push_displayed`. State the denominator wherever the number appears.

## Cardinality

Banned as event properties: user IDs, raw timestamps, full URLs, free text, search queries,
cart contents, error messages, interpolated copy. Bucket to a `*_band` or an enum.

| Raw value in this project | Bucketed replacement |
|---|---|
| | |

Keep any breakdown property under ~50 distinct values.

## Sampling and cost settings

Set these before launch, not after the first bill. See the `cost-control` skill.

| Setting | Where | Value |
|---|---|---|
| PostHog `captureTouches` | RN init | `false` |
| PostHog `captureScreens` | RN init | `true` |
| PostHog session replay | RN init | <off / sampled at N%> |
| PostHog billing limit — analytics | Billing settings | <$N or event cap> |
| PostHog billing limit — replay | Billing settings | <$N> |
| PostHog reverse proxy | `api_host` + `ui_host` | <proxy domain> / `https://us.posthog.com` |
| Local flag evaluation | server SDK | <on/off> |
| Sentry `tracesSampler` baseline | `Sentry.init` | `0.1` |
| Sentry `tracesSampler` critical flows | `Sentry.init` | `1.0` on <routes> |
| Sentry `replaysSessionSampleRate` | `Sentry.init` | `0.0` |
| Sentry `replaysOnErrorSampleRate` | `Sentry.init` | `1.0` |
| Sentry spike protection | project settings | on |
| Internal traffic filter | PostHog cohort | <how> |

## Privacy

- [ ] No PII in any event property
- [ ] Replay masking defaults left ON in both SDKs
- [ ] Sentry `sendDefaultPii: false` + `beforeSend` scrubbing
- [ ] Analytics vendors listed in the iOS Privacy Manifest and Play Data Safety form
- [ ] Account deletion removes data from analytics and crash reporting vendors

## Decisions log

| Date | Decision | Why | Consequence |
|---|---|---|---|
| | Activation defined as <X> | | Everything upstream is funnel, downstream is engagement |
| | | | |

## Changelog

| Date | Change | By |
|---|---|---|
| | Initial spec | |

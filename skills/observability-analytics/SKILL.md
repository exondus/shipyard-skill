---
name: observability-analytics
description: >
  Instrument an app so its failures and its funnels are both visible — Sentry for crashes, traces and
  release health, PostHog for product analytics, feature flags, experiments, session replay and
  surveys. Use when adding error tracking or analytics, designing the event taxonomy, wiring sourcemaps
  so stack traces resolve, setting up feature flags or an A/B test, deciding sampling rates, reconciling
  revenue events with product events, or when someone asks why a funnel cannot be answered, why stack
  traces are unreadable, or why the observability bill is high.
---

# Instrumentation

Two systems with two different jobs. Sentry answers "what broke, for whom, in which release".
PostHog answers "what did people do, and did the change help". Neither substitutes for the other, and
both are close to useless if the taxonomy is decided after the fact.

The rule that governs everything below: **instrument while building the thing, never afterwards.** A
funnel that was not instrumented as it was built cannot be diagnosed later, only rebuilt.

## Sentry

The setup is quick; the parts that fail are these.

**Sourcemaps for over-the-air updates.** Native release builds upload sourcemaps as part of the build.
OTA updates do not — they need a separate upload step after publishing. Skipping it is the number one
cause of unreadable production stack traces, and it fails silently: you only discover it when you need
it.

**Release and dist tagging, plus the OTA update identifiers**, so a broken JavaScript update can be
told apart from a broken binary. Alert on the update ID.

**Sampling.** Ship traces and profiles at a low rate and raise it selectively on the flows that matter
— checkout, paywall, sign-in — with a sampler function rather than a global rate. Session replay stays
error-triggered.

**Privacy.** Mobile replay masks all text, images and vectors by default. Never disable that globally;
unmask individual non-PII views. Turn off automatic PII collection and scrub in the send hook: user
email and IP, query strings, authorisation headers, breadcrumb payloads. High-cardinality URLs also
destroy span quota, so parameterise them.

**Alerts worth having**, and they are few: a new fatal issue in a release; a percentage-change
regression in crash-free rate against the previous release; a failure-rate alert on one named critical
transaction; and an alert scoped to a specific OTA update. Delete every "any new issue" rule — noisy
alerting trains people to ignore the channel, which is worse than no alerting.

**Quota.** The free tier is small, especially for replays, and one crash loop can burn a month of
error quota in hours. Filter known noise — network aborts, non-error rejections, injected WebView
scripts — enable spike protection, and rate-limit client-side.

## PostHog

**Leave touch autocapture off in production** — it is off by default, and turning it on is a decision
people make once and regret on the invoice. On mobile it produces a large multiple of the events you
want and cannot infer meaning from a tap on a label. Screen views and lifecycle events are worth
keeping. Instrument the things that matter explicitly.

**Identity.** Identify with a stable ID at login so the anonymous person merges into the identified
one. Never identify with an unstable ID and never identify twice with different ones — those cannot be
merged afterwards. Flags evaluated before identification see only anonymous properties, which is the
usual cause of a flag appearing to flip mid-session.

**Feature flags**: bootstrap the payload so the first render does not flicker, and evaluate locally on
the server so a flag check is not a network round trip per request.

**Experiments**: one primary metric, declared before launch, and make sure the exposure event fires
only when the variant actually renders — otherwise every denominator is wrong. Do not peek and stop.

**Replay and surveys** are useful and expensive; sample replay low and treat it as a diagnostic tool
for a specific question, not as always-on.

Reverse-proxy the ingestion endpoint to recover events lost to blockers, setting both the API host and
the UI host or the toolbar breaks.

## The taxonomy

Decide it once, write it in `docs/app/analytics-spec.md`, and treat it as an interface.

Rules: `object_action`, snake case, past tense. A fixed vocabulary of event names. **Properties carry
the variance, never the event name** — `paywall_viewed` with a `variant` property, never
`paywall_a_viewed`. No unbounded-cardinality properties: no user IDs, timestamps, free text, full URLs
or basket contents as properties; bucket them into bands. High cardinality is both the main analysis
problem and one of the main billing problems.

About fifteen events answer nearly every question a consumer app has: app opened, onboarding started,
each onboarding step viewed and completed, signup started and completed, **the activation event**,
paywall viewed and dismissed, checkout started, subscription started, renewed and cancelled, and the
core action performed. `references/event-spec.md` has the table with the properties for each.

The test of a good taxonomy is not coverage. It is that **every step in a funnel carries the same
discriminating property**, so the funnel can be broken down by variant, placement or cohort without
re-instrumenting anything.

## Revenue

The payment platform is the source of truth for money; product analytics is the source of truth for
behaviour. Send paywall views and checkout starts from the client, but **emit subscription started,
renewed and cancelled server-side from the payment webhooks**, keyed to the same identity — set the
payment provider's app user ID to your analytics distinct ID at login.

Client-side purchase events double-count, and they cannot see renewals, refunds or billing retries at
all. This is the most common reason an app's revenue dashboard disagrees with its bank balance.

## Reference files

- `references/sentry.md` — setup, sourcemaps including OTA, sampling, scrubbing, alert rules
- `references/posthog.md` — setup, identity, flags, experiments, replay, proxying, cost controls
- `references/event-spec.md` — the event vocabulary; the single source, extended here before elsewhere
- `assets/analytics-spec-template.md` — copy into `docs/app/analytics-spec.md` and fill it in

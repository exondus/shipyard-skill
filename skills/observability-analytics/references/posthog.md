# PostHog for Expo + Web

Time-sensitive: SDK option names, autocapture defaults and free-tier allowances change. Verify against [posthog.com/docs/libraries/react-native](https://posthog.com/docs/libraries/react-native) and [posthog.com/pricing](https://posthog.com/pricing) before relying on specifics.

## Install

**Expo:**
```bash
npx expo install posthog-react-native expo-file-system expo-application expo-device expo-localization
```

**Bare React Native:**
```bash
yarn add posthog-react-native @react-native-async-storage/async-storage react-native-device-info react-native-localize
```

The peer packages are not optional — they supply persistence, app version, device metadata and locale. Missing ones produce events with empty context rather than a crash, so the failure is silent.

**React Native Web / macOS:** do *not* use `expo-file-system`; use `@react-native-async-storage/async-storage` instead. Web and macOS targets are unsupported by the file-system backend.

**Web:** `posthog-js`, initialised once in a client component / provider.

```jsx
<PostHogProvider
  apiKey="<ph_project_token>"
  options={{ host: 'https://us.i.posthog.com' }}
  autocapture={{ captureTouches: false, captureScreens: true }}
>
  <App />
</PostHogProvider>
```

EU projects use `https://eu.i.posthog.com`. Getting the region wrong yields a silently accepted key with zero events arriving.

## Mobile autocapture: what it does and does not do

Captured automatically: `Application Opened`, `Application Became Active`, `Application Backgrounded`, `Application Installed`, `Application Updated`, `$screen` events, touch interactions and exceptions.

Defaults: **`captureTouches: false`, `captureScreens: true`.** Other options: `ignoreLabels`, `customLabelProp`, `maxElementsCaptured`.

What it does **not** do: infer meaning. Touch autocapture records that a component with some accessibility label was tapped. It cannot tell you a user purchased, activated, or completed onboarding. No amount of autocapture substitutes for explicit instrumentation of your funnel.

**Keep `captureTouches: false` in production.** Enabling it multiplies event volume by roughly 10–50× against a 1M/month free allowance, and produces events keyed on labels that change whenever someone edits copy — so your historical data breaks on every UI tweak. Turn it on temporarily during exploratory research, then turn it back off.

Keep `captureScreens: true`; screen views are low-volume and genuinely useful. Make sure screens have stable names (`expo-router` route names work well) rather than including IDs.

## Identity and merging

Anonymous events attach to a device-generated `distinct_id`. On login:

```js
posthog.identify(user.id, { email: user.email, plan: user.plan });
```

PostHog merges the anonymous person into the identified one, so pre-login behaviour is preserved in funnels.

Rules that prevent unrecoverable data damage:

- **Only ever identify with a stable, server-issued user ID.** Never an email (users change them), never a session ID, never a random UUID generated on the client.
- **Never call `identify()` twice with different IDs for the same person.** Identified-to-identified merges are not supported; you get two permanent person records that cannot be joined.
- Use `alias()` only to link a second known identifier to an existing person (cross-device, or linking a server-side ID).
- Call `posthog.reset()` on logout. Skipping it attributes the next user's events to the previous one — the symptom is impossible funnels where one person appears to sign up twice from the same device.

**The flag-before-identify bug.** Feature flags evaluated before `identify()` see only anonymous properties. If a flag targets `plan == 'pro'`, the anonymous evaluation returns the control variant, then the post-identify re-evaluation flips it. **Symptom: the UI changes underneath the user a second after launch, and experiment exposure counts exceed the identified population.** Fix by gating flag-dependent UI on identity being resolved, or by bootstrapping (below).

## Feature flags

Two mechanisms matter for production quality:

**Bootstrapping** kills the first-render flicker. Fetch flags server-side (or read a cached payload) and pass them into init so the first paint already has the right variant:

```js
posthog.init(key, {
  bootstrap: {
    distinctID: user.id,
    featureFlags: { 'new-paywall': 'variant-b' },
  },
});
```

Without it, every flag-gated component renders the default, then swaps — visible flicker, and a real conversion penalty on paywalls.

**Local evaluation** removes a network round-trip per flag check on the server. Initialise the server SDK with a personal API key so flag definitions are pulled periodically and evaluated in-process. Local evaluation only works for flags whose conditions use properties you pass in at call time — flags depending on cohort membership still hit the network.

Free tier includes **1M flag requests/month**; a server-rendered page checking five flags per request consumes that faster than you expect. Local evaluation is the main mitigation.

## Experiments

Define **one primary metric before launching.** PostHog reports Bayesian win probability with a credible interval; the failure mode is peeking daily and stopping the moment a variant looks ahead, which manufactures significance from noise.

**Exposure-event correctness is the rule that decides whether the result means anything.** The exposure event must fire when and only when the variant is actually *rendered to the user* — not when the flag is fetched, not on app boot, not in a component that mounts behind a route the user never reaches. Firing early inflates the denominator and dilutes a real effect toward zero; firing late (only for engaged users) inflates the numerator and manufactures one.

Practical check before trusting a readout: exposures per variant should be within a few percent of each other, and total exposures should be plausible against DAU. A large split imbalance means the flag is being evaluated somewhere it shouldn't be.

## Session replay on mobile

Enable with `enableSessionReplay: true`. React Native SDKs **always record in screenshot mode; this is not configurable** ([mobile replay docs](https://posthog.com/docs/session-replay/mobile)). Masking defaults are restrictive — automatic masking is applied — but verify masking behaviour on your own screens before enabling on a production build with real user data.

Replay is the single fastest way to exhaust the free tier: **5,000 recordings/month.** Sample it (10% or lower) rather than recording everything, and treat it as a research tool you enable for a week, not permanent infrastructure.

Performance: screenshot-mode capture costs CPU and bandwidth on low-end Android. If users report battery or jank complaints after enabling replay, disable it before investigating anything else.

## Surveys

In-app surveys are cheap signal — **1,500 responses/month free.** Keep them targeted: trigger on a feature flag or a specific event rather than showing to everyone, cap frequency, and never show one during onboarding or checkout. One question with fixed options beats free text, both for analysis and because free-text answers are unbounded-cardinality data you then have to scrub for PII.

## Reverse proxy

Ad blockers block known analytics domains; proxying through your own subdomain typically recovers **10–30% of events** ([proxy docs](https://posthog.com/docs/advanced/proxy)).

PostHog Cloud includes a **managed reverse proxy free** — create a CNAME to the generated proxy domain; status moves waiting → issuing → live in a few minutes. Self-hosted options include Next.js rewrites, Cloudflare Workers, CloudFront, Vercel and Netlify.

**Always set both hosts:**

```js
posthog.init(key, {
  api_host: 'https://ph.yourdomain.com',   // your proxy
  ui_host: 'https://us.posthog.com',       // PostHog's real domain
});
```

**Symptom of setting only `api_host`: the toolbar and replay links break**, opening dead URLs on your own domain.

## Cost control

Free tier, **per product per month**: 1M analytics events, 5k session recordings, 1M feature-flag requests, 1,500 survey responses, 100k error-tracking exceptions, 1M data-warehouse rows.

Teams blow the bill three ways, in this order:

1. **Touch autocapture left on** — the 10–50× event multiplier.
2. **Replay at 100% sampling** — 5k recordings is a few days of modest traffic.
3. **High-cardinality properties** — user IDs, raw timestamps, full URLs, free text and cart contents as event properties. Bucket them (`price_band: '10-20'`) instead.

Controls to set on day one:

- **Billing limits per product** (Billing settings). PostHog *drops* events over the limit rather than charging you. Set one for analytics, replay and flags separately — this is the hard backstop.
- Property allow-list; review new properties monthly and delete ones nobody queries.
- Sampling on replay; `captureTouches: false` on analytics.
- Filter internal traffic by cohort so your own team doesn't consume quota or skew funnels.

# Sentry for Expo + Next.js

Time-sensitive: SDK package names, the Expo config plugin path, quota ceilings and prices change. Verify against [docs.sentry.io](https://docs.sentry.io/platforms/react-native/manual-setup/expo/) and [sentry.io/pricing](https://sentry.io/pricing/) before relying on any number here.

## Packages

| Use | Package | Note |
|---|---|---|
| Expo / React Native | `@sentry/react-native` | Requires **Expo SDK 50+** |
| Next.js | `@sentry/nextjs` | Covers client, server and edge runtimes |
| Legacy Expo | `sentry-expo` | **Deprecated — do not install.** Migrate to `@sentry/react-native` ([migration guide](https://github.com/expo/fyi/blob/main/sentry-expo-migration.md)) |

If you find `sentry-expo` in a `package.json`, removing it is the first task, not an optional cleanup. It no longer receives updates.

Fastest correct setup: `npx @sentry/wizard@latest -i reactNative`. It installs deps, patches the Metro config, adds the plugin and writes the init block ([Expo guide](https://docs.expo.dev/guides/using-sentry/)).

## Config plugin and auth token

```json
{
  "expo": {
    "plugins": [
      ["@sentry/react-native/expo", {
        "url": "https://sentry.io/",
        "project": "your-project-slug",
        "organization": "your-org-slug"
      }]
    ]
  }
}
```

The auth token is **never** in `app.json`. Set `SENTRY_AUTH_TOKEN` as an EAS secret with *sensitive* visibility; it needs the **Source Map Upload** and **Release Creation** scopes (granted automatically for wizard-created tokens).

```bash
eas secret:create --scope project --name SENTRY_AUTH_TOKEN --value <token> --type string
```

Locally, put it in `.env.local` and confirm `.env.local` is gitignored. A token committed to the repo is a revocation event, not a warning.

**Gotcha — symptom: builds succeed but Sentry shows an empty Releases page and every trace is minified.** The config plugin was not applied during EAS cloud prebuild, or `SENTRY_AUTH_TOKEN` is missing from the build environment. Check the build log for the Sentry upload step; silence there means no upload happened.

## Sourcemaps: two separate paths

**Native release builds:** sourcemaps upload automatically during the EAS build when the plugin is configured. Nothing extra to run.

**OTA updates: they do NOT upload automatically.** This is the number one cause of unreadable stack traces in Expo apps. Every `eas update` ships new JS that Sentry cannot symbolicate unless you upload separately:

```bash
eas update --branch production --message "fix checkout crash"
npx sentry-expo-upload-sourcemaps dist
```

Make this a single script so the two commands cannot drift apart:

```json
{ "scripts": {
  "deploy:ota": "eas update --branch production && npx sentry-expo-upload-sourcemaps dist"
} }
```

If an incident produces minified frames, check *first* whether the crashing build came from an OTA update whose sourcemaps were never uploaded — before assuming the SDK is misconfigured.

## Release, dist and OTA tagging

Release defaults to `<bundleIdentifier>@<version>+<buildNumber>`; dist defaults to the build number. Keep the defaults unless you have a reason — hand-rolled release names are the second most common symbolication failure.

The Expo integration adds OTA context automatically as searchable tags:

| Tag | Use |
|---|---|
| `expo-update-id` | Identifies the exact OTA payload running |
| `expo-update-group-id` | Groups the platform variants of one update |
| `expo-is-embedded-update` | `true` = the JS shipped inside the binary; `false` = delivered OTA |

Triage rule: filter on `expo-is-embedded-update:false` to isolate "the OTA I just shipped broke people" from "this binary was always broken." These two have completely different remediations — roll back the update channel vs. ship a new build.

## Production sampling

Docs show `1.0` for tracing and explicitly say to lower it in production. Uniform sampling wastes span quota on chatty screens while under-sampling the flows that make money. Use a `tracesSampler`:

```js
Sentry.init({
  dsn: process.env.EXPO_PUBLIC_SENTRY_DSN,
  sendDefaultPii: false,
  tracesSampler: (ctx) => {
    const name = ctx.name ?? '';
    if (name.includes('checkout') || name.includes('paywall') || name.includes('signup')) return 1.0;
    if (name.includes('feed') || name.includes('scroll')) return 0.01;
    return 0.1;
  },
  profilesSampleRate: 0.1,          // relative to sampled traces
  replaysSessionSampleRate: 0.0,    // see replay section
  replaysOnErrorSampleRate: 1.0,
  integrations: [Sentry.mobileReplayIntegration()],
});
```

`profilesSampleRate` multiplies against traces — `0.1 × 0.1` means 1% of sessions profiled, which is the right order of magnitude.

## Mobile session replay

`mobileReplayIntegration()` masks **all text, all images and all vectors by default** (`maskAllText`, `maskAllImages`, `maskAllVectors` all `true`) ([replay docs](https://docs.sentry.io/platforms/react-native/session-replay/)).

**Never disable these globally.** Do not write `maskAllText: false` to "make replays useful" — that ships every email address, message body and account balance to a third party. Unmask specific non-sensitive views instead, using the per-component mask/unmask wrappers.

Set `replaysSessionSampleRate: 0.0` and `replaysOnErrorSampleRate: 1.0` on the free tier: it allows only **50 replays/month**, so spend all of them on sessions that actually errored. Session sampling at even 0.1 exhausts the allowance in a day at modest traffic.

## PII scrubbing in beforeSend

`sendDefaultPii` defaults to sending IP addresses and cookies. Set it `false` and scrub explicitly:

```js
beforeSend(event) {
  if (event.user) {
    delete event.user.email;
    delete event.user.ip_address;
    delete event.user.username;
  }
  if (event.request?.headers) {
    delete event.request.headers.Authorization;
    delete event.request.headers.Cookie;
  }
  if (event.request?.url) {
    event.request.url = event.request.url.split('?')[0];
  }
  event.breadcrumbs = event.breadcrumbs?.map((b) =>
    b.category === 'http' ? { ...b, data: { ...b.data, body: undefined } } : b
  );
  return event;
},
beforeSendTransaction(tx) {
  // Collapse high-cardinality path params: /users/abc123 -> /users/:id
  tx.transaction = tx.transaction?.replace(/\/[0-9a-f]{8,}/gi, '/:id');
  return tx;
}
```

Path params left uncollapsed inflate span cardinality and burn the 5M span allowance without producing usable aggregates.

## Alert rules worth having

1. **New fatal issue in the current release.** `is:new AND level:fatal`, filtered to `environment:production`. This is the page-someone alert.
2. **Crash-rate regression by percentage change**, comparing the current release to the previous one. Absolute-threshold crash alerts fire constantly as traffic grows; percentage-change alerts fire when something actually got worse.
3. **Failure-rate metric alert on one named critical transaction** (checkout, signup). Scope it to the transaction name, not to all transactions.
4. **OTA-scoped regression**, filtered on `expo-is-embedded-update:false`, so a bad JS-only push surfaces distinctly from a binary problem.

### Delete these
- Any "alert me on every new issue" rule — it trains everyone to ignore Sentry within a week.
- Per-event notifications (as opposed to per-issue).
- Any alert without an `environment` filter; dev and preview noise will dominate.
- Duplicate rules routed to both email and Slack for the same condition.

## Quota management

Free (Developer) tier: **5,000 errors, 5M spans, 50 replays, 5GB logs, 1GB attachments, 1 cron monitor, 1 uptime monitor, 30-day retention, 1 seat.** Team is **$26/mo** annual → 50k errors, unlimited seats, 90-day retention; error overage around $0.00036/error at the first band ([pricing](https://sentry.io/pricing/)).

A single crash loop can consume a month of error quota in hours. Defend in four places:

```js
ignoreErrors: [
  'Network request failed',
  'AbortError',
  'Non-Error promise rejection captured',
  'TypeError: cancelled',
  /^Request (timed out|aborted)$/,
],
denyUrls: [
  /extensions\//i,
  /^chrome:\/\//i,
  /webkit-masked-url/i,
],
```

- **`ignoreErrors`** — client-side, catches known-noise strings before they cost quota.
- **`denyUrls`** — drops errors thrown by injected scripts and browser extensions in WebViews.
- **Inbound filters** (project settings) — server-side; enable legacy-browser and localhost filters, and filter by release for builds you no longer support.
- **Spike protection** — enable it per project. It caps a runaway burst rather than letting one incident consume the month.

Also set a **rate limit per key** in project settings. It is the only control that survives a bug in your own `beforeSend`.

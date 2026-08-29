---
name: performance-security
description: >
  Measure and improve app startup time, frame rate, bundle size and binary size, and harden the app
  against the things that actually get exploited. Use when the app feels slow, startup is sluggish,
  lists jank, the download size is too large, web vitals are poor, or before a release as a deliberate
  optimisation pass. Also use for mobile security review — secrets in the bundle, token storage, deep
  link validation, WebView hardening, whether certificate pinning is worth it — and for confirming
  that authorisation is enforced on the server rather than in the UI.
---

# Performance and hardening

Two disciplines that share one habit: **measure before changing anything, and measure the thing the
user experiences rather than the thing that is easy to measure.**

## Measure first

Optimisation without a baseline is guesswork that produces churn and regressions. Before touching
anything, record in `docs/app/` the current cold start time on a mid-tier Android device, the
JavaScript bundle size per platform, the download and install size from the store reports, and where
frames are actually dropping.

Then measure in the right place. **Release builds, on a real low-end Android device.** A simulator on
a fast laptop will tell you the app is fine right up until users tell you otherwise. Web vitals come
from field data at the 75th percentile, not from a local run.

Reasonable targets, as conventions rather than published thresholds: cold start under about two seconds
on a mid-tier Android, warm start under one; JavaScript bundle in the low single-digit megabytes; no
dropped frames while scrolling; the JavaScript thread never blocked for more than about 100ms during
an interaction. On web: LCP within 2.5 seconds, INP within 200 milliseconds, CLS within 0.1.

## Startup and frame rate

In rough order of effect:

- The New Architecture and Hermes — no longer optional on current SDKs, but confirm the app is actually
  on them.
- **Route-level code splitting** so the first screen does not pay for the whole app, and inline
  requires so modules load when used.
- **Trim the dependency graph.** Every autolinked native module costs startup and binary size. Audit
  what is installed against what is used; this is usually the largest single win and nobody does it.
- **Images**: correct dimensions, a proper image component with memory and disk caching, and never a
  full-resolution asset in a list row.
- **Lists**: a virtualised list with stable keys. A mapped array inside a ScrollView is the standard
  cause of a "the app gets slow with lots of data" report.
- **Re-render storms**: the React compiler where the toolchain supports it, otherwise memoisation at
  the specific components that re-render, identified by profiling rather than by sprinkling.
- **Animation on the wrong thread.** Anything driven from a JavaScript scroll handler, or animating
  layout properties instead of transform and opacity, costs a frame every frame. `premium-ui` has the
  rules.

On the web side: server components and streaming to unblock the largest paint, explicit image
dimensions with priority on the hero to kill layout shift, and client components kept at the leaves.

## Size

What actually makes a React Native binary large: unused native modules, uncompressed image and font
assets, multiple architecture slices, duplicated icon sets, and debug symbols.

Measure with the store's own size report — those are the numbers the platform's download limits use —
and with the Android bundle analyser per split. Then ship an Android App Bundle so the store generates
per-architecture and per-density splits, enable minification and resource shrinking for release,
remove native modules you do not use, convert assets to modern formats, prefer remotely loaded media,
and drop unused locales.

Typical consumer app downloads land in the tens of megabytes on both platforms. Well above that is
worth investigating; well above that on a cellular connection is worth fixing, because the download
threshold is where installs are abandoned.

## Security

Frame it with the OWASP mobile standard, but the working list for a consumer app is short.

**Nothing in the JavaScript bundle is secret.** Publicly prefixed environment variables are inlined as
text into the bundle; anyone can unzip the app package and read them. This is not a risk to manage, it
is a fact to design around. Verify rather than assume: export the bundle in CI and grep for key
prefixes, `secret`, and PEM headers, and fail the build on a hit.

**Storage**: the platform secure store, backed by Keychain and Keystore, for tokens and keys.
General-purpose async storage is plaintext and is for cache and preferences only.

**Authorisation is server-enforced.** Hiding a button is not authorisation; removing a screen from the
navigator is not authorisation. Every endpoint re-validates the session and re-checks ownership, and
every table has a policy. `clerk-auth` and `postgres-data` make the two halves of this argument.

**Deep links**: validate and allow-list every incoming URL. Never navigate to or fetch an
attacker-supplied URL, and never let a deep link carry an auth token or perform a state change without
confirmation. Prefer domain-verified universal links over custom schemes.

**WebViews**: restrict the origin allow-list to your own domains, disable JavaScript where it is not
needed, never inject script built from remote data, and disable file access.

**Certificate pinning is usually not worth it** for a pre-revenue consumer app — it breaks on
certificate rotation and can brick every installed client. Adopt it only for high-value financial or
health flows, and only with a remote kill switch. Similarly, obfuscation and root detection are speed
bumps, not controls: they satisfy specific threat models such as anti-cheat or regulated finance, and
nothing else. Never make them load-bearing.

**Privacy**: scrub PII in the error reporter's send hook, keep replay masking on, and make sure the
privacy manifest and data safety declarations actually match what the SDKs do — `store-submission`
covers why that is also a rejection risk.

## The pass

Run this as a deliberate pass before a release, not continuously:

1. Baseline the four measurements above.
2. Trim dependencies; re-measure. This is usually the biggest single delta.
3. Fix the top three profiler findings; re-measure after each, not after all three.
4. Run the secret grep, the deep link audit, and one server-side authorisation spot check per
   authenticated route.
5. Record the before and after numbers. Unrecorded optimisation regresses silently within two releases.

Then hand to `preflight-audit` for the release gate; this skill is the tuning, not the verdict.

## Reference files

- `references/performance.md` — measurement tooling, the lever list with expected effects, web vitals
- `references/size.md` — what to measure, splits, minification, asset pipeline
- `references/security.md` — the hardening checklist and the CI gates that enforce it

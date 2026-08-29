# Performance: React Native + Next.js

Time-sensitive: React Compiler status, New Architecture defaults and Expo SDK version gates move every release cycle. Verify against [docs.expo.dev](https://docs.expo.dev/guides/react-compiler/) and [react.dev](https://react.dev/blog/2025/10/07/react-compiler-1) before acting on version claims.

## Measurement first

Never optimise from a hunch. Establish the number, change one thing, re-measure.

| Platform | What | Tool |
|---|---|---|
| RN both | Cold/warm start (TTI) | Sentry app-start spans (`@sentry/react-native` instruments this automatically); real device, release build |
| RN both | Frame drops, JS thread | React Native DevTools profiler; on-device perf monitor |
| RN both | Re-render counts | React DevTools Profiler, "highlight updates" |
| RN both | Bundle composition | `expo-atlas` (below) |
| iOS | Native startup phases | Instruments → App Launch template |
| Android | Startup, jank | `adb shell am start -W`, Android Studio Profiler, Macrobenchmark |
| Web | Field vitals | PostHog/Vercel Analytics real-user data |
| Web | Lab vitals | Lighthouse, `next build` output, `@next/bundle-analyzer` |

**Always measure release builds on a mid-tier physical Android device.** Debug-build and simulator numbers are meaningless — the JS bundle is unminified, dev-mode warnings run, and the simulator has desktop-class CPU. A "fast" app measured on an iPhone Pro simulator routinely takes 4–5s to start on the Android hardware most users actually own.

## RN levers, in priority order

Work down this list. Each entry says roughly what it is worth; the estimates are directional, not benchmarked guarantees [UNVERIFIED].

1. **New Architecture + Hermes.** Both are defaults from RN 0.76 / Expo SDK 52 onward. Hermes is the default engine; the New Architecture (Fabric + TurboModules) removes the async bridge. If a project has explicitly disabled either, re-enabling is the single largest win available — and the reason is usually one incompatible legacy library that should be replaced. Verify with `newArchEnabled` in app config rather than assuming.

2. **Lazy routes with `expo-router`.** File-based routes give route-level code splitting. The startup bundle should contain the first screen and its dependencies, not the settings screen's chart library. Worth several hundred ms of TTI on a large app.

3. **Inline requires.** Enabled by default in Expo's Metro config. It defers module evaluation from bundle-parse time to first use, which is most of the difference between "the bundle is 4MB" and "the app takes 4MB worth of time to start." Confirm it's on before hand-optimising imports; the symptom of it being off is startup time scaling linearly with total bundle size.

4. **Trim the dependency graph.** The heaviest thing in most RN apps is a library imported for one function — moment, lodash (import the specific function, not the barrel), a full icon set, an entire charting library for one sparkline. Atlas shows you which. Frequently 500KB–1.5MB of bundle.

5. **`expo-image`, used correctly.** Set explicit dimensions, appropriate `contentFit`, and `cachePolicy: 'memory-disk'`. Serve pre-resized images from the server — never download a 3000px asset to render a 100px avatar. This is usually the biggest *perceived* performance and data-usage win in a media app.

6. **List virtualization.** `FlashList` or `FlatList` with a stable `keyExtractor`, `getItemLayout` where item heights are known, and no inline arrow functions in `renderItem`. Never `.map()` over an unbounded array. Symptom of getting this wrong: scroll jank that worsens the further down the list you go.

7. **Stop re-render storms.** Context providers holding frequently-changing values re-render every consumer; a new object or array literal in props defeats memoization. Profile first — memoizing the wrong component costs more than it saves.

8. **React Compiler** (below) — automates step 7 once the above are done.

## Bundle analysis

```bash
# Production export, then inspect
EXPO_ATLAS=true npx expo export
npx expo-atlas .expo/atlas.jsonl

# Or against the dev server, production mode for accurate sizes
EXPO_ATLAS=true npx expo start --no-dev
# then Shift + M -> Atlas in the dev tools menu
```

Atlas visualizes the production bundle and attributes size to libraries; ⌘-click a node to see the Babel transform and dependency edges ([docs](https://docs.expo.dev/guides/analyzing-bundles/)). Use `--platform` to check iOS and Android separately — they diverge.

For bare RN, `react-native-bundle-visualizer`. For SDK 50 and earlier, `source-map-explorer`.

Read the treemap for: duplicated libraries at different versions, dev-only tooling that leaked into the production graph, polyfills, and barrel imports pulling entire packages.

## React Compiler

**Status: React Compiler 1.0 shipped in October 2025 and supports React Native. It is NOT enabled by default in Expo.** Opt in:

```json
{ "expo": { "experiments": { "reactCompiler": true } } }
```

- SDK 54+ configures Babel automatically. SDK 53 and earlier require installing `react-compiler-runtime@beta` manually.
- Still labelled **beta** in Expo's installation flow.
- Runs on **application code only** (not `node_modules`), and is disabled during server rendering.
- Class components are not optimized — migrate to function components.
- Opt a component out with the `"use no memo"` directive.

It automatically memoizes components and hooks, which removes most hand-written `useMemo`/`useCallback`/`React.memo`. Do not rip out existing memoization the same day you enable it — turn it on, verify behaviour and measure, then simplify. Its correctness depends on components following the rules of React; a component that mutates props or reads refs during render can behave differently once compiled, and the symptom is a stale or frozen UI in one specific screen.

## Target numbers

**These are working conventions and typical industry expectations, not published Expo, Meta or Apple thresholds. [UNVERIFIED] — do not present them to a client as official.**

| Metric | Target | Measured how |
|---|---|---|
| Cold start (TTI) | < 2s on mid-tier Android | Release build, physical device |
| Warm start | < 1s | Same |
| JS bundle (minified, per platform) | < 3–4 MB | `expo export` output / Atlas |
| Frame budget | 16.6ms @ 60Hz; 8.3ms @ 120Hz | Perf monitor during scroll |
| Dropped frames in a scroll | effectively zero | Profiler |
| JS thread block during interaction | < 100ms | Profiler |
| Time to first meaningful screen | < 1s after splash | Sentry span |

The only genuinely published numbers in this space are the web ones below. Treat mobile targets as budgets you set and defend, not as external standards.

## Next.js and Core Web Vitals

Published thresholds, measured at the **75th percentile** of real users ([web.dev/articles/vitals](https://web.dev/articles/vitals)):

| Metric | Good | Measures |
|---|---|---|
| **LCP** | ≤ 2.5s | Loading |
| **INP** | ≤ 200ms | Interactivity (replaced FID; stable since 2024) |
| **CLS** | ≤ 0.1 | Visual stability |

Levers:

- **RSC + streaming.** Server Components keep data-fetching libraries out of the client bundle entirely. `loading.tsx` / `<Suspense>` streams a shell so LCP is not blocked behind the slowest query. Keep client components at the *leaves* of the tree — one `'use client'` near the root pulls everything below it into the client bundle, which is the most common Next.js performance mistake.
- **`next/image`** with explicit `width`/`height` (prevents CLS) and `priority` on the LCP element (prevents lazy-loading the hero). Serving a correctly sized, modern-format hero image is usually the largest single LCP improvement available.
- **`next/font`** — self-hosts and preloads fonts, eliminating the layout shift from FOUT/FOIT.
- **Bundle analysis:** `@next/bundle-analyzer`, plus the per-route First Load JS table printed by `next build`. Watch for a shared chunk growing over time.
- **INP specifically:** break long tasks, avoid synchronous work in event handlers, and defer non-critical third-party scripts with `next/script` (`strategy="lazyOnload"`). Analytics and tag managers are the usual INP culprits.
- Measure **field** data, not just Lighthouse. Lab scores routinely look fine while real users on slow networks fail LCP.

# React Native Implementation Stack

Time-sensitive: every version below was read from the npm registry on **29 August 2026**. Re-check with `npx expo install --check` before relying on any number here.

---

## Versions

> **The SDK pin wins. Install with `npx expo install <pkg>`, never `npm install <pkg>@latest`.** Expo pins a tested combination that lags the registry, and the Reanimated/worklets/Gesture Handler trio must move together. The "Latest published" column is context for planning an upgrade — it is **not** what you get, and writing against it will fail at runtime.

**Use column = what `npx expo install` resolves on SDK 57. Latest column = registry `latest` on 29 Aug 2026.**

| Package | Use (SDK 57) | Latest published | New Architecture |
|---|---|---|---|
| `expo` | 57.0.x | 57.0.18 | SDK 57 released 30 Jun 2026 ([changelog](https://expo.dev/changelog/sdk-57)) |
| `react-native` | **0.86** | 0.87.1 | Default; legacy deprecated |
| `react-native-reanimated` | **4.5** | 4.6.0 | **New Arch only** from v4 |
| `react-native-worklets` | **0.10** | 0.12.1 | Required peer of Reanimated 4; must match the [compatibility table](https://docs.swmansion.com/react-native-reanimated/docs/guides/compatibility) |
| `react-native-gesture-handler` | **2.32** | 3.2.1 | v2 works on both; **v3 is New Arch only** |
| `expo-router` | 57.0.x | 57.0.17 | |
| `expo-image` | 57.0.x | 57.0.3 | |
| `expo-haptics` | 57.0.x | 57.0.2 | |
| `@shopify/react-native-skia` | resolved by `expo install` | 2.11.1 | |
| `@shopify/flash-list` | resolved by `expo install` | 2.3.2 | |
| `@legendapp/list` | not in the SDK — pin manually | 3.3.9 | **New Arch required** |
| `@gorhom/bottom-sheet` | not in the SDK — pin manually | 5.2.14 | |
| `react-native-safe-area-context` | resolved by `expo install` | 5.9.1 | |
| `react-native-edge-to-edge` | resolved by `expo install` | 1.8.1 | |
| `react-native-svg` | resolved by `expo install` | 15.15.5 | |
| `react-native-keyboard-controller` | not in the SDK — pin manually | 1.22.4 | |
| `@react-navigation/native` | resolved by `expo install` | 7.3.18 | |
| `react-native-bottom-tabs` | not in the SDK — pin manually | 1.4.0 | |
| `lucide-react-native` | any | 1.37.0 | |

The four bold rows are the ones that bite. SDK 57 gives you **Reanimated 4.5, worklets 0.10 and Gesture Handler 2.32** — so Reanimated 4 APIs are available but **Gesture Handler 3 APIs are not**. Check `package.json` before writing gesture code.

### Availability at a glance

| API | Requires | Available on SDK 57? |
|---|---|---|
| `scheduleOnRN` / `scheduleOnUI` / `scheduleOnRuntime` / `runOnUISync` | Reanimated 4 + worklets | Yes |
| `react-native-worklets/plugin` Babel plugin | Reanimated 4 | Yes |
| `withSpring({ energyThreshold })` | Reanimated 4 | Yes |
| CSS-style `animationName` / `transitionProperty` props | Reanimated 4 | Yes |
| `EntryExitTransition` (replaces `combineTransition`) | Reanimated 4 | Yes |
| Gesture `onActivate` / `onDeactivate` callbacks | **Gesture Handler 3** | **No — v2.32 uses `onStart` / `onEnd`** |
| Hook-based gesture API (React Compiler compatible) | **Gesture Handler 3** | **No** |
| Shared values directly in gesture config (no re-render) | **Gesture Handler 3** | **No** |
| `Touchable` from `react-native-gesture-handler` | **Gesture Handler 3** | **No — use `Pressable`** |
| Gestures attached to `<Text>` | **Gesture Handler 3** | **No** |
| `Stack.Toolbar` | expo-router 55+ | Yes |
| `<NativeTabs>` | expo-router 55+ (preview) | Yes, preview |
| `Link.Trigger` + `withAppleZoom` | expo-router 55+, Apple only | Yes, preview |

To use Gesture Handler 3 on SDK 57 you must override the pin manually and accept that it is untested against that SDK; the New Architecture requirement is already satisfied, but do not do this casually. [UNVERIFIED whether GH 3 is compatible with the SDK 57 native build.]

---

## Reanimated 4 breaking changes

**Requires Reanimated ≥4.0 — available on SDK 57 (4.5).** From the [3.x → 4.x migration guide](https://docs.swmansion.com/react-native-reanimated/docs/guides/migration-from-3.x/).

**Architecture:** supports only the New Architecture. On Paper you must upgrade or stay on 3.x.

**Worklets extracted** into `react-native-worklets`. Install it, rebuild native, and change the Babel plugin:

```js
// babel.config.js
plugins: ['react-native-worklets/plugin']  // was 'react-native-reanimated/plugin'
```

**Renamed threading functions** (now in `react-native-worklets`, and they take arguments directly rather than returning a callable):

| v3 | v4 |
|---|---|
| `runOnJS` | `scheduleOnRN` |
| `runOnUI` | `scheduleOnUI` |
| `runOnRuntime` | `scheduleOnRuntime` |
| `executeOnUIRuntimeSync` | `runOnUISync` |

**Removed:** `useWorkletCallback` (use `useCallback` with a `'worklet'` directive), `useAnimatedGestureHandler` (use Gesture Handler's `Gesture` API), `combineTransition` (use `EntryExitTransition`), React Native V8 support.

**Spring:** `restDisplacementThreshold`/`restSpeedThreshold` → `energyThreshold`; perceptual `duration` completes ~1.5× faster than nominal. Re-tune ported configs.

---

## Gesture Handler 3

**Everything in this section requires `react-native-gesture-handler` ≥3.0. SDK 57 pins 2.32, so none of it is available by default — on SDK 57 write the v2 `Gesture` API with `onStart`/`onEnd` and use `Pressable` for buttons.** From the [3.0 announcement](https://swmansion.com/blog/introducing-gesture-handler-3-0-hook-based-api-deeper-reanimated-integration-more-9185b0c8e305/).

- **New Architecture required.** Legacy dropped.
- **Hook-based API**, React Compiler compatible. Callback renames: `onStart` → `onActivate`, `onEnd` → `onDeactivate`. *(v3 only)*
- **Shared values accepted directly in gesture config**, so you can change gesture properties with **no re-renders** — the main craft win: thresholds and enabled-state can be animated. *(v3 only)*
- Gestures can attach to `Text`; `StateManager` is reachable from the JS thread. *(v3 only)*
- New **`Touchable`** replaces `TouchableOpacity`/`RectButton` etc.; benchmarks 1.03–1.31× `Pressable`, larger gains on low-end hardware. *(v3 only)*
- v2 APIs still work in v3 — migrate screen by screen after upgrading.

**What to write on SDK 57:** `Gesture.Pan().onBegin().onUpdate().onEnd()` with `runOnJS`-free worklet callbacks, wired to Reanimated 4 shared values. That combination is fully supported and is what every gesture example in `motion.md` assumes.

---

## CSS-style animations vs shared values

**Requires Reanimated ≥4.0 — available on SDK 57.** Reanimated 4 ships a declarative CSS-like API. Documented properties: `animationName`, `animationDuration`, `animationDelay`, `animationTimingFunction`, `animationDirection`, `animationIterationCount`, `animationFillMode`, `animationPlayState`; and `transitionProperty`, `transitionDuration`, `transitionDelay`, `transitionTimingFunction`, `transitionBehavior`, plus pseudo-selectors.

**Use the CSS API for:** state-driven, non-interactive motion — enter/exit, hover/press styling, loading shimmers, anything you'd write as a CSS transition on the web. It's less code and keeps the animation declarative.

**Use shared values + `useAnimatedStyle` for:** anything driven by a gesture or by scroll position, anything needing velocity handoff, anything that must be interrupted and retargeted mid-flight, and anything reading a continuously changing value.

Do not mix both on the same style property of the same node.

---

## Navigation and shared elements

All of the below require **expo-router ≥55**, so all are available on SDK 57.

- **Expo Router** is the default. `Stack.Toolbar` is stable (with placement options and the platform glass effect).
- **`<NativeTabs>`** with `NativeTabs.Trigger` and `NativeTabs.BottomAccessory` gives real native tab bars, including Material 3 dynamic colour on Android. Shipped as preview in Router v55 and moving toward stable ([announcement](https://expo.dev/blog/expo-router-v55-more-native-navigation-more-powerful-web)); stability status as of SDK 57 [UNVERIFIED].
- **Shared element / zoom transitions:** `Link.Trigger` with `withAppleZoom` — native, gesture-driven, interruptible, **Apple platforms only**. There is no equivalent first-party Android zoom transition; design a fallback (a plain fade/slide) rather than a JS-driven shared element, which will jank.
- Reanimated's own `sharedTransitionTag` shared transitions exist but are less reliable than the native route; prefer the native path where available. [UNVERIFIED: current support level of Reanimated shared transitions on 4.6.]

---

## Lists

| | FlatList | FlashList 2.3.2 | Legend List 3.3.9 |
|---|---|---|---|
| Dependency | Built in | Shopify | Legend |
| Architecture | Any | Any (v2 targets New Arch) | **New Arch required** (Fabric + Reanimated) |
| Recycling | Destroys off-screen views | Recycles ~30 instances | Recycles, Reanimated-driven |
| `estimatedItemSize` | n/a | v2 removes the requirement [UNVERIFIED against official v2 docs] | Recommended |
| Blank flashes | Frequent | Rare | None reported |

Rule of thumb ([comparison](https://www.pkgpulse.com/guides/flashlist-vs-flatlist-vs-legendlist-react-native-lists-2026)): under ~300 simple rows, `FlatList` is fine and has zero setup cost. At 500+ rows or with visible jank, move to FlashList. Legend List is the strongest option when you're already all-in on the New Architecture and need a hard 60fps floor.

Craft rules regardless of library: fixed-height rows wherever possible; `expo-image` with `recyclingKey` for row images; memoise `renderItem` and keep it free of inline closures; **do not put layout animations inside recycled rows** — recycling and layout animation fight, producing visible pops.

---

## UI-thread performance rules

**What runs where.** Worklets execute on the **UI runtime**. Shared values are synchronised between runtimes automatically. `useAnimatedStyle`, `useAnimatedScrollHandler`, `useAnimatedReaction` and Gesture Handler callbacks are worklets.

**What crosses back to JS, and what it costs.** Any call to `scheduleOnRN` (Reanimated ≥4; the v3 name was `runOnJS`) schedules work on the JS thread — a hop per call, plus argument serialisation. Calling it per frame from a scroll handler or gesture update is the single most common cause of jank. Batch: accumulate in a shared value and cross over once, on gesture end or on a threshold crossing. React `setState` from a worklet always costs a hop plus a render.

**What causes layout every frame.** Animating `width`, `height`, `padding`, `margin`, `flex`, `top`/`left`, or text content re-runs Fabric layout on every frame. This is why `LinearTransition` and layout animations jank — they *are* layout animations by definition. Mitigations: animate a wrapper's `transform: scale/translate` instead of its box; give animated containers fixed dimensions; avoid layout animations inside lists; avoid animating anything with text reflow.

**What to animate.** `transform` (translate/scale/rotate) and `opacity`. Also cheap: `backgroundColor` on a leaf node, `borderRadius` in most cases. Expensive: shadow properties on iOS (rasterisation), `backdrop-filter`/blur on Android, `overflow: hidden` combined with transforms.

**Other rules.** Read `.value` only inside worklets, never during render. Don't create shared values inside loops or `renderItem`. Keep worklet closures small — captured variables are copied to the UI runtime. Use `expo-image` (not `Image`) for anything remote, with `cachePolicy` set and explicit dimensions. Enable edge-to-edge via `react-native-edge-to-edge` and read insets from `react-native-safe-area-context`, never hardcoded.

---

## Profiling

1. **Release build, low-end Android, real device.** A debug build on a recent iPhone tells you nothing. This is the rule that matters most — most reported "smooth" animations were tested in the wrong configuration.
2. **React Native DevTools performance panel** for JS-thread work, render counts and commit cost. SDK 57's DevTools also emulate light/dark mode, useful for theme checks.
3. **Reanimated frame-drop warnings** in dev — they name the worklet that overran.
4. **Xcode Instruments → Core Animation / Time Profiler** for iOS: check for off-screen rendering (shadow + `overflow: hidden` is the usual culprit) and where main-thread time goes.
5. **Android Studio Profiler / Perfetto** for Android: watch for jank frames in the Frame Timeline, and confirm animations are on the RenderThread rather than the JS thread.
6. **Isolate the thread.** If an animation stays smooth while the JS thread is deliberately blocked (a long synchronous loop), it's genuinely on the UI thread. If it stutters, something is crossing back to JS.
7. **Measure before and after, on the same device and build.** Report frame times, not impressions.

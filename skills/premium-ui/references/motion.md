# Motion Standard

Time-sensitive: the Reanimated API names and spring config below track Reanimated 4.x. Check the npm registry and the migration guide before installing — v3 APIs were renamed, not aliased.

Numbers here come from [Emil Kowalski's animation standards](https://github.com/emilkowalski/skills/blob/main/skills/review-animations/STANDARDS.md) and the [Material 3 easing & duration tokens](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs).

---

## Duration by interaction class

| Interaction | Duration | Notes |
|---|---|---|
| Press / tap feedback | 100–160ms | Must begin on touch-down, not on release |
| Colour, opacity, hover | 100–150ms | |
| Tooltip, small popover | 125–200ms | |
| Dropdown, select, menu | 150–250ms | Scale from trigger |
| Toast / snackbar in | 200–300ms | |
| Modal, drawer, bottom sheet | 200–500ms | Larger travel → longer |
| Screen / route transition | 250–350ms | |
| Full-screen hero, onboarding | 400–600ms | Rare moments only |

**Hard rule: the overwhelming majority of UI animation is under 300ms.** Duration scales with distance travelled and with area covered — a 12px chevron rotation is not a 400ms animation.

**Exit is 0.7–0.8× the enter duration.** Users have already decided; get out of the way.

### Material's token ladder

Use as a quantised scale so durations are chosen from a set rather than typed freehand.

| Token | Values (ms) |
|---|---|
| short 1–4 | 50, 100, 150, 200 |
| medium 1–4 | 250, 300, 350, 400 |
| long 1–4 | 450, 500, 550, 600 |
| extra-long 1–4 | 700, 800, 900, 1000 |

Long and extra-long are for full-screen and brand moments only. If a utility control uses a `long` token, that is a bug.

---

## Easing

Decision hierarchy:

| Situation | Curve |
|---|---|
| Entering or exiting | `ease-out` |
| Moving on-screen (already visible) | `ease-in-out` |
| Hover, colour, opacity | `ease` |
| Continuous / indeterminate | `linear` |
| Unsure | `ease-out` |

**Never use `ease-in` on entering UI.** It delays exactly the moment the user is watching, and reads as lag.

### Named curves

Stronger than the CSS keyword defaults; use these as tokens.

```css
--ease-out:     cubic-bezier(0.23, 1,     0.32,  1);
--ease-in-out:  cubic-bezier(0.77, 0,     0.175, 1);
--ease-drawer:  cubic-bezier(0.32, 0.72,  0,     1);
```

Material equivalents, if you want to align with Android platform feel:

| Name | Curve | Use |
|---|---|---|
| Standard | `cubic-bezier(0.2, 0, 0, 1)` | Most UI motion |
| Standard decelerate | `cubic-bezier(0, 0, 0, 1)` | Entering |
| Standard accelerate | `cubic-bezier(0.3, 0, 1, 1)` | Exiting |
| Emphasized decelerate | `cubic-bezier(0.05, 0.7, 0.1, 1)` | Hero entry |
| Emphasized accelerate | `cubic-bezier(0.3, 0, 0.8, 0.15)` | Hero exit |
| Linear | `cubic-bezier(0, 0, 1, 1)` | Indeterminate progress only |

Pair decelerate-in with accelerate-out on the same element. Reserve emphasized curves for brand moments; use standard curves in information-dense layouts.

---

## Spring vs timing

**Timing** for discrete, predictable state changes with a known start and end: fades, colour, disclosure, tooltips, most enter/exit.

**Spring** for anything continuous, gesture-adjacent, or velocity-carrying: drag momentum, sheet dismissal, card reordering, swipe-to-delete, pull-to-refresh. Springs absorb release velocity and retarget mid-flight; timing curves cannot.

Apple-style config, the recommended default:

```js
{ duration: 0.5, bounce: 0.2 }
```

Keep `bounce` in 0.1–0.3. Use `bounce: 0` for most utility UI — bounce on a routine control reads as toy-like. Reserve visible overshoot for rare/reward moments.

### Reanimated 4 spring API changes

`withSpring` in Reanimated 4 replaced `restDisplacementThreshold` and `restSpeedThreshold` with a single **`energyThreshold`**, and the perceptual `duration` parameter now completes roughly **1.5× faster** than the nominal value — a `duration: 0.5` spring settles visually well before 500ms ([migration guide](https://docs.swmansion.com/react-native-reanimated/docs/guides/migration-from-3.x/)). If you ported v3 spring configs verbatim, re-tune them.

```js
withSpring(1, { duration: 0.5, dampingRatio: 0.8, energyThreshold: 6e-9 });
```

---

## Frequency governs restraint

The most important rule, and the one that separates elegant from cartoonish.

| How often the user does it | Animation |
|---|---|
| 100+ times/day | **None.** Instant. |
| Tens of times/day | Minimal — opacity/colour only, ≤150ms |
| Occasional | Standard animation |
| Rare / first-run / reward | Delight permitted |

**Never animate keyboard-initiated actions.** They repeat hundreds of times daily; animation makes them feel slow and disconnected from the keypress.

Corollary: an animation is not "free" because it's short. Every repeated animation is a tax paid on every repetition.

---

## Physicality

- **Never `scale(0)`.** Enter from `scale(0.94–0.97)` with `opacity: 0`. Scaling from zero looks like a cartoon, not an object.
- **`transform-origin` matters.** Popovers, menus and dropdowns scale *from their trigger*. Modals scale from centre. A menu that grows from its own centre reads as unattached.
- **Press state:** `scale(0.97)` plus a small opacity or surface-tint change, 160ms `ease-out`, applied on touch-down. On native, use `Pressable`'s pressed state or Gesture Handler's `Touchable` and drive the transform on the UI thread.
- **Animate `transform` and `opacity` only.** They skip layout and paint. `width`, `height`, `padding`, `margin`, `top`, `left` trigger layout every frame.
- **Don't cross-fade moving objects.** If an element persists across states, move it; don't fade one out and another in.

---

## Choreography

- **Stagger 30–80ms** between list items. Longer feels sluggish; shorter reads as simultaneous.
- **Cap the stagger** at ~6 items, then bring the remainder in as one block. A 40-item staggered list takes 1.6s to finish arriving.
- **Stagger is decorative — never let it block interaction.** Items must be tappable the instant they're visible, mid-animation.
- **Asymmetric timing:** slow where the user decides (opening a menu, revealing options), fast where the system responds (confirming, dismissing, committing).
- Animate the *container* first, contents second — not every child independently.

---

## Interruptibility and gesture handoff

- Use **transitions/springs that retarget from the current value**, not keyframes that restart from zero. In CSS, `transition` is interruptible; `@keyframes` restarts. On native, shared values driven by `withSpring`/`withTiming` retarget correctly; `Animated` sequences generally do not.
- A gesture-driven surface must **track the finger 1:1** during the drag, then hand the release velocity to a spring. Anything that animates to a fixed duration on release feels detached.
- Every gesture must be **cancellable mid-flight**: a second touch during a sheet's dismissal animation should grab it and reverse.
- On the web, gate hover: `@media (hover: hover) and (pointer: fine)` — otherwise touch devices get stuck hover states.

---

## Reduced motion

Reduced motion means **fewer and gentler animations, not zero.** Keep opacity and colour transitions; drop translation, scale, parallax and looping motion.

**Web:**

```css
@media (prefers-reduced-motion: reduce) {
  .thing { animation: fade 200ms ease; transition-duration: 150ms; }
}
```

**React Native / Reanimated 4** ([accessibility docs](https://docs.swmansion.com/react-native-reanimated/docs/guides/accessibility/)):

```js
import { useReducedMotion, ReducedMotionConfig, ReduceMotion } from 'react-native-reanimated';

// App-wide policy
<ReducedMotionConfig mode={ReduceMotion.System} />

// Per-component branch
const reduced = useReducedMotion();
```

`ReduceMotion.System` follows the OS setting; `.Always` disables regardless; `.Never` keeps motion on always. When reduced motion is active: `withSpring`/`withTiming` return `toValue` immediately, `withDecay` returns the current value, `withDelay` starts the next animation immediately, layout animations reach their endpoints instantly, and **exiting animations and shared transitions are omitted entirely**. Design so that an instant jump is still coherent — if your UI only makes sense mid-animation, it's wrong.

`useReducedMotion()` reflects the setting **at app startup**, not live. For runtime changes subscribe to `AccessibilityInfo.addEventListener('reduceMotionChanged', …)`. [UNVERIFIED for the exact Reanimated 4.6 behaviour on live toggling.]

---

## Micro-interactions worth implementing

These are what actually make an app feel expensive. One-line implementation note each.

| Interaction | Implementation |
|---|---|
| **Press state** | `scale(0.97)` + tint on touch-down via a Reanimated shared value driven from Gesture Handler's `Touchable` or `Pressable`; never wait for release |
| **Haptics paired to state change** | `expo-haptics`: `selectionAsync()` on picker/segment snap, `impactAsync(Light)` on toggle commit, `notificationAsync(Success)` on task completion. Fire on the *state change*, never on every tap, and never on scroll |
| **Optimistic UI** | Apply the mutation to local state immediately, reconcile on response, animate a rollback (shake or colour flash, 200ms) on failure |
| **Scroll-linked header** | `useAnimatedScrollHandler` + `useAnimatedStyle` — runs entirely on the UI thread; interpolate height/opacity/blur from `scrollY`. Never drive this from a JS `onScroll` |
| **List item enter/exit** | Reanimated `FadeIn`/`FadeOut` with `LinearTransition` for reflow; keep out of recycled rows in FlashList/Legend List, where layout animation fights recycling |
| **Pull-to-refresh** | Custom worklet-driven indicator interpolating from the pan translation, with a spring settle on release; haptic `impactAsync(Light)` at the trigger threshold |
| **Keyboard-aware transitions** | `react-native-keyboard-controller` — drives layout from the native keyboard animation curve instead of a guessed duration, so content and keyboard move as one |
| **Shared element / zoom transition** | Expo Router `Link.Trigger` with `withAppleZoom` on Apple platforms — gesture-driven and interruptible ([Expo Router v55](https://expo.dev/blog/expo-router-v55-more-native-navigation-more-powerful-web)) |
| **Sheet drag** | `@gorhom/bottom-sheet` or a Gesture Handler pan → shared value → `withSpring` on release using the gesture velocity |
| **Selection tick** | Scale 0.8→1 with `bounce: 0.25` plus `selectionAsync()`; one of the few places overshoot is correct |
| **Skeleton loading** | A slow linear shimmer (1200–1500ms, `linear`, looping) on a layout that matches the final content exactly — no spinners |
| **Count/number change** | Animate the digit with a vertical translate + fade, 200ms `ease-out`; never a smooth numeric tween on a value the user must read |

---

## Quick audit

Collect every duration in the file. One value everywhere = fail. Collect every easing. `ease-in` on entry, or `transition-all`, = fail. Check for a reduced-motion guard. Check that press feedback exists and starts on touch-down. Check that any gesture-driven surface is interruptible. Check that nothing animates a layout property.

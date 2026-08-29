# Craft References

Time-sensitive: product design changes between releases. Descriptions below reflect these apps as of mid-2026; verify against the current build before citing a specific screen. Where a claim is about internal technique rather than observable behaviour it is marked.

Use this file to name a **concrete reference and mechanism** instead of saying "make it premium". "Model the sheet on Apple Wallet's card stack — spring-driven, velocity-handed-off, interruptible mid-dismiss" is actionable. "Make it feel premium" is not.

---

## Linear — latency and restraint

**Take:** the idea that *speed is the aesthetic*.

**Mechanism:** a local-first sync engine. Mutations apply to the local store and render immediately; the network round trip is invisible and reconciles behind the UI. There is no spinner between intent and result, because there is no wait. Their design writing lives at [linear.app/now/craft](https://linear.app/now/craft).

**Also take:**
- **Keyboard-first surfaces.** Every action reachable by a command palette and a shortcut, with the shortcut shown in the menu that triggers it — the UI teaches its own keyboard model.
- **Monochrome with one accent.** Near-complete absence of colour except for status, priority and the current selection. Colour carries meaning, never decoration.
- **Motion only for continuity.** Transitions exist to explain where a thing went, not to entertain. Repeated actions have no animation at all — this is the frequency rule applied ruthlessly.
- **Density without noise.** High information density held together by type weight and spacing rather than by borders and boxes.

**Don't take:** its visual restraint as universal. Linear is a tool for people who use it eight hours a day; a consumer onboarding flow with Linear's austerity reads as unfinished.

---

## Things 3 (iOS) — spacing rhythm and gesture physics

**Take:** typography and spacing as the entire visual system. There is almost no ornament — hierarchy comes from size, weight, colour temperature and generous, unequal whitespace. It is the clearest available demonstration of the proximity rule: related lines sit close, groups sit far apart, and the difference is large enough to read at a glance.

**Mechanism worth copying:** the "magic plus" — a draggable button that becomes the new item, inserted at the position where you drop it. The insertion point is chosen by the gesture rather than by a menu, and the new row *opens* from the drop point rather than appearing. The whole interaction is continuous and interruptible: you can drag, hesitate, reverse, and let go anywhere.

**Also take:** every list state is designed — an empty project, a completed day, a filtered view with no matches each has its own considered rendering, not a shared "nothing here" component.

---

## Apple Wallet / Weather (iOS) — layered depth and scroll linkage

**Take:** depth expressed by stacked, overlapping physical surfaces with consistent shadow direction — not by blur applied to everything.

**Mechanisms:**
- **Card stack physics.** Cards compress toward the top as the stack scrolls, with the shadow between cards deepening as they separate. Every card responds to the same drag with an offset appropriate to its depth. This is parallax used as a depth cue, not as decoration.
- **Scroll-linked header.** In Weather, the location title, temperature and background all interpolate off a single scroll offset, continuously — no discrete snap between "large" and "small" header states. Implement this with `useAnimatedScrollHandler` driving several `useAnimatedStyle` interpolations from one shared value.
- **Interruptible dismissal.** Pulling a card down and releasing hands velocity to a spring; grabbing it again mid-flight catches it at its current position.

---

## Family (Ethereum wallet, iOS) — the motion reference

**Take:** the most-cited 2025–26 reference for continuous, physical motion on mobile.

**Mechanisms:**
- **Nothing restarts.** Every transition is a spring driven from the element's current position and velocity. Interrupt any animation and it retargets rather than snapping or replaying. This is the practical difference between shared-value/spring animation and keyframes.
- **Haptics coupled to state change, not to touch.** A haptic fires when a value *commits* — a snap point reached, a threshold crossed, a transaction confirmed — so the haptic carries information rather than noise.
- **Morphing rather than cross-fading.** Elements that persist across states move and reshape; they are not faded out and replaced. This requires laying out the two states from a shared geometry rather than as independent screens.

**Caveat:** Family's motion budget is high because the app is used occasionally and its interactions are consequential (money). Do not port that budget to a high-frequency utility screen.

---

## Raycast — density with hierarchy

**Take:** how to be information-dense without becoming noisy.

**Mechanisms:** a single accent used only for the current selection; hierarchy from type weight and one-step size differences rather than from boxes and dividers; hairline separators at very low contrast; icons at one consistent optical size and stroke.

**Also take:** its empty and loading states — the empty command list is genuinely useful (it suggests actions) rather than an apology, and results stream in without a layout-shifting spinner.

---

## Arc / Dia — structural courage

**Take:** proof that layout can deviate from the hero-plus-three-cards skeleton and remain legible. Navigation moved to an unexpected place, chrome collapsed away, the content given the whole frame.

**Use it as:** the counter-example to cite when a screen is drifting toward the canonical template. The point is not to copy Arc's specific sidebar; the point is that structure can be argued from the product's actual behaviour.

**Don't take:** novelty for its own sake. Arc's structure earns itself because browsing genuinely is tab-management; the same move applied to a form is just confusing.

---

## Stripe (web/docs) — typographic system and content-first layout

**Take:** a genuine type scale, visible and consistent across marketing, docs and dashboard; a body measure that stays in the 45–75 character band; real code and real product surfaces used as imagery rather than illustration.

**Mechanism:** documentation laid out from content structure outward — the code sample dictates the column, the column dictates the page, rather than content being poured into a pre-chosen three-column grid.

---

## Duolingo — reward moments only

**Take:** the one place where bouncy, overshooting, character-driven animation is *correct*, because frequency-of-use and emotional reward are the product.

**Mechanism:** the celebration animations are reserved for genuine completion events, and the routine interactions (selecting an answer, advancing) are fast and quiet. Even here the frequency rule holds — the delight is on the rare event, not on every tap.

**Cite it only for:** streak celebrations, first-run moments, achievement unlocks, successful completion of a long flow.

**Never cite it for:** buttons, navigation, forms, list interactions, or anything a user does more than a few times a session.

---

## Utility UI vs reward moments

The single most common failure when "taking inspiration" is applying a reward-moment reference to a utility surface.

| | Utility UI | Reward moments |
|---|---|---|
| Examples | Forms, lists, navigation, search, settings, tables, keyboard actions | Onboarding completion, first successful action, streaks, achievements, payment confirmed, empty-state first use |
| Frequency | Tens to hundreds of times a day | Rare, sometimes once |
| Motion budget | 0–200ms, opacity/colour, `bounce: 0` | Up to 600ms, spring with visible overshoot, staggered choreography |
| Haptics | Selection tick at most | Success notification |
| Reference | Linear, Raycast, Things, Stripe | Duolingo, Family, Apple's onboarding |

**Rule:** decide which category a surface is in *before* choosing a reference. A checkout button that celebrates on every press is the same error as a streak screen that fades in flatly — both cite the wrong reference for the surface.

---

## How to use a reference in practice

1. **Name the app and the specific screen or interaction**, not the app in general.
2. **State the mechanism**, not the impression — "spring driven from release velocity, interruptible" rather than "smooth".
3. **State what you are not taking.** Every reference carries decisions inappropriate to your context; naming them prevents wholesale imitation.
4. **Check the surface category first.** Utility or reward — the same reference is right for one and wrong for the other.
5. **If you cannot state a mechanism, you do not have a reference.** "Make it look like Linear" without "monochrome, one accent for status, no animation on repeated actions" is a vibe, and vibes are how slop gets built.

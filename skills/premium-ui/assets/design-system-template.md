# Design system — <app name>

Locked <date>. Every screen in this project is built against this file and audited against it before merge.
Change it deliberately and record the change in the decisions log rather than editing a row in place.

If a value is not in this file, it does not exist. A hex, size, radius or duration hardcoded in a component
is a defect, not a shortcut.

## Craft reference

| | |
|---|---|
| Primary reference | <app name — e.g. Linear> |
| What we take | <the specific mechanism, not the impression — e.g. "local-first mutations render before the round trip; no spinner between intent and result"> |
| What we do NOT take | <the decision that does not fit this product — e.g. "its austerity; our onboarding needs warmth"> |
| Secondary reference | <app> — <mechanism> |
| Surface category | utility / reward — governs the motion and haptics budget below |

## Typefaces

| Role | Family | Weights shipped | Licence | Status |
|---|---|---|---|---|
| Display / headings | <family> | <400, 600, 700> | <OFL / commercial / variable> | <purchased / free / pending> |
| Body / UI | <family> | <400, 500, 600> | | |
| Mono (code, numerals) | <family> | <400, 500> | | |

Tabular numerals enabled on: <where — balances, counts, timers>.
Variable `opsz` axis available: <yes / no>. If no, the tracking column below is the manual substitute.

## Type scale

Ratio <1.200 minor third / 1.250 major third>. Base <16>px.

| Step | Token | Size | Line height | Tracking | Weight | Used for |
|---|---|---|---|---|---|---|
| −1 | `text-xs` | <12> | <16 / 1.35> | <+0.02em> | <500> | Labels, captions, overline |
| 0 | `text-sm` | <14> | <20 / 1.45> | <+0.005em> | <400> | Secondary body, list meta |
| 1 | `text-base` | <16> | <25 / 1.55> | <0> | <400> | Body |
| 2 | `text-lg` | <20> | <28 / 1.40> | <−0.005em> | <500> | Subhead, card title |
| 3 | `text-xl` | <25> | <31 / 1.25> | <−0.015em> | <600> | Section heading |
| 4 | `text-2xl` | <31> | <37 / 1.18> | <−0.02em> | <600> | Page title |
| 5 | `text-3xl` | <39> | <43 / 1.10> | <−0.03em> | <700> | Display |

Body measure: <45–75> characters. Line height tightens and tracking goes negative as size grows — never one
line height across all steps.

## Colour

### Neutral ramp

Hue <deg>, shifted <5–15>° toward the accent. Saturation <2–6>% light end → <8–12>% dark end.

| Step | Hex | | Step | Hex |
|---|---|---|---|---|
| 50 | <#> | | 500 | <#> |
| 100 | <#> | | 600 | <#> |
| 200 | <#> | | 700 | <#> |
| 300 | <#> | | 800 | <#> |
| 400 | <#> | | 900 | <#> |
| | | | 950 | <#> |

### Accent

One accent. It marks the primary action and the current state, nothing else.

| | Light | Dark | Why this hue |
|---|---|---|---|
| Accent | <#> (step <600>) | <#> (step <400>) | <stated reason — brand, category, contrast> |
| Accent foreground | <#> | <#> | |
| Accent subtle | <#> | <rgba(...)> | |

Hue is **not** in 255–280. If it is, justify it here or change it.

### Semantic map

Components reference only this column. Dark is a remap, never an inversion.

| Token | Light | Dark |
|---|---|---|
| `bg` | <#> | <#0B0B0E — not pure black> |
| `surface` | <#> | <#> |
| `surfaceRaised` | <#> | <#> |
| `overlay` | <#> | <#> |
| `scrim` | <rgba> | <rgba> |
| `border` | <#> | <rgba(255,255,255,0.10)> |
| `borderStrong` | <#> | <rgba(255,255,255,0.18)> |
| `text` | <#> | <#EDEDF0 — not pure white> |
| `textMuted` | <#> | <#> |
| `textInverse` | <#> | <#> |
| `accent` | <#> | <#> |
| `danger` | <#> | <#> |
| `success` | <#> | <#> |
| `warning` | <#> | <#> |

Dark-mode corrections applied: accent saturation reduced <%> and lightened <n> steps; display weight dropped
one step at ≥<25>px; borders are white alphas not grey hexes; images get a <4–8>% dim overlay.

## Elevation

Depth is surface luminance plus a hairline. Shadows only for genuinely floating objects. In dark mode,
elevation is lightness — shadows are invisible there.

| Level | Surface | Border | Shadow | Used for |
|---|---|---|---|---|
| 0 | `bg` | none | none | Page ground |
| 1 | `surface` | 1px `border` | none | Cards at rest, list containers |
| 2 | `surfaceRaised` | 1px `border` | `shadow-1` | Hover/pressed cards, sticky headers |
| 3 | `overlay` | 1px `borderStrong` | `shadow-2` | Menus, popovers, tooltips |
| 4 | `overlay` | 1px `borderStrong` | `shadow-3` + scrim | Sheets, modals, dialogs |

Hairline width: `StyleSheet.hairlineWidth` (native) / `1px` (web).

Shadow family — one light source, above and slightly behind. X always 0.

| Token | Value |
|---|---|
| `shadow-1` | `0 1px 2px <rgba>, 0 1px 3px <rgba>` |
| `shadow-2` | `0 4px 8px <rgba>, 0 2px 4px <rgba>` |
| `shadow-3` | `0 12px 24px <rgba>, 0 4px 8px <rgba>` |

Never tint a shadow with the accent. Two elements at the same level share a shadow token exactly.

## Spacing

Base unit derived from body line height (<25> ÷ 4 ≈ <6>, rounded to <4>).

Scale: `4, 8, 12, 16, 20, 24, 32, 40, 56, 72, 96, 128`. No arbitrary values.

**Proximity rule:** the gap between related items is at least **two scale steps smaller** than the gap
separating groups. Label→input `<8>`; group→group `<24–32>`. Equal spacing collapses hierarchy and is the
most common slop tell.

Density decisions:

| Region | Row height / vertical rhythm | Internal padding |
|---|---|---|
| List row | <44–56> | <12–16> |
| Card | — | <16–24> |
| Form group separation | <24–32> | — |
| Content section | <48–64> | — |
| Marketing section | <96–160> | — |

## Radius

| Token | Value | Element classes |
|---|---|---|
| `radius-1` | <4> | Chips, tags, badges |
| `radius-2` | <8> | Buttons, inputs, selects |
| `radius-3` | <12> | Cards, list containers, images |
| `radius-4` | <20> | Sheets, modals |
| `full` | 999 | Avatars and pills **only** |

**Nested radius rule:** inner radius = outer radius − padding. A `radius-3` card with `<8>`px padding holds a
`radius-1` inner element. Never one radius everywhere; never `full` on a rectangular button.

## Iconography

| | |
|---|---|
| Set | <lucide-react-native / SF Symbols / custom> — one set, no exceptions |
| Stroke width | <1.5>px |
| Optical sizes | <16 / 20 / 24>, no free-scaling |
| Alignment | Cap-height of adjacent text, not the text box |
| Emoji as icons | **Forbidden** |

## Motion

Budget follows the surface category above: utility surfaces get 0–200ms and no bounce; reward moments get
up to 600ms and visible spring.

| Token | Value | Used for |
|---|---|---|
| `duration-instant` | 0 | Actions performed 100+×/day; all keyboard-initiated actions |
| `duration-fast` | <150> | Press feedback, colour, opacity, tooltips |
| `duration-base` | <250> | Menus, dropdowns, route transitions |
| `duration-slow` | <400> | Sheets, modals, drawers |
| `ease-out` | `cubic-bezier(0.23,1,0.32,1)` | Entering and exiting — the default |
| `ease-in-out` | `cubic-bezier(0.77,0,0.175,1)` | On-screen movement |
| `ease-drawer` | `cubic-bezier(0.32,0.72,0,1)` | Sheets |
| `spring-default` | `{ duration: 0.5, bounce: <0> }` | Gesture handoff, drag momentum |
| `spring-reward` | `{ duration: 0.5, bounce: <0.25> }` | Reward moments only |
| `stagger` | <50>ms, capped at <6> items | List entry |

Rules in force: never `ease-in` on entering UI; exit is 0.7–0.8× enter; never `scale(0)` — enter from
`scale(<0.96>)`; popovers use `transform-origin` at the trigger; animate transform and opacity only;
reduced motion is honoured via `<ReducedMotionConfig mode={ReduceMotion.System} />` and `useReducedMotion()`.

## Haptics

| Event | Haptic | Notes |
|---|---|---|
| Picker / segment snap | `selectionAsync()` | |
| Toggle commit | `impactAsync(Light)` | On state change, not on touch |
| Threshold crossed (pull-to-refresh) | `impactAsync(Light)` | |
| Task / flow completed | `notificationAsync(Success)` | |
| Destructive confirmed | `notificationAsync(Warning)` | |
| Everything else | **none** | Never on scroll, never on every tap |

Platform: <iOS only / both>. Respect the system haptics setting.

## State inventory

Every data-bearing screen ships all of these before it merges. Tick per screen.

- [ ] **Loading** — skeleton matching the final layout, not a spinner
- [ ] **Empty** — explains the state *and* offers the primary action
- [ ] **Error** — names what failed and what to do; has a retry
- [ ] **Offline / stale** — distinguishable from error
- [ ] **Partial** — some data loaded, some failed
- [ ] **Success** — confirmed, with the optimistic write reconciled
- [ ] **Optimistic + rollback** — user-initiated mutations apply immediately, animate a rollback on failure
- [ ] **Pressed / focused / selected / disabled** — visually distinct from each other, disabled explains why

Microcopy for each is written, not placeholder. No "Something went wrong".

## Accessibility floor

| | Requirement |
|---|---|
| Touch targets | ≥44×44pt iOS / 48×48dp Android; `hitSlop` for smaller visuals |
| Contrast | 4.5:1 body, 3:1 large text and UI boundaries, **verified per theme**; APCA cross-check on tinted surfaces |
| Dynamic type | Scales to ≥200%; `maxFontSizeMultiplier` capped only on <tab bars, badges>; layouts reflow, never clip |
| Layout switch | Row → stacked above `fontScale` <1.3> |
| Screen reader | Every custom pressable has `accessibilityRole`, `accessibilityLabel`, `accessibilityState`; compound rows grouped with `accessible` on the parent |
| Decorative views | `importantForAccessibility="no-hide-descendants"` |
| Async results | Announced with `AccessibilityInfo.announceForAccessibility` |
| Focus | Moves into sheets on open, restores to the trigger on close, trapped while open; visible `:focus-visible` ring on web |
| Reduced motion | Honoured; UI is coherent when animations jump to their end state |

## Decisions log

| Date | Decision | Alternative rejected | Why | By |
|---|---|---|---|---|
| <date> | <e.g. accent = #155EC9> | <indigo> | <hue 255–280 is the 2026 AI tell; blue-600 reads as trustworthy in fintech> | <name> |

A decision that changes more than one token gets an ADR in `docs/app/decisions/`.

## Run before merging a screen

1. Run the full **slop checklist** (`references/slop-checklist.md`). Grep first, judge second. **3+ hits = redesign, not patch.**
2. Confirm no hardcoded hex, size, radius or duration in the diff: `rg '#[0-9a-fA-F]{6}|[0-9]+px' <files>`.
3. Confirm every size in the diff is a step in the type scale table above.
4. Confirm the proximity rule holds: related gaps are ≥2 steps tighter than group gaps.
5. Walk the state inventory. Every box ticked or explicitly N/A with a reason.
6. Toggle dark mode. Re-check contrast; confirm elevation still reads.
7. Set text size to the largest accessibility size. Confirm nothing clips.
8. Enable Reduce Motion. Confirm the screen is still coherent.
9. Traverse with VoiceOver / TalkBack. Every control announces role, label and state.
10. Test the interaction on a **release build on a low-end Android device**. Impressions from a debug build on a recent iPhone do not count.

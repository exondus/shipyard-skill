---
name: premium-ui
description: >
  Design and build app interfaces that look deliberately made rather than generated — establishing the
  token system and type scale, laying out screens, choosing and tuning motion, and auditing existing UI
  against the tells of AI-generated design. Use whenever building or restyling a screen, component or
  landing page, setting up a design system or theme, adding animation, micro-interactions or haptics,
  implementing dark mode, or when someone says the UI looks generic, templated, AI-made, cheap or
  unpolished, or asks to make something feel premium, polished or high-end. Also owns interface
  accessibility — VoiceOver and TalkBack labelling, dynamic type and font scaling, touch targets,
  contrast and focus management. Covers React Native / Reanimated and web.
---

# Premium interface

Two jobs. Do not skip the first one.

**Job one: do not produce slop.** There is now a recognisable house style to machine-generated
interfaces, and users clock it in under a second — indigo-violet primary, gradient on a headline,
centred hero over three identical feature cards, one radius everywhere, emoji as icons, and no state
that isn't the happy path. Producing it is the default outcome, not a risk; avoiding it takes
deliberate effort on every screen.

**Job two: build the thing that makes an app feel expensive**, which is not decoration. It is
hierarchy, restraint, states that all exist, and motion that behaves like physics rather than
punctuation.

## The audit, first and last

Read `references/slop-checklist.md` before designing and run it against the finished screen. The
checklist has a static half and a rendered half: grep finds the defaults, and `visual-verification`
finds what only exists once rendered — clipping at maximum text size, real contrast after compositing, a
skeleton that does not match the layout it replaces, a target covered by a sibling. `premium-ui` still
owns the verdict. It is a concrete list — colour, type, layout, icons, copy, states, motion — and it
is checkable, which opinions about taste are not. **Three or more hits means redesign, not adjust.**

The five that catch the most work:

1. A primary colour in the indigo-violet band, or a purple-to-cyan gradient anywhere.
2. Every corner the same radius, and every gap the same size regardless of whether the things are
   related.
3. Emoji standing in for icons.
4. No empty, loading, error or offline state designed — only the state where everything worked.
5. Every animation the same duration, or a hover-scale on everything.

If you cannot name the specific reason a value was chosen — this radius, this weight, this 24px — it
was defaulted, and defaults are what the checklist detects.

## Establish the system before the screens

Write `docs/app/design-system.md` and `packages/tokens` first, in three tiers: **primitive** (raw
ramps, never referenced by a component), **semantic** (`bg`, `surface`, `surfaceRaised`, `border`,
`text`, `textMuted`, `accent` — the only layer a theme swaps), **component**. One token source
generates both the native theme and the web CSS variables, so the two platforms cannot drift.

**Type.** Pick a modular scale and derive every size from it; six steps is enough. Distinct
line-height per step. Negative tracking above about 28px, and never a heading that differs from body
by weight alone. Pair a display face with a body face, or one superfamily at two optical sizes; one
face at default weights is a tell.

**Colour.** One accent, used only for the primary action and current state. Everything else is a
neutral ramp — and build a custom one, hue-shifted slightly toward the accent, rather than shipping a
framework's default grey, which is itself a tell. Semantic colours are for state, never decoration.

**Depth.** Express elevation with layered surfaces and a hairline border, not with shadows. Reserve
real shadows for things that genuinely float, and derive every one from a single light source. In dark
mode raise surfaces by lightening; shadows are invisible on dark, and inverting a light palette is not
a dark theme.

**Spacing.** Derive the spacing scale from the type scale rather than an arbitrary 8px grid. Space
between related things must be at least two steps smaller than space between groups — proximity is
what makes a layout readable, and uniform spacing is what makes it look generated. Vary density
deliberately: a list row and a marketing section should not share a padding token.

**Radius.** Four steps, assigned by element class. Nested radius equals outer minus the gap.

**Icons.** One set, one stroke width, one optical size, aligned to cap height.

## States are not optional

Every data surface ships loading (a skeleton matching the final layout, not a spinner), empty
(explains, and offers the primary action), error (says what failed and what to do), offline, and
success. Optimistic UI for anything the user initiates.

This is the highest-leverage half-day in the whole build. It is also the thing most reliably missing
from generated work, which is why it is on the checklist.

Lay out from real content before styling: the longest string, the missing avatar, the three-digit
count, the pseudo-localised label. `localization-foundation` explains why the last one matters even in
a single-locale launch.

## Motion

Restraint is the whole discipline. `references/motion.md` has the tokens; the rules that matter:

- **Frequency governs.** An action performed a hundred times a day gets no animation. Occasional
  actions get standard motion. Only rare and first-run moments earn delight.
- **Durations**: press feedback 100–160ms, tooltips 125–200ms, menus 150–250ms, sheets and modals
  200–500ms, screen transitions 250–350ms. Most UI motion stays under 300ms, and duration scales with
  distance travelled.
- **Easing**: ease-out entering, ease-in-out moving on screen, linear for continuous. **Never ease-in
  on entering UI** — it reads as lag.
- **Springs for anything with or handed off from a gesture**, because they absorb velocity and are
  interruptible; timing curves for discrete state changes. Keep bounce low; overshoot on a routine
  action is the cartoonish register, not the expensive one.
- Never scale from zero — enter from 0.94–0.97 with opacity. Popovers scale from their trigger's
  origin. Animate only transform and opacity; animating width, height or padding triggers layout every
  frame and is the usual cause of jank in list and layout animations.
- Stagger 30–80ms per item, capped at about six, then fade the rest in as a block. Exit at roughly
  0.7–0.8× the enter duration.
- **Respect reduced motion.** The correct response is fewer and gentler animations — keep opacity and
  colour, drop translation and scale — not zero.

The micro-interactions that actually read as expensive: an immediate press state, haptics paired only
to a state change and never to every tap, optimistic writes with rollback, a scroll-linked collapsing
header driven on the UI thread, list items that enter and leave, and keyboard transitions that follow
the native keyboard curve rather than a guessed duration.

## Implementation

`references/stack.md` names the libraries and the versions that were current in August 2026 — check
them before installing. The performance rules are short and non-negotiable: worklets run on the UI
thread and anything touching React state crosses back at a cost, so batch it; reading a shared value
in render or driving animation from a JS scroll handler puts work on the JS thread every frame;
profile in release builds on a low-end Android, never in a simulator.

Choose the styling layer once and record it in `stack.md`. A StyleSheet-flavoured runtime with
C++-side theme updates is the better default for animation-heavy native apps; a Tailwind-compatible
one is the better default when a monorepo shares tokens and components with a web app built on
Tailwind. Either is fine. Mixing two is not.

## Accessibility is a craft signal

Not a compliance chore — the same discipline read from another angle, and Apple's editorial team
notices it.

Support font scaling to at least 200% and let layouts reflow rather than clip; cap the multiplier only
on fixed-height chrome, and never disable scaling wholesale. Touch targets at 44pt / 48dp, with hit
slop for visually smaller controls. Contrast verified per theme, not once in light mode. Every custom
pressable gets a role, a label and a state; compound rows are grouped so a screen reader reads one
item, not five. Focus moves into a sheet on open and returns to the trigger on close.

## Name a reference

Vague ambition produces average results. Before building, name a specific app and the specific thing
being borrowed — the interruptible, velocity-aware card motion of a wallet app; the density and
state-completeness of a command palette; the spacing rhythm and gesture-driven list interactions of a
task app. Write it in `docs/app/design-system.md`. "Make it premium" is not a brief; "match this
app's press-state latency and its empty states" is.

`references/references.md` lists apps worth citing and what specifically is good about each.

## Reference files

- `references/slop-checklist.md` — the audit, run before and after every screen
- `references/motion.md` — duration and easing tokens, spring configuration, choreography
- `references/stack.md` — libraries, versions, performance rules, styling-layer choice
- `references/tokens.md` — the three-tier token architecture and dark mode done properly
- `references/references.md` — named craft references and what to take from each
- `assets/design-system-template.md` — copy into `docs/app/design-system.md` and fill it in

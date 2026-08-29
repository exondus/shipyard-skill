# The Slop Checklist

Time-sensitive: the specific hex values and utility class names below are the 2025–2026 tells. Defaults move — re-check the current shadcn `components.json` baseColor and Tailwind palette before trusting a specific class name as evidence.

Every item is a detectable signal, not a vibe. If you can't point at a hex, a class, a number, or a structure, it isn't on this list.

---

## Colour

- [ ] Primary/CTA colour has hue in the **255–280** range. Detect: `#6366f1`, `#7c3aed`, `#8b5cf6`, `#a855f7`, `indigo-500/600`, `violet-*`, `purple-*`, or CSS `--primary` at `hsl(2xx …)`. Called the single loudest AI tell of 2026 ([925studios](https://www.925studios.co/blog/ai-slop-design-tells)).
- [ ] Gradient from purple to blue or purple to cyan. Detect: `from-purple-* to-blue-*`, `from-indigo-* to-cyan-*`, `bg-gradient-to-br` on a hero or card.
- [ ] **Gradient on text.** Detect: `bg-clip-text text-transparent`, or `background-clip: text` with a gradient fill.
- [ ] The counter-cliché "tasteful default" palette: cream/sage/serif. Detect: `#faf8f5`, `#f5f1e8`, `bg-stone-50`, `bg-stone-100`, plus a deep green primary around `#15573a`–`#1a4d3a` ([Unslop UI](https://www.claudecodehq.com/playbooks/unslop-ui)).
- [ ] Untouched shadcn/Tailwind defaults. Detect: `components.json` with `"baseColor": "slate"`, unmodified `--background/--foreground/--primary` vars, repeated `bg-slate-*` or `bg-zinc-*` on cards.
- [ ] Unprompted neon glow. Detect: `shadow-[0_0_*]` with a saturated colour, `box-shadow` whose colour is the accent at high alpha, `text-shadow` glow on dark.
- [ ] More than one accent competing for "primary", or gradients on three or more distinct surface types in one screen.

**Instead:** one accent hue chosen for a stated reason, a custom neutral ramp hue-shifted 5–15° toward that accent, semantic colours reserved for state, gradients limited to at most one restrained surface and never on type.

---

## Type

- [ ] Inter, Geist, or Roboto is the only typeface, at stock weights, with no tracking adjustment.
- [ ] The counter-cliché: Instrument Serif, Fraunces, or Playfair as heading face with **no paired body face**.
- [ ] No modular scale. Detect: font sizes that are not derivable from a ratio — e.g. 13, 15, 16, 18, 22, 31 with no relationship; or arbitrary `text-[17px]` values scattered.
- [ ] Headings differ from body **only** by weight or only by size, never both plus line-height and tracking.
- [ ] Same line-height across every step (e.g. `leading-normal` everywhere). Display type at 1.5 line-height is a reliable tell.
- [ ] No negative tracking on large type. Detect: any text ≥28px with `letter-spacing: 0` / no `tracking-tight`.
- [ ] Measure over ~80 characters for body copy, or under ~40 on desktop.

**Instead:** a 6-step modular scale (1.200 for dense UI, 1.250 for marketing), per-step line-height (1.1–1.2 display, 1.3 subhead, 1.45–1.6 body) and per-step tracking (−0.01 to −0.03em above 28px, positive on small caps/labels), and a display face paired with a body face or one superfamily at two optical sizes.

---

## Layout

- [ ] **The canonical skeleton:** centred hero → oversized headline → subheading → two buttons (one filled, one outline) → `grid grid-cols-1 md:grid-cols-3` feature cards → CTA band → footer. Detect the `md:grid-cols-3` feature grid directly.
- [ ] Cards structurally identical: icon at top, heading, exactly two lines of body, repeated 3× or 6×.
- [ ] **Uniform radius on everything.** Detect: `rounded-2xl` / `rounded-3xl` / `rounded-full` applied to cards, inputs, buttons, avatars and containers alike; or `border-radius: 9999px` on non-pill elements.
- [ ] Everything centred. Detect: `text-center` + `mx-auto` + `items-center` on every section with no left-aligned content anywhere.
- [ ] Glassmorphism applied to more than one layer. Detect: `backdrop-blur-*` on cards *and* nav *and* modal, rather than on a single floating layer over real content.
- [ ] No optical alignment corrections. Detect: icon+label centred by bounding box rather than optical mass; a play/chevron glyph not nudged toward its optical centre; nested radii equal to their parent's (inner radius should be outer − padding).
- [ ] Every section the same shape and density: same width container, same vertical padding, no variation between a dense data region and an editorial region.
- [ ] No content-driven layout: nothing handles the longest string, a missing avatar, a 4-digit count, or wrapped text.

**Instead:** structure follows the content's purpose; vary section shape and density; show a real product screenshot instead of an icon-card grid; define a 4-step radius ladder assigned by element class; correct optical alignment by eye, not by box.

---

## Spacing

- [ ] Rigid grid with no rhythm. Detect: every section `py-24`, every card `p-6`, list rows and marketing blocks sharing the same padding token.
- [ ] **Equal spacing between related and unrelated elements.** Detect: gap between a label and its input identical to the gap between two separate form groups. This is the single most common hierarchy failure.
- [ ] Mixed arbitrary values — the opposite failure. Detect: `p-3` next to `p-7`, `mt-[37px]`, `gap-[13px]`, values not on any scale.
- [ ] No density decision: a data table or list row taller than ~56px, or a marketing section with under ~64px of vertical padding.
- [ ] Spacing scale unrelated to the type scale — an 8px grid imposed on a 17px/1.5 body rhythm, so nothing aligns to a baseline.

**Instead:** derive the base spacing unit from the body line-height (÷2 or ÷4); make between-group spacing at least two scale steps larger than within-group spacing; choose density per region (44–56px list rows, 96–160px marketing sections).

---

## Icons & imagery

- [ ] **Emoji used as UI iconography.** Detect: 🚀 ✨ ⚡ 🔒 ✅ 🎯 💡 in headings, feature titles, bullets or buttons. Near-conclusive on its own.
- [ ] More than one icon set in the build. Detect: `lucide-react` alongside `react-icons`, Heroicons, or inline hand-drawn SVGs.
- [ ] One set at mixed stroke widths or mixed optical sizes. Detect: `strokeWidth` differing between icons in the same row; a 16px and a 24px icon rendered at the same visual size.
- [ ] Icons sitting at the top of every card, thin-line and interchangeable.
- [ ] Stock/3D-blob/gradient-figure illustration standing in for the actual product, or placeholder imagery still present (`unsplash.com/random`, `via.placeholder.com`, grey boxes).

**Instead:** one icon set, one stroke width (1.5px at 20–24px), one optical size, aligned to cap-height not to the text box; real product screenshots over decorative illustration.

---

## Copy

- [ ] Cliché verbs and constructions. Detect the literal strings: "Transform your", "Supercharge", "Unleash", "Effortlessly", "Seamlessly", "Take your X to the next level", "Build faster. Ship smarter."
- [ ] Headline that names no audience and no specific outcome — it could sit on any of ten thousand products.
- [ ] Feature titles that are category nouns ("Analytics", "Security", "Integrations") with a generic sentence beneath.
- [ ] Placeholder-grade microcopy shipped as final: "Something went wrong", "No data", "Loading…", "Oops!".
- [ ] Lorem ipsum, or invented statistics ("10,000+ teams") with no source.

**Instead:** name the user and the specific outcome in the headline; every error says what failed and what to do next; every empty state explains the state and offers the primary action.

---

## States

- [ ] Only the happy path exists. Detect: no loading, empty, error, offline, partial, or success rendering in the component.
- [ ] Loading is a centred spinner rather than a skeleton matching the final layout.
- [ ] Empty state is a sentence with no action affordance.
- [ ] Error state has no retry, and no distinction between "failed" and "nothing here".
- [ ] No optimistic update on a user-initiated mutation — the UI waits for the server round trip.
- [ ] Disabled states rendered only as reduced opacity, with no explanation of *why* it's disabled.
- [ ] No pressed / focused / selected visual distinct from hover.

**Instead:** every data surface ships loading (layout-shaped skeleton), empty (explains + offers the primary action), error (cause + recovery), offline/partial, and success. Optimistic writes with rollback for anything the user initiates.

---

## Motion

- [ ] One duration for everything. Detect: a single `duration-300` or `transition-all` used on presses, menus and modals alike.
- [ ] `transition-all`. It animates layout properties by accident.
- [ ] Animation on every element. Detect: `whileHover={{ scale: 1.05 }}` on all cards, `data-aos="fade-up"` on every section, scroll-jacking libraries.
- [ ] `ease-in` on entering UI, or the default `ease` where `ease-out` belongs.
- [ ] Bounce/overshoot on routine, high-frequency actions.
- [ ] Elements scaling from `scale(0)` rather than 0.94–0.97.
- [ ] Popovers/menus animating from centre instead of from the trigger (`transform-origin`).
- [ ] Animating `width`, `height`, `padding`, `margin`, `top`, `left` — layout every frame.
- [ ] No `prefers-reduced-motion` (web) / `useReducedMotion()` or `ReducedMotionConfig` (Reanimated) handling anywhere.
- [ ] Hover effects not gated behind `@media (hover: hover) and (pointer: fine)` — causes stuck hover states on touch.
- [ ] Animation on keyboard-initiated actions, which repeat hundreds of times a day.

**Instead:** duration by interaction class (see `motion.md`); `ease-out` for entry/exit; frequency governs whether to animate at all; transform and opacity only; reduced motion means fewer and gentler, not zero.

---

## Explicitly NOT slop — do not flag these

Mesh / blob / aurora backgrounds used deliberately. Bento grids. Dark mode itself. shadcn or Tailwind as tools. Rounded corners as such. A serif display face that is genuinely paired. These get mistaken for tells; the tell is the *default*, not the technique ([Unslop UI](https://www.claudecodehq.com/playbooks/unslop-ui)).

---

## Scoring

Count checked boxes across all groups.

| Hits | Verdict |
|---|---|
| 0–1 | Ship. Note the hits as follow-ups. |
| 2 | Fix in place before shipping. |
| **3+** | **Redesign.** Do not patch — three tells means the underlying decisions were defaults, not choices. Return to colour, type and layout and make each one deliberately. |

Weighted overrides — any **one** of these alone is a redesign: emoji as iconography; gradient on text; the exact hero + `md:grid-cols-3` + CTA skeleton; a 255–280 hue primary that nobody chose.

---

## How to run this audit on an existing screen

1. **Read the code before looking at the render.** Grep for the literal signals: `md:grid-cols-3`, `bg-clip-text`, `rounded-3xl`, `rounded-full`, `#6366f1|#7c3aed|#8b5cf6`, `indigo-|violet-|purple-`, `bg-slate-|bg-stone-`, `transition-all`, `whileHover`, `backdrop-blur`, `shadow-[0_0`, and the emoji range. Grep is faster and more objective than judgement.
2. **Check the config files.** `components.json` baseColor, the Tailwind theme block, the font imports. Untouched defaults here explain most downstream hits.
3. **Extract the type scale.** List every font size used in the file. If they don't fall on a ratio, that's a hit.
4. **Extract the spacing values.** List every padding/gap/margin. Look specifically at whether related and unrelated elements are spaced identically.
5. **Extract the radii.** More than 4 distinct values, or exactly 1 value applied everywhere, are both hits.
6. **Enumerate states.** For each data-bearing component, ask: where is loading, empty, error, offline, success? Missing = hit.
7. **Enumerate durations.** Collect every duration in the file. One value = hit. No reduced-motion guard = hit.
8. **Score, then act.** Report hits with file:line evidence. At 3+, state plainly that this needs redesign rather than patching, and start from the colour/type/layout decisions.

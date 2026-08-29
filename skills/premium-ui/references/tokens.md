# Design Tokens & Theming

Time-sensitive: the styling-library recommendation at the end tracks NativeWind 4.2.6, Unistyles 3.3.0 and Uniwind 1.11.0 as of 29 Aug 2026. Check the registry — this area is moving fast, and NativeWind v5 and Uniwind are both in flight.

---

## Three-tier architecture

**Primitive** → raw values. Never referenced by a component.
**Semantic** → roles. The only tier a theme swaps.
**Component** → per-component aliases pointing at semantic tokens.

The rule that makes this work: **a component file may reference only component or semantic tokens.** A raw hex or a primitive name inside a component is a defect. Grep for `#[0-9a-f]{6}` in `components/` as an audit.

```ts
// tokens/primitive.ts
export const primitive = {
  gray: { 50:'#F7F7F8', 100:'#EDEDF0', 200:'#DCDCE2', 300:'#B9B9C4',
          400:'#8E8E9E', 500:'#6B6B7B', 600:'#4E4E5C', 700:'#3A3A45',
          800:'#26262E', 900:'#17171C', 950:'#0B0B0E' },
  accent:{ 50:'#EEF6FF', 100:'#D9EBFF', 200:'#B4D6FF', 300:'#7FB8FF',
           400:'#4A97FF', 500:'#1F76F2', 600:'#155EC9', 700:'#12489B',
           800:'#123A78', 900:'#132F5E' },
  red:   { 500:'#DC3A34', 600:'#B32B27' },
  green: { 500:'#1E9E62', 600:'#177A4C' },
  amber: { 500:'#C98A0E', 600:'#9E6B08' },
  space: { 1:4, 2:8, 3:12, 4:16, 5:20, 6:24, 7:32, 8:40, 9:56, 10:72, 11:96, 12:128 },
  radius:{ 1:4, 2:8, 3:12, 4:20 },
  size:  { 1:12, 2:14, 3:16, 4:20, 5:25, 6:31, 7:39 },
  duration:{ instant:0, fast:150, base:250, slow:400 },
  ease:  { out:'cubic-bezier(0.23,1,0.32,1)',
           inOut:'cubic-bezier(0.77,0,0.175,1)',
           drawer:'cubic-bezier(0.32,0.72,0,1)' },
} as const;
```

```ts
// tokens/semantic.ts
export const light = {
  bg:            primitive.gray[50],
  surface:       '#FFFFFF',
  surfaceRaised: '#FFFFFF',
  overlay:       '#FFFFFF',
  scrim:         'rgba(11,11,14,0.45)',
  border:        primitive.gray[200],
  borderStrong:  primitive.gray[300],
  text:          primitive.gray[900],
  textMuted:     primitive.gray[500],
  textInverse:   primitive.gray[50],
  accent:        primitive.accent[600],
  accentFg:      '#FFFFFF',
  accentSubtle:  primitive.accent[50],
  danger:        primitive.red[600],
  success:       primitive.green[600],
  warning:       primitive.amber[600],
};

export const dark: typeof light = {
  bg:            primitive.gray[950],   // #0B0B0E — not #000
  surface:       primitive.gray[900],
  surfaceRaised: primitive.gray[800],
  overlay:       primitive.gray[700],
  scrim:         'rgba(0,0,0,0.6)',
  border:        'rgba(255,255,255,0.10)',
  borderStrong:  'rgba(255,255,255,0.18)',
  text:          primitive.gray[100],   // #EDEDF0 — not #FFF
  textMuted:     primitive.gray[400],
  textInverse:   primitive.gray[950],
  accent:        primitive.accent[400], // lighter, less saturated in dark
  accentFg:      primitive.gray[950],
  accentSubtle:  'rgba(74,151,255,0.14)',
  danger:        primitive.red[500],
  success:       primitive.green[500],
  warning:       primitive.amber[500],
};
```

```ts
// tokens/component.ts
export const component = (t: typeof light) => ({
  button: {
    primary:  { bg: t.accent,  fg: t.accentFg, radius: primitive.radius[2] },
    secondary:{ bg: t.surface, fg: t.text, border: t.border, radius: primitive.radius[2] },
    minHeight: 44,
  },
  card:  { bg: t.surface, border: t.border, radius: primitive.radius[3], padding: primitive.space[5] },
  input: { bg: t.surface, border: t.border, focusRing: t.accent, radius: primitive.radius[2], minHeight: 44 },
  sheet: { bg: t.overlay, radius: primitive.radius[4] },
});
```

---

## Type scale derivation

Pick a ratio: **1.200 (minor third)** for dense/product UI, **1.250 (major third)** for marketing. Base = body size (16px web, 16–17px native). Six or seven steps is enough.

At 1.200 from 16: 12.8 → 16 → 19.2 → 23 → 27.6 → 33.2 → 39.8. Round to integers.

| Step | Size | Line-height | Tracking | Weight | Use |
|---|---|---|---|---|---|
| −1 | 12 | 1.35 (16) | +0.02em | 500 | Labels, captions, overline |
| 0 | 14 | 1.45 (20) | +0.005em | 400/500 | Secondary body, list meta |
| 1 | 16 | 1.55 (25) | 0 | 400 | Body |
| 2 | 20 | 1.40 (28) | −0.005em | 500 | Subhead, card title |
| 3 | 25 | 1.25 (31) | −0.015em | 600 | Section heading |
| 4 | 31 | 1.18 (37) | −0.02em | 600 | Page title |
| 5 | 39 | 1.10 (43) | −0.03em | 700 | Display |

Rules: line-height tightens as size grows; tracking goes negative as size grows and positive as it shrinks. Use a variable font's `opsz` axis where it exists; otherwise these tracking values are the manual substitute. Body measure 45–75 characters.

**Never** ship one line-height across all steps — display type at 1.5 is the most visible amateur tell.

---

## Neutral ramp construction

Do not ship `slate`, `zinc` or `stone`. Build the ramp:

1. Take the accent's hue.
2. Shift 5–15° toward it for the neutral hue (a blue accent → very slightly blue-grey neutrals).
3. Saturation 2–6% at the light end, rising to 8–12% at the dark end (dark neutrals carry tint better).
4. Lightness steps roughly: 97, 93, 88, 76, 62, 48, 36, 27, 18, 11, 5.
5. Check adjacent steps are visually even in **perceptual** lightness (OKLCH `L`), not in HSL `L`.

Verify text pairs with **APCA** (myndex.com/APCA) as well as WCAG ratios — APCA is the sharper judge on tinted and dark surfaces.

---

## Depth: layered surfaces, not shadows

Elevation is expressed by **surface luminance plus a hairline**, with real shadows reserved for genuinely floating objects.

| Level | Light | Dark | Border | Shadow |
|---|---|---|---|---|
| 0 background | `bg` | `bg` | none | none |
| 1 surface | `surface` | +1 gray step | 1px `border` | none |
| 2 raised (card, hover) | `surfaceRaised` | +2 steps | 1px `border` | shadow-1 |
| 3 overlay (menu, popover) | `overlay` | +3 steps | 1px `borderStrong` | shadow-2 |
| 4 sheet / modal | `overlay` | +3 steps | 1px `borderStrong` | shadow-3 + scrim |

The **hairline border** is what reads as craft: `rgba(0,0,0,0.06)` in light, `rgba(255,255,255,0.10)` in dark, always 1 physical pixel (`StyleSheet.hairlineWidth` on native).

**In dark mode, elevation is lightness, never shadow.** Shadows are invisible on dark grounds. If your dark theme is the light theme with the same shadow tokens, nothing reads as raised.

### One light source

Every shadow derives from a single light: above, slightly behind. Y-offset always positive, X always 0, blur roughly 2× the offset, spread negative.

```
shadow-1: 0 1px 2px  rgba(11,11,14,0.06), 0 1px 3px  rgba(11,11,14,0.04)
shadow-2: 0 4px 8px  rgba(11,11,14,0.07), 0 2px 4px  rgba(11,11,14,0.05)
shadow-3: 0 12px 24px rgba(11,11,14,0.10), 0 4px 8px rgba(11,11,14,0.06)
```

Two elements at the same elevation must share a shadow token exactly. Differing shadows on same-level elements is a tell. Never colour a shadow with the accent.

---

## Spacing derived from the type scale

Base unit = body line-height ÷ 4 → 25/4 ≈ 6, or ÷2 ≈ 12. Round to a usable base of 4.

Scale: **4, 8, 12, 16, 20, 24, 32, 40, 56, 72, 96, 128.** No arbitrary values; no `mt-[37px]`.

**Proximity rule:** the gap between related items must be **at least two scale steps smaller** than the gap separating groups. Label→input = 8; group→group = 24 or 32. When these are equal, hierarchy collapses and the screen reads as machine-generated.

**Density is a decision, not a default:**

| Region | Vertical rhythm |
|---|---|
| Dense list / table row | 44–56px row height, 12–16px internal padding |
| Card | 16–24px padding |
| Form section | 24–32px between groups |
| Content section | 48–64px |
| Marketing section | 96–160px |

Using `p-6` and `py-24` uniformly across all of these is the rigidity tell.

---

## Radius ladder

Four steps, assigned by element class:

| Token | Value | Elements |
|---|---|---|
| radius-1 | 4 | Chips, tags, badges, small toggles |
| radius-2 | 8 | Buttons, inputs, selects |
| radius-3 | 12 | Cards, list containers, images |
| radius-4 | 20 | Sheets, modals, large surfaces |
| full | 999 | Avatars and pills **only** |

**Nested radius rule:** inner radius = outer radius − padding. A 12px card with 8px padding holds a 4px inner element. Equal inner and outer radii produce the visible "corner gap" that reads as unresolved.

Never apply one radius to everything, and never use `rounded-full` on a rectangular button.

---

## Dark mode as a semantic remap

Dark mode swaps the **semantic** tier only. Components never branch on theme. Specific corrections:

- **No pure black.** Use ~`#0B0B0E`. Pure black exaggerates OLED smear and kills elevation headroom.
- **No pure white text.** Use ~`#EDEDF0` at ~87% effective. Pure white on near-black glares and blooms.
- **Reduce accent saturation ~10–20% and raise lightness one to two steps.** A saturated light-mode accent vibrates on dark. `accent-600` in light → `accent-400` in dark.
- **Reduce weight one step at large sizes.** Light text on dark optically thickens; a 700 display in light may want 600 in dark.
- **Borders become white alphas**, not grey hexes — `rgba(255,255,255,0.10)` composites correctly over any surface level.
- **Elevation by lightness**, shadows only as scrims under modals.
- **Re-verify contrast per theme.** A pair that passes in light frequently fails in dark, especially muted text and disabled states.
- **Images and illustrations need dark variants** or a 4–8% dimming overlay; a bright screenshot on a dark surface is a light-leak.

---

## Monorepo: one source, two outputs

```
packages/tokens/
  src/primitive.ts      # plain TS, no platform imports
  src/semantic.ts       # light + dark maps
  src/component.ts
  build/
    to-css.ts           # → web: CSS custom properties / Tailwind @theme
    to-native.ts        # → native theme object
```

`to-css.ts` emits:

```css
:root { --color-bg:#F7F7F8; --color-surface:#FFF; --color-accent:#155EC9;
        --radius-2:8px; --space-5:20px; --duration-base:250ms; }
:root[data-theme="dark"] { --color-bg:#0B0B0E; --color-surface:#17171C; --color-accent:#4A97FF; }
```

Tailwind v4 consumes these directly in an `@theme` block; shadcn components then read `--primary`, `--background` etc. mapped onto your semantic names — **overwrite the shadcn defaults, don't add alongside them.**

`to-native.ts` emits the theme object consumed by Unistyles' `StyleSheet.configure({ themes })`, or by a NativeWind/Uniwind Tailwind config generated from the same file.

Non-negotiable: **neither platform hand-writes a hex.** A colour that exists only in the web CSS or only in the native theme is drift, and drift is what makes cross-platform products feel like two products.

---

## Styling library recommendation

| | NativeWind 4.2.6 | Unistyles 3.3.0 | Uniwind 1.11.0 |
|---|---|---|---|
| API | Tailwind `className` | `StyleSheet.create` + theme | Tailwind `className` |
| Tailwind version | v3 (v5 preview targets v4) | n/a | v4 only |
| Build | Babel preset | Babel | Metro plugin only |
| Theme switching | ThemeProvider (React context) | C++ side, no re-render | No provider |
| Perf (2k views, iOS) | 197ms | — | 81ms ([vendor benchmark](https://uniwind.dev/vs-nativewind)) |

**Recommendation:** Unistyles for native-only, animation-heavy premium apps — no context re-renders on theme change and no class-string indirection over animated styles. NativeWind when a monorepo genuinely shares Tailwind/shadcn vocabulary with web and the team thinks in utilities. Uniwind if you want Tailwind v4 and the perf, accepting it is young [UNVERIFIED at production scale]. Plain `StyleSheet.create` remains correct for a small, tightly designed component library.

Whichever you pick, the token package above is the source of truth and outlives the choice.

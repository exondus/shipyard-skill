# RTL: Arabic, Hebrew, Farsi, Urdu

Time-sensitive: `I18nManager` behaviour around auto-flipping has changed across React Native versions, and the New Architecture altered some layout-direction handling. Verify against [reactnative.dev/docs/i18nmanager](https://reactnative.dev/docs/i18nmanager) and test on both platforms for the RN version in use — do not trust this table blind.

## Enablement flow

```ts
import { I18nManager } from 'react-native';
import * as Updates from 'expo-updates';

// At app start, once, before first render:
I18nManager.allowRTL(true);

// When the user picks an RTL language (or an LTR one while in RTL):
async function applyDirection(locale: Locale) {
  const wantRTL = RTL_LOCALES.has(languageCodeOf(locale)); // ar, he, fa, ur, ps, sd, yi
  if (wantRTL === I18nManager.isRTL) return;
  I18nManager.forceRTL(wantRTL);
  await Updates.reloadAsync();          // dev: DevSettings.reload()
}
```

Three facts that dictate the UX:

1. **`allowRTL` and `forceRTL` are persisted natively** and survive restarts. They are not React state.
2. **Neither takes effect until a full app restart.** There is no way to flip layout direction live in RN.
3. `I18nManager.isRTL` is the read. It is true when `forceRTL` is set, or when `allowRTL` is true *and* the device language is RTL *and* the app declares that language (see `CFBundleLocalizations` in `setup.md` — omit `ar` there and iOS will never report RTL).

Therefore the language switcher must either (a) restart immediately after persisting the choice, or (b) show "Restart required to apply" and offer a button. Persist the locale choice **before** calling `reloadAsync()`, or the restart loses it. Do not fire a restart on the OS-locale path without asking — an app that relaunches itself unprompted reads as a crash.

`forceRTL` is documented as development-only. In practice it is the only mechanism available for an in-app RTL language override, so it is used in production; keep `allowRTL(true)` set so device-driven RTL also works, and always pair `forceRTL(false)` when switching back to an LTR language.

`I18nManager.swapLeftAndRightInRTL(false)` opts out of automatic left/right swapping for the whole app — use it only if you have fully migrated to logical properties and want physical values to stay literal (e.g. a chart or canvas). It does not change `isRTL`.

## What flips and what does not

| Property | Auto-flips in RTL? | Use instead |
|---|---|---|
| `flexDirection: 'row'` | **Yes** | Nothing needed. `row-reverse` also flips — beware double negation. |
| `marginLeft` / `marginRight` | Yes (when `doLeftAndRightSwapInRTL`) | `marginStart` / `marginEnd` — explicit, survives the swap setting |
| `paddingLeft` / `paddingRight` | Yes | `paddingStart` / `paddingEnd` |
| `borderLeftWidth` / `borderRightWidth` | Yes | `borderStartWidth` / `borderEndWidth` |
| `borderTopLeftRadius` etc. | Yes | `borderTopStartRadius` / `borderTopEndRadius` |
| `left` / `right` in `position:'absolute'` | **No — unreliable** | `start` / `end` |
| `textAlign: 'left'` | No | `textAlign: 'start'` (or omit; default follows direction) |
| `writingDirection` | n/a | Set `'rtl'` only to force a specific run; usually leave to default |
| `transform: translateX` | **No** | Negate manually: `translateX: I18nManager.isRTL ? -x : x` |
| `ScrollView` horizontal offset | Partially, platform-divergent | Test both platforms; `contentOffset` origin differs |
| `shadowOffset.width` | No | Negate manually |
| Gesture `dx` (Pan/Swipe) | No | Negate the sign for direction-meaningful gestures |
| Chart / canvas / SVG coordinates | No | Intentional — leave physical |

Practical rule: **write `start`/`end` everywhere, always, from day one, and never write `left`/`right` except inside a deliberate physical-coordinate system.** Add an ESLint rule banning `marginLeft|marginRight|paddingLeft|paddingRight|left:|right:` in style objects with an escape-hatch comment.

## Animations

Every `translateX` in an RTL-capable app needs its sign negated. Wrap it once:

```ts
export const rtlX = (x: number) => (I18nManager.isRTL ? -x : x);
// Reanimated:
const style = useAnimatedStyle(() => ({ transform: [{ translateX: rtlX(offset.value) }] }));
```

Same for: carousel paging direction, drawer slide-in edge, swipe-to-delete direction, progress-bar fill origin (`transformOrigin` / anchor), and any `interpolate` output range built from screen width.

## Icon mirroring

**Mirror these** — their meaning is directional and tied to reading order:
back / forward arrows, chevrons used for navigation or disclosure, "next"/"previous" media *navigation* (not playback), undo / redo, reply / forward, indent / outdent, list bullets and tree indentation, progress bars and steppers, sliders, tabs order, breadcrumb separators, page-turn, send (paper-plane), trending arrows tied to a timeline, speech-bubble tails, hamburger→drawer edge, pencil/annotation tools with a directional nib, question-mark-in-flow diagrams.

**Do not mirror** — the glyph is an object, a logo, or a universal convention:
play / pause / stop / record buttons, clocks and watch faces (time still runs clockwise), checkmarks, the ✗ close glyph, brand logos and third-party sign-in buttons, camera, phone/handset, magnifier (either orientation is acceptable but pick one and keep it — mirroring is optional and often looks wrong against a familiar brand), musical notes, physical objects (books, cups, cars — unless the design language mirrors them consistently), anything containing embedded Latin text or numerals, volume/wifi/battery indicators, emoji.

Implementation: a single `<Icon mirror>` prop that applies `transform: [{ scaleX: -1 }]` when `I18nManager.isRTL`, and a per-icon default in the icon registry. Never mirror at the asset level — you would need two asset sets.

## Numbers, bidi and mixed content

Numbers, Latin brand names, URLs, code and phone numbers stay LTR inside RTL text. The Unicode bidi algorithm usually gets this right for a clean run, but breaks at boundaries — a price like `‎$9.99/mo` beside Arabic text can render with the `$` or `/mo` on the wrong side.

Isolate any embedded LTR run:

```ts
const FSI = '⁨', PDI = '⁩';   // first-strong isolate
const isolate = (s: string) => `${FSI}${s}${PDI}`;
t('paywall.price', { price: isolate(product.localizedPriceString) });
```

Use `⁦` (LRI) / `⁧` (RLI) when you need to force a specific direction rather than infer it. Do **not** use the deprecated LRM/RLM marks for whole runs. Apply isolation to: prices, phone numbers, emails, URLs, usernames/handles, file names, version numbers, and any user-generated string interpolated into a localised sentence.

Arabic-Indic digits: whether `١٢٣` or `123` is shown is a locale/numbering-system decision — let `Intl.NumberFormat` decide from the locale tag; do not transliterate by hand.

## Web side (Next.js)

```tsx
export default function RootLayout({ children, params: { locale } }) {
  const dir = RTL_LOCALES.has(languageCodeOf(locale)) ? 'rtl' : 'ltr';
  return <html lang={locale} dir={dir}>{children}</html>;
}
```

`dir` on `<html>` drives the whole CSS logical-property system, so no restart problem exists on web — a route change to `/ar` is enough.

Use CSS logical properties exclusively:

| Physical | Logical |
|---|---|
| `margin-left` / `margin-right` | `margin-inline-start` / `margin-inline-end` |
| `padding-top` / `padding-bottom` | `padding-block-start` / `padding-block-end` |
| `left` / `right` | `inset-inline-start` / `inset-inline-end` |
| `width` / `height` | `inline-size` / `block-size` |
| `text-align: left` | `text-align: start` |
| `border-left` | `border-inline-start` |
| `float: left` | `float: inline-start` |

Tailwind ships logical utilities — use `ms-*`, `me-*`, `ps-*`, `pe-*`, `start-*`, `end-*`, `text-start`, `text-end`, `border-s-*`, `rounded-s-*` and never `ml-*`, `mr-*`, `left-*`, `right-*`, `text-left`. Enforce with an ESLint/Tailwind lint rule; a single stray `ml-4` is invisible in LTR review.

`transform: translateX` on the web has the same negation problem; prefer `inset-inline-start` transitions or `translate: logical` where available, otherwise branch on `[dir="rtl"]`.

## Cost of retrofitting

Built in from day one: an ESLint rule, an `<Icon mirror>` prop, an `rtlX()` helper, and a habit. Effectively free.

Retrofitted: a full-app visual sweep — every screen at both directions, every absolutely-positioned element, every animation, every gesture, every horizontal scroll, plus the icon audit. Assume weeks of QA for a mid-size app, and expect a long tail of reports from native speakers. [UNVERIFIED — no published measurement of retrofit cost exists; this is an engineering-judgement estimate, not a sourced figure.]

## Per-screen RTL QA checklist

Run every screen twice (device set to Arabic, and via the in-app override) against:

- [ ] Text alignment follows direction; no stray left-aligned paragraph.
- [ ] Header back button on the trailing edge; title centred or leading correctly.
- [ ] Tab bar / segmented control order reversed.
- [ ] Absolutely-positioned badges, close buttons, FABs on the correct edge.
- [ ] Icons: directional ones mirrored, object/brand ones not.
- [ ] Prices, phone numbers, URLs, handles rendered with correct bidi (no stray `$` or `/` on the wrong side).
- [ ] Horizontal scroll starts at the correct end; paging indicator order matches.
- [ ] Swipe gestures move the right way; drawer opens from the trailing edge.
- [ ] Animations and transitions play in the mirrored direction.
- [ ] Progress bars, sliders and steppers fill from the leading edge.
- [ ] Text inputs: caret starts on the trailing side; placeholder aligned; mixed LTR input (email, URL) behaves.
- [ ] Long Arabic strings do not truncate mid-word; Arabic line height is taller than Latin — check for clipping.
- [ ] Charts and maps left physical (not accidentally mirrored).
- [ ] Screenshots for the store re-captured in RTL.

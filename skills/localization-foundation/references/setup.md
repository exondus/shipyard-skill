# i18n Setup: Expo + Next.js Monorepo

Time-sensitive: Hermes `Intl` coverage changes with every React Native release, and `expo-localization`'s API surface has moved between SDKs. Verify the Hermes support table and the Expo API names against [Expo Localization docs](https://docs.expo.dev/versions/latest/sdk/localization/) and the installed RN version before writing code.

## Catalogue layout

One shared package. Both apps import it; neither owns catalogues.

```
packages/i18n/
  src/index.ts              # createI18n(), resources map, type augmentation
  src/detect.native.ts      # expo-localization
  src/detect.web.ts         # Accept-Language / route segment
  locales/
    en/  common.json  onboarding.json  paywall.json  errors.json  settings.json
    de/  ...
    ja/  ...
  types/resources.d.ts      # GENERATED — do not hand-edit
apps/mobile/                # Expo Router
apps/web/                   # Next.js App Router, /[locale] segment
```

Rules: `en` is the source of truth and the only catalogue a human edits by hand. One namespace per feature area, plus `common`. Namespace granularity is the lazy-loading unit and the translator batch unit — keep files under ~150 keys.

Key naming: semantic, hierarchical, lowercase dot-separated. `paywall.trial.cta`, not `Try for $0.00`. English-as-ID (the Lingui/FormatJS default) gives free fallback but silently reuses stale translations when copy is tweaked and collides on homonyms ("Post" verb vs noun). Semantic keys plus a mandatory `description` win at any size worth localising.

## i18next configuration

`packages/i18n/src/index.ts`:

```ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ICU from 'i18next-icu';
import en from '../locales/en';           // static: always bundled

export const NAMESPACES = ['common','onboarding','paywall','errors','settings'] as const;
export const SUPPORTED = ['en','de','ja','fr','es','ar'] as const;
export type Locale = typeof SUPPORTED[number];

export function createI18n(locale: Locale, loadResources: Loader) {
  return i18n
    .use(ICU)                            // ICU MessageFormat, not i18next's own plural suffixes
    .use(initReactI18next)
    .init({
      lng: locale,
      fallbackLng: 'en',
      ns: NAMESPACES,
      defaultNS: 'common',
      resources: { en },
      interpolation: { escapeValue: false },  // RN and React already escape
      returnNull: false,                      // makes typed t() return string, not string|null
      react: { useSuspense: false },          // Suspense + RN navigation is a footgun
    });
}
```

Use `i18next-icu` (or Lingui) so plurals go through CLDR rules rather than i18next's `_plural` key suffixes, which only model English-shaped languages. See `icu.md`.

Next.js App Router: instantiate a fresh i18next instance per request in RSC (never a module-level singleton — it leaks locale across requests), and mount a client provider with only the namespaces that route needs.

## Locale detection

Native:

```ts
import * as Localization from 'expo-localization';

const [loc] = Localization.getLocales();   // guaranteed non-empty
loc.languageTag       // "de-AT"
loc.languageCode      // "de"
loc.regionCode        // "AT"
loc.textDirection     // 'ltr' | 'rtl'
loc.currencyCode      // "EUR"   (null on web)
loc.measurementSystem // 'metric' | 'us' | 'uk'  (null on web)
loc.decimalSeparator  // ","
Localization.getCalendars()[0].timeZone  // IANA zone id
```

`useLocales()` / `useCalendars()` are the reactive hooks.

**Android caveat:** the user can change system locale while the app is alive, and the process is not necessarily restarted. iOS values are constant for the process lifetime. So on Android, re-read on foreground:

```ts
AppState.addEventListener('change', s => {
  if (s !== 'active') return;
  const tag = Localization.getLocales()[0].languageTag;
  if (!hasOverride() && resolve(tag) !== i18n.language) i18n.changeLanguage(resolve(tag));
});
```

`resolve()` must negotiate: exact tag → language code → fallback `en`. Never pass a raw `languageTag` to `changeLanguage` — `de-AT` will not match a `de` catalogue.

Web: locale comes from the `/[locale]` route segment (shareable, indexable), seeded from a middleware that reads `Accept-Language` and a cookie override.

## Typed keys

Augment i18next's types from the English catalogue:

```ts
// packages/i18n/types/resources.d.ts  (generated)
import type en from '../locales/en';
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: typeof en;
    returnNull: false;
  }
}
```

This gives autocomplete on `t('paywall.trial.cta')`, a compile error on unknown keys, and — with `i18next` ≥23 — checked interpolation variable names ([locize guide](https://www.locize.com/blog/i18next-typescript/)).

CI step (also a pre-commit hook):

```
pnpm i18n:types      # regenerates locales/en/index.ts barrel + types/resources.d.ts
git diff --exit-code packages/i18n/types packages/i18n/locales/en/index.ts
```

A non-empty diff fails the build with "run pnpm i18n:types". This makes the English catalogue the type contract and stops drift.

Consequence to enforce: **no dynamically constructed keys.** `t(\`errors.${code}\`)` defeats both typing and unused-key detection. Use an explicit `Record<Code, TKey>` map instead.

## Lazy loading

| Target | Mechanism |
|---|---|
| `en` (both) | Statically bundled. Always available offline, always the fallback. |
| Web, other locales | `i18next-http-backend` or per-route `import()` of the namespace JSON; Next splits automatically. |
| Native, other locales | `import()` inside a switch on locale — Metro emits separate chunks. Or fetch from CDN, cache in `expo-file-system`, and version the cache key so OTA copy fixes land. |

```ts
const loaders: Record<Locale, () => Promise<Resources>> = {
  en: async () => en,
  de: () => import('../locales/de'),
  ja: () => import('../locales/ja'),
  // ...
};
```

Never `require()` every locale eagerly. That is the single most common bundle-size regression in a localised RN app: catalogues plus `Intl` locale data compound.

Show `en` while a catalogue loads rather than blocking the first frame; swap in via `i18n.addResourceBundle` + `changeLanguage`.

## Hermes partial `Intl` — the real constraint

Hermes does not ship full ICU. Verified support table ([callstack RN best-practices reference](https://github.com/callstackincubator/agent-skills/blob/main/skills/react-native-best-practices/references/native-sdks-over-polyfills.md)):

| API | Hermes | Action |
|---|---|---|
| `Intl.Collator` | Supported | Use natively (sorting, search) |
| `Intl.getCanonicalLocales` | Supported | Native |
| `Intl.supportedValuesOf` | Supported | Native |
| `Intl.DateTimeFormat` | **Partial** | Works for common options; audit `dateStyle`/`timeStyle`, `timeZoneName`, non-Gregorian calendars |
| `Intl.NumberFormat` | **Partial** | Audit `notation:'compact'`, `unit` style, `roundingIncrement` |
| `Intl.PluralRules` | **Missing** | `@formatjs/intl-pluralrules` — required, ICU plurals depend on it |
| `Intl.RelativeTimeFormat` | **Missing** | `@formatjs/intl-relativetimeformat` |
| `Intl.Locale` | **Missing** | `@formatjs/intl-locale` |
| `Intl.DisplayNames` | **Missing** | `@formatjs/intl-displaynames` (language-picker names) |
| `Intl.ListFormat` | **Missing** | `@formatjs/intl-listformat` |
| `Intl.Segmenter` | **Missing** | `@formatjs/intl-segmenter` (grapheme/word counts, CJK) |

"Constructor exists" ≠ "your options work". Test the exact option bags you use on a real device before trusting partial support.

**Size warning:** polyfills plus locale data can exceed 400 KB. Import only the locales you ship, never the `/locale-data/index` barrel:

```ts
import '@formatjs/intl-pluralrules/polyfill';
import '@formatjs/intl-pluralrules/locale-data/en';
import '@formatjs/intl-pluralrules/locale-data/de';
// one line per shipped locale, per polyfill
```

Generate these imports from `SUPPORTED` in a codegen step so adding a locale cannot forget one. `@formatjs/intl-localematcher` has known performance problems on Hermes ([formatjs#4276](https://github.com/formatjs/formatjs/issues/4276)) — avoid it on the startup path.

## Platform locale declaration — not optional

iOS reads `CFBundleLocalizations` to decide which languages the app *claims*. If the language is absent, iOS reports the app as English regardless of what your JS catalogue contains, which breaks `getLocales()` negotiation and the App Store language list.

```json
// app.json
{ "expo": { "ios": { "infoPlist": {
    "CFBundleLocalizations": ["en","de","ja","fr","es","ar"] } } } }
```

Android: declare the same set. In a bare/prebuild config, `android.defaultConfig.resConfigs`; with the Expo config plugin, add a `locales_config.xml` (Android 13+ per-app language) so the system language picker shows your app. Play Console listing languages are configured separately from the app binary.

Keep one source list (`SUPPORTED`) and generate `CFBundleLocalizations`, `locales_config.xml`, and the polyfill imports from it. Divergence between these three is a common and silent bug.

## In-app language override

Default to the OS locale, but always ship an override — diaspora users routinely want a language their device is not set to.

```ts
const KEY = 'app.locale.override';

export async function setLocale(next: Locale | null) {
  next ? await AsyncStorage.setItem(KEY, next) : await AsyncStorage.removeItem(KEY);
  await ensureLoaded(next ?? osLocale());
  await i18n.changeLanguage(next ?? osLocale());
  if (isRTL(next ?? osLocale()) !== I18nManager.isRTL) await promptRestart(); // see rtl.md
}
```

Resolution order at boot: stored override → OS locale (negotiated) → `en`. Persist the override before restarting, and read it before the first render — a flash of English is the tell that you resolved too late.

On web, the override is a cookie plus a redirect to the `/[locale]` route so the URL stays canonical and shareable.

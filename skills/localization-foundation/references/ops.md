# Translation Operations and CI Gates

Time-sensitive: TMS pricing and free-tier limits change often, and the market-revenue ranking below is derived from 2025 calendar-year data. Re-verify pricing on each vendor's page and the market ranking before making a spend or locale decision.

## The workflow

```
dev writes en key + description
        ↓  (PR merged to main)
CI extract  →  push source strings to TMS
        ↓
MT pre-translate (DeepL / LLM with glossary + tone prompt)  →  all locales
        ↓
human review  →  only the top 3–5 revenue locales
        ↓
CI pull (scheduled + on demand)  →  opens a PR with updated catalogues
        ↓
CI gates (below) must pass  →  merge  →  ships in the next build / OTA
```

Non-negotiables:

- **Machine translation is the draft, never the ship state for a revenue locale.** MT is fine for a long-tail locale you would otherwise not ship at all, but label it internally so you know what has been reviewed.
- **Give the MT step a glossary and a tone prompt.** Product name, feature names and never-translate terms go in a glossary (all TMSs support this). Tone: "second person, informal (du/tu), sentence case, no exclamation marks, max 24 characters for keys tagged `button`." Untuned MT produces formal-register copy that reads like a bank.
- **Never let a translator edit English.** Copy changes are PRs.
- **Translations arrive as a PR, not a live fetch**, so a bad translation cannot ship without review and so the catalogue is versioned with the code that uses it. (A CDN-fetched catalogue is fine as a *fast-fix* channel on top of the bundled one — see lazy loading in `setup.md`.)
- **Changing an English string requires a new key or an explicit "invalidate translations" flag.** Otherwise every locale silently keeps the old meaning. This is the most common production i18n bug.

## Platform comparison

| | Tolgee | Crowdin | Lokalise | Locize |
|---|---|---|---|---|
| Model | Open source, self-hostable or cloud | Cloud (free OSS tier) | Cloud only | Cloud, by the i18next authors |
| Pricing posture | Most generous free/cheap tier; self-host = $0 | Cheapest at scale; free for open source | Most expensive; enterprise-shaped | Mid; usage-based on translations + downloads |
| Standout | In-context editing (click a string in the running app to translate it) | Largest integration surface, GitHub/CLI/CI maturity | Best UX, branching, QA checks, workflow/review states | Zero-friction with i18next; CDN delivery built in |
| Weakness | Smaller ecosystem, fewer vendor integrations | UI is dated, agency-oriented | Cost jumps hard past the starter tier | Only sensible if you are on i18next |
| ICU support | Yes | Yes | Yes | Yes |

Sources: [Tolgee vs Crowdin](https://tolgee.io/tolgee-vs-crowdin), [locize platform comparison](https://www.locize.com/compare/localization-platforms), [Lokalise alternatives](https://www.locize.com/compare/lokalise-alternatives).

**Recommendation for an indie:** Tolgee (self-hosted or cloud free tier). The in-context editor is the feature that actually saves time — most translation errors are context errors, and seeing the string in the running screen fixes them at the source. Move to Crowdin if you outgrow it and need vendor/agency integrations. Choose Locize only if you want i18next-native CDN delivery and will pay for the convenience. Lokalise is hard to justify below a dedicated localisation budget.

If you have fewer than ~300 keys and 3 locales, a TMS is optional: JSON files in the repo plus an LLM pre-translate script plus native-speaker review on a shared doc is genuinely fine, and the CI gates below matter more than the tool.

## CI gates

All four run on every PR. All four fail the build.

**1. Missing keys, for shipped locales only.**

```bash
node scripts/i18n-check-missing.mjs --locales de,ja,fr --strict
# For each ns: keys(en) − keys(locale) must be empty.
# Also flag keys(locale) − keys(en) → stale keys to delete.
```

Scope it to locales you actually ship (`SUPPORTED` in `packages/i18n`). Gating on a long-tail MT-only locale just blocks merges. Report — don't fail — for those.

**2. ICU syntax validation.** ICU errors throw at *format* time, not build time, so an unvalidated catalogue is a crash waiting for the right locale and count.

```ts
import { IntlMessageFormat } from 'intl-messageformat';
for (const [key, msg] of everyMessage()) {
  try { new IntlMessageFormat(msg, locale); }
  catch (e) { fail(`${locale}/${ns}:${key} — ${e.message}`); }
}
```

Extend it to check that (a) every `plural`/`select` has an `other` branch, (b) the placeholder set in each translation is a subset of the English one — a translator inventing `{name}` where English has `{userName}` produces a blank in production, and (c) every category the *target* locale requires is present (use `Intl.PluralRules(locale).resolvedOptions().pluralCategories`).

**3. Unused key detection.**

```bash
# every t('…') / <Trans i18nKey="…"> literal in src, minus keys(en)
node scripts/i18n-check-unused.mjs
```

This only works if keys are never dynamically constructed. Enforce that separately: ban `t(\`` (template literal) via lint. Where a dynamic lookup is genuinely needed, use an explicit `Record<Code, TKey>` map — the literals then appear in the scan. Keep an `i18n-allow-unused.json` for keys referenced from native code or server pushes.

**4. Bare string literal lint.**

```js
// .eslintrc
plugins: ['i18next'],
rules: { 'i18next/no-literal-string': ['error', {
  markupOnly: false,
  onlyAttribute: ['title','placeholder','accessibilityLabel','label'],
  ignoreCallee: ['require','import','console.*','styled.*','test','describe'],
}]}
```

Tune the ignore list until it is quiet, then treat every new violation as a bug. This is what stops the slow leak of untranslated strings back into the codebase.

Optional fifth gate: fail if any key in `en` lacks a `description`. Cheap, and it is the highest-value metadata in the pipeline.

## Pseudo-localisation

A build-time locale that transforms English into a fake language that is still readable but exercises every failure mode:

```
Save  →  [!!Šåṽé — ẋẋẋẋẋẋẋ!!]
```

Four properties, each catching a distinct bug class:
- **Accented characters** → catches font/encoding gaps and any string that stayed pure ASCII (= hardcoded, not going through `t()`).
- **Padding to +40%** → catches truncation, clipping, and fixed-width layouts.
- **Bracket delimiters** → catches concatenation: a sentence built from two keys shows `[!!…!!][!!…!!]` mid-sentence.
- **Preserved placeholders** → `{count}` must survive untouched; if it is mangled, the interpolation path is wrong.

Wire it as a locale `en-XA` generated from `en` at build time, exposed in dev builds and in the in-app language override behind a debug flag. Add a visual-snapshot test run in `en-XA` for the top screens. See [SimpleLocalize's pseudo-localisation guide](https://simplelocalize.io/blog/posts/pseudo-localization-guide/).

**Expansion budget** — design against these, not against English:

| Source length (en) | Typical expansion |
|---|---|
| 1–10 chars | up to +100–200% |
| 11–20 chars | +80–100% |
| 21–30 chars | +60–80% |
| 31–50 chars | +40% |
| 50+ chars | +30% |

By language, for medium strings: German and Finnish **+30–40%** (worst case far higher for compound nouns — `Geschwindigkeitsbegrenzung`), French and Spanish **+15–25%**, Russian **+15%**, Portuguese **+20%**, Arabic **+20–25%**, Japanese/Chinese **−30 to −50%** (contraction, but taller line height and no word wrapping at spaces) ([SimpleLocalize text expansion](https://simplelocalize.io/blog/posts/text-expansion-ui-localization/), [POEditor](https://poeditor.com/blog/text-expansion-and-contraction-localization/)).

Layout consequences: no fixed-width buttons; `flexShrink: 1` on text containers; avoid five-label single-line tab bars; allow two-line buttons; test pseudo-locale *combined with* 200% system font scale — that combination is what breaks accessibility and localisation simultaneously and neither test finds alone. And: **no text baked into images.** Store screenshots, onboarding hero art, empty-state illustrations — text as an overlaid text layer.

## Locale ROI ordering

Derived from 2025 calendar-year app-store revenue by market; the top 12 markets are ~88% of global store revenue ([localizelistings market ranking](https://localizelistings.com/blog/12-highest-revenue-app-store-markets)). **[UNVERIFIED for 2026 — this is one vendor's aggregation of 2025 data. Re-verify against current Sensor Tower / Appfigures data before committing spend.]**

| Phase | Locales | Cumulative revenue coverage | Effort |
|---|---|---|---|
| 1 | en-US, en-GB, en-AU, en-CA | ~46% | Spelling variants only — an afternoon |
| 2 | ja, de, fr | ~64% | Highest return per unit effort; ja has the best revenue-per-user for non-games |
| 3 | ko, zh-Hans, zh-Hant, it, es | ~75% | zh-Hans requires a China distribution decision (iOS only in that ranking) |
| 4 | pt-BR, ru, hi, nl, pl, tr, ar, id | ~88% | ar brings the RTL cost — see `rtl.md` |

Sequencing rule: **localise the store listing before the app.** Listing metadata (title, subtitle, keywords, description, screenshots) drives impressions-to-install and is cheap to translate and to revert. If a localised listing moves installs in a market, that is the signal to localise the app for it. Screenshot text overlays matter as much as the description.

Also localise: the App Store keyword field per locale (it is not shared), the subscription display name and description in App Store Connect / Play Console (these appear in the system purchase sheet and are a common rejection cause when missing), push notification copy, and transactional email.

# ICU MessageFormat and Intl Formatting

Time-sensitive: CLDR plural rules for individual languages are revised between CLDR releases, and `Intl` option support varies by engine (see `setup.md` for the Hermes table). Verify any specific language's category set against the [CLDR plural rules chart](https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html) rather than trusting memory.

## CLDR plural categories

CLDR defines six cardinal categories: `zero`, `one`, `two`, `few`, `many`, `other`. Only `other` is required — a language with a single form uses `other` alone. The names are **arbitrary labels**, not linguistic descriptions: a category exists for a language when some set of numeric values triggers a distinct grammatical form ([CLDR spec](https://cldr.unicode.org/index/cldr-spec/plural-rules)).

| Language | Categories used | Note |
|---|---|---|
| Japanese, Chinese, Korean, Vietnamese, Thai, Indonesian, Turkish | `other` | One form. `1 個` and `5 個`. |
| English, German, Dutch, Spanish, Italian, Swedish, Greek | `one`, `other` | The only shape `x`/`xs` handles. |
| French, Portuguese (pt-BR) | `one`, `many`, `other` | fr treats 0 and 1 as `one`. |
| Russian, Ukrainian, Croatian, Serbian | `one`, `few`, `many`, `other` | `one`: 1, 21, 31… `few`: 2–4, 22–24… `many`: 0, 5–20, 25–30… |
| Polish, Czech, Slovak | `one`, `few`, `many`, `other` | Different boundaries from Russian — do not share rules. |
| Arabic | `zero`, `one`, `two`, `few`, `many`, `other` | All six. |
| Welsh | `zero`, `one`, `two`, `few`, `many`, `other` | All six. |
| Hebrew | `one`, `two`, `many`, `other` | Dual form. |
| Irish, Lithuanian, Latvian, Romanian, Maltese | 3–5 categories | Each distinct. |

Consequence: `count === 1 ? 'item' : 'items'` is not a shortcut, it is a bug that ships. Russian needs three number-driven forms, Arabic six. There is no way to retrofit this from the call site — the *message* must own the branching.

Note the reversed-looking Arabic mapping: CLDR itself records that `many` and `other` for Arabic would arguably have been better swapped. Do not reason about category names; write all branches the language declares and let CLDR pick.

## ICU syntax — copy-ready

**Plural**

```json
{
  "cart.items": "{count, plural, =0 {Your cart is empty} one {# item} other {# items}}",
  "cart.items_ru": "{count, plural, =0 {Корзина пуста} one {# товар} few {# товара} many {# товаров} other {# товара}}"
}
```

`#` interpolates the formatted number with locale digit grouping. To show a raw number, use a named argument instead.

**`=0` vs `zero` — the distinction that trips people.** `=0` is an *exact value match* and fires before category matching, in every language. The `zero` category is a *grammatical* category that in Arabic also covers certain non-zero shapes and in most languages never matches at all. Use `=0` for "empty state" copy ("Your cart is empty"). Use `zero` only when a translator needs a grammatically distinct zero form. Both may coexist; `=0` wins.

**Offset** — for "you and 3 others":

```
{n, plural, offset:1 =0 {No one liked this} =1 {You liked this} one {You and # other} other {You and # others}}
```

`offset:1` subtracts 1 before both category selection and `#` rendering.

**Select (gender, or any enum)**

```
{gender, select, female {She invited you} male {He invited you} other {They invited you}}
```

`other` is mandatory. Never build gender by concatenating a pronoun — many languages inflect the verb, the adjective, and the object too.

**Selectordinal**

```
{place, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}
```

Ordinal categories are a *separate* rule set from cardinals: English ordinals use `one/two/few/other` while English cardinals use `one/other`. Requires `Intl.PluralRules(locale, { type: 'ordinal' })`.

**Nested plural inside select** — legal and often necessary:

```
{gender, select,
  female {{n, plural, one {She sent # message} other {She sent # messages}}}
  other  {{n, plural, one {They sent # message} other {They sent # messages}}}}
```

Keep nesting to one level. Beyond that, split into two keys and choose at the call site — translators cannot reliably edit three-deep ICU.

**Inline formatting inside a message**

```
"order.total": "Total {amount, number, ::currency/USD} due {due, date, medium}"
```

Prefer formatting in the message over pre-formatting in JS: it lets the translator move the value and gives the ICU engine the locale.

## Intl formatting patterns

Construct formatters once and memoise by `(locale, optionsKey)` — construction is the expensive part, and on Hermes it is expensive enough to show up in a list render.

```ts
// Number
new Intl.NumberFormat(locale).format(1234.5);                       // "1.234,5" in de
new Intl.NumberFormat(locale, { notation: 'compact' }).format(12400); // "12K" — audit on Hermes
new Intl.NumberFormat(locale, { style: 'percent', maximumFractionDigits: 1 }).format(0.073);

// Currency — never hardcode "$", never convert client-side
new Intl.NumberFormat(locale, { style: 'currency', currency: 'JPY' }).format(1200);
// Store prices come from StoreKit / Play Billing (RevenueCat: localizedPriceString). Use those verbatim.

// Date — always pass an explicit IANA timeZone
new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeZone: tz }).format(d);
new Intl.DateTimeFormat(locale, { hour: 'numeric', minute: '2-digit', timeZone: tz }).format(d);
// 12h vs 24h comes from the locale; do not branch on it yourself.
// Localization.getCalendars()[0] gives timeZone, uses24hourClock, firstWeekday.

// Relative time
const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' }); // 'auto' → "yesterday"
rtf.format(-1, 'day');   // "yesterday"
rtf.format(3, 'hour');   // "in 3 hours"

// Collation — sorting and search
const coll = new Intl.Collator(locale, { sensitivity: 'base', numeric: true, usage: 'sort' });
names.sort(coll.compare);   // byte order is wrong in sv, de, tr, cs
// usage:'search' + sensitivity:'base' for accent/case-insensitive filtering

// Ordinal
const pr = new Intl.PluralRules(locale, { type: 'ordinal' });
pr.select(23); // "few" in en → "23rd"

// Lists
new Intl.ListFormat(locale, { type: 'conjunction' }).format(['a','b','c']); // "a, b, and c"

// Language names for the picker
new Intl.DisplayNames([locale], { type: 'language' }).of('de'); // "German" / "Deutsch"
```

Language picker rule: show each language **endonymically** (in itself — "Deutsch", "日本語"), not translated into the current UI language. A user who cannot read the current UI needs to find their language by shape.

Time zones: store UTC ISO-8601 plus the IANA zone id (`Europe/Berlin`), never a numeric offset — offsets change twice a year. Day boundaries for streaks, "today" filters and daily-goal resets must be computed in the *user's* zone. This is the single most common source of off-by-one-day and broken-streak bugs.

## Message patterns that go wrong

1. **Concatenation.** `t('you_have') + ' ' + n + ' ' + t('items')` cannot be reordered, cannot be pluralised, and cannot be inflected. German and Japanese put the verb elsewhere. One key = one complete sentence.
2. **Building sentences from a fragment table.** "Sort by" + `["date","name"]` produces ungrammatical output wherever the object inflects. Write the full sentence per case.
3. **Interpolating a translated fragment into a translated sentence.** `t('banner', { action: t('upgrade') })` — the fragment's case/gender cannot agree. Acceptable only for proper nouns, numbers, and user-supplied text.
4. **Gender assumed from a name or avatar.** Pass an explicit `gender` argument with an `other` branch, or write gender-neutral source copy — many languages have no neutral option, so the translator needs the argument to exist even if you always send `other`.
5. **Units and measurement.** `measurementSystem` from `expo-localization` decides metric/US/UK; use `Intl.NumberFormat(locale, { style:'unit', unit:'kilometer' })` rather than appending "km". Do not infer units from language — en-GB is mixed.
6. **Hardcoded date/number glue.** `${d.getDate()}/${d.getMonth()+1}` is US/UK-ambiguous and wrong nearly everywhere.
7. **Truncation by character count.** `slice(0, 30)` splits grapheme clusters and CJK badly; use `Intl.Segmenter` or CSS/`numberOfLines` truncation.
8. **Missing `other` branch.** ICU throws at format time, not build time — validate catalogues in CI (see `ops.md`).
9. **Percent signs and currency symbol position.** `%` precedes the number in Turkish; the currency symbol follows in French. `Intl` knows; you do not.
10. **Placeholder names that carry meaning only to the developer.** `{v1}` gives the translator nothing. Use `{userName}`, `{daysLeft}` and add a `description`.

Every key must ship a translator `description`: what it is, where it appears, any length limit, and whether a placeholder is a person, a count, or a product name. This is the highest-leverage habit in the whole pipeline — translators guess otherwise, and a guess is invisible until a native speaker complains in a review.

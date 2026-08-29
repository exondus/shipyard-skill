---
name: localization-foundation
description: >
  Build an app so it can be translated later without a rewrite, and translate it when the time comes.
  Use when setting up i18n, adding a language, handling plurals, dates, currency or number formatting,
  supporting right-to-left languages, deciding which locales to launch in, localising App Store or Play
  listings, or setting up a translation workflow. Also use at the start of any new app — the catalogue,
  ICU messages and logical layout properties are wired on day one even for a single-language launch,
  because retrofitting them is a full-app sweep.
---

# Localisation foundations

The point of this skill for most projects is not translation. It is that **a single-locale app built
the right way costs almost nothing extra, and the same app built the ordinary way costs a full-app
sweep to internationalise later**. Wire the foundation on day one and decide about languages whenever
the business does.

## Day one, regardless of launch locale

Six things. All cheap now, all expensive later.

1. **A catalogue, from the first string.** `packages/i18n` with namespaces per feature. No user-visible
   string is ever written inline in a component. Enforce it with a lint rule, not discipline — the rule
   is what makes this survive a busy week.
2. **ICU message format for anything with a count or a variable.** `count === 1 ? 'item' : 'items'` is
   an English-only assumption; CLDR defines six plural categories and languages select different
   subsets — Russian and Polish use several, Arabic uses all six, Japanese uses one. Write the ICU
   plural form even when only English ships.
3. **No concatenation.** One key holds a whole sentence with placeholders. German and Japanese need
   different word order, and a concatenated string cannot be reordered.
4. **No text baked into images.** Onboarding art, empty-state illustrations and store screenshots get
   text as an overlaid layer.
5. **Logical layout properties everywhere** — start/end rather than left/right, and the CSS logical
   equivalents on web. This is what makes right-to-left support a configuration change rather than a
   project.
6. **A description on every key**, written for a translator who cannot see the screen: what it is, what
   it does, any length constraint. This is the single highest-leverage habit in the whole area, and the
   one most often skipped.

Then add **pseudo-localisation to development builds**. It renders `Save` as something like
`[!!Ŝåṽé—ẋẋẋẋ!!]`, which in one pass exposes every hardcoded string (it stays plain), every truncation,
and every concatenation. Budget German at roughly 30–40% longer than English for medium strings, more
for short labels; test at that expansion together with 200% font scale, because the two combine and
that combination is what actually breaks layouts.

## The stack

`expo-localization` for detection, `i18next` for the runtime, one shared catalogue used by both apps.
The reasoning is unglamorous: it is the only mature option that behaves identically under Hermes, in
the Next App Router and in Node scripts, and it has the deepest tooling ecosystem. Alternatives with
compile-time extraction are defensible; record the choice in `docs/app/stack.md` either way.

Type the keys by generating types from the English catalogue in CI, so an unknown key or a missing
interpolation variable is a build error rather than a blank space in production.

Two practical traps: **Hermes ships only partial `Intl` support** — several formatters used for
plurals and relative time are missing and must be polyfilled, and the polyfill plus locale data is
large, so import only the locales actually shipped. And **do not eagerly require every locale**; ship
the launch language in the bundle and load the rest on demand.

## Formatting is not translation

The half that gets forgotten:

- **Currency**: never convert on the client, and never hardcode a symbol. On mobile the displayed price
  comes from the store's localised product, because Apple and Google pricing tiers set the local price
  and they do not map linearly across countries.
- **Dates and numbers** through `Intl` only. Decimal commas, thousands separators, non-Latin digits.
- **Sorting** with a locale collator; byte order is wrong in Swedish, German and Turkish.
- **Time zones**: store UTC plus the IANA zone identifier, never an offset, and compute "today"
  boundaries in the user's zone. This is the single most common source of streak bugs.
- **Names**: one full-name field travels better than first and last. **Addresses**: field order and
  labels are country-driven. **Phone numbers**: parse and store in E.164.

## Right to left

Enabling RTL persists and requires an app restart, which means it is a deliberate flow with a warning,
not a toggle. Beyond that: use logical properties (row direction flips automatically, absolute
left/right does not), mirror directional icons — back arrows, chevrons, progress, undo — and do not
mirror clocks, media transport controls, checkmarks or logos. Numbers stay left-to-right inside
right-to-left text, and prices and phone numbers need bidi isolation or they visually reorder.

Any animation using a horizontal translation must negate it under RTL. This is the thing that is
always missed.

Built in from the start this is a lint rule and some discipline. Retrofitted it is a full visual QA
sweep of every screen — assume weeks, not days.

## Choosing locales

Store listings first: localising the App Store and Play listing is cheap, drives impressions to
install, and can be done before a single string is translated.

For in-app languages, the revenue-weighted order for an indie is broadly: English variants (spelling
only, near-zero cost), then Japanese, German and French, then Korean and the Chinese variants, Italian
and Spanish, then Portuguese-Brazil, Russian, Hindi and the rest. Japan has the highest revenue per
user for non-games. Verify current market data before committing spend.

Follow the OS locale by default but always ship an in-app override, persisted — people frequently want
a language their device is not set to. On web, prefix the route so the locale is shareable and
indexable.

One iOS trap: the app must declare its supported localisations in the native config or it presents as
English regardless of what the catalogue contains.

## Translation operations

Developer writes English plus a description → CI extracts and pushes to the translation platform →
machine pre-translation with a glossary and a tone-of-voice prompt → human review for the top few
revenue locales only → pulled back into the repo as a pull request.

Choose the platform on the free tier and the in-context editing rather than the feature matrix; for an
indie, an open-source self-hostable option or the one native to your i18n library are both sensible.

CI gates worth having: fail on a key missing from a shipped locale, validate ICU syntax on every
catalogue, report unused keys, and fail on a bare string literal in a component. The last one is what
keeps the whole thing from decaying.

## Reference files

- `references/setup.md` — catalogue layout, i18next configuration, typed keys, Hermes polyfills
- `references/icu.md` — plurals, select, ordinals, and the formatting patterns worth copying
- `references/rtl.md` — the RTL checklist, mirroring rules, and what breaks
- `references/ops.md` — translation workflow, platform comparison, CI gates

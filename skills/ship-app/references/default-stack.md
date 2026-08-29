# The default stack

Verified 29 August 2026. Versions rot fastest of anything in this plugin — check with
`npx expo install --check` and the [Expo SDK changelog](https://expo.dev/changelog) before installing,
and update `docs/app/stack.md` when a version moves.

This is the locked stack. Shipyard is opinionated because a decided stack is worth more than an
optimal one: the decision cost is paid once and the integration cost is paid forever.

**Each row has a real escape.** The escape conditions below are specific and testable — a market, a
platform constraint, a measured number — not hedging. Taking one is normal. Taking one without
recording it in `docs/app/stack.md` is not.

Copy `assets/stack-template.md` (in this skill) into `docs/app/stack.md` and fill it in. That template
is the only one; this file is the reasoning behind it.

---

## The rows

| Concern | Default | Version (Aug 2026) | Why | The escape |
|---|---|---|---|---|
| Package manager | **pnpm workspaces** | 11.x | Deterministic, fast, and Expo has supported it for several SDKs | Bun if the team already uses it and native builds are green; switch `nodeLinker: hoisted` at the first native resolution error either way |
| Task runner | **Turborepo** | 2.x | Cheap caching, minimal config at this size | Nothing, below ~15 packages. Nx only earns its config cost above that |
| Mobile | **Expo SDK + React Native** | SDK 57 / RN 0.86 / React 19.2 | Config plugins, EAS, OTA updates, and a managed native layer you do not maintain | Bare React Native only if you need a native capability no config plugin can reach — and then keep Expo modules |
| Architecture | **New Architecture** | mandatory from SDK 55 | Not a choice any more | None. A library that has not adopted it is a fork you have not written yet |
| Router | **expo-router** | 57.x, typed routes on | File-based, deep links map for free, one mental model with web | React Navigation directly only for an existing app mid-migration |
| Dev environment | **development builds** | `expo-dev-client` | Expo Go ships a fixed native binary; anything with a config plugin behaves differently there | None. Expo Go is for a five-minute demo, never for acceptance |
| Web | **Next.js App Router** | 16.x | Marketing pages, SEO surfaces and the web checkout | **Expo Router web** instead when the web surface is the same app rather than a marketing site — one bundler, one router, no react-native-web/Next interop tax. Take this escape if `apps/web` would mostly re-implement `apps/mobile` |
| API | **Hono + tRPC in `packages/api`** | Hono 4.x / tRPC 11.x | **React Native cannot use React Server Components**, so native needs a plain HTTP/JSON boundary. Keeping it standalone stops mobile releases being coupled to web deploys | oRPC if you want OpenAPI output for free; Next route handlers alone if there will never be a second consumer and you accept the coupling; expo-router `+api.ts` for BFF glue only, never as the whole backend |
| Auth | **Clerk** | `@clerk/expo` 4.x, `@clerk/nextjs` 7.x (Core 3) | Native sign-in, passkeys, organizations, and a production migration path that is documented rather than discovered | **better-auth** if you need to own the user table outright, run fully self-hosted, or the per-MAU cost is the binding constraint at your scale. Budget the org/roles and native-OAuth work you inherit. Do not migrate auth after launch — decide now |
| Database | **Supabase Postgres** | | Postgres with RLS, storage, realtime and a generated REST API, at a price a pre-revenue app can pay | **Neon** when you want scale-to-zero branches per pull request, or when you do not need storage/realtime/PostgREST and would rather not carry them. Plain RDS/Cloud SQL when an existing platform team owns the database |
| Row level security | **on, every table, one policy per operation** | | The mobile client is untrusted by construction | None. "We'll add policies later" is how data leaks |
| ORM | **Drizzle, server-only** | | Compiles to readable SQL, edge-compatible, generates plain `.sql` migrations, and models RLS policies in the same typed file as the tables | Prisma if the team is already fluent and its migration engine is not fighting the Supabase CLI. Raw SQL for hot paths regardless. **Never** in the mobile bundle either way |
| Payments — stores | **RevenueCat** | `react-native-purchases` 10.x | Normalises App Store and Play, remote offerings and paywalls without a release, and one webhook feed | Direct StoreKit 2 + Play Billing only if the revenue share genuinely outweighs the maintenance, which for a solo build it does not |
| Payments — web | **Stripe**, or **Paystack** for an African-registered entity | | Stripe is the default everywhere it operates | **Stripe does not onboard South African entities.** For a ZA business the default is Paystack; also consider a local gateway, or a merchant-of-record such as Paddle if global VAT handling matters more than fees. Record which, because it changes the webhook code and the dunning you have to write yourself |
| Entitlements | **one table you own** | | Every provider writes into it; every server-side gate reads it | None |
| Design tokens | **`packages/tokens`, one source** | | Native theme and web CSS variables generated from the same file, so the platforms cannot drift | None. This is the cheapest thing in the plugin and the most expensive to retrofit |
| Styling — native | **Unistyles** | 3.x | C++-side theme updates, no re-render on theme change, fastest for animation-heavy screens | **NativeWind** when the monorepo genuinely shares Tailwind components with `apps/web` and the team thinks in utility classes. Both are fine; **mixing two is not** |
| Styling — web | **Tailwind + shadcn** | Tailwind 4.x | Fast, and the component source is yours to edit | Anything, provided it consumes `packages/tokens` rather than defining its own values |
| Animation | **Reanimated + Gesture Handler** | whatever the SDK pins | UI-thread animation and interruptible gestures | None |
| i18n | **expo-localization + i18next + ICU, wired day one** | | Wiring the catalogue on day one costs a lint rule; retrofitting it is a full-app sweep. **This applies to a single-locale launch too** — the point is the plumbing, not the translations | Lingui if you prefer compile-time extraction and will accept the heavier build config. **Not "skip it"** |
| Errors | **Sentry** | `@sentry/react-native`, `@sentry/nextjs` | Release health, OTA-aware tagging, and sourcemaps that resolve | None worth the switching cost |
| Product analytics | **PostHog** | | Events, flags, experiments and replay in one place, which matters when you are one person | Amplitude or a privacy-first tool if replay and flags are not wanted. Keep the taxonomy either way |
| E2E | **Maestro** | | YAML flows, runs as a first-class EAS Workflows job | Detox only when Maestro flake is the measured bottleneck, not when it is suspected |
| CI | **GitHub Actions + EAS Workflows** | | Actions for lint/typecheck/test where it is free and fast; EAS Workflows for anything touching builds, updates, Maestro or submissions, because it fingerprints and only builds natively when native inputs changed | Actions alone if you are willing to reimplement the fingerprint logic. Most people are not |
| Hosting — API | **Cloudflare Workers**, or Fly/Railway | | Workers is cheapest and matches Hono's fetch model; a long-lived process when you need WebSockets or a colocated database | Vercel if `apps/web` is Next.js and you want one deploy target — note Hobby forbids commercial use |

---

## Reading the escapes

Three of these decisions are effectively permanent and deserve the most thought now: **auth**,
**database**, and **payments web processor**. Migrating any of them after launch is a multi-week
project with user-visible risk.

The rest are reversible. Styling layer, list library, analytics tool, E2E framework and hosting can
all be changed in a sprint. Do not spend the discovery phase debating a reversible decision.

## What is not negotiable

- The New Architecture, because the ecosystem moved.
- Development builds as the acceptance environment.
- RLS on every table.
- The ORM staying out of the mobile bundle.
- One token source.
- i18n plumbing on day one.
- Server-side authorisation, whatever the auth provider.

Everything else has a price and a condition.

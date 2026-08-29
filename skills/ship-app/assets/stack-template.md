# Stack — <app name>

Locked <date>. Every skill in Shipyard reads this file before doing anything. Change it deliberately,
and record the change in the deviations table rather than editing a row in place.

## Locked choices

| Concern | Choice | Version at lock | Notes |
|---|---|---|---|
| Package manager | pnpm workspaces | | |
| Task runner | Turborepo | | |
| Mobile | Expo SDK / React Native | | New Architecture, development builds only |
| Router (mobile) | expo-router | | typed routes on |
| Web | Next.js App Router | | marketing + web checkout |
| API | Hono + tRPC in `packages/api` | | native cannot use RSC |
| Auth | Clerk | | `@clerk/expo` + `@clerk/nextjs` |
| Database | Supabase Postgres | | RLS on every table |
| ORM | Drizzle, server-only | | never in the mobile bundle |
| Styling (native) | | | |
| Styling (web) | Tailwind + shadcn | | tokens from `packages/tokens` |
| Payments (stores) | RevenueCat | | |
| Payments (web) | | | Stripe, or Paystack for a ZA entity |
| i18n | expo-localization + i18next + ICU | | wired day one |
| Errors | Sentry | | |
| Analytics | PostHog | | |
| E2E | Maestro | | |
| CI | GitHub Actions + EAS Workflows | | |
| Hosting | | | |

## Environments

| | Bundle ID / package | Channel | Database | Notes |
|---|---|---|---|---|
| development | | development | local | |
| preview | | preview | | |
| production | | production | | |

## Deviations from the Shipyard defaults

| Choice | Replaced | Why | Date | Consequences |
|---|---|---|---|---|

A deviation with consequences beyond one package also gets an ADR in `docs/app/decisions/`.

## Paid services

| Service | Plan | Free ceiling | What runs out first | Reviewed |
|---|---|---|---|---|

Set a billing limit or spend cap on every row before launch. See the `cost-control` skill.

## Version review

Versions in this file rot. Re-check with `npx expo install --check` and `npx expo-doctor` before each
release, and update the table when a version moves.

| Date reviewed | By | Changes |
|---|---|---|

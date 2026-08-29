# Shipyard

Sixteen skills for taking a consumer app from an idea to a store listing, on an Expo + Next.js
monorepo. Opinionated on purpose: it picks a stack, writes the decisions down, and refuses to start
coding before it knows what it is building.

## What it does

| Skill | Owns |
|---|---|
| `ship-app` | The entry point. Reloads the project brief and stack, decides which skill owns the task, enforces the research gate |
| `product-discovery` | Research and scope before any code. Produces `docs/app/brief.md` |
| `stack-scaffold` | The monorepo, Metro and Next config, EAS build/update/submit, env vars, CI, quality gates |
| `clerk-auth` | Clerk end to end, and the dev-to-production migration that is where auth actually fails |
| `postgres-data` | Schema, RLS and its performance traps, indexing, pooling, migrations that survive old mobile clients |
| `premium-ui` | The AI-slop audit, the token system, motion tokens, and the implementation stack |
| `onboarding-flow` | The first-run sequence, permission priming, where the paywall goes, and the funnel that measures it |
| `payments-paywalls` | RevenueCat, Stripe, Paystack, one entitlements table you own, and the paywall rules |
| `push-engagement` | Push credentials, token storage, the send path and receipts, server-side scheduling, deep linking, cadence |
| `localization-foundation` | i18n wired on day one so it is a config change later, not a rewrite |
| `aso-growth` | Keyword research, store page conversion, ratings, retention, launch |
| `store-submission` | Getting through app review the first time — the architectural requirements, the assets, the notes |
| `observability-analytics` | Sentry and PostHog, and an event taxonomy that funnels can actually be run against |
| `performance-security` | Measure, then fix: startup, frames, bundle, binary size, and the security checks that matter |
| `cost-control` | What the free tiers really give you and which line grows first |
| `self-review` | Adversarial review of every slice before it counts as done |

## How it fits together

Everything a project decides lives in `docs/app/` in that project's repo — the brief, the locked
stack, the design system, the analytics spec, the entitlement model, and one ADR per non-obvious call.
Skills read those files rather than re-deciding, which is what stops fifteen skills becoming fifteen
opinions.

Work moves in vertical slices — schema through policy through API through screen through event — and
`self-review` runs on each one before the next starts.

Before submission, Shipyard hands off to the **`preflight-audit`** skill, which is the actual go/no-go
gate. `store-submission` prepares the material; `preflight-audit` decides whether it ships.

## The defaults

pnpm + Turborepo · Expo SDK 57 with expo-router and the New Architecture · Next.js 16 App Router for
web · Hono + tRPC in `packages/api` · Clerk · Supabase Postgres with RLS and Drizzle server-side ·
RevenueCat plus Stripe or Paystack · one `packages/tokens` feeding both platforms · i18next with ICU ·
Sentry and PostHog · Maestro · GitHub Actions plus EAS Workflows.

Deviations are expected. They go in the deviations table in `docs/app/stack.md` with a reason and a
date, so the project has one story about itself rather than an archaeology problem.

## A warning about dates

Every reference file was verified in **August 2026** and each one says so at the top. The
fastest-rotting material, in order: store payment rules (under active litigation), Expo SDK versions,
Clerk package names, vendor pricing, and required screenshot sizes. Treat the reference files as a
place to start checking, not as authority — they are written to tell you what to verify and where.

## Getting started

Say what you want to build. `ship-app` picks it up, runs discovery, and comes back with a brief before
it writes a line of code.

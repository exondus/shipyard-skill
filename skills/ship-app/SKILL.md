---
name: ship-app
description: >
  Orchestrate building a consumer mobile or web app from idea to store submission, and route to the
  specialist Shipyard skills for each stage. This is the entry point — prefer it over any other Shipyard
  skill when a request could belong to more than one. Use whenever someone wants to build, start,
  scaffold, plan or ship an app or MVP — "build me an app", "I have an app idea", "start a new project",
  "help me get this to the App Store", "what should I build next", "add a feature to my app" — and
  whenever work begins on a repo that has a docs/app/ directory. Use it also for anything about the
  launch schedule: "we're launching next week", "will we make it", "how long will this take", "what's
  left before we can ship", "are we on track", a deadline, or a date. Use it at the start of any app
  work to establish or reload the project brief and locked stack before writing code, and to decide
  which specialist skill owns the task at hand.
---

# Ship an app

This is the entry point and the traffic controller. Its job is to make sure two things are true
before any code is written, and to keep them true afterwards:

1. **The work is grounded in research, not assumption.** No scaffolding, no dependency choices,
   no schema until `docs/app/brief.md` exists and the user has agreed with it.
2. **Every decision is written down once and read by everything else.** The specialist skills do not
   re-litigate the stack. They read `docs/app/stack.md` and obey it.

## The gate

**Do not write application code until `docs/app/brief.md` exists.**

If it does not exist, invoke the `product-discovery` skill. That is the entire first move for a new
project, no matter how eager the request sounds. "Just build me a habit tracker" is a request to do
discovery quickly, not to skip it — 20 minutes of research changes the schema, the paywall placement
and the keyword set, and all three are expensive to change later.

Exceptions, which must be stated out loud when taken: a throwaway spike explicitly framed as
disposable, or a single isolated bug fix in an existing project.

If `docs/app/brief.md` does exist, read it and `docs/app/stack.md` before doing anything else. They
are the project's memory. They are short by design; read them fully.

## The project files

Everything Shipyard knows about a project lives in `docs/app/`. Create it at the repo root.

| File | Written by | Contains |
|---|---|---|
| `brief.md` | `product-discovery` | Who it is for, the one job it does, the competitive read, what is in and out of v1, the activation event |
| `stack.md` | `ship-app` (this skill) | The locked technology choices and every documented deviation, with the reason |
| `research/*.md` | `product-discovery`, `aso-growth` | Competitor teardowns, keyword sets, evidence with dates and links |
| `design-system.md` | `premium-ui` | Tokens, type scale, motion tokens, the named craft reference |
| `analytics-spec.md` | `observability-analytics` | The event taxonomy, one row per event |
| `entitlements.md` | `payments-paywalls` | Products, offerings, entitlement keys, the source-of-truth table |
| `decisions/NNNN-*.md` | anyone | One short ADR per non-obvious call: context, decision, consequence |
| `review/*.md` | `self-review` | Review passes and their closure records |

Templates live in `assets/` here, except the brief's (with `product-discovery`), the design system's
(with `premium-ui`), the entitlement model's (with `payments-paywalls`) and the analytics spec's (with
`observability-analytics`). Keep every file short. A brief nobody reads is worse than no brief, because
it looks like grounding and is not.

## Phases and routing

Work moves through these phases. They are not strictly serial — instrumentation and localisation are
built in from the start, not bolted on — but nothing later starts before the phase gate above it has
produced its artifact.

| Phase | Gate artifact | Skill |
|---|---|---|
| 1. Discover | `docs/app/brief.md` | `product-discovery` |
| 2. Decide the stack | `docs/app/stack.md` | this skill (below) |
| 3. Scaffold | a repo that builds on both platforms | `stack-scaffold` |
| 4. Identity | sign-in working in a dev build, not Expo Go | `clerk-auth` |
| 5. Data | schema + RLS policies + migrations | `postgres-data` |
| 6. Interface | `docs/app/design-system.md` + the first real screen, walked | `premium-ui`, then `visual-verification` |
| 7. First-run | the onboarding flow and its instrumented funnel | `onboarding-flow` |
| 8. Money | entitlements table, paywall, webhooks | `payments-paywalls` |
| 8b. Return | push credentials, token storage, the reminders that bring people back | `push-engagement` |
| 9. Reach | catalogue and locale plumbing in place from day one | `localization-foundation` |
| 10. Instrument | `docs/app/analytics-spec.md` + Sentry + PostHog live | `observability-analytics` |
| 11. Optimise | measured startup, bundle, size, security sweep | `performance-security` |
| 12. Position | keyword set, listing copy, screenshots, launch plan | `aso-growth` |
| 13. Prepare | metadata, assets, demo account, review notes | `store-submission` |
| 14. Gate | go / no-go | **`preflight-audit`** — the user's own skill |
| 15. Submit | build, submit, respond to review | `store-submission` |

Cross-cutting, invoked repeatedly rather than once: `self-review` after every vertical slice,
`visual-verification` on any slice a user can see, and `cost-control` whenever a new paid service is
about to be added or a bill is questioned.

**Before submission, hand off to `preflight-audit`.** That skill is the gate, not this plugin. Do not
substitute a Shipyard checklist for it and do not run it as a formality — run its intake first if the
project has never had one, then its audit, then remediate and verify. `store-submission` prepares the
material; `preflight-audit` decides whether it goes.

`preflight-audit` is a separate skill, not part of Shipyard. If it is not installed, say so plainly
rather than proceeding as though the gate happened: run `store-submission`'s checklist, run
`self-review` in its adversarial mode across the whole project rather than one slice, and tell the
user that what they got was a checklist, not an audit.

**The phases are not a schedule and the phase numbers are not weeks.** Several run in parallel and two
of them — Play's closed-testing requirement for new personal accounts, and Clerk's production DNS and
certificate wait — have external clocks that start long before the phase they sit in. Read
`references/timeline.md` before promising a launch date; the most common way a solo launch slips is
discovering a three-week external dependency in week nine.

## Phase 2: lock the stack

Shipyard is opinionated on purpose: a decided stack is worth more than an optimal one, because the
decision cost is paid once and the integration cost is paid forever. Write `docs/app/stack.md` from
`references/default-stack.md` and only deviate with a recorded reason.

The defaults, in one line each:

- **Monorepo** — pnpm workspaces + Turborepo; shared packages are source-only TypeScript, no build step
- **Mobile** — Expo SDK 57 (RN 0.86, React 19.2), expo-router, New Architecture, development builds not Expo Go
- **Web** — Next.js 16 App Router for the marketing site and web checkout
- **API** — Hono + tRPC in `packages/api`, mounted by web and deployable standalone
- **Auth** — Clerk (Core 3: `@clerk/expo`, `@clerk/nextjs`)
- **Data** — Supabase Postgres, RLS on every table, Drizzle server-side only
- **Money** — RevenueCat for the stores; Stripe or Paystack for web; one `entitlements` table you own
- **UI** — one `packages/tokens`; Unistyles on native, Tailwind v4 + shadcn on web; Reanimated 4
- **i18n** — expo-localization + i18next with ICU, wired on day one even for a single-locale launch
- **Observability** — Sentry (crashes, traces) + PostHog (product, flags, experiments)
- **CI** — GitHub Actions for lint/typecheck/test; EAS Workflows for builds, updates, Maestro, submits

Read `references/default-stack.md` for the version numbers, the reasoning, and the conditions under
which each default is the wrong choice. Check every version against the live registry before
installing — this file ages.

**Deviations are cheap to record and expensive to forget.** A deviation gets a line in `stack.md` and,
if it has consequences beyond one package, an ADR in `docs/app/decisions/`.

## How to run a build session

1. Read `docs/app/brief.md` and `docs/app/stack.md`. If either is missing, go back to the gate.
2. State which phase the work belongs to and which skill owns it. Invoke that skill.
3. Build the smallest **vertical slice** that a user could actually touch — schema through API through
   screen — rather than a horizontal layer. Horizontal layers hide integration failures until the end.
4. Walk a user-visible slice with `visual-verification` first, then run `self-review` on the slice
   before moving on — the review's first question asks for rendered evidence the walk is what produces.
5. Append anything decided to `stack.md` or a new ADR. Update the task list.

## Things that waste the most time on these projects

Stated plainly, because each is a natural instinct:

**Scaffolding before deciding.** Every hour of scaffolding on an undecided stack is an hour that gets
thrown away or, worse, defended.

**Building horizontally.** All the screens, then all the API, then the schema. The integration bugs
all arrive at once, at the end, under launch pressure.

**Treating store rules as a submission-day problem.** Account deletion, restore purchases, privacy
manifests, permission strings and the paywall disclosure rules are architecture, not paperwork. They
are cheap when built in and expensive as rework. `store-submission` is readable from day one and
should be read early, not first opened the week of launch.

**Deferring instrumentation.** An onboarding funnel that was not instrumented while it was built
cannot be diagnosed later, only rebuilt.

**Deferring localisation plumbing.** Retrofitting i18n is a full-app sweep. Wiring the catalogue on
day one and shipping one locale costs almost nothing.

**Letting Expo Go be the acceptance environment.** It has a fixed native binary. Anything with a
config plugin or a native module behaves differently there. Use a development build from the first day.

**Optimising before measuring.** `performance-security` starts with measurement for a reason.

## Reference files

- `references/default-stack.md` — the locked stack, versions, reasoning, and when each default is wrong
- `references/vertical-slice.md` — how to cut a slice, and the definition of done for one
- `references/timeline.md` — the external clocks that set the launch date, and a ten-week shape
- `assets/stack-template.md`, `assets/adr-template.md` — and the brief's template lives in the
  `product-discovery` skill's own `assets/`

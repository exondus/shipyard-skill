# Timeline and external clocks

Verified 29 August 2026. The waiting periods below are set by Apple, Google and Clerk and change
without notice — verify each against the source named in the linked reference file before committing
to a date.

The phase table in `SKILL.md` is a dependency order, not a schedule. This file is the schedule.

## The clocks that are not yours

These start when you start them and cannot be compressed by working harder. Every one of them has
ended a launch date that was otherwise achievable, and every one is invisible until you go looking.

| Clock | Duration | Starts when | Where |
|---|---|---|---|
| **Google Play closed testing** — personal accounts created since Nov 2023 need a minimum number of testers continuously opted in for a fixed period, then a production application reviewed separately | Roughly 3–4 weeks from a cold start, including recruiting testers | You have an installable build and a tester list | `store-submission/references/play.md` |
| **Play developer verification** — organisation accounts need D-U-N-S and site/email verification | Days to weeks | Account creation | same |
| **Clerk production DNS + certificate** | Up to 48 hours after records are added | You add the records | `clerk-auth/references/production-checklist.md` |
| **Your own OAuth credentials** — Google, Apple, and any other provider, created in each provider's console and swapped into the production Clerk instance | Hours of work, but it blocks every social sign-in in production | Any time after the domain exists | same |
| **Apple age rating questionnaire** and any current age-assurance obligation | Minutes, but an unanswered questionnaire can block submitting an update at all | Any time | `store-submission/references/apple-technical.md` |
| **TestFlight external review** | Usually short, but it is a review and it can come back | First external build | `store-submission/SKILL.md` |
| **App review itself, plus one rejection cycle** | Assume at least one round trip | Submission | `store-submission/references/rejections.md` |
| **App Store featuring nomination** | Submit at least three weeks before the publication date | Any time, but the date must be set | `aso-growth/references/launch.md` |
| **Translation turnaround**, if you are launching in more than one language | Days to weeks depending on the vendor | Catalogue is stable | `localization-foundation/references/ops.md` |

**Start the Play testing clock and the Clerk production clock in the first fortnight**, well before
the phases that own them. They need almost nothing from the app — an installable build and a domain —
and starting them early costs nothing while starting them late costs the launch date.

## A ten-week shape

An honest sketch for one person building a subscription app for both stores. It is a shape, not a
plan; adjust it, but adjust it knowing which parts are elastic.

| Week | Build work | Clock started that week |
|---|---|---|
| 1 | Discovery, brief, stack locked, scaffold, first development build on a device | Play account created, testers being recruited, domain bought |
| 2 | Auth slice end to end; schema and RLS for the core object | Clerk production instance, DNS records in, own OAuth apps created |
| 3 | Token system and the first real screen; the activation-path slice | Play closed testing opened with a rough build |
| 4 | Onboarding sequence, instrumented as it is built | |
| 5 | Entitlements, paywall, purchase sandbox working end to end | Store listings drafted; keyword research done and the **name and subtitle frozen** |
| 6 | Push credentials and the reminder jobs; polish pass on the core loop | Screenshots and preview video produced |
| 7 | Performance and size pass; security sweep; the states nobody built yet | First external TestFlight build submitted |
| 8 | Fix what TestFlight found; localisation catalogue frozen if shipping more than one language | Featuring nomination submitted if the date is firm |
| 9 | `preflight-audit` intake, audit, remediate | Play production application submitted if testing has run its course |
| 10 | Verify pass, submit, respond to review | |

The elastic weeks are 4 through 7. Weeks 9 and 10 are not elastic and neither are any of the clocks in
the first table.

## What this means for the phase table

Read the phase order as "do not start this until that artifact exists", not as a calendar. In practice:

- **Store requirements are week-one reading, not week-nine work.** Account deletion, restore
  purchases, report and block, permission handling and the paywall disclosures are all build tasks in
  the feature they belong to. `store-submission` says this at the top for a reason.
- **ASO's name and subtitle freeze happens mid-build**, not at the end, because the name goes into the
  binary, the listing, the marketing site and the press kit, and changing it late touches all four.
- **Instrumentation is not a phase.** It is a condition every other phase is built under.
- **Localisation plumbing is not a phase either.** The decision about which languages to ship is; the
  plumbing is day one.

## When the date is already fixed

If a date is immovable and the clocks do not fit, the honest options are to cut scope, to launch one
platform first — iOS usually, because the Play testing clock is the longest external dependency — or
to move the date. Working faster is not on the list, because the binding constraints are other
people's queues.

Say which of the three is being chosen, out loud, and write it in `docs/app/brief.md`. A launch that
slips because nobody named the constraint is the same slip as one that was planned, minus the
preparation.

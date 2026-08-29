---
name: product-discovery
description: >
  Research and scope an app idea before any code is written — who it is for, what job it does, who
  already does it, what is genuinely in v1, and what the one activation event is. Use when someone asks
  "is this worth building", "what should the MVP be", "scope this for me", "who else is doing this",
  "what should be in v1", or wants competitor or market research on an app idea; and whenever work is
  about to begin on a project that has no docs/app/brief.md. Also use before adding a significant new
  feature to an existing app, to check the same evidence questions. For a general "build me an app"
  request, ship-app routes here first. Produces the project brief every other Shipyard skill reads.
---

# Product discovery

Building starts here, always. Not because process is virtuous, but because four specific decisions
get made in the first hour whether or not anyone researches them — who the user is, what the app is
called, what the schema looks like, and where the paywall goes — and all four are expensive to change
and cheap to get right up front.

The output is one short file, `docs/app/brief.md`, plus whatever teardowns are worth keeping in
`docs/app/research/`. Not a business plan. A page the build can be checked against.

## The rule

**Do not propose an architecture, a schema, a package list or a screen until the brief is written and
the user has agreed with it.** If the user is impatient, do the research fast and out loud, but do it.
The single most expensive failure mode in agent-built apps is a beautifully executed answer to a
question nobody asked.

## What to find out

Six questions. Each has a "you don't have this yet" test — if the answer is generic, the research is
not done.

**1. Who, specifically.** Not "busy professionals". A person with a situation: "someone tracking a
chronic condition their GP asked them to log daily". Test: can you name where this person currently
complains about the problem — a subreddit, a Discord, a review section? If not, you have a demographic,
not a user.

**2. The one job.** The single thing the app does that the person would miss. Everything else in v1
exists to make that one thing usable. Test: state it in one sentence with no "and".

**3. What they do today.** The incumbent is almost never a competitor app — it is a notes app, a
spreadsheet, a WhatsApp message to themselves, or nothing. Understand why that is tolerable, because
that is the bar. Test: you can describe their current workflow step by step.

**4. Who else is in the store.** 8–12 apps that would appear for the same searches. For each: what
they charge, their rating count (your proxy for how immovable they are in search), and — most
usefully — **what their 1–3 star reviews complain about**. Negative reviews of competitors are the
highest-yield research available and they are free. Test: you can name three specific complaints that
recur across competitors.

**5. Where the money is.** Free, subscription, one-off, or free with a hard paywall. Decide the shape
now because it changes the onboarding, the schema and the store metadata. The evidence is blunt:
median day-35 install-to-paid is roughly 10.7% behind a hard paywall against 2.1% for freemium, with
essentially identical twelve-month retention (RevenueCat, State of Subscription Apps 2026). Freemium
is a defensible choice; it is not the safe default it feels like. Route the detail to
`payments-paywalls`.

**6. The activation event.** The one action, performed once, that most strongly predicts the user
coming back in week four. Log the first meal. Finish the first lesson. Send the first message. This
single sentence goes on to define the onboarding sequence, the first analytics funnel, and what "the
app works" means. Test: it is one user action, observable in a database row.

## How to research it

Search rather than recall. Prices, competitors, review sentiment, category norms and store rules all
move, and confident recall about any of them is usually stale.

- **Store reconnaissance.** Search the App Store and Play listings for the obvious queries a user
  would type. Read the top apps' subtitles and screenshots — that is their positioning, stated by
  people who paid to learn it. Read their recent 1–3 star reviews.
- **Where the users complain.** Reddit, Discord, X, App Store reviews of the incumbent. Quote them
  verbatim in the brief; the user's own words become the store listing copy and the onboarding
  microcopy later.
- **Technical feasibility spike.** Name every capability that is not obviously solved — background
  location, HealthKit, on-device ML, offline sync, video processing, a specific third-party API. For
  each: does a maintained Expo-compatible library exist, does it work under the New Architecture, and
  does it need a config plugin? An unfeasible core capability discovered in week three is the whole
  project. Check React Native Directory and the library's actual recent release history, not its
  README.
- **Regulatory read.** Health, finance, kids, UGC, dating, crypto and AI-chat categories carry
  specific store obligations that shape the build. Flag them now; `store-submission` has the detail.

Dispatch parallel sub-agents for the competitor teardown and the feasibility spike when there are more
than a handful of each — they are independent and the wall-clock saving is real. Give each one the
brief's framing so it does not return a generic summary.

## Scoping v1

The purpose of scoping is not to make a small app. It is to make an app that can be judged.

Sort every feature into three lists and write all three down:

- **In v1** — required for the one job and the activation event. If removing it means the activation
  event cannot happen, it is in.
- **Fast follow** — genuinely wanted, deliberately not now. Naming these is what makes cutting them
  survivable.
- **Not this product** — the ideas that quietly turn a habit tracker into a social network.

Then apply the store floor. Certain things are not optional even in v1 because a reviewer will reject
without them: in-app account deletion if there are accounts, restore purchases if there are purchases,
report/block if there is user-generated content, a privacy policy reachable inside the app, and an
experience that works when a permission is denied. These belong in the "in v1" list from the
beginning, not in a pre-submission scramble.

## Writing the brief

Use `assets/brief-template.md`. Keep it to roughly one page. Every claim that came from research
carries a link and the date it was read — six weeks later nobody can tell a researched fact from a
guess, and the difference matters.

End the brief with **the three things most likely to make this fail**, named honestly. Not risks in
the abstract: the specific thing. "The core interaction depends on a library last published in 2023."
"Every competitor is free and ad-supported." "The activation event requires a permission most users
deny."

Then present the brief and ask for agreement before moving to the stack. Ask about the parts you had
to assume; do not ask about the parts the research settled.

## After the brief

Hand back to `ship-app` to lock the stack. Keep the brief alive: when a build decision contradicts it,
one of the two is wrong, and finding out which is a five-minute conversation now and a rebuild later.

Re-run a lightweight version of this — questions 4, 5 and 6 — before every significant new feature.
"Which competitor complaint does this answer, and which event proves it worked?" is a two-minute
question that kills a surprising number of features.

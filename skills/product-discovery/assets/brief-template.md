# Project brief — <app name>

Written <date>. Last reviewed <date>.

Keep this to one page. Every researched claim carries a link and the date it was read, because six
weeks from now nobody can tell a researched fact from a guess and the difference matters.

---

## The user

<A person in a situation, not a demographic. "Someone tracking a chronic condition their GP asked them
to log daily", not "health-conscious adults".>

**Where they talk about this problem:** <subreddit, Discord, review section, forum — with a link>

## The one job

<One sentence, no "and". The single thing the app does that this person would miss.>

## What they do today

<Their current workflow, step by step. The incumbent is usually a notes app, a spreadsheet, a message
to themselves, or nothing. This is the bar.>

## Who else is in the store

| App | Price | Rating count | What its 1–3★ reviews complain about |
|---|---|---|---|
| | | | |

**Recurring complaints across competitors** (this is the highest-yield research available):

1.
2.
3.

**Where we are different, in a sentence a user would repeat:**

## Money

**Model:** <free · subscription · one-off · free with hard paywall>
**Reasoning:**
**Processor:** <RevenueCat + Stripe/Paystack — see docs/app/stack.md>

## The activation event

<One user action, observable as a database row, that most predicts them being here in week four.>

This defines the onboarding sequence, the first analytics funnel, and what "the app works" means.

## Scope

**In v1** — required for the one job and the activation event:

-

**Fast follow** — wanted, deliberately not now:

-

**Not this product** — the ideas that would turn this into something else:

-

**Store floor, non-negotiable in v1** (see the `store-submission` skill):

- [ ] In-app account deletion that deletes, plus a web deletion URL for Play
- [ ] Restore purchases, if there are purchases
- [ ] Report and block, if there is user-generated content
- [ ] Privacy policy reachable inside the app
- [ ] Works with every permission denied
- [ ] Sign in with Apple, if social login is the primary path

## Technical unknowns

| Capability | Library / approach | Maintained? New Arch? | Verdict |
|---|---|---|---|
| | | | |

## Regulatory read

<Health, finance, kids, UGC, dating, crypto, AI chat — anything that carries specific store or legal
obligations. Note it here even if the answer is "none".>

## The three things most likely to make this fail

Specific, not abstract.

1.
2.
3.

---

## Changelog

| Date | Change | Why |
|---|---|---|

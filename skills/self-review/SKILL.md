---
name: self-review
description: >
  Adversarially review work that was just produced — a feature slice, a schema change, a screen, a
  refactor — before calling it done. Use after finishing any unit of implementation work, when someone
  asks "did that actually work", "review what you just built", "check your own work", "is this done",
  or before marking a task complete. Use it whenever a change is about to be committed, merged or
  handed back. This is per-slice review during the build; for whole-project readiness before a release
  or store submission use the preflight-audit skill instead.
---

# Self-review

The failure mode of an agent reviewing its own work is not laziness. It is that the reviewer already
believes the code is correct, having just written it, and so reads it looking for confirmation. Every
technique here exists to break that.

The output of a review is never "looks good". It is a list of specific claims about specific lines,
each with the evidence that makes it true or the execution that proves it.

## When to run it

After every vertical slice, before moving to the next. Also before any commit, before handing work
back, and immediately after fixing a bug (the fix is the highest-risk code in the repo — it was
written under time pressure by someone who had already been wrong once about this area).

Skip it for pure formatting, a rename with no behaviour change, or content-only edits. Say that you
are skipping it and why.

## The four questions

Ask them in this order. The order matters — later questions are meaningless if an earlier one fails.

### 1. Does it run?

Not "does it compile". Run it. Typecheck, lint, tests, and then the actual path a user takes through
the change. For a screen, that means rendering it in a dev build via `visual-verification` — a screen
claimed to render without having been walked is an inferred result, not an executed one. For an API
change, that means calling it. For a migration, that means applying it to a real database and querying
through the policy the app actually uses.

Report the **command you ran and its output**, not the diff. A diff is a claim; an execution is
evidence. If you could not execute something, say so explicitly and label everything downstream of it
as inferred.

### 2. Is it wired?

The most common defect in agent-written code is not a wrong implementation. It is a correct
implementation that nothing calls.

For each thing added, name the call site. A hook that no component uses, a policy that no query
exercises, a feature flag that nothing reads, a guard that runs after the thing it was meant to
guard, an error boundary that wraps a component that cannot throw, an event that fires in a code path
that is unreachable — all of these read as finished work in a diff.

Ask directly: **if I deleted this file, what would break, and how would I notice?** If the answer is
"nothing" or "I wouldn't", the work is not done.

### 3. Was the old thing removed?

The second most common defect: the safe path was added and the unsafe one was left callable.

- The new query helper exists; the raw unfiltered query is still exported and still called in two places
- Validation was added to the form; the API still accepts the unvalidated payload
- The RLS policy was written; the service-role client is still used on that route
- The new component was built; the old one is still what the route renders
- The retry was added; the original un-retried call still runs on the cold path

Grep for the old symbol by name. Grep for the pattern the fix was meant to eliminate. If the old path
must stay — sometimes it must — justify why it is safe to leave standing, in writing.

### 4. What did I break?

Assume the change broke something and go looking. Concretely:

- What else imports what I touched? Read those call sites, do not assume.
- What is the behaviour for an existing user, on an existing device, with existing local state, with
  an old app version still in the wild? Mobile users do not update. A schema or API change that only
  works for fresh installs is a production incident on a delay.
- What happens offline, on a cold start, on a slow network, on the smallest supported screen, at
  200% font scale, with the permission denied, with an empty list, with a very long string?
- What does this cost — an extra query per row, a new subscription, a new paid service tier?

## Adversarial passes

Two passes that reliably find what the four questions miss.

**Read it as if someone else wrote it and you dislike them.** Not to be unkind — to change what you
are looking for. You are now hunting for the shortcut, the unhandled case, the comment that explains
what instead of why, the `any`, the swallowed error, the TODO that will never be done.

**Write the bug report from the future.** "It is two weeks after launch. This exact code caused a
support ticket. What does the ticket say?" This produces different findings from a checklist, because
a checklist can only catch what someone already thought to write down.

For a slice that touches money, auth, data deletion, or anything a store reviewer will look at,
**dispatch a fresh sub-agent** that has not seen the implementation. Give it the requirement, not the
solution, and ask "is this true of the code as written". An agent told what was fixed will find it
fixed.

## Domain checks

Run the ones that apply. Each maps to a specialist skill that has the detail.

| If the slice touched | Check | Skill |
|---|---|---|
| Auth | The route is protected server-side, not only in the UI. Session claims are re-read, not cached in state. Sign-out clears the token cache. | `clerk-auth` |
| Data | RLS is enabled and a policy exists per operation. Every column used in a policy is indexed. The migration is forward-only and old clients still work. | `postgres-data` |
| UI | Loading, empty, error and offline states exist. Touch targets ≥44pt. It survives 200% font scale. Motion respects reduced motion. It does not fail the slop checklist. | `premium-ui` |
| Money | Entitlement is checked server-side against your own table, not a client SDK. Webhooks verify the raw body and are idempotent. Restore purchases is reachable. | `payments-paywalls` |
| Onboarding | Every step emits an event with the same discriminator. Permission asks are primed, not cold. | `onboarding-flow` |
| Any user-visible string | It is in the catalogue, has a translator description, and uses ICU for plurals. | `localization-foundation` |
| Anything at all | No secret reached the client bundle. No PII reaches Sentry. | `performance-security` |

## The closure record

End every review with this, per finding. It is deliberately the same shape the `preflight-audit` skill
uses, so findings carry forward without translation.

```
FINDING:  what and where (file:line)
ADDED:    what now exists
REMOVED:  what no longer exists — the old path, the stale call site.
          If nothing: why the old path is safe to leave standing
WIRED:    the call site or policy that makes the added thing take effect.
          Existing in the repo is not wired
PROOF:    the command run and its output. Not the diff — the execution
STATUS:   CLOSED | PARTIAL | DEFERRED | NOT-A-BUG
```

Then state, in one line, what you could **not** check and why. That line is the most useful sentence
in the review, and the one most often omitted.

**Where it goes.** A review of a routine slice belongs in the conversation. Write it to
`docs/app/review/YYYY-MM-DD-<slice>.md` when any of these is true: a finding is left PARTIAL or
DEFERRED, the slice touched money, auth or data deletion, or the review found something that changes a
decision recorded in `docs/app/stack.md`. Those are the reviews someone will need to find again, and
`preflight-audit` reads them as history when it runs its intake.

## Do not

- Do not report "no issues found" without saying which of the four questions you actually executed
  and which you only reasoned about. Zero findings from a review that ran nothing is not a clean
  result, it is an absent one.
- Do not soften a finding to be encouraging. Rank honestly; put warmth in how the fix is framed.
- Do not fix and re-review in the same breath — write the findings down first, then fix, then verify
  against the original findings rather than against your memory of them.
- Do not mark a task complete with a PARTIAL or DEFERRED finding outstanding unless the user has seen
  it and agreed.

# Before the first walk of a project

Not time-sensitive. Read once per project, then it is a checklist.

A driven walk is not a read-only operation. It taps real buttons in a real build against whatever
backends that build points at. Four things it can damage, in descending order of how often it actually
happens.

## 1. The analytics funnel

This is the one that bites, because nothing appears to go wrong.

`observability-analytics` defines an event taxonomy and `onboarding-flow` requires every step to emit
an event. A walk through onboarding therefore fires a complete, perfectly-formed activation funnel —
from a machine, repeatedly, sometimes dozens of times a day. Those events are indistinguishable from
real ones. Conversion rates drift, an experiment reads wrong, and the funnel that the whole product
was supposed to be measured against quietly stops being trustworthy. Nobody notices for weeks, because
the data looks fine. It is just false.

Arrange one of these before the first walk and record which in `docs/app/stack.md`:

- A separate analytics project for development builds — cleanest, and the default worth setting up.
- A super-property on every event identifying the session as automated, with the production dashboards
  filtering it out. Cheaper, but depends on a filter nobody forgets.
- Analytics disabled in dev builds. Simplest, and it forfeits the chance to verify instrumentation,
  which is one of the better reasons to walk in the first place. Prefer one of the first two.

Whichever it is, **verify it once by walking two stops and confirming where the events landed.** An
isolation scheme that was configured but not checked is the same shape of defect this whole skill
exists to catch.

## 2. Money

Purchases must run through the store sandbox, never live billing. `payments-paywalls` owns the setup;
what matters for a walk is that a paywall stop is one tap from a real charge if the environment is
wrong, and that webhooks fired by sandbox purchases still hit whatever endpoint the build is
configured against — so a sandbox purchase can still write a real entitlement row into a real
database.

Confirm before the first paywall walk: sandbox account signed in, and the webhook endpoint pointing at
a development environment. Then check the entitlements table afterwards to see which rows the walk
created, and clean them up. A test entitlement left in production data is a support ticket waiting for
a real user with the same ID.

## 3. Real people

If the build points at a production database, a walk can send a push notification to real users, write
rows against real accounts, or trigger a real email. Push is the sharpest edge here — `push-engagement`
wires a send path, and a walk that exercises it from a production-configured build reaches actual
devices belonging to actual people.

Point walks at a development or staging backend. Where that is not possible, name the production
operations the walk will perform, get explicit agreement first, and do not walk any destructive path —
account deletion in particular, which store rules require to actually delete.

## 4. Secrets and personal data in the artifacts

A walk produces screenshots and log dumps, and both are full of things that should not be pasted into
a report or committed to a repo: session tokens in a network panel, an API key in a console line, a
signed-in user's email in a header, a real name in seeded data, a support ticket's contents.

`preflight-audit` makes this point about its own verification pass and it applies here with more
force, because this skill generates output it has not seen before it shows it.

Practically:

- Walk with a seeded test account carrying obviously fake data. Never a real user's account, and never
  your own personal one.
- Filter log and network captures before they go into a report. **Names, not values** — say that an
  `Authorization` header was present and well-formed, not what it contained.
- Look at a screenshot before including it. This sounds obvious and is the step that gets skipped,
  because the screenshot was taken to prove something else.
- Artifacts under `docs/app/review/` are committed to the repo. Treat that directory as public.

## The one-time setup

Once per project, then never again:

- [ ] Dev/staging backend confirmed, or the production operations named and agreed
- [ ] Analytics isolated, and the isolation verified by a two-stop walk
- [ ] Billing sandbox confirmed; webhook endpoint pointing somewhere safe
- [ ] Seeded test account with fake data, and a reset-to-first-run mechanism that works
- [ ] Artifact handling agreed: what gets committed, what gets filtered
- [ ] All of the above written into `docs/app/stack.md`, because the next walk will assume it

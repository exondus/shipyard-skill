# Vertical slices

Not time-sensitive. This is a working method, not a fact about a vendor.

## What a slice is

A slice is the thinnest path through every layer that a user could actually touch, built end to end
before anything else is built at all: one table, one policy, one endpoint, one screen, one event.

The alternative — all the screens, then all the API, then the schema — is the default instinct because
each horizontal layer feels coherent while you are in it. It fails for one reason: **integration
defects are only discovered at integration**, so building horizontally postpones every one of them to
the same week, which is the week before launch.

A slice also produces something demonstrable, which matters more than it sounds. A demonstrable thing
gets feedback; a layer gets a status update.

## Cutting one

Take the activation event from `docs/app/brief.md` and ask what the smallest observable version of it
is. Then cut the slice around that, not around a feature area.

Good first slices:

- "A signed-in user can save one item and see it after a cold restart."
- "A user can complete the first onboarding question and the answer is in the database."
- "A user hits the paywall, the purchase sandbox completes, and the server sees the entitlement."

Bad first slices, all of which are layers wearing a slice's clothes:

- "Set up the design system" — no user touches it.
- "Build the auth screens" — the screens without the session are half the problem and the easy half.
- "Create all the tables" — schema without a query exercising it is untested schema.

## The order inside a slice

Bottom up, because the constraints run that way and discovering them late is what costs:

1. **Schema and policy.** The table, the RLS policy, the index the policy needs. Apply the migration
   to a real database.
2. **Query, through the policy the app will actually use.** Not as a superuser. A query that works as
   the service role and fails as the user is the most common false completion in this whole process.
3. **The endpoint or procedure**, with authorisation re-checked server-side.
4. **The screen**, with all its states — loading, empty, error, offline — not only the happy one.
5. **The event**, emitted with the properties `docs/app/analytics-spec.md` specifies.
6. **The test** that would catch the regression: a Maestro flow for the path, or a unit test for the
   logic that was actually subtle.

## Done

A slice is done when all of these are true. Anything less is in progress, whatever the diff looks
like.

- It runs on a **development build on a real device**, not only in a simulator, and not in Expo Go.
- It survives a **cold restart** — the session persists, the data is there.
- Every state renders: loading, empty, error, offline, and the longest plausible string.
- The server rejects the request when it should. Verified by making the bad request, not by reading
  the code.
- The event fires, and it is visible in the analytics tool. Not "the call is in the code".
- `self-review` has been run over it and every finding is CLOSED, or DEFERRED with the user's
  agreement.
- Anything decided along the way is written into `docs/app/stack.md` or a new ADR.

## Sequencing slices

Roughly this order, because each removes uncertainty for the next:

1. **Riskiest technical unknown first.** If the app depends on a capability nobody has proved — a
   library, an API, a device feature, a permission users may deny — prove it in week one with the
   ugliest possible slice. This is the only case where ugly is correct: the question is "is this
   possible", and design work spent before that answer is at risk.
2. **Auth**, because everything else assumes an identity and retrofitting one rewrites every policy.
3. **The activation path**, because it is the product.
4. **Money**, because entitlement architecture is invasive and because it is the thing most likely to
   be rejected.
5. **Everything else**, in the order the brief's in-scope list puts it.

Localisation plumbing, the token system, and instrumentation are not slices — they are conditions the
first slice is built under. Wiring them costs almost nothing on day one and is a full-app sweep later.

## When a slice grows

If a slice cannot be finished in a sitting, it was not a slice. Cut it again rather than pushing
through: half a slice left overnight loses the state that made it coherent, and the half that gets
finished is usually the visible half, which leaves the unwired half looking complete.

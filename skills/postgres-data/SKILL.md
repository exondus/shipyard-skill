---
name: postgres-data
description: >
  Design and operate the Postgres data layer for an app, on Supabase or off it. Use for schema design,
  choosing primary keys, row level security policies and their performance traps, indexing, pagination,
  connection pooling and pool sizing, choosing and configuring an ORM, migrations that keep old mobile
  clients working, Supabase Storage/Realtime/Edge Functions, and moving to or from Neon or another
  Postgres host. Also use for "my query is slow", "RLS broke my query", "too many connections",
  "prepared statement does not exist", or planning a schema change that ships to users who never update.
---

# The data layer

Two facts shape every decision here, and both are easy to forget until they hurt.

**Row level security is a query planner problem, not just a security feature.** A policy is a
predicate added to every query. Written naively it turns a millisecond scan into a two-minute one, and
the failure looks like "Postgres is slow" rather than "the policy is wrong".

**Mobile clients never fully update.** A schema change is not deployed when it is applied; it is
deployed when the last user running the old app has upgraded, which may be a year. Every migration is
therefore a compatibility exercise, not a state change.

## Schema defaults

Take these unless there is a reason not to, and record the reason if there is:

- **UUIDv7 primary keys generated client-side.** The mobile client needs to mint IDs offline for
  optimistic writes and idempotent retries, and v7's time-ordered prefix keeps B-tree inserts local —
  UUIDv4 scatters them, which shows up as index bloat and cache misses. Reserve `bigint GENERATED
  ALWAYS AS IDENTITY` for high-volume append-only internal tables that never appear in a URL or on a
  device. Never `serial`.
- `timestamptz` always, never `timestamp`. `text` with a `CHECK`, not `varchar(n)`. `numeric` for
  money, never a float. `jsonb` only for genuinely schemaless data.
- `created_at` / `updated_at` maintained by a trigger, not by the client, with the client's write
  privilege on those columns revoked.
- **Soft delete via `deleted_at timestamptz`**, not a boolean — it records when, and mobile delta sync
  needs the tombstone anyway. Every index over the table then carries `WHERE deleted_at IS NULL`.
- A lookup table with a foreign key, or a `text` column with a `CHECK`, in preference to a Postgres
  enum. Enum values cannot be removed or reordered, and an old client will keep sending the old value
  long after you stopped wanting it.
- `snake_case` throughout. Denormalise the tenant key (`user_id`, or `org_id` for team products) onto
  every row so a policy never has to join upward.

## RLS that does not destroy performance

Enable RLS on every table in the exposed schema, write **one policy per operation** (never `FOR ALL`),
target the `authenticated` role explicitly, and index every column a policy touches.

The one habit that matters most: **wrap the auth function in a subquery** — `(select auth.uid())`
rather than `auth.uid()`. That turns a per-row function call into a cached initplan evaluated once.
Supabase's own published measurements put the difference at roughly 179ms against 9ms on a test table;
adding the missing index on the policy column takes 171ms to under a tenth of a millisecond, and
replacing a policy that joins with a `SECURITY DEFINER` helper function took one case from about
eleven seconds to seven milliseconds.

A policy that queries another RLS-protected table is the recursive trap. Put the lookup in a
`SECURITY DEFINER STABLE` function in a private schema with a pinned empty `search_path`, and call it
from the policy inside a subquery.

Also filter in the application query even though the policy already does. It is not redundant to the
planner — it gives it a predicate to plan against rather than a filter to apply afterwards.

`references/rls.md` has the canonical policy set to copy, the helper-function pattern, and the
Supabase performance advisor lints to drive to zero.

## Indexing and pagination

Composite before multiple singles whenever a query filters on one column and orders by another; the
equality predicate leads. `INCLUDE` payload columns to make hot list queries index-only. Partial
indexes for the soft-delete and status predicates you always apply.

**Keyset pagination, always. Never `OFFSET`.** `OFFSET n` makes Postgres read and discard n rows, so
page 1000 costs a thousand times page 1, and rows shift under the user as new ones arrive. Order by
`(created_at desc, id desc)` and pass the client an opaque cursor, never a page number.

Read plans with `EXPLAIN (ANALYZE, BUFFERS)` and look at three things: actual against estimated rows
(a large gap means stale statistics), `Rows Removed by Filter` (a missing index), and `shared read`
against `shared hit` (cache misses). Sort `pg_stat_statements` by total execution time, not mean — the
query that runs ten thousand times is the problem, not the one that takes a second once.

## Connections

Getting this wrong presents as random production failures under load, not as a config error.

- Migrations, dumps and long-lived servers: the direct connection.
- Serverless, edge and Lambda: the transaction-mode pooler, which **does not support prepared
  statements** — set the driver flag (`prepare: false`, or the equivalent) or every deploy fails with
  a prepared-statement error nobody can reproduce locally.
- Never run migrations through the transaction pooler.
- Size the pool from the instance's direct connection limit, minus what the platform reserves, divided
  by the number of app instances. On a small instance that is single digits per Node process and
  exactly one per serverless function.

## ORM

Drizzle server-side, with raw SQL through a Postgres driver for the hot paths. It compiles to SQL you
can read, works on edge runtimes, generates plain `.sql` migrations that drop straight into the
Supabase migrations folder, and models RLS policies in the same typed schema file as the tables —
which is decisive, because policies that live away from the schema drift from it.

**The ORM never enters the mobile bundle.** Native talks to PostgREST or to your API; `packages/db` is
server-only and enforced by lint rule.

## Migrations for clients that never update

Forward-only. No down migrations in production; fix forward with a new file. Then **expand, migrate,
contract**, always:

1. **Expand** — add the new nullable column or table, and a trigger or dual-write keeping old and new
   in sync. Deploy. Old clients are unaffected.
2. **Migrate** — backfill in batches so no lock is held long. New app versions read and write the new
   shape.
3. **Contract** — drop the old column only once telemetry shows the old client versions are below your
   threshold. That is typically months, not weeks.

Never rename a column, drop one, or narrow a type in a single step. Never add a `NOT NULL` column
without a default while old clients still insert. Ship a minimum-supported-version gate in the API
from day one — an endpoint that returns "upgrade required" below a floor — because without it the
contract step can never safely happen.

## Supabase specifics

Realtime's Postgres Changes is RLS-checked per subscriber and scales worst; prefer Broadcast for
anything fan-out. Storage policies live on the objects table and key off the bucket and the first path
segment — and a public bucket bypasses them entirely, which is the standard way private files leak.
Branching is data-less by default. Edge Functions have a short CPU budget that catches people doing
real work in them.

Local development is the CLI: init, start, `migration new`, edit SQL, `db reset` to replay everything
against a clean database, `db push`. Generate types into `packages/db` so the schema is the source of
the app's types.

**Egress is the bill.** Serving media directly from Storage to a mobile app burns the allowance
quickly; put a CDN in front and never `select *` on wide rows for a list view. `cost-control` has the
numbers and the thresholds at which moving off is rational.

Off Supabase — Neon, RDS, or anything else — you rebuild what came free: the auth role and claim
plumbing that RLS policies assume, object storage with authorization, realtime, and the generated REST
API. Neon's scale-to-zero makes it markedly cheaper for staging and per-branch preview environments,
which is a good reason to use both.

## Reference files

- `references/rls.md` — policy patterns, the performance fixes with measured effects, helper functions
- `references/performance.md` — indexing, keyset pagination, reading plans, the advisor lints
- `references/connections.md` — pooler modes, driver flags, pool sizing
- `references/migrations.md` — expand/contract worked examples and the version-gate pattern
- `references/supabase.md` — Storage, Realtime, Edge Functions, CLI workflow, limits

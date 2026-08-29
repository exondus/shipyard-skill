# Migration discipline for an app with old clients in the wild

Verified August 2026. Limits, prices and platform behaviour change — check the live docs before relying on numbers here.

## Forward-only

No `down` migrations in production. A rollback script is one nobody has run against real data, written before the failure was understood, and it usually destroys the rows the incident is about.

- Migrations are timestamped SQL files in `supabase/migrations/`, committed, reviewed, applied by CI.
- Never edit a migration applied anywhere but your laptop. Fix forward with a new file.
- Every migration must be safe to apply while the **previous app version is still serving traffic**. That is the whole discipline; expand/contract is how you achieve it.
- Use an explicit transaction except for `CREATE INDEX CONCURRENTLY`, `ALTER TYPE ... ADD VALUE` and `VACUUM`, which cannot run inside one.
- Set a lock timeout on any migration touching a hot table so blocked DDL fails fast instead of queueing every reader behind it:

```sql
set local lock_timeout = '3s';
set local statement_timeout = '30s';
```

## Expand → migrate → contract

Mobile is why. An iOS or Android build in the wild is not updatable on your schedule; a meaningful tail of users sits on a release for **6–12 months**, and some never update. Any schema change must therefore be split into phases where old and new clients are both correct.

### 1. Adding a column

Safe in one step if — and only if — it is nullable or has a default, and no old client does `insert` with an explicit column list that omits it while the column is `NOT NULL` without a default.

```sql
-- expand (safe, instant on PG11+: non-volatile defaults are metadata-only)
alter table public.posts add column excerpt text;
alter table public.posts add column view_count integer not null default 0;
```

Never `add column ... not null` without a default: it rewrites the whole table and takes an `ACCESS EXCLUSIVE` lock for the duration. Symptom: the migration hangs and every query on the table piles up behind it.

### 2. Renaming a column (`title` → `headline`)

Never `ALTER TABLE ... RENAME COLUMN` in one shot. Old clients select `title`; the rename makes every one of them 400.

```sql
-- PHASE 1 — EXPAND (ship before the new app version)
alter table public.posts add column headline text;

create or replace function public.posts_sync_headline() returns trigger
language plpgsql as $$
begin
  if new.headline is distinct from old.headline then
    new.title := new.headline;                 -- new client wrote headline
  elsif new.title is distinct from old.title then
    new.headline := new.title;                 -- old client wrote title
  end if;
  return new;
end $$;

create trigger posts_sync_headline
  before insert or update on public.posts
  for each row execute function public.posts_sync_headline();
```

```sql
-- PHASE 2 — MIGRATE (backfill, batched; see below)
-- then ship the app version that reads and writes `headline`
```

```sql
-- PHASE 3 — CONTRACT (only after telemetry says old clients are gone)
drop trigger posts_sync_headline on public.posts;
drop function public.posts_sync_headline();
alter table public.posts drop column title;
```

### 3. Changing a type (`integer` → `bigint`, `text` → `numeric`)

An in-place `ALTER COLUMN ... TYPE` rewrites the table and holds `ACCESS EXCLUSIVE`. On anything large, add a new column instead.

```sql
-- EXPAND
alter table public.orders add column amount_cents bigint;

create or replace function public.orders_sync_amount() returns trigger
language plpgsql as $$
begin
  new.amount_cents := coalesce(new.amount_cents, (new.amount * 100)::bigint);
  new.amount       := coalesce(new.amount, (new.amount_cents / 100.0)::numeric);
  return new;
end $$;
create trigger orders_sync_amount before insert or update on public.orders
  for each row execute function public.orders_sync_amount();

-- MIGRATE: backfill, then add the constraint without a full-table lock
alter table public.orders
  add constraint orders_amount_cents_not_null
  check (amount_cents is not null) not valid;      -- instant, only checks new rows
alter table public.orders validate constraint orders_amount_cents_not_null;  -- SHARE UPDATE EXCLUSIVE

-- CONTRACT
drop trigger orders_sync_amount on public.orders;
alter table public.orders drop column amount;
alter table public.orders alter column amount_cents set not null;
```

`NOT VALID` then `VALIDATE` is the general trick for adding constraints (including foreign keys) to a large live table: the first step takes a brief lock, the second scans under a weaker lock that does not block reads or writes.

### 4. Dropping a column

`DROP COLUMN` is metadata-only and fast, but breaks every old client that selects it explicitly — and `select *` clients that deserialize into a strict struct.

Sequence: stop writing it → confirm no reads via `pg_stat_statements` and app telemetry → wait out the client tail → drop. If you cannot wait, just stop populating it; a dead nullable column costs almost nothing.

### 5. Adding an index on a live table

Always concurrently, outside a transaction, over the direct connection:

```sql
create index concurrently if not exists posts_user_created_idx
  on public.posts (user_id, created_at desc) where deleted_at is null;
```

Symptom of forgetting `concurrently`: writes to the table block for the whole build. Symptom of a failed concurrent build: an `INVALID` index that the planner ignores — check `select * from pg_index where not indisvalid;`, then `drop index concurrently` and retry.

## Batched backfill

Never `update posts set headline = title;` on a large table — one long transaction, table-wide dead tuples, held locks, replication lag.

```sql
do $$
declare
  n integer;
begin
  loop
    with batch as (
      select id from public.posts
      where headline is null
      order by id
      limit 5000
      for update skip locked
    )
    update public.posts p
       set headline = p.title
      from batch b
     where p.id = b.id;

    get diagnostics n = row_count;
    exit when n = 0;
    commit;                       -- procedures/DO with commit require PG11+ and no outer txn
    perform pg_sleep(0.1);        -- give autovacuum and replicas room
  end loop;
end $$;
```

If your runner wraps everything in a transaction, run the backfill as a one-off job or `pg_cron` task, not inside the migration file. Add a partial index on the backfill predicate (`where headline is null`) so each batch's lookup stays cheap; drop it afterwards.

## Minimum-supported-version API gate

Old clients are only manageable if you can measure and eventually refuse them.

- Every request from the app sends `X-App-Version: 3.4.1` and `X-App-Platform: ios|android`.
- The API records `(version, platform)` per request into a low-cardinality counter (or your analytics pipeline) — this is the telemetry that makes the contract decision possible.
- A config value `min_supported_version` per platform is served from the database and enforced in the edge/route middleware:

```ts
if (semverLt(appVersion, cfg.minSupported[platform])) {
  return new Response(JSON.stringify({ code: 'UPGRADE_REQUIRED', storeUrl }), {
    status: 426, headers: { 'content-type': 'application/json' },
  });
}
```

- The app handles `426` with a blocking "Update required" screen linking to the store. Ship this handler in version 1 — you cannot add it retroactively to clients already in the field.
- Also ship a soft gate (`recommended_version`, dismissible prompt), and use `expo-updates` OTA for JS-only changes so the store tail only matters for native ones.

## Deciding when contract is safe

Do not guess. Query the version telemetry:

```sql
select app_version, platform, count(distinct user_id) as users,
       round(100.0 * count(distinct user_id)
             / sum(count(distinct user_id)) over (partition by platform), 2) as pct
from api_requests
where requested_at > now() - interval '14 days'
group by 1, 2
order by platform, app_version;
```

Contract when **every version below the cutoff is under ~1% of 14-day active users per platform**, and you raised `min_supported_version` above that cutoff at least one release cycle earlier so the stragglers are already blocked, not silently broken. Typical expand→contract elapsed time on a consumer app: 3–6 months, longer on Android.

Track every uncontracted expand (a `docs/pending-contracts.md` or issues labelled `contract`) with its cutoff version and earliest safe date. Without it the dual-write triggers survive forever and become the schema.

## Compatibility views

When the shape change is too big to bridge with a column, give old clients a view with the old shape and point new clients at the table.

```sql
create view public.posts_v1
  with (security_invoker = true) as
select id, user_id, headline as title, created_at
from public.posts
where deleted_at is null;

grant select on public.posts_v1 to authenticated;
```

`security_invoker = true` is required or the view runs as its owner and silently bypasses RLS on `posts`. Route by version in the client SDK, not the database. Delete the view at contract time.

Alternative: `pgroll` generates versioned views per migration automatically and rolls back schema changes without touching data (https://xata.io/blog/pgroll-schema-migrations-postgres). Worth it for many breaking changes; overkill for a handful.

## Supabase CLI workflow

```bash
supabase init                        # creates supabase/ with config.toml
supabase start                       # local Postgres + Studio + Auth + Storage in Docker
supabase migration new add_headline  # creates supabase/migrations/<ts>_add_headline.sql
# ...write SQL...
supabase db reset                    # drop, replay ALL migrations, run seed.sql — the real test
supabase db diff -f add_headline     # optional: capture Studio-made changes into a migration
supabase link --project-ref <ref>
supabase db push                     # apply pending migrations to the linked project (direct 5432)
supabase gen types typescript --linked > packages/db/src/database.types.ts
supabase test db                     # pgTAP tests, including your RLS impersonation tests
```

`supabase db reset` is the only honest check that your migration set applies from zero — run it in CI on every PR. `supabase db push` is what CI runs on merge to `main`.

**Branching** (https://supabase.com/docs/guides/deployment/branching): a preview branch is a fresh project that replays `supabase/migrations/` plus `seed.sql`; persistent branches survive for staging. Branches are **data-less by default** — no production rows, no auth users, no storage objects — which is deliberate and also means a branch will not surface a backfill that is slow on real data. Branches bill at $0.01344 per branch-hour on Pro/Team (https://supabase.com/pricing), so tear down preview branches on PR merge.

Do not run `supabase db diff` against production and commit the result as a migration; it produces a schema *snapshot* diff that will happily include a destructive drop. Write migrations by hand for anything with data implications.

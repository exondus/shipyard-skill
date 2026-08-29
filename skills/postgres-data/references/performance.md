# Indexing, pagination and query performance

Verified August 2026. Limits, prices and platform behaviour change — check the live docs before relying on numbers here.

## Composite index vs several single-column indexes

Postgres *can* combine two single-column indexes with a BitmapAnd, but it pays for it: two index scans, a bitmap build, then a heap re-check of every candidate row, and the result comes back unordered so any `ORDER BY` needs a separate sort. A composite index does one scan and can also satisfy the ordering.

Use a composite index when a query filters on more than one column, or filters on one and orders by another. Use single-column indexes when the columns are genuinely queried independently.

**Column-order rule, in priority order:**

1. Columns compared with **equality** first (`user_id = $1`, `org_id = $1`, `status = 'active'`).
2. Then the column used for **range or ordering** (`created_at desc`).
3. Then any remaining low-selectivity filters.

A composite index `(a, b, c)` serves queries on `(a)`, `(a, b)` and `(a, b, c)` — the leading prefix. It does **not** serve a query on `(b)` alone. So `(user_id, created_at)` makes `posts_user_id_idx` redundant; drop the single-column one. `(created_at, user_id)` does not, and is the wrong order for a per-user feed.

```sql
-- one index, serves the feed query and the ownership check
create index posts_user_created_idx
  on public.posts (user_id, created_at desc, id desc)
  where deleted_at is null;
```

Symptom that you got the order wrong: `EXPLAIN` shows an Index Scan but with a large `Rows Removed by Filter`, or a Bitmap Heap Scan plus a Sort node.

## Covering indexes (`INCLUDE`)

`INCLUDE` appends payload columns to the leaf pages so a query can be answered **index-only** with no heap fetch. The included columns are not part of the ordering or the uniqueness, so they do not distort the key.

```sql
create index posts_feed_covering
  on public.posts (user_id, created_at desc)
  include (id, title, thumbnail_url)
  where deleted_at is null;
```

Use it for the two or three hot list queries that select a handful of small columns. Do not include wide `text`/`jsonb` — you will bloat the index past the point where it stays in cache and lose more than you gain.

An index-only scan still consults the visibility map, so it only pays off on tables that are vacuumed. Symptom of a stale visibility map: `EXPLAIN` says `Index Only Scan` but `Heap Fetches:` is a large number. Fix with `vacuum (analyze) posts;` and, on a hot table, a lower `autovacuum_vacuum_scale_factor`.

## Partial indexes

`WHERE` on the index shrinks it to the rows you actually query. On a table with soft deletes or a status column where 95% of rows are irrelevant, this is often a 10–20x size reduction, which is the difference between an index that lives in shared buffers and one that does not.

```sql
create index orders_pending_idx on public.orders (created_at desc)
  where status = 'pending';

create index posts_live_user_idx on public.posts (user_id, created_at desc)
  where deleted_at is null;
```

The planner only uses a partial index when it can prove the query's WHERE implies the index's WHERE. `deleted_at is null` in the query matches `where deleted_at is null` on the index; `deleted_at is not distinct from null` may not. Keep the predicate textually identical across query and index.

Related: BRIN for append-only, naturally ordered columns. Supabase notes BRIN "routinely results in indexes that are +10x smaller than the equivalent default B-tree index" on always-increasing fields (https://supabase.com/docs/guides/database/query-optimization). Good for an events table scanned by time range; useless for point lookups.

## Keyset pagination — and why OFFSET dies

`LIMIT 20 OFFSET 10000` makes Postgres produce and then throw away 10,000 rows. Cost grows linearly with page number, so page 500 is 500x page 1. Worse, if a row is inserted between requests every subsequent page shifts and the user sees a duplicate or misses an item — which on a mobile infinite-scroll feed reads as a bug.

Keyset (seek) pagination compares against the last row you returned. Reference: https://use-the-index-luke.com/no-offset

```sql
-- page 1
select id, title, created_at
from public.posts
where user_id = $1
  and deleted_at is null
order by created_at desc, id desc
limit 20;

-- page n+1: pass back the last row's (created_at, id) as the cursor
select id, title, created_at
from public.posts
where user_id = $1
  and deleted_at is null
  and (created_at, id) < ($2::timestamptz, $3::uuid)
order by created_at desc, id desc
limit 20;
```

Supporting index — the ordering columns must match the index exactly, including direction:

```sql
create index posts_user_created_idx
  on public.posts (user_id, created_at desc, id desc)
  where deleted_at is null;
```

Notes:

- The row-comparison form `(a, b) < (x, y)` is what lets a single index scan seek directly; `a < x or (a = x and b < y)` usually does not.
- Include a tiebreaker (`id`) or rows sharing a timestamp will be skipped or repeated.
- Hand the client an **opaque base64 cursor**, never a page number, and never expose the raw timestamp shape — you want to change it later without breaking old mobile clients.
- In PostgREST: `.order('created_at', {ascending:false}).order('id', {ascending:false}).lt(...)` or, more reliably for the tuple comparison, an RPC.

## Reading `EXPLAIN (ANALYZE, BUFFERS)`

Always all three: `explain (analyze, buffers, format text) select ...;`. On Supabase you can also enable `explain()` through PostgREST by setting `pgrst.db_plan_enabled` on the authenticator role — do it only behind an IP filter, it leaks schema shape (https://supabase.com/docs/guides/api/rest/debugging-performance).

The three things to look at, in order:

1. **Estimated vs actual rows.** `(cost=... rows=50 ...) (actual ... rows=48000 ...)`. A gap of 10x or more means the planner is working from bad statistics and every join choice above that node is suspect. Fix: `analyze <table>;`, raise `alter table t alter column c set statistics 1000;`, or add extended statistics (`create statistics ... (dependencies) on a, b from t`) for correlated columns.
2. **`Rows Removed by Filter`.** Large numbers mean you fetched rows only to discard them — a missing or wrongly ordered index, or an RLS predicate that could not use one.
3. **`Buffers: shared hit=... read=...`.** `hit` is cache, `read` is disk. High `read` on a query that runs constantly means the working set does not fit; either the index is too big (make it partial/covering) or the compute add-on is too small. `Buffers` is the only metric that is stable across a warm and cold cache — timings are not.

Also flag: any `Seq Scan` on a table over a few thousand rows; a `Sort` with `Sort Method: external merge Disk:` (raise `work_mem` for that statement or index the ordering); `Nested Loop` with a large outer row count.

## `pg_stat_statements`

Enabled on Supabase; it backs the Dashboard's Query Performance report (https://supabase.com/docs/guides/database/extensions/pg_stat_statements).

```sql
select
  round(total_exec_time::numeric, 0)          as total_ms,
  calls,
  round(mean_exec_time::numeric, 2)           as mean_ms,
  round((100 * total_exec_time /
         sum(total_exec_time) over ())::numeric, 1) as pct,
  rows,
  query
from pg_stat_statements
order by total_exec_time desc
limit 25;
```

**Sort by `total_exec_time`, not `mean_exec_time`.** A 4 ms query called 2 million times an hour costs far more, and is far easier to fix, than a 900 ms report run twice a day. `mean` sorting surfaces the analytics query nobody cares about and hides the N+1 in your feed endpoint.

Companion views worth knowing: `pg_stat_user_tables` (`seq_scan` high + `idx_scan` low = missing index; `n_dead_tup` high = vacuum problem), `pg_stat_user_indexes` (`idx_scan = 0` = index you are paying write cost for and never reading — drop it), and `pg_stat_activity` for what is running right now. `select pg_stat_statements_reset();` before a benchmark run.

## `index_advisor`

Supabase ships `index_advisor`, which uses HypoPG to test hypothetical indexes and report the cost delta (https://supabase.com/docs/guides/database/extensions/index_advisor):

```sql
create extension if not exists index_advisor;

select * from index_advisor(
  'select id, title from public.posts
   where user_id = ''...'' and deleted_at is null
   order by created_at desc limit 20'
);
-- returns startup_cost_before/after, total_cost_before/after, index_statements
```

Feed it your top 20 statements from `pg_stat_statements`. Treat the output as a suggestion, not an instruction: it does not know about write amplification, and it will happily propose five overlapping indexes where one composite would do.

## Query shapes that are slow through PostgREST — make them RPCs

PostgREST generates one SQL statement from the URL. Some shapes generate pathological SQL or simply cannot express what you need. Move these into `create function ... returns setof ...` and call `.rpc()`:

- **Deep or multi-level embedding** (`select=*,author(*),comments(*,author(*))`) — becomes correlated subqueries with a JSON aggregate per parent row, and every embedded table's RLS is evaluated per row.
- **Filtering a parent by a child's column** (`comments.author.name=eq.x`) — inner-join semantics through embedding are fragile and the planner often cannot push the predicate down.
- **Aggregations and window functions** — counts, group-by dashboards, ranking, running totals.
- **Tuple/row-comparison keyset cursors** — `(created_at, id) < (?, ?)` has no clean PostgREST syntax.
- **Full-text search with ranking** — `ts_rank`, highlighting, trigram similarity ordering.
- **Anything that needs a transaction** across multiple writes — PostgREST gives you one statement; an RPC gives you a function body that is one transaction.
- **`count=exact` on a large table** — forces a full count on every page request. Use `count=planned` or `estimated`, or return no count at all and let the client stop when a page comes back short.

In the RPC, keep `security invoker` (the default) so RLS still applies, mark it `stable` if it only reads, and pin `set search_path = ''`.

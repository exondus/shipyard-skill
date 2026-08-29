# Connections, poolers and pool sizing

Verified August 2026. Limits, prices and platform behaviour change — check the live docs before relying on numbers here.

## Endpoints, ports and modes

Source: https://supabase.com/docs/guides/database/connecting-to-postgres

| Use case | Host | Port | Mode | Notes |
|---|---|---|---|---|
| Migrations, `pg_dump`/`pg_restore`, long-lived VM or container | `db.<ref>.supabase.co` | 5432 | direct | IPv6 by default; needs the IPv4 add-on on IPv4-only networks |
| Long-lived server on an IPv4-only network | `aws-<region>.pooler.supabase.com` | 5432 | Supavisor **session** | One Postgres connection held per client connection; prepared statements work |
| Serverless / edge / Lambda / Vercel functions | `aws-<region>.pooler.supabase.com` | 6543 | Supavisor **transaction** | Connection returned to the pool at the end of each transaction; IPv4 on all tiers |
| Latency-sensitive, paid tiers | `db.<ref>.supabase.co` | 6543 | Dedicated pooler (PgBouncer), transaction only | Lower latency than the shared pooler; paid plans only |

Username format differs: direct connections use `postgres`; the shared pooler uses `postgres.<project-ref>` (the project ref is part of the username, that is how Supavisor routes).

**Session mode on port 6543 was removed on 28 February 2025** (https://supabase.com/changelog/32755-supabase-connection-pooler-deprecating-session-mode-on-port-6543-on-february-28). Any config still pointing session-mode traffic at 6543 is broken; session mode is 5432 on the pooler host.

**IPv4.** The direct connection resolves to an AAAA record only. The IPv4 add-on costs $0.0055/hour ≈ **$4/month** and *swaps* the DNS record — it is not dual-stack (https://supabase.com/docs/guides/troubleshooting/supabase--your-network-ipv4-and-ipv6-compatibility-cHe3BP). Both Supavisor modes are IPv4-reachable without the add-on, so the add-on is only needed for direct-connection tooling on an IPv4-only network.

Self-hosted equivalent: PgBouncer in `pool_mode = transaction`, `max_client_conn` sized to your fleet, `default_pool_size` sized to your Postgres `max_connections` minus superuser reserve. All the transaction-mode caveats below apply identically.

## Transaction mode breaks prepared statements

In transaction mode a client's connection is handed back to the pool after every transaction, so a `PREPARE` issued on one physical connection is not there when the next statement lands on a different one.

Symptoms:

- `prepared statement "s0" already exists` or `prepared statement "s1" does not exist`
- `ERROR 42P05` / `26000`
- Intermittent — works under low load when the pool happens to reuse the same backend, fails under concurrency. This intermittency is the tell.

Driver flags:

| Client | Flag |
|---|---|
| Prisma | Append `?pgbouncer=true&connection_limit=1` to the pooled URL; set `directUrl` to the 5432 direct connection for migrations (https://supabase.com/docs/guides/database/prisma, https://supabase.com/docs/guides/database/prisma/prisma-troubleshooting) |
| `postgres.js` (and Drizzle's `drizzle-orm/postgres-js`) | `postgres(url, { prepare: false })` |
| `node-postgres` / `pg` (and `drizzle-orm/node-postgres`) | Do not use `client.query({ name: '...' })`; unnamed statements are fine |
| TypeORM | `extra: { prepareThreshold: 0 }` [UNVERIFIED against current TypeORM docs] |
| SQLAlchemy / asyncpg | `prepared_statement_cache_size=0`, or `statement_cache_size=0` on asyncpg [UNVERIFIED] |

Also unavailable in transaction mode: `LISTEN`/`NOTIFY`, session-level `SET` that must persist across statements, advisory locks held across statements, `WITH HOLD` cursors, and `pg_advisory_lock` used as a distributed mutex. If you need any of those, use session mode.

Note that `set_config(..., true)` (transaction-local) *does* work in transaction mode — this is what makes the Drizzle-on-Supabase RLS pattern (set `request.jwt.claims` inside a transaction, run the query, reset) safe through the pooler.

## Never migrate through the pooler

Run every migration, `pg_dump`, `pg_restore`, `CREATE INDEX CONCURRENTLY`, and extension install over the **direct connection on 5432**.

Why: DDL frequently needs session state and advisory locks that transaction mode drops; `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block at all and the pooler's implicit transaction wrapping will break it; and a migration that fails halfway through because its connection was recycled leaves the schema in a state your migration table does not describe.

Symptoms of migrating through 6543: `CREATE INDEX CONCURRENTLY cannot run inside a transaction block`, advisory-lock timeouts in Prisma/Drizzle migrate ("Timed out trying to acquire a postgres advisory lock"), or a migration marked applied whose DDL is not actually present.

Concretely with Prisma:

```
DATABASE_URL="postgres://postgres.<ref>:<pw>@aws-<region>.pooler.supabase.com:6543/postgres?pgbouncer=true&connection_limit=1"
DIRECT_URL="postgresql://postgres:<pw>@db.<ref>.supabase.co:5432/postgres"
```

With the `supabase` CLI, `supabase db push` already uses the direct connection; do not override it with a pooler URL.

## Pool sizing arithmetic

Per-compute-size limits (https://supabase.com/docs/guides/platform/compute-and-disk):

| Instance | Direct connections | Pooler client connections |
|---|---|---|
| Nano | 60 | 200 |
| Micro | 60 | 200 |
| Small | 90 | 400 |
| Medium | 120 | 600 |
| Large | 160 | 800 |
| XL | 240 | 1,000 |
| 2XL | 380 | 1,500 |
| 4XL | 480 | 3,000 |
| 8XL | 490 | 6,000 |
| 12XL | 500 | 9,000 |
| 16XL | 500 | 12,000 |

Supabase's own services (PostgREST, Realtime, Storage, Auth, pg_cron, the dashboard) hold persistent connections even when your app is idle — budget roughly 20–30 of the direct limit for them, and confirm the real number with `select count(*), usename from pg_stat_activity group by 2;`.

**Long-lived servers (Next.js on a VM/container, worker processes):**

```
pool_size_per_instance = floor((direct_limit - reserved) / instance_count)
```

On Micro (60) with 30 reserved and 3 Node instances: `floor(30 / 3) = 10`. Do not set it higher because "we might get more traffic" — an oversized pool converts a database saturation problem into a database *outage*.

Sanity ceiling regardless of the limit: Postgres does not get faster past roughly `(2 × cores) + effective_spindle_count` concurrently *active* connections. A Micro (2 vCPU) is saturated at about 5–6 concurrent queries; a pool of 40 just queues them inside Postgres, where you cannot see or control the queue.

**Serverless / edge:** pool size **1** per function instance, over transaction mode on 6543. Each concurrent invocation is its own instance; the pooler is the pool. Set an aggressive `connect_timeout` (5–10 s) and `idle_timeout` so an instance frozen between invocations does not hold a slot.

**Two poolers share one budget.** Supavisor and the dedicated PgBouncer each have their own configured pool size, but the *combined* connections across both cannot exceed the instance's limit. Running both without accounting for that is a common self-inflicted outage.

## Symptom → cause table

| Symptom | Likely cause | Fix |
|---|---|---|
| `remaining connection slots are reserved for non-replication superuser connections` | Total connections exceed the instance's direct limit | Reduce per-instance pool size, move app traffic to the pooler, or size up compute |
| `sorry, too many clients already` | PgBouncer/Supavisor `max_client_conn` exceeded | Raise pooler client limit or reduce client concurrency |
| `prepared statement "s0" already exists`, intermittent | Prepared statements over transaction mode | `prepare: false` / `?pgbouncer=true` |
| `Timed out fetching a new connection from the connection pool` (Prisma) | App pool too small for concurrency, or queries too slow | Fix the slow query first; only then raise `connection_limit` |
| `ENETUNREACH` / `connect ETIMEDOUT` to `db.<ref>.supabase.co` | IPv6-only direct connection from an IPv4-only network (common on older CI runners and some corporate VPNs) | Use the pooler, or buy the IPv4 add-on |
| `Timed out trying to acquire a postgres advisory lock` during migrate | Migrating through the pooler | Use the direct 5432 URL |
| `CREATE INDEX CONCURRENTLY cannot run inside a transaction block` | Same | Same |
| Works locally, fails on Vercel under load | Session-mode string (5432) used from serverless; each invocation holds a real backend | Switch to 6543 transaction mode, pool size 1 |
| `LISTEN` never fires | Transaction mode drops the session | Use session mode 5432, or use Realtime/Broadcast instead |
| Latency spikes only at cold start on Neon | Scale-to-zero | Raise the suspend timeout or set always-on on the Scale plan |

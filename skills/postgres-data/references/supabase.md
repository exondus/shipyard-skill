# Supabase platform specifics and their limits

Verified August 2026. Limits, prices and platform behaviour change — check the live docs before relying on numbers here.

## Realtime: prefer Broadcast over Postgres Changes

Limits by plan (https://supabase.com/docs/guides/realtime/limits):

| | Free | Pro | Pro (spend cap off) | Team | Enterprise |
|---|---|---|---|---|---|
| Concurrent peak connections | 200 | 500 | 10,000 | 10,000 | 10,000+ |
| Messages / second | 100 | 500 | 2,500 | 2,500 | 2,500+ |
| Channel joins / second | 100 | 500 | 2,500 | 2,500 | 2,500+ |
| Broadcast payload | 256 KB–3,000 KB | same | same | same | 3,000 KB+ |
| Postgres Changes payload | 1,024 KB | 1,024 KB | 1,024 KB | 1,024 KB | 1,024 KB |

**Why Postgres Changes does not scale.** It reads the WAL and then, for every subscriber, re-evaluates the RLS policy for the changed row to decide whether that subscriber may see it. Cost is O(subscribers × changes), all of it inside your database's CPU budget, competing with your queries. Past a few hundred concurrent subscribers on an active table it becomes the dominant load.

Second trap: when a change exceeds the 1,024 KB payload limit, the `new` and `old` records are truncated to only fields whose value is ≤64 bytes. Symptom: your client receives an event whose payload is mysteriously missing the large `content` or `jsonb` field, intermittently, only for big rows.

**Use Broadcast instead.** Send from the database with a trigger calling `realtime.broadcast_changes()`, or from your server with `channel.send`, on a topic you control (`org:<org_id>`, `chat:<room_id>`), authorized once at subscribe time via RLS on `realtime.messages`. Fan-out then costs one authorization per *channel join*, not per message.

Rules: one channel per logical scope, not per row; send *what changed* (id + version) and let the client refetch instead of shipping the row; expect to hit 500 concurrent connections on Pro-with-spend-cap sooner than you think — and `supabase-js` auto-reconnects in a thundering herd that makes it worse (https://supabase.com/docs/guides/platform/manage-your-usage/realtime-peak-connections).

## Storage: buckets, RLS, and the public bypass

Buckets are rows in `storage.buckets`; files are rows in `storage.objects`. There is no bucket-level policy DSL — you write ordinary RLS on `storage.objects` and discriminate on `bucket_id`. Storage allows **no uploads at all** to a bucket with no policies (https://supabase.com/docs/guides/storage/security/access-control).

```sql
create policy "avatars_insert_own" on storage.objects
  for insert to authenticated with check (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "avatars_select_own" on storage.objects
  for select to authenticated using (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "avatars_delete_own" on storage.objects
  for delete to authenticated using (
    bucket_id = 'avatars' and owner_id = (select auth.jwt()->>'sub')
  );
```

Convention: first path segment is the owning id (`<uid>/avatar.png` or `<org_id>/<uid>/file.pdf`), because `storage.foldername(name)[1]` is the only cheap thing to match on.

**Public buckets bypass all of it.** A bucket marked public is served from an unauthenticated CDN URL; `storage.objects` policies do not gate those reads. Symptom: "my RLS is right but anyone with the link can fetch it." Fix: private bucket + `createSignedUrl(path, ttlSeconds)`. Do not use a public bucket for anything user-specific — object keys are guessable more often than people think.

Cost note: serving media directly from Storage to a mobile app is the fastest way to burn the 250 GB Pro egress allowance ($0.09/GB over; cached egress $0.03/GB — https://supabase.com/pricing). Put a CDN in front and use image transformations sparingly.

## Edge Functions

Limits (https://supabase.com/docs/guides/functions/limits):

| | Value |
|---|---|
| Memory | 256 MB |
| CPU time | **2 s** (actual CPU, excluding async I/O waits) |
| Wall clock | 150 s free / 400 s paid |
| Request idle timeout | 150 s (then 504) |
| Bundle size | 20 MB (CLI bundling) / 5 MB (server-side bundling) |
| Functions per project | 100 free / 1,000 Pro / 2,000 Team |
| Secrets | 100 per project, 48 KiB each |
| Log line | 10,000 chars; 100 events per 10 s |

Runtime is Deno-compatible (Supabase Edge Runtime), TypeScript-first, deployed via `supabase functions deploy`. Outbound ports 25 and 587 are blocked — no direct SMTP. Web Worker and Node `vm` APIs are unavailable; multithreaded native Node libraries do not work.

The 2 s **CPU** limit is what bites: image processing, large JSON transforms and crypto hit it, while awaiting a slow upstream API for 60 s is fine. Symptom: `WORKER_LIMIT`, function terminated with no useful stack. Pin DB-heavy functions with regional invocation (https://supabase.com/docs/guides/functions/regional-invocation) or every query pays a cross-region round trip.

## Database webhooks are fire-and-forget

Supabase Database Webhooks are triggers that call `pg_net`'s `net.http_post()`. `pg_net` is **asynchronous**: the trigger enqueues the request and returns immediately, and the HTTP call happens in a background worker.

Consequences you must design for:

- The webhook is **not transactional** with the write. A rolled-back transaction can still have queued a request [UNVERIFIED whether current pg_net enqueues inside the transaction — verify before relying on either behaviour].
- There is **no retry and no dead-letter**. A 500 from your endpoint is lost. Responses land in `net._http_response` (retained briefly) — that is your only forensic trail.
- A slow endpoint does not slow the transaction, but a flood of writes can back the queue up.

Symptom: "some events never arrived", non-reproducible, worse under load. Fix: for anything that must not be lost, write an `outbox` row in the same transaction and drain it with `pg_cron` + `pg_net`, marking rows delivered only on a 2xx. Keep webhooks for best-effort side effects (analytics pings, cache busts).

## pg_cron

Enable the `pg_cron` extension (Dashboard → Database → Extensions, or `create extension pg_cron;`). Jobs live in the `cron.job` table and history in `cron.job_run_details`; the scheduler runs against the `postgres` database.

```sql
select cron.schedule(
  'drain-outbox',
  '*/5 * * * *',
  $$ select public.drain_outbox(200); $$
);

select cron.unschedule('drain-outbox');

select * from cron.job_run_details
where jobid = (select jobid from cron.job where jobname = 'drain-outbox')
order by start_time desc limit 20;
```

Supabase surfaces this as "Supabase Cron" and documents sub-minute schedules such as `'30 seconds'` (https://supabase.com/docs/guides/cron) [UNVERIFIED exact syntax string]. Prune `cron.job_run_details` with a scheduled delete — it grows without bound and eats your database size allowance. Overlapping runs are not prevented: take a `pg_try_advisory_lock` inside the job if it is not idempotent.

## PostgREST: row caps and embedding pitfalls

- Responses are capped by `db-max-rows` (Supabase default 1000) [UNVERIFIED number — confirm in Project Settings → API]. Symptom: a query silently returns exactly 1000 rows and your client believes that is the whole table. Always paginate explicitly (keyset), never rely on the cap.
- `count=exact` forces a full count on every request. On a large table that is the slowest part of your feed endpoint. Use `planned`/`estimated`, or omit the count.
- **Deep embedding** (`select=*,author(*),comments(*,author(*))`) generates correlated subqueries with JSON aggregation per parent row, and evaluates each embedded table's RLS per row. It is the single most common cause of a 200 ms endpoint becoming a 6 s endpoint after "just one more relation".
- Filtering a parent by a grandchild's column through embedding is fragile; the predicate often cannot be pushed down.
- No aggregations, window functions, tuple comparisons, multi-statement transactions, or ranked full-text search. All of these belong in an RPC (`create function ... returns setof ...`, `security invoker`, `set search_path = ''`).
- `explain()` through PostgREST is off by default; enabling it requires setting `pgrst.db_plan_enabled` on the authenticator role and should be IP-restricted in production (https://supabase.com/docs/guides/api/rest/debugging-performance).
- Statement timeouts are set per role (`anon`, `authenticated`, `service_role`) — a long report run as `authenticated` will be killed [UNVERIFIED default values; check `select rolname, rolconfig from pg_roles;`].

## Local development

```bash
supabase init && supabase start        # Postgres + Studio + Auth + Storage + Edge Runtime in Docker
supabase migration new <name>
supabase db reset                      # replay all migrations + seed.sql — the honest test
supabase functions serve <name>        # local Edge Function with hot reload
supabase gen types typescript --linked > packages/db/src/database.types.ts
supabase test db                       # pgTAP, including RLS impersonation tests
supabase link --project-ref <ref> && supabase db push
```

`config.toml` is committed and drives branch deployments. Keep `seed.sql` small and deterministic — it runs on every reset and branch create.

Platform facts: Postgres **18 was not available on Supabase as of mid-2026** (https://github.com/orgs/supabase/discussions/42681), so no native `uuidv7()` — generate it client-side. Disk attributes change at most **4 times per rolling 24 h** and disk size only grows (https://supabase.com/docs/guides/platform/compute-and-disk). Backups: none Free, 7-day Pro, 14-day Team; PITR +$100/month per 7 days (https://supabase.com/pricing).

## What you rebuild if you leave

| Supabase gives you | Off-platform replacement |
|---|---|
| `auth.uid()`, `auth.jwt()`, the `authenticated`/`anon` roles | On **Neon**: `pg_session_jwt` — but note the functionality formerly called Neon RLS / Neon Authorize is folded into the Neon Data API, and **the Data API and Neon RLS cannot both be enabled** (https://neon.com/docs/guides/neon-rls). Self-hosted: your own JWT verification + `set_config('request.jwt.claims', ...)` per transaction and your own `authenticated` role. |
| Auth service (email, OAuth, magic links, refresh tokens) | Clerk / WorkOS / Auth.js / Better Auth — and you now own the JWT → RLS bridge |
| Storage + policies on `storage.objects` | S3 or Cloudflare R2 + presigned URLs + your own ACL table; RLS no longer covers files |
| Realtime (Broadcast, Presence, Postgres Changes) | Ably / Pusher / a WS service; or `LISTEN`/`NOTIFY` plus your own gateway (and remember `LISTEN` does not work through a transaction-mode pooler) |
| Auto-generated REST API (PostgREST) | Write the API. Or self-host PostgREST — it is open source and the RLS model transfers unchanged. |
| Edge Functions | Vercel/Cloudflare Workers/Deno Deploy |
| Dashboard advisors, `index_advisor`, query performance report | `pg_stat_statements` yourself, plus pganalyze/Datadog |

**Neon** is the strongest database-only alternative: instant branching (10 branches Free/Launch, 25 Scale; extras $1.50/branch-month), autoscaling to 16 CU, and **scale-to-zero** (5 min default on Launch; 1 min to always-on on Scale), which makes per-PR database branches genuinely cheap. Launch $0.106/CU-hour, Scale $0.222/CU-hour, storage $0.35/GB-month, 500 GB egress then $0.10/GB (https://neon.com/docs/introduction/plans). The trade: cold-start latency, plus rebuilding everything in the table above.

Also credible: **AWS RDS / Aurora Serverless v2** (boring, expensive, no branching), **Google Cloud SQL**, self-hosted **CloudNativePG** (cheapest at scale, the only path to PG18 today, but you own backups and failover).

Move off when compute add-ons dominate the bill, you need read replicas or an unserved region, PITR beyond $100/month matters, or you are fighting PostgREST/Realtime limits rather than Postgres. Do not move for raw performance — that is a compute-size or index problem.

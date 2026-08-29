# Clerk Database Sync: Claims, Webhooks, Supabase

Verified August 2026. Versions, package names and dashboard flows change — check the live docs before relying on anything here. Canonical index: <https://clerk.com/docs/guides/development/integrations/databases>

## Two mechanisms, different jobs

| | Read the claim at request time | Mirror via webhooks |
|---|---|---|
| Source | Session JWT via `await auth()` | Clerk → your endpoint → your DB |
| Latency | Zero (no network call) | Seconds to minutes, retried |
| Freshness | ≤60s stale (token refresh interval) | Eventually consistent, can silently lag |
| Correct for | **Authorization.** `userId`, `orgId`, role/permission checks, tenant scoping | **Queryable profile data.** Email, name, avatar for joins, search, admin lists, emails you send |

**Rule: authorize from claims, never from the mirrored table.** A stale mirror that says "admin" after a demotion is a privilege-escalation bug. Clerk's own guidance is that webhooks are unsuitable for synchronous flows — for immediate data, read the session token or call the Backend API (<https://github.com/clerk/skills/blob/main/skills/features/clerk-webhooks/SKILL.md>).

**Rule: store the Clerk `userId` as your foreign key.** Do not mint your own user IDs and map them. `user_id text not null` referencing Clerk's `user_...` keeps every table joinable without a lookup, and makes RLS trivial.

You usually need both: claims for every request, a webhook mirror so `SELECT … JOIN users` works and admin screens can show names.

## Webhook handler

Verify with the framework helper; it wraps Svix signature checking.

```ts
// app/api/webhooks/clerk/route.ts
import { verifyWebhook } from '@clerk/nextjs/webhooks'

export async function POST(req: Request) {
  const evt = await verifyWebhook(req)   // throws on bad signature
  // evt.type, evt.data
}
```

Requires `CLERK_WEBHOOK_SIGNING_SECRET` (**per-instance** — dev and prod differ).

*Skipping verification presents as: anyone who learns the URL can POST a forged `user.created` and create accounts in your database.* Clerk: *"Skipping verification, even for notification-only handlers, exposes the endpoint to spoofed events."*

**Exclude the route from middleware protection.** Clerk's servers carry no session cookie. *Presents as: every delivery 404s or redirects to sign-in; the Svix dashboard shows 100% failure and your users table stays empty.*

### Events that matter

| Event | Action |
|---|---|
| `user.created` | Upsert user row |
| `user.updated` | Upsert (email, name, avatar, public metadata) |
| `user.deleted` | Soft-delete or cascade |
| `organization.created` / `.updated` / `.deleted` | Mirror orgs |
| `organizationMembership.created` / `.updated` / `.deleted` | Mirror membership; **display only — authorize from `orgId`/`org_role` claims** |

Also available: sessions, billing, payments, email/SMS events. Subscribe narrowly; every extra event is load and another failure mode.

### Idempotency

Svix retries on any non-2xx, so **duplicate deliveries are normal, not exceptional**. Dedupe on the delivery ID from the **`svix-id` header**.

```sql
create table webhook_events (
  svix_id text primary key,
  received_at timestamptz not null default now()
);
```

Insert `svix-id` with `on conflict do nothing`; if zero rows inserted, return 200 and stop. *Without this, presents as: duplicate rows, doubled welcome emails, or double-charged credits — intermittently, under retry conditions you cannot reproduce locally.*

### Unordered delivery

Svix does **not** guarantee ordering. A `user.updated` can land before the `user.created` it follows, and two rapid updates can arrive reversed.

Defend with **upsert plus a timestamp guard** — never a bare `INSERT`, never a blind `UPDATE`:

```sql
insert into users (id, email, name, updated_at)
values ($1, $2, $3, $4)
on conflict (id) do update
  set email = excluded.email,
      name = excluded.name,
      updated_at = excluded.updated_at
  where users.updated_at < excluded.updated_at;
```

Use the event payload's `updated_at`, not `now()`. *Without the guard, presents as: a user changes their name and it reverts a few seconds later, because an older event arrived last.* Out-of-order `user.created` is handled for free because the upsert creates the row either way.

Return 2xx fast. Do slow work (emails, third-party calls) on a queue. *Presents as: Svix marks the endpoint failing and backs off, so events arrive minutes late or get dropped after the retry window.*

### Backfill and drift

- **Backfill** before cutover: paginate `clerkClient.users.getUserList()` from the Backend API and upsert. Necessary because users created before the endpoint existed generate no events.
- **Reconcile on a schedule.** Deliveries fail, endpoints have outages, retry windows expire. Run a nightly job comparing Clerk's user list against your table; upsert missing, flag orphans. Do not assume the mirror is complete.
- Treat the mirror as a cache that can be rebuilt from Clerk at any time. If a value cannot be rebuilt, it does not belong in the mirror — put app-owned data in its own table keyed by the Clerk `userId`.

## Clerk + Supabase

### The old method is deprecated — most tutorials are stale

The **JWT template + shared JWT secret** approach was deprecated **1 April 2025**, over security concerns about sharing the JWT secret and implementation complexity. Projects on it were excluded from TP-MAU charges only through **1 Jan 2026** (<https://supabase.com/docs/guides/auth/third-party/clerk>, <https://clerk.com/changelog/2025-03-31-supabase-integration>).

Any guide that tells you to paste Supabase's JWT secret into a Clerk JWT template named `supabase`, or to call `getToken({ template: 'supabase' })`, is out of date. The current method needs **no shared secret and no per-request template token**.

### Configure both sides

**Clerk side.** Dashboard → the Supabase integration → activate. This adds `"role": "authenticated"` to session tokens (Supabase's APIs require that claim) and surfaces your **Clerk domain**.

**Supabase side.** Authentication → **Third-Party Auth** → add Clerk → paste the Clerk domain. Or in `config.toml`:

```toml
[auth.third_party.clerk]
enabled = true
domain = "your-clerk-domain"
```

*Forgetting the `role: authenticated` claim presents as: every query returns empty or `permission denied for schema public`, even though the JWT looks valid.*

### Client

Pass an `accessToken` callback — Supabase then fetches a fresh Clerk token per request itself.

```ts
// client
const supabase = createClient(url, anonKey, {
  accessToken: async () => session?.getToken() ?? null,   // useSession()
})

// server (Next.js App Router)
const supabase = createClient(url, anonKey, {
  accessToken: async () => (await auth()).getToken(),
})
```

Do **not** also pass an `Authorization` header or set a global header — `accessToken` supersedes it, and mixing them presents as intermittent 401s.

### Claims available in RLS

| Claim | Expression | Meaning |
|---|---|---|
| `sub` | `auth.jwt()->>'sub'` | **Clerk user ID** — the join key |
| `org_id` | `auth.jwt()->>'org_id'` | Active organization |
| `org_role` | `auth.jwt()->>'org_role'` | Role in that org, e.g. `org:admin` |
| `fva` | `auth.jwt()->'fva'->>1` | Factor verification age — second-factor recency, for MFA-restrictive policies |

```sql
alter table tasks enable row level security;

create policy "own tasks: select" on tasks
for select to authenticated
using (auth.jwt()->>'sub' = user_id);

create policy "own tasks: insert" on tasks
for insert to authenticated
with check (auth.jwt()->>'sub' = user_id);

create policy "org admins manage docs" on documents
for all to authenticated
using (
  auth.jwt()->>'org_id' = org_id
  and auth.jwt()->>'org_role' = 'org:admin'
);
```

Use `fva` in a **restrictive** policy to require recent MFA for sensitive tables.

*Enabling RLS with no policy presents as: every query silently returns zero rows — no error. Forgetting RLS entirely presents as: the anon key reads every row of every tenant.* Always verify with a second test user.

`auth.uid()` is Supabase-Auth-specific and is **not** what you want here — `auth.jwt()->>'sub'` carries the Clerk ID. [UNVERIFIED: whether `auth.uid()` is populated under third-party auth; use the explicit `sub` expression.]

Edge Functions need the same `accessToken` client construction; passing the raw anon key there is a common cause of policies appearing to fail only in functions (<https://github.com/orgs/supabase/discussions/34988>).

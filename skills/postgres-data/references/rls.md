# Row Level Security: policies that are correct and fast

Verified August 2026. Limits, prices and platform behaviour change — check the live docs before relying on numbers here.

## The canonical policy set

One policy per operation. Never `FOR ALL`. Copy this per table and change the table name and the ownership predicate.

```sql
alter table public.posts enable row level security;

create policy "posts_select_own"
  on public.posts
  for select
  to authenticated
  using ( (select auth.uid()) = user_id );

create policy "posts_insert_own"
  on public.posts
  for insert
  to authenticated
  with check ( (select auth.uid()) = user_id );

create policy "posts_update_own"
  on public.posts
  for update
  to authenticated
  using      ( (select auth.uid()) = user_id )
  with check ( (select auth.uid()) = user_id );

create policy "posts_delete_own"
  on public.posts
  for delete
  to authenticated
  using ( (select auth.uid()) = user_id );

create index posts_user_id_idx on public.posts (user_id);
```

Clause by clause:

| Clause | Why it is written that way |
|---|---|
| `alter table ... enable row level security` | Without it the policies exist but are never enforced; PostgREST will happily return every row. Supabase lints the omission as `rls_disabled_in_public`. |
| separate policies per operation | `USING` is evaluated on rows being read/matched; `WITH CHECK` on rows being written. `FOR ALL` collapses them and makes it impossible to allow reads but restrict writes, and it makes each policy harder to reason about and to index. |
| `to authenticated` | Restricts the policy to that role so Postgres skips it entirely for `anon`. Supabase measured **170 ms → <0.1 ms** from adding this alone (https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv). |
| `(select auth.uid())` not `auth.uid()` | The subquery makes the planner evaluate it once as a cached **InitPlan** instead of once per row. Measured **179 ms → 9 ms**. Only valid when the result does not depend on the row — which is true for `auth.uid()`, `auth.jwt()` and any `STABLE` helper. |
| `update` has both `USING` and `WITH CHECK` | `USING` alone lets a user update a row they own into a row someone else owns (`set user_id = <other>`). Omitting `WITH CHECK` on update is the single most common real RLS hole. |
| index on `user_id` | RLS predicates are just WHERE clauses. Unindexed, Supabase measured **171 ms → <0.1 ms** from adding the index. |

## Performance fixes, with measured effect

All figures from Supabase's own troubleshooting guide (https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv, mirrored as https://github.com/orgs/supabase/discussions/14576).

| Fix | Before → after |
|---|---|
| Index every column used in a policy that is not already a PK/unique | 171 ms → <0.1 ms |
| Wrap `auth.uid()` / `auth.jwt()` in `(select ...)` | 179 ms → 9 ms |
| Replace a policy that joins another RLS-protected table with a `SECURITY DEFINER` helper | 11,000 ms → 7 ms |
| Add `TO authenticated` | 170 ms → <0.1 ms |
| Rewrite `exists (select 1 from join_table where ...)` as `col in (select ...)` | 9,000 ms → 20 ms |
| Also filter in the client/app (`.eq('user_id', uid)`), do not rely on the policy to do the filtering | 171 ms → 9 ms |
| `col = any (array(select helper()))` on large membership sets | >2 min → 2 ms |

The last row matters more than it looks: RLS is a *filter*, not an *index hint*. The planner often cannot push a policy predicate down as well as it pushes an explicit user WHERE clause. Always send the redundant filter from the app as well.

## The recursive-policy problem

Symptom: a query hangs, times out at the statement timeout, or errors with `infinite recursion detected in policy for relation "memberships"`.

Cause: the policy on `posts` selects from `memberships`, and `memberships` itself has RLS whose policy selects from `memberships` (or from `posts`). Postgres re-enters policy evaluation per row.

Fix: put the lookup in a `SECURITY DEFINER STABLE` function, which runs as the function owner and therefore bypasses RLS on the tables it reads.

```sql
create schema if not exists private;

create or replace function private.user_org_ids()
returns uuid[]
language sql
security definer
stable
set search_path = ''            -- pin it; unqualified names are a privilege-escalation vector
as $$
  select coalesce(array_agg(m.org_id), '{}')
  from public.memberships m
  where m.user_id = auth.uid();
$$;

revoke execute on function private.user_org_ids() from public, anon;
grant  execute on function private.user_org_ids() to authenticated;
```

Rules for these helpers:

- `SECURITY DEFINER` **plus** `set search_path = ''` **plus** fully qualified table names. A `SECURITY DEFINER` function without a pinned `search_path` can be hijacked by a caller who creates a shadowing object in a schema they control.
- `STABLE`, not `VOLATILE` — `VOLATILE` cannot be folded into an InitPlan and will be re-evaluated per row.
- Live in a schema that is **not** exposed to PostgREST (`private`, not `public`), and `revoke execute ... from anon`.
- Call it wrapped: `(select private.user_org_ids())`.

## Multi-tenant / org-scoped policies

Denormalize `org_id` onto every row. Do not make RLS walk a hierarchy.

```sql
create policy "documents_select_org"
  on public.documents
  for select
  to authenticated
  using ( org_id = any ((select private.user_org_ids())) );

create policy "documents_write_admin"
  on public.documents
  for insert
  to authenticated
  with check (
    org_id = any ((select private.user_org_ids()))
    and (select private.user_role_in(org_id)) in ('owner','admin')
  );

create index documents_org_idx on public.documents (org_id) where deleted_at is null;
```

If the membership set is large, prefer `= any (array(select ...))` over `in (select ...)` — that is the >2 min → 2 ms case above, because the array form is materialised once and the index scan gets a real equality-any predicate.

For "public plus mine" reads, use two permissive policies (they OR together) rather than one policy with an `OR`:

```sql
create policy "posts_select_public" on public.posts
  for select to anon, authenticated using ( visibility = 'public' and deleted_at is null );
create policy "posts_select_own"    on public.posts
  for select to authenticated using ( (select auth.uid()) = user_id );
```

Use `as restrictive` only when you want an AND — e.g. a global "never expose soft-deleted rows" rule layered under every permissive policy.

## Advisor lints to drive to zero

Supabase's Performance/Security Advisor (Dashboard → Advisors, docs at https://supabase.com/docs/guides/database/database-advisors) is the fastest audit you have. Treat these as build-breaking:

| Lint | Meaning |
|---|---|
| `0003_auth_rls_initplan` | An auth function is called unwrapped in a policy. Wrap it in `(select ...)`. https://supabase.com/docs/guides/database/database-advisors?lint=0003_auth_rls_initplan |
| `multiple_permissive_policies` | Two permissive policies for the same role+action; each is evaluated per row. Merge, or split by role. |
| `rls_disabled_in_public` | Table is exposed via PostgREST with RLS off. |
| `policy_exists_rls_disabled` | Policies written but RLS never enabled — the classic false sense of security. |
| `unindexed_foreign_keys` | Usually the same column your policy filters on. |
| `security_definer_view` | A view owned by a superuser silently bypasses the underlying table's RLS. Prefer `security_invoker = true` on views over exposed tables. |

## Storage: policies live on `storage.objects`

Buckets are rows in `storage.buckets`; files are rows in `storage.objects`. There is no per-bucket policy language — you write ordinary RLS on `storage.objects` and discriminate on `bucket_id`. By default Storage allows no uploads to a bucket without policies (https://supabase.com/docs/guides/storage/security/access-control).

```sql
-- user-scoped folder: avatars/<uid>/whatever.png
create policy "avatars_insert_own"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "avatars_select_own"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'avatars'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "avatars_delete_own"
  on storage.objects for delete to authenticated
  using ( bucket_id = 'avatars' and owner_id = (select auth.jwt()->>'sub') );
```

**The public-bucket bypass.** A bucket marked public serves every object over an unauthenticated CDN URL — RLS on `storage.objects` does not gate those reads. Symptom: "my policy is correct but anyone with the URL can fetch the file." Fix: make the bucket private and issue signed URLs (`createSignedUrl`) with a short TTL, or accept that public means public and never put anything user-specific in it. Note that the `service_role` key bypasses all of this; it must never ship in the Expo bundle.

## How to test a policy properly

Testing as the dashboard SQL editor user, or with the service role key, proves nothing — both bypass RLS. Impersonate.

```sql
-- in a transaction so nothing leaks into the session
begin;
  select set_config('role', 'authenticated', true);
  select set_config('request.jwt.claims',
    json_build_object('sub', '00000000-0000-0000-0000-000000000001',
                      'role','authenticated')::text, true);

  -- should return only that user's rows
  select count(*) from public.posts;

  -- negative test: must fail or affect 0 rows
  update public.posts set user_id = '00000000-0000-0000-0000-000000000002'
   where user_id = '00000000-0000-0000-0000-000000000001';
rollback;
```

Checklist for each table:

1. Positive read as owner returns the expected rows.
2. Read as a *different* authenticated user returns zero rows.
3. Read as `anon` returns zero rows (`select set_config('role','anon',true)`).
4. Insert with a forged `user_id` is rejected by `WITH CHECK`.
5. Update that reassigns ownership is rejected by `WITH CHECK`.
6. `explain (analyze, buffers)` of the owner read shows an Index Scan on the policy column, not a Seq Scan, and shows the auth function as an InitPlan evaluated once.

Keep these as SQL files under `supabase/tests/` and run them in CI with `supabase test db` (pgTAP) so a new policy cannot regress an old one.

---
name: clerk-auth
description: >
  Wire Clerk authentication end to end across Expo and Next.js, from a development instance to a
  working production one. Use for sign-in and sign-up flows, social and native OAuth, Sign in with
  Apple, passkeys, session tokens and claims, route and resource protection, organizations and roles,
  syncing Clerk users into your own Postgres, connecting Clerk to Supabase RLS, webhooks, and the
  production migration — DNS, own OAuth credentials, live keys, native app registration. Also use for
  "users get logged out on restart", "social login works in dev but not production", "auth.uid() is
  null in my policy", or account deletion requirements.
---

# Clerk, development through production

Auth is the part of an app that looks finished long before it is. A dev instance signs users in on the
first afternoon; the production instance does not exist until roughly a dozen separate things are
true, several of which fail silently. This skill exists mostly to make that list explicit.

**Verify package versions and API names against the live docs before writing code.** Clerk renamed its
packages and replaced several core components in Core 3, and stale recall here produces code that
looks right and does not build. `references/api.md` records the current shape as of August 2026.

## The shape of it

- `@clerk/expo` on native and `@clerk/nextjs` on web (the older `@clerk/clerk-expo` and
  `@clerk/clerk-react` names are deprecated).
- On Expo, **`publishableKey` must be passed explicitly** — environment variables are not inlined in
  RN production builds the way they are on web — and **`tokenCache` must be passed explicitly**, or
  tokens live in memory only and every cold start signs the user out. That single omission is the most
  common Clerk bug in Expo apps.
- On Next, the provider goes inside `<body>`, and the middleware matcher must include Clerk's own
  proxy routes or auth breaks in ways that do not look like a matcher problem.
- Gating reads the session claim (`auth()` on the server) rather than fetching the user. Fetching the
  full user object hits the Backend API; doing it in a layout that renders on every request is a
  latency bug you will find later and blame on the database.

## Authorization is server-side

Say this out loud in every design that involves auth: **hiding a screen is not authorization.**
expo-router's protected routes remove screens from the navigator; the JavaScript is still in the
bundle and the API is still on the internet. Every endpoint re-validates the session and re-checks
ownership. `postgres-data` makes the same argument from the database end, and both are required.

Session claims refresh on a cadence, so a role or entitlement change can be up to a minute stale. For
anything destructive or paid, re-check server-side against the source of truth rather than trusting
the token in hand.

Custom claims have a hard size ceiling — exceed it and the session cookie is silently not set, which
presents as total auth failure for exactly the users with the most organization memberships. Put IDs
in claims and fetch bodies from your database.

## Native sign-in

Prefer native Google and Apple sign-in over the browser-based flow. The web-view flow measurably loses
users — one reported figure is roughly 30% of Android attempts returning a dismissal — and it feels
like a redirect, which is precisely the moment an install is abandoned.

Two things that catch everyone: Android needs SHA fingerprints registered for **all three** signing
keys (local debug, EAS managed, and Google Play app signing), and native flows plus passkeys do not
work in Expo Go or on Android emulators, so they must be tested in a development build on a real
device.

**If you offer any third-party social login as the primary sign-up path, Apple requires an equivalent
that limits collection to name and email and offers a private relay address.** Sign in with Apple is
the cheap way to satisfy it. This is guideline 4.8 and it is a routine rejection. `store-submission`
has the exact conditions and the exemptions.

Account deletion is not optional either: if the app creates accounts, it must offer in-app deletion
that actually deletes, plus a public web deletion URL for Google Play. Build it while building auth —
it touches every table and is miserable to retrofit the week before submission.

## Connecting to the database

Two mechanisms, and the distinction matters:

**Read the claim at request time** for authorization. The user ID from the verified session is current
within the refresh window and costs nothing. This is what your foreign keys point at.

**Use webhooks only to mirror profile data** you need to query or join — email, display name, avatar.
Webhooks are retried, unordered and at-least-once, so: dedupe on the delivery ID, upsert rather than
insert, ignore events older than the row's stored timestamp, and exclude the webhook route from
auth middleware. Add a scheduled reconcile against the Backend API, because deliveries do fail and
drift is invisible until someone's name is wrong.

**Never make a webhook the authorization source.** If a webhook has not arrived yet, the user must
still be able to use the app.

### With Supabase

Clerk is registered as a **third-party auth provider** in Supabase; the client passes an `accessToken`
callback that returns the Clerk session token. The older JWT-template-plus-shared-secret approach was
deprecated in 2025 — if you find it in a tutorial, the tutorial is stale. In policies, the Clerk user
ID is the `sub` claim; organization context arrives as its own claims. `postgres-data` owns how to
write those policies without destroying query performance.

## The production checklist

This is the part that fails. Work through `references/production-checklist.md` in full; the headline
items:

1. **Live keys everywhere, then redeploy.** Next inlines public env vars at build time, so changing
   the key without rebuilding changes nothing.
2. **DNS records for the frontend API, the account portal and email**, then the certificate. Allow up
   to 48 hours.
3. **Replace Clerk's shared development OAuth credentials with your own Google, Apple and other
   provider apps.** This is the number one launch blocker. Development instances borrow Clerk-owned
   OAuth clients; production instances refuse them, and nothing warns you until the first real social
   sign-in fails in production.
4. **Register the native apps** — iOS bundle ID and team prefix, Android package and SHA-256 — and
   repoint associated domains at the production frontend API.
5. **New webhook endpoint and a new signing secret** (secrets are per-instance).
6. **Pin authorized parties** so tokens minted for your app are not accepted from elsewhere.

Then test the whole thing on a production build on a real device: fresh install, social sign-in, cold
restart still signed in, sign-out, delete account, sign up again with the same email.

## Cost

The free tier is generous on user count; what pushes a small app onto a paid plan is usually a
*feature* — multi-factor, removing Clerk branding, extra enterprise connections, satellite domains —
rather than volume. Check which one you actually triggered before upgrading. `cost-control` has the
comparison against the alternatives, and the honest answer that migrating auth later is expensive
enough that this is a decision to make once.

## Reference files

- `references/api.md` — current package names, provider setup, hooks, server helpers, what Core 3 renamed
- `references/production-checklist.md` — the full dev-to-production migration, in order
- `references/database-sync.md` — webhooks, idempotency, backfill, Supabase third-party auth, RLS claims
- `references/testing.md` — testing tokens, bot protection in E2E, seeding users

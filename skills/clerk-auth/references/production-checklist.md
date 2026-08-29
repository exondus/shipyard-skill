# Clerk Dev → Production Checklist

Verified August 2026. Versions, package names and dashboard flows change — check the live docs before relying on anything here. Canonical index: <https://clerk.com/docs/guides/development/deployment/production>

Clerk dev and production are **separate instances with separate keys, user tables, webhook secrets and OAuth credentials**. Nothing carries over automatically. Work this list in order.

## Shortcut: the `clerk deploy` CLI

Since June 2026, `clerk deploy` clones the dev instance to production and walks DNS + OAuth: it creates the production instance, prints the CNAME records (exportable as a zone file), detects enabled social connections and prompts for production credentials with JSON import for Google/Apple, then verifies DNS, SSL and email records and reports what is incomplete (<https://clerk.com/changelog/2026-06-10-clerk-deploy>). `--mode agent` emits read-only JSON status instead of prompting — use it in CI.

Run the CLI, then use the rest of this file to verify.

## 1. Keys

- [ ] Swap `pk_test_…` → `pk_live_…` and `sk_test_…` → `sk_live_…` in the hosting provider's env settings.
- [ ] **Rebuild and redeploy.** `NEXT_PUBLIC_*` is inlined at build time; changing the env var without a rebuild ships the old key. *Presents as: production site still talking to the dev instance — users "disappear", or the Clerk dev banner shows in prod.*
- [ ] Expo: set `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` to the live key and cut a **new EAS build**. OTA updates do not change compiled env values reliably.
- [ ] Confirm `CLERK_SECRET_KEY` is server-only and not in any `NEXT_PUBLIC_` var or client bundle.

## 2. DNS

Add from Clerk Dashboard → **Domains**. Record set, confirmed from Clerk's Domain-Connect template (<https://github.com/Domain-Connect/Templates/blob/master/clerk.com.app.json>) — `%mailtoken%` is instance-specific and shown in the dashboard:

| Host | Type | Points to | Purpose |
|---|---|---|---|
| `clerk` | CNAME | `frontend-api.clerk.services` | Frontend API |
| `accounts` | CNAME | `accounts.clerk.services` | Account Portal |
| `clkmail` | CNAME | `mail.%mailtoken%.clerk.services` | Transactional mail |
| `clk._domainkey` | CNAME | `dkim1.%mailtoken%.clerk.services` | DKIM 1 |
| `clk2._domainkey` | CNAME | `dkim2.%mailtoken%.clerk.services` | DKIM 2 |

A secondary mail group (`clkmail2`, `pdk1._domainkey.clkmail2`, `pdk2._domainkey.clkmail2`, `track.clkmail2`) also exists in the template; the dashboard says whether your instance needs it. [UNVERIFIED: which instances get the secondary set.]

- [ ] All records created, **proxying disabled** on Cloudflare (orange cloud off). *Presents as: certificate never provisions, or handshake errors.*
- [ ] Wait for propagation — **up to 48 hours**.
- [ ] Skipping the mail records presents as: **verification codes, magic links and password resets never arrive, or land in spam** — invisible in testing, where you reuse an existing session.

## 3. Certificates

- [ ] Once records validate, the **"Deploy certificates"** button appears in the Dashboard. Click it. This is a discrete manual step people forget after DNS goes green.

## 4. Replace Clerk's shared dev OAuth credentials — the #1 launch blocker

**Development instances use Clerk-owned, shared OAuth clients** so social login works with zero setup. **Production instances refuse them.** You must supply your own OAuth app per provider — no automatic migration, no warning until a real user signs in.

*Presents as: every social sign-in in production fails — provider error page, `invalid_client`, `redirect_uri_mismatch`, or a blank callback — while email/password still works. Usually found by the first customer, not by you, because your own session predates the cutover.*

Do this for **every** enabled social connection, before launch.

### Google

- [ ] Google Cloud Console → create or select a project.
- [ ] Configure the **OAuth consent screen**. External apps requesting beyond basic scopes need verification — **days to weeks**, so start early. Publish it out of "Testing" status, or only allowlisted accounts can sign in.
- [ ] Credentials → **Create OAuth client ID** → *Web application*.
- [ ] **Authorized redirect URI** must be your production Clerk Frontend API callback — the value Clerk shows on the connection's settings page, of the form `https://clerk.<yourdomain>.com/v1/oauth_callback`. Copy it verbatim from the dashboard rather than constructing it. *A trailing slash or the dev URL here presents as: `redirect_uri_mismatch`.*
- [ ] Paste Client ID + Client Secret into Clerk Dashboard → the Google connection → toggle **"Use custom credentials"**.
- [ ] Native Google on Expo additionally needs **separate iOS and Android OAuth client IDs** in the same Google project, plus SHA-1 fingerprints registered in Google Cloud Console for the debug keystore, the EAS managed keystore, **and the Google Play app signing key**.

### Apple

- [ ] Apple Developer → Certificates, Identifiers & Profiles.
- [ ] Create/confirm an **App ID** with *Sign in with Apple* enabled.
- [ ] Create a **Services ID** — this is the client ID for web/OAuth flows, distinct from the bundle ID.
- [ ] Configure the Services ID: add your domain and the **Return URL** = the Clerk production callback shown in the dashboard.
- [ ] Create a **Sign in with Apple private key (.p8)**, note the **Key ID** and your **Team ID**. Download the .p8 once — it cannot be re-downloaded.
- [ ] Enter Services ID, Team ID, Key ID and .p8 contents in Clerk.
- [ ] Apple's client secret is a JWT with a **maximum 6-month lifetime**. [UNVERIFIED: whether Clerk auto-rotates it for you — confirm in the dashboard.] *If not rotated, presents as: Apple sign-in dies abruptly ~6 months post-launch with no code change.*
- [ ] Verify the domain via Apple's domain-association file if prompted.

### Other providers

- [ ] Repeat for GitHub, Microsoft, Facebook, etc. Each needs its own app, production redirect URI, and custom credentials toggled on in Clerk.
- [ ] Audit the Dashboard's connections list; confirm **none** still uses Clerk's shared dev credentials.

## 5. Native app registration

- [ ] **iOS**: register under Clerk Dashboard → Native Applications with **App ID Prefix** and **Bundle ID**.
- [ ] Update **Associated Domains** in the app to point at the **production** Frontend API URL (`clerk.<yourdomain>.com`), not the dev `*.accounts.dev` host. *Presents as: passkeys and universal-link callbacks silently fail on the store build.*
- [ ] **Android**: register **Package Name** and **SHA-256** certificate fingerprint (all three keystores — see above).
- [ ] Allowlist production redirect URLs.

## 6. Webhooks

- [ ] Create the endpoint on the **production** instance pointing at the production URL.
- [ ] Copy the **new signing secret** — `CLERK_WEBHOOK_SIGNING_SECRET` is **per-instance**; the dev secret will not verify prod deliveries. *Presents as: every webhook 400s, user rows never appear in your database, and the app half-works because session auth is fine.*
- [ ] Confirm the webhook route is excluded from middleware protection.
- [ ] Subscribe to the same event list as dev.

## 7. Origins and domains

- [ ] Set **`authorizedParties`** on `clerkMiddleware()` / `authenticateRequest()` to your production origins. Omitting it leaves the door open to token replay from other origins.
- [ ] Configure the subdomain allowlist if you serve auth across subdomains.
- [ ] **Satellite domains** (`isSatellite`, `domain`, `signInUrl`, `allowedRedirectOrigins`) if you have more than one domain. **$10/mo each in production**, free in development. Core 3 sets `satelliteAutoSync: false` by default (<https://clerk.com/docs/guides/dashboard/dns-domains/satellite-domains>). Satellite domains need their own CNAME records.
- [ ] Update CSP headers per Clerk's CSP guide if you send them.

## 8. Plan gating

- [ ] MFA and removing Clerk branding require **Pro or above**; custom organization roles require the B2B add-on in production. *Presents as: a feature that worked in dev is missing in prod.* [UNVERIFIED: exact dev-instance plan-gating per feature.]

## Smoke test on a production build

Run these against the real production build, in a fresh incognito window or freshly installed app, with a brand-new account — not your existing session.

- [ ] Sign up with email → **verification email arrives** (check spam; confirm the From domain is yours).
- [ ] Password reset email arrives.
- [ ] Sign in with **each** social provider you enabled — web and native separately.
- [ ] Sign in with Apple on a real iOS device from TestFlight.
- [ ] Native Google sign-in from a **Play-signed** build (internal testing track), not just a local dev build.
- [ ] Passkey registration and login on a **physical** device.
- [ ] Cold-start the mobile app after force-quit → **still signed in** (proves `tokenCache`).
- [ ] Confirm a `user.created` webhook landed and the row exists in your database.
- [ ] Hit a protected API route unauthenticated → correct 401/redirect.
- [ ] Check an org-scoped page as a non-admin → correctly denied.
- [ ] Confirm no Clerk development banner and no `.accounts.dev` URL appears anywhere.
- [ ] Sign out → session actually cleared on both web and native.

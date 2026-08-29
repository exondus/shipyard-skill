# Clerk API and Package Reference

Verified August 2026. Versions, package names and dashboard flows change — check the live docs before relying on anything here. Canonical index: <https://clerk.com/docs>

## Packages: current vs. deprecated

Clerk Core 3 renamed packages. Training data and most tutorials still show the old names.

| Install this | Latest (2026-08-28) | Replaces | Peer requirements |
|---|---|---|---|
| `@clerk/expo` | 4.6.1 | `@clerk/clerk-expo` (2.20.0, **deprecated on npm**) | `expo >=54 <58`, `react-native >=0.75`, react 18/19 |
| `@clerk/nextjs` | 7.8.3 | — (v6 is Core 2) | `next ^15.2.8 … ^16.0.10 \|\| ^16.1.0-0` |
| `@clerk/react` | 6.14.8 | `@clerk/clerk-react` (**deprecated on npm**) | react 18/19 |
| `@clerk/backend` | 3.16.13 | — | — |
| `@clerk/expo-passkeys` | ≥1.1.0 for Expo SDK 55 | — | earlier versions cap at SDK 54 |
| `@clerk/testing` | see testing.md | — | — |

The npm deprecation string on `@clerk/clerk-expo` reads: *"Migrate to @clerk/expo by following the Core 3 upgrade guide."* Core 2 has LTS until **January 2027** (<https://clerk.com/docs/guides/development/upgrading/upgrade-guides/core-3>). Automate the rename with `npx @clerk/upgrade`.

Core 3 floors: Node ≥20.9.0 (up from 18), Next ≥15.2.3 (13/14 dropped), Expo SDK ≥53.

## Core 3 renames

**`<Show>` replaces `SignedIn`, `SignedOut` and `Protect`** — all three, one component:

```tsx
<Show when="signed-in">…</Show>
<Show when="signed-out">…</Show>
<Show when={{ role: 'org:admin' }}>…</Show>
```

*Presents as: `SignedIn is not exported from @clerk/nextjs`, or a silent render of nothing.*

**`createRouteMatcher()` is deprecated** and emits a runtime warning. Clerk's own guidance is now explicit: *"Middleware is not the best place to protect routes"* — protect as close to the resource as possible (<https://clerk.com/docs/reference/nextjs/clerk-middleware>). Keep `clerkMiddleware()` for context injection; do the authorization in the route handler, server component, or data layer.

**`appearance.layout` → `appearance.options`.** *Presents as: appearance props silently ignored, default Clerk styling in production.*

**`getToken()` throws `ClerkOfflineError`** when offline and now does proactive background refresh. *Presents as: unhandled promise rejection on flaky mobile networks.*

**Satellite apps no longer auto-sync on first visit** (`satelliteAutoSync` defaults `false`). *Presents as: users appear signed out on the satellite domain until they click sign-in.*

## Next.js: middleware file and matcher

Next 16 renamed the file. Use **`proxy.ts`** on Next 16+, **`middleware.ts`** on 15 and below, at project root or `src/`.

```ts
import { clerkMiddleware } from '@clerk/nextjs/server'
export default clerkMiddleware()
export const config = { matcher: [
  '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
  '/(api|trpc)(.*)',
  '/__clerk/(.*)',
]}
```

**`/__clerk/(.*)` is required** — these are Clerk's Frontend API proxy routes. *Presents as: handshake loops, `auth() was called but Clerk can't detect usage of clerkMiddleware()`, or sign-in that redirects forever* (<https://clerk.com/docs/reference/nextjs/errors/auth-was-called>).

`<ClerkProvider>` goes **inside `<body>`**, not wrapping `<html>` (<https://clerk.com/docs/nextjs/getting-started/quickstart>). Env: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`.

## `auth()` vs `currentUser()`

`auth()` is **async — always `await` it**. It reads the session JWT with no network call and returns `userId`, `orgId`, `sessionClaims`, `has()`, `protect()`, `redirectToSignIn()`, `isAuthenticated` (<https://clerk.com/docs/reference/nextjs/app-router/auth>).

```ts
const { isAuthenticated, userId, orgId, has, redirectToSignIn } = await auth()
if (!isAuthenticated) return redirectToSignIn()
```

`currentUser()` calls the Backend API and returns the full `User` object (email, name, avatar, metadata).

| Use | When |
|---|---|
| `auth()` | Gating, getting `userId`/`orgId` for a DB query, permission checks. Default choice. |
| `currentUser()` | You genuinely need profile fields you have not mirrored locally. |

*Calling `currentUser()` in a root layout presents as: every page render costs a Backend API round-trip, latency climbing under load, and eventual rate limiting.* Forgetting `await` on `auth()` presents as: `Cannot destructure property 'userId' of ... as it is undefined`.

## Expo provider setup

```bash
npx expo install @clerk/expo expo-secure-store expo-auth-session expo-crypto expo-web-browser expo-dev-client
```

```tsx
import { ClerkProvider } from '@clerk/expo'
import { tokenCache } from '@clerk/expo/token-cache'

<ClerkProvider
  publishableKey={process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY!}
  tokenCache={tokenCache}
>
```

Both props are load-bearing:

- **`publishableKey` is required in Core 3** because environment variables are not inlined into React Native production builds the way they are in web bundlers. *Presents as: works in Expo Go and dev, throws "Missing publishableKey" only in the TestFlight/Play build.*
- **`tokenCache` must be passed explicitly.** Without it, tokens are memory-only. *Presents as: users are signed out on every cold start — the single most common Expo Clerk bug.*

Add `"expo-secure-store"` and `"@clerk/expo"` to `app.json` → `plugins`.

Native components (SwiftUI / Jetpack Compose, beta) require `useAuth({ treatPendingAsSignedOut: false })`.

## Social sign-in on native

**`useOAuth()` is deprecated → `useSSO()`** (<https://clerk.com/docs/reference/expo/native-hooks/use-sso>).

```ts
const { startSSOFlow } = useSSO()
await startSSOFlow({ strategy: 'oauth_google', redirectUrl })
```

`strategy` is `'oauth_<provider>'` or `'enterprise_sso'` (SAML/OIDC/EASIE, needs `identifier`). `redirectUrl` defaults to the `sso-callback` path. Requires `WebBrowser.maybeCompleteAuthSession()` at module scope; `warmUpAsync`/`coolDownAsync` improve Android UX.

**Prefer native over the web view.** Browser OAuth is measurably unreliable — one Expo team reported *"roughly 30% of Android sign-in attempts returned a `DISMISS` result"* (<https://clerk.com/articles/native-vs-browser-oauth-in-expo-a-decision-guide-for-social-login>). Native Google comes from a subpath import:

```ts
import { useSignInWithGoogle } from '@clerk/expo/google'
const { startGoogleAuthenticationFlow } = useSignInWithGoogle()
const { createdSessionId, setActive } = await startGoogleAuthenticationFlow()
if (createdSessionId && setActive) await setActive({ session: createdSessionId })
```

Env: `EXPO_PUBLIC_CLERK_GOOGLE_IOS_CLIENT_ID`, `EXPO_PUBLIC_CLERK_GOOGLE_IOS_URL_SCHEME` (reversed client ID), `EXPO_PUBLIC_CLERK_GOOGLE_ANDROID_CLIENT_ID`.

**Three Android SHA fingerprints must all be registered** — debug keystore, EAS managed keystore, and Google Play app signing key. SHA-1 goes in Google Cloud Console; SHA-256 goes in Clerk Dashboard → Native Applications. *Presents as: Google sign-in works locally and in internal testing but fails with a bare `DEVELOPER_ERROR` / code 10 once shipped through Play — because the Play signing key fingerprint was never registered.*

**Apple Guideline 4.8:** offering any third-party social login obliges you to also offer Sign in with Apple. Use `expo-apple-authentication`. *Presents as: App Store rejection.*

**Expo Go and emulator limits.** `useSignInWithGoogle()` and `<AuthView />` do not work in Expo Go — the `NativeClerkGoogleSignIn` TurboModule is absent. Use a dev build. Expo Go also has no OAuth redirects and no custom URL schemes. **Passkeys need a physical device**; Android emulators do not support them.

## Organizations, roles, permissions

Default roles: `org:admin` (all system permissions), `org:member` (read members, read billing). Custom permission keys follow `org:<feature>:<permission>`, e.g. `org:invoices:create` (<https://clerk.com/docs/guides/organizations/roles-and-permissions>).

```ts
const { has } = await auth()
if (has({ role: 'org:admin' })) …
if (has({ permission: 'org:invoices:create' })) …
```

Limits: **max 10 custom roles per instance**, and custom roles require the B2B Authentication add-on in production. Creator and Default roles cannot be deleted. Roles must be added to a Role Set before assignment.

## Machine auth

`auth({ acceptsToken })` accepts `'session_token'` (default), `'oauth_token'`, `'m2m_token'`, `'api_key'`, an array, or `'any'` (<https://clerk.com/docs/guides/development/machine-auth/overview>). Three token types exist: OAuth access tokens (authorization-code flow), M2M tokens (service-to-service inside your infra), and API keys (your users delegate access to your API). OAuth **client-credentials flow is not supported yet**.

## Session token size ceiling

Custom claims cap at **~1.2KB**, because browsers cap cookies at 4KB total. Exceed it and *"the cookie [is] not set, which will break your app as Clerk depends on cookies"* (<https://clerk.com/docs/guides/sessions/customize-session-tokens>).

*Presents as: total auth failure — but only for the subset of users with many organization memberships or large metadata, so it passes every test and breaks for your biggest customer.* Put IDs in claims; fetch bodies from your database.

Claims refresh every **60 seconds**, so a role or permission change can be up to a minute stale. Re-check server-side before destructive actions. Type claims via a global `CustomJwtSessionClaims` interface in `types/globals.d.ts`.

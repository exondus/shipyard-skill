# Mobile Security Hardening

Time-sensitive: OWASP MASVS control names, Expo SecureStore APIs and platform ATS/cleartext defaults change. Verify against [mas.owasp.org/MASVS](https://mas.owasp.org/MASVS/) and current Expo docs before treating any control as satisfied.

Reference frame: **OWASP MASVS v2**, control groups **MASVS-STORAGE, -CRYPTO, -AUTH, -NETWORK, -PLATFORM, -CODE, -RESILIENCE, -PRIVACY**, with the MASTG providing the matching test cases. Cite the group when justifying a control — it turns "we should probably encrypt that" into a reviewable requirement.

## Checklist as verifiable checks

Each item is phrased so it can be *proven*, not asserted.

| # | Check | How to verify | MASVS |
|---|---|---|---|
| 1 | No secrets in the JS bundle | CI grep gate over `expo export` output (below) | CODE |
| 2 | Tokens in SecureStore, not AsyncStorage | grep for `AsyncStorage` writes of `token`/`session`/`key` | STORAGE |
| 3 | Every endpoint re-authorizes server-side | Call a peer's resource with your own token; expect 403 | AUTH |
| 4 | RLS enabled on every table | Query `pg_tables` for `rowsecurity = false` | AUTH |
| 5 | TLS only, no cleartext | `NSAllowsArbitraryLoads` absent; `usesCleartextTraffic` false | NETWORK |
| 6 | Deep links allow-listed | Fire a hostile URL via `xcrun simctl openurl` / `adb shell am start` | PLATFORM |
| 7 | WebView origin-restricted | Review every `WebView` for `originWhitelist` and `injectJavaScript` | PLATFORM |
| 8 | PII scrubbed before leaving device | Inspect a real Sentry event payload | PRIVACY |
| 9 | Dependencies free of known CVEs | `npm audit --production` in CI | CODE |
| 10 | Privacy manifest / Data Safety accurate | Compare declaration against actual SDK behaviour | PRIVACY |

## Nothing in the bundle is secret

Expo states it plainly: `EXPO_PUBLIC_` variables "will be visible in plain-text in your compiled application," and "when an end-user runs your app, they have access to all of the code and embedded environment variables in your app" ([docs](https://docs.expo.dev/guides/environment-variables/)).

This means **every** value the JS bundle can read is public: API keys, feature-flag payloads, pricing logic, admin route names. Extracting them requires unzipping an IPA/APK — a two-minute exercise, not an attack.

What may be in the bundle: publishable/anon keys designed for client use (Stripe publishable key, Supabase anon key *with RLS enforced*, PostHog project token, Sentry DSN). What may never: service-role keys, Stripe secret keys, webhook signing secrets, private keys, admin credentials, anything prefixed `sk_`.

### CI grep gate

```bash
#!/usr/bin/env bash
# scripts/check-bundle-secrets.sh — fail the build if a secret is embedded
set -euo pipefail

npx expo export --platform all --output-dir /tmp/bundle-audit >/dev/null

PATTERNS='sk_live_|sk_test_|rk_live_|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|service_role|SUPABASE_SERVICE|xox[baprs]-|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}'

if grep -rEoI "$PATTERNS" /tmp/bundle-audit | tee /tmp/bundle-secrets.txt | grep -q .; then
  echo "SECRET FOUND IN CLIENT BUNDLE — build blocked:"
  cat /tmp/bundle-secrets.txt
  exit 1
fi
echo "OK: no known secret patterns in bundle."
```

Run it on every PR. Add project-specific patterns (your vendor prefixes). Grep the *export output*, not the source tree — the point is catching values that reached the bundle through a config path nobody remembered.

**Symptom this catches: nothing, visibly.** Leaked keys produce no error; you find out via a bill or a breach. That is exactly why it must be automated.

If a secret did ship: rotate it first, then remove it. A released binary cannot be recalled — every install retains the old bundle.

## Storage: SecureStore vs AsyncStorage

**`expo-secure-store`** → iOS Keychain / Android Keystore. Use for: auth tokens, refresh tokens, biometric flags, anything whose disclosure harms the user.

**`AsyncStorage`** is **unencrypted plaintext** on disk. Use only for: UI preferences, cache, non-sensitive draft state, feature-flag snapshots.

```ts
import * as SecureStore from 'expo-secure-store';
await SecureStore.setItemAsync('refresh_token', token, {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
});
```

**Gotcha — symptom: writes silently fail or throw on large values.** SecureStore has a small practical per-value size limit (around 2KB). Storing a large JWT-plus-profile blob hits it. Store the token only; fetch the profile.

Also: nothing in either store survives a rooted device with a determined attacker. SecureStore raises cost substantially; it is not a vault.

## Authorization is server-enforced

Client-side role checks are **UI affordances, not security**. Hiding a button hides nothing — the endpoint is still callable with curl.

Requirements:
- Every endpoint independently validates the session **and** that this user owns/may access this resource. "The client wouldn't send that ID" is not a control.
- Supabase: RLS **on for every table**, with policies that reference `auth.uid()`. A table without RLS is world-readable via the anon key that ships in your bundle. This is the single most common serious flaw in Expo+Supabase apps.
- Never trust client-supplied `user_id`, `role`, `price`, `is_premium` or `quantity`. Derive them server-side from the session and your own database.
- Entitlement checks (is this user subscribed?) are server-side against RevenueCat/Stripe, not from a client boolean.

Test it: authenticate as user A, request user B's resource by ID, expect a 403. Do this for every resource type.

## Deep link validation

Deep links are attacker-controlled input arriving from any app or webpage.

- Allow-list routes and validate every parameter (type, range, ownership) before use.
- **Never navigate to or fetch a URL supplied in a link parameter** — that is an open redirect and, in a WebView, a phishing vector.
- **Never accept auth tokens or session material via deep link** unless it is a single-use, short-TTL, server-issued magic-link token bound to the request.
- Never let a link perform a destructive or state-changing action without an in-app confirmation. `myapp://delete-account` must land on a confirmation screen.
- Prefer **Universal Links / App Links** (domain-verified) over custom schemes, which any app may claim.

Verify by firing hostile URLs at a release build:
```bash
xcrun simctl openurl booted "myapp://profile?id=../../admin"
adb shell am start -a android.intent.action.VIEW -d "myapp://open?url=https://evil.example"
```

## WebView hardening

- Set `originWhitelist` to your own domains; default-open WebViews will follow any link.
- Disable JavaScript if the content doesn't need it (`javaScriptEnabled={false}`).
- Never `injectJavaScript` with interpolated remote or user data — that is XSS with native bridge access.
- Disable file access (`allowFileAccess={false}`, `allowUniversalAccessFromFileURLs={false}`).
- Never expose a bridge handler that executes arbitrary messages from page content; validate `onMessage` payloads against a fixed schema.
- Never render untrusted HTML in a WebView that shares cookies/session with your authenticated origin.

## Honest assessment: pinning, obfuscation, root detection

These are MASVS-RESILIENCE controls. Resilience protects against an attacker **who owns the device** — a different threat model from protecting users from third parties. Applying them by default costs reliability and buys little.

**Certificate pinning — usually not worth it for a pre-revenue consumer app.** It defends against a compromised CA or a user-installed proxy. Costs: the app hard-fails when a certificate rotates, and a mispinned release *bricks every installed client* until they update — a bug you cannot fix over the air. Adopt when: you handle financial, health or regulated data, or a compliance regime requires it. If you do, pin to the intermediate CA or use multiple backup pins, ship a remote kill-switch, and rehearse rotation.

**Obfuscation — a speed bump, not a control.** JS obfuscation raises the effort of reading your bundle from minutes to hours for a motivated attacker. It never converts a public value into a secret. Worth it only for genuine client-side IP (a proprietary algorithm that must run offline). It is **never** an acceptable substitute for moving a secret server-side, and it complicates crash symbolication.

**Root/jailbreak detection — defeatable by design.** Anything the app can check, a rooted device can lie about; bypass tooling is commodity. Warranted for anti-cheat, DRM, banking and regulated finance, where the goal is raising bulk-abuse cost. Never make it load-bearing, and never hard-block on it in a consumer app — you will lock out legitimate power users and custom-ROM owners while stopping no one determined.

Rule: **if removing the control would expose a secret or bypass authorization, the design is wrong.** Fix the design; don't add resilience theatre.

## PII scrubbing and privacy

- Sentry: `sendDefaultPii: false` plus a `beforeSend` that strips user email/IP, `Authorization` and `Cookie` headers, query strings and HTTP breadcrumb bodies.
- Session replay: keep masking defaults on in **both** Sentry and PostHog. Never globally disable `maskAllText`/`maskAllImages`/`maskAllVectors`.
- Analytics: no PII in event properties — no emails, names, free text or message bodies.
- Ship an accurate **iOS Privacy Manifest** and **Play Data Safety** declaration reflecting what your SDKs actually collect, including analytics and crash reporting. Inaccurate declarations are a review rejection and a regulatory problem.
- Log hygiene: no tokens or PII in `console.log`. Release builds should strip logging entirely.
- Have a deletion path: account deletion must actually delete, including from analytics and crash-reporting vendors.

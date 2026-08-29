# Testing Clerk in CI

Verified August 2026. Versions, package names and dashboard flows change — check the live docs before relying on anything here. Canonical index: <https://clerk.com/docs/guides/development/testing/overview>

## The problem

Clerk runs bot detection on sign-in. Headless browsers trip it. *Presents as: E2E tests that pass locally and fail in CI at the sign-in step — a CAPTCHA widget, a stuck spinner, or "we couldn't verify you're human" — with no code change between runs.*

The fix is a **Testing Token**, which bypasses bot detection for the request.

## Setup

```bash
npm i -D @clerk/testing
```

Env vars in the test environment: `CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` (<https://clerk.com/docs/guides/development/testing/playwright/overview>).

**`clerkSetup()`** — call once in global setup; it fetches a Testing Token so individual tests do not have to.

```ts
// global.setup.ts
import { clerkSetup } from '@clerk/testing/playwright'
export default async function () { await clerkSetup() }
```

**`setupClerkTestingToken({ page })`** — call inside a test to inject the token into that page's requests.

```ts
import { setupClerkTestingToken } from '@clerk/testing/playwright'

test('signs in', async ({ page }) => {
  await setupClerkTestingToken({ page })
  await page.goto('/sign-in')
  // …
})
```

Cypress has an equivalent (<https://clerk.com/docs/guides/development/testing/cypress/overview>).

## The project-based setup file requirement

`clerkSetup()` must run in a **project-based setup file** wired through `playwright.config.ts` `projects` with a `setup` dependency — **not** a function-based `globalSetup`. Environment variables set in a function-based global setup do not propagate to test workers.

*Presents as: `clerkSetup()` appears to run fine, but tests still hit bot protection, because workers never saw `CLERK_TESTING_TOKEN`.*

```ts
projects: [
  { name: 'setup', testMatch: /global\.setup\.ts/ },
  { name: 'chromium', dependencies: ['setup'], use: { ...devices['Desktop Chrome'] } },
]
```

Alternative: obtain a token via the Backend API and set `CLERK_TESTING_TOKEN` yourself, skipping `clerkSetup()`.

## Production testing tokens

Testing Tokens work against production instances as of August 2025 (<https://clerk.com/changelog/2025-08-19-production-testing-tokens>), so you can smoke-test the real production build rather than only a dev instance. Guard the secret key accordingly and prefer a dedicated test tenant.

## Seeding test users

- Create users via the Backend API `clerkClient.users.createUser()` in setup; delete in teardown. Deterministic and parallel-safe when each worker gets a unique email.
- Use `+tag` email addressing (`qa+${workerIndex}@example.com`) to keep workers isolated.
- Clerk supports reserved test email/phone patterns that skip real delivery and accept a fixed verification code, which avoids inbox polling for OTP flows. [UNVERIFIED: the exact reserved address format and code — check the testing docs before relying on it.]
- Prefer seeding by API over driving the sign-up UI: sign-up flows are the slowest and flakiest path, and you usually want to test *your* app, not Clerk's forms.
- Sign in once, persist `storageState`, and reuse it across tests to avoid repeating auth.

*Reusing one shared test user across parallel workers presents as: random failures from session/state collisions that disappear when you rerun with `--workers=1`.*

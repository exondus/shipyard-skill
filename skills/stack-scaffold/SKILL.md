---
name: stack-scaffold
description: >
  Scaffold and configure an Expo + Next.js monorepo, and keep its build machinery working — workspace
  layout, Metro and Next config, expo-router, EAS build/update/submit profiles, environment variables,
  app variants, CI and quality gates. Use when starting a new app repo, adding a web or mobile app to
  an existing one, wiring a shared package, setting up EAS or CI, or debugging "unable to resolve
  module", duplicate React errors, "no compatible update found", Expo Go versus development build
  confusion, pod install failures, or SDK upgrade breakage. Read docs/app/stack.md first.
---

# Scaffold and build machinery

The scaffold is not interesting work and it is where a week disappears. Everything here exists to make
the boring part deterministic so the interesting parts get the time.

**Check every version against the live registry before installing.** `references/versions.md` records
what was current in August 2026 and is the single fastest-ageing file in this plugin. Use
`npx expo install` (which resolves to the SDK-sanctioned range) rather than `npm install` for anything
Expo-adjacent, and never install `react-native@latest` — it runs ahead of the SDK.

## Non-negotiables

Four rules that prevent most of the pain:

1. **Development builds, never Expo Go, as the acceptance environment.** Expo Go ships a fixed native
   binary: config plugins, custom native modules and half the libraries you will use simply are not in
   it. Code that works there and fails in a build is the single most common "mystery" in Expo projects.
   Scaffold straight to `expo-dev-client` with a `development` profile.
2. **One copy of `react`, one of `react-native`, one of each Expo module.** Duplicates present as
   "Invalid hook call" or native link errors and cost hours. Diagnose with
   `pnpm why --depth=10 react-native`; fix with root `resolutions`/`overrides`.
3. **Shared packages are source-only TypeScript.** `"main": "./src/index.ts"`, no build step. Metro and
   Next both transpile them. This removes the entire stale-`dist` class of bug.
4. **Do not hand-write Metro monorepo config.** `expo/metro-config` has detected workspaces since SDK
   52. Inherited `watchFolders`, `nodeModulesPaths`, `extraNodeModules` or `disableHierarchicalLookup`
   now actively fight it — delete them and run `npx expo start --clear`.

## The tree

```
repo/
  pnpm-workspace.yaml        # apps/*, packages/*
  turbo.json                 # dev (persistent, uncached), build, lint, typecheck, test
  tsconfig.base.json         # strict + path aliases; no project references
  apps/
    mobile/                  # Expo, expo-router, app.config.ts, eas.json, .maestro/
    web/                     # Next.js App Router
  packages/
    tokens/                  # design tokens — one source for both platforms
    ui/                      # cross-platform components (.tsx + .web.tsx)
    api/                     # Hono + tRPC router; the typed client type
    db/                      # Drizzle schema + migrations — SERVER ONLY
    i18n/                    # message catalogues
    config/                  # tsconfig/eslint/tailwind presets, zod env schema
  .eas/workflows/            # EAS Workflows YAML
  .github/workflows/         # lint, typecheck, test
```

`packages/db` must never be importable from the Expo bundle. Enforce it with an ESLint
`no-restricted-imports` rule, not a convention — an ORM in the mobile bundle is both a size disaster
and a credential leak waiting to happen.

Set up `packages/tokens` in the same commit as the scaffold even before there is any UI. `premium-ui`
depends on it existing, and retrofitting a token layer over hardcoded values is a whole-app sweep.

## Environment variables

The one rule that matters: **`EXPO_PUBLIC_*` is a compile-time text substitution, not a secret.** Its
value is inlined into the JS bundle, and anyone can unzip an IPA or APK and read it. API keys, database
URLs and service credentials are read only in server code. Add a CI grep over the exported bundle for
`sk_`, `secret`, `AKIA` and `-----BEGIN` so this is enforced rather than remembered.

Use EAS environment variables (three environments — `development`, `preview`, `production`; three
visibilities — plain, sensitive, secret) bound to build profiles, not a `.env` in the repo. Commit
`.env.example` only. Validate at boot with a zod schema in `packages/config` so a missing variable
fails the build rather than the app.

App variants come from `APP_VARIANT` in `app.config.ts`, varying `name`, `ios.bundleIdentifier`,
`android.package`, `icon` and `scheme` so dev, preview and production installs coexist on one device.

## EAS

`references/eas.md` has the annotated `eas.json`, the workflow YAML and the submission wiring. The
parts that cause the most confusion:

- **`appVersionSource: "remote"` with `autoIncrement`.** EAS owns build numbers; you own the
  user-facing `version`. Hand-editing both is how duplicate-build-number upload failures happen.
- **`runtimeVersion` policy `fingerprint`.** It hashes everything that affects the native runtime, so
  an OTA update can never be delivered to a build that lacks its native code. The `appVersion` policy
  is the classic footgun: bump `version` for a JS-only release and every existing install reports "no
  compatible update found".
- **Channel → branch.** An update reaches a device only when platform, channel-to-branch link and
  `runtimeVersion` all match. When an update does not arrive, check those three in that order.
- **EAS Workflows over hand-rolled Actions for anything touching builds**, because it fingerprints the
  project and does a native build only when native inputs changed, publishing an OTA update otherwise.
  Keep lint/typecheck/unit tests on GitHub Actions where they are free and fast.

## Quality gates

TypeScript `strict` plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
`noImplicitOverride`, `verbatimModuleSyntax`. ESLint flat config via `npx expo lint`, with Prettier as
a lint error so formatting is never a review topic. `jest-expo` + React Native Testing Library for
hooks, reducers and API procedures — not for pixel output. Maestro for end-to-end, run as a first-class
job on EAS Workflows; it remains the pragmatic choice for a small team, and Detox only earns its
configuration cost when Maestro flake becomes the actual bottleneck.

Per PR: `turbo typecheck lint test`. Nightly or pre-release: a build on the e2e profile, Maestro on
both platforms, `npx expo-doctor`, and `npx expo install --check`.

## The API layer

React Native cannot use React Server Components, so native must talk to a plain HTTP/JSON boundary.
That single fact settles the architecture: put the server logic in `packages/api` behind Hono + tRPC,
mount it from the Next app for convenience, and keep it deployable standalone so the mobile release
cadence is never coupled to a web deploy. Use expo-router `+api.ts` routes for BFF glue — an OAuth code
exchange, a signed URL — not as the whole backend.

## When something breaks

`references/failure-modes.md` is the triage list. Read it before debugging by intuition; nearly every
Expo monorepo failure is one of about a dozen known shapes, and the symptom rarely names the cause.

The three that account for most of it: duplicate `react-native` in the tree; leftover manual Metro
monorepo config; and an SDK upgrade where a library imports internals that moved. Run
`npx expo install --check` and `npx expo-doctor@latest` before blaming your own code.

## Upgrading an SDK

Never as part of a feature. Its own branch, its own review. Read the changelog for every skipped
version, run the codemods it ships, `npx expo install --fix`, build on both platforms, then run the
Maestro suite. The New Architecture has been mandatory since SDK 55 — a library that has not adopted it
is not a dependency, it is a fork you have not written yet.

## Reference files

- `references/versions.md` — versions and toolchain minimums as of Aug 2026, with what changed per SDK
- `references/monorepo.md` — workspace, Metro, Next interop, TypeScript, Turborepo config
- `references/eas.md` — eas.json, workflows, updates, submit, versioning
- `references/failure-modes.md` — symptom-to-cause triage

# EAS: Build, Update, Submit, Workflows

Verified 29 August 2026. This is the fastest-ageing file in the plugin — check every version against the live registry with `npx expo install --check` and the SDK changelog before installing: https://expo.dev/changelog

`eas-cli` current: **23.0.0**.

## Annotated `eas.json`

```jsonc
{
  "cli": {
    "version": ">=23.0.0",
    "appVersionSource": "remote",   // EAS owns buildNumber/versionCode
    "requireCommit": true           // no builds from a dirty tree
  },

  "build": {
    // Shared base — every profile extends this.
    "base": {
      "node": "22.13.0",            // must match .nvmrc and CI
      "env": {}
    },

    // Dev client: install alongside prod app, points at a local dev server.
    "development": {
      "extends": "base",
      "developmentClient": true,
      "distribution": "internal",
      "environment": "development", // binds EAS env vars
      "channel": "development",
      "env": { "APP_VARIANT": "development" },
      "ios": { "simulator": true },
      "android": { "buildType": "apk" }
    },

    // Preview: real release build, internal distribution, staging backend.
    "preview": {
      "extends": "base",
      "developmentClient": false,
      "distribution": "internal",
      "environment": "preview",
      "channel": "preview",
      "env": { "APP_VARIANT": "preview" },
      "android": { "buildType": "apk" }
    },

    // Production: store distribution, auto build-number bump.
    "production": {
      "extends": "base",
      "distribution": "store",
      "environment": "production",
      "channel": "production",
      "autoIncrement": true,
      "ios": { "provisioning": "universal" },
      "android": { "buildType": "app-bundle" }
    },

    // E2E: unsigned simulator/emulator artifacts for Maestro.
    "e2e-test": {
      "extends": "base",
      "withoutCredentials": true,
      "environment": "preview",
      "ios": { "simulator": true },
      "android": { "buildType": "apk" }
    }
  },

  "submit": {
    "production": {
      "ios": {
        "appleId": "you@example.com",
        "ascAppId": "1234567890",
        "appleTeamId": "ABCDE12345"
      },
      "android": {
        "serviceAccountKeyPath": "../../secrets/play-service-account.json",
        "track": "internal",
        "releaseStatus": "draft"
      }
    }
  }
}
```

Other keys: `resourceClass` (`default`/`medium`/`large`), `image`, `prebuildCommand`, `cache`, `artifactPath`, `ios.scheme`, `ios.buildConfiguration`, `ios.cocoapods`, `ios.fastlane`, `android.gradleCommand`, `android.ndk`, `android.withoutCredentials` ([build-reference/eas-json](https://docs.expo.dev/build-reference/eas-json/)). `releaseChannel` is legacy Classic Updates — never use it; use `channel`.

## `appVersionSource` and `autoIncrement`

`"appVersionSource": "remote"` (recommended since EAS CLI 12) makes EAS servers the source of truth for the **developer-facing** build version: `ios.buildNumber` and `android.versionCode`. With `"autoIncrement": true` on a profile, EAS bumps it every build, so you can never submit a duplicate. It does **not** touch the user-facing `version` (`1.4.0`) — you bump that by hand at release time.

Source: [build-reference/app-versions](https://docs.expo.dev/build-reference/app-versions/)

**What hand-editing breaks.** Under `remote`, editing `ios.buildNumber` / `android.versionCode` in app config does nothing — EAS ignores local values and you debug a number that was never read ("I set versionCode to 42 and the build came out 17").

- Migrating from `local` to `remote`: `eas build:version:set` seeds the remote counter from your current local values. Do this once, then stop touching the local fields.
- Building locally in Xcode / Android Studio: `eas build:version:sync` pulls the remote values down into the project first.
- Prefer not to store `buildNumber`/`versionCode` in the config at all under `remote`, so nobody is tempted.

## Development builds, not Expo Go — hard rule

Scaffold straight to a development build. `expo-dev-client@57.0.16`, profile `development` with `"developmentClient": true` and `"distribution": "internal"`.

Expo Go ships a **fixed** native binary, so anything changing native code does not exist inside it: config plugins, custom native modules, any library outside its bundled set. Code working in Expo Go can fail in a build and vice versa. Availability has made this worse, not theoretical:

- **SDK 55**: App Store / Play Store Expo Go stayed on **SDK 54**. SDK 55 Expo Go was CLI, TestFlight beta, or `eas go` only.
- **SDK 56**: Expo Go was **never published** to the App Store or Play Store at all.
- Expo Go supports only the New Architecture.

So on a current SDK, the store version of Expo Go is not even running your SDK. Do not let Expo Go be anyone's acceptance environment.

```sh
eas build --profile development --platform ios
eas build --profile development --platform android
npx expo start --dev-client
```

## EAS environment variables

Replaces the old `eas secret`. Source: [eas/environment-variables](https://docs.expo.dev/eas/environment-variables/)

**Three environments**: `development`, `preview`, `production`. (Custom names on Enterprise/Production plans.) A build profile opts in with `"environment": "<name>"`.

**Three visibilities**:

| Visibility | Readable on the website | Readable via EAS CLI | Shown in build logs |
|---|---|---|---|
| Plain text | yes | yes | yes |
| Sensitive | behind a toggle | yes | obfuscated |
| Secret | **no** | **no** | **no** |

Secrets exist to control **job execution** (npm tokens, service-account JSON, signing material). They do **not** protect a value that gets compiled into client code — see `EXPO_PUBLIC_` below.

Variables can be scoped project-wide or account-wide.

```sh
eas env:create --environment production --name DATABASE_URL --value "..." --visibility secret
eas env:list --environment production
eas env:pull --environment development     # writes .env.local for local dev
eas env:update --environment preview --name API_URL
eas env:delete --environment preview --name API_URL
```

`eas env:pull` is the replacement for hand-managed `.env` files and `NODE_ENV` juggling. Commit `.env.example` only; gitignore `.env`, `.env.*.local`.

### `EXPO_PUBLIC_` is not a secret

`process.env.EXPO_PUBLIC_FOO` is **statically substituted into the JS bundle at build time**. It is plain text inside the IPA/APK and anyone can extract it. Expo's docs say it outright: do not store private keys in `EXPO_PUBLIC_` variables.

Anything not public must be read only in server code — `+api.ts` route handlers and `packages/api` see **all** env vars, not just prefixed ones. Validate everything at boot with a zod schema in `packages/config` so a missing var fails the build rather than the app.

## App variants via `APP_VARIANT`

`app.config.ts` over `app.json` — you need dynamic config for variants. Keep static defaults in `app.json`, override dynamically:

```ts
// apps/mobile/app.config.ts
import type { ExpoConfig, ConfigContext } from 'expo/config';

const VARIANT = process.env.APP_VARIANT ?? 'production';
const IS_DEV = VARIANT === 'development';
const IS_PREVIEW = VARIANT === 'preview';

const id = IS_DEV
  ? 'com.acme.app.dev'
  : IS_PREVIEW
    ? 'com.acme.app.preview'
    : 'com.acme.app';

const name = IS_DEV ? 'Acme (Dev)' : IS_PREVIEW ? 'Acme (Preview)' : 'Acme';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name,
  slug: 'acme',
  scheme: IS_DEV ? 'acme-dev' : IS_PREVIEW ? 'acme-preview' : 'acme',
  icon: `./assets/icon${IS_DEV ? '-dev' : IS_PREVIEW ? '-preview' : ''}.png`,
  ios: { ...config.ios, bundleIdentifier: id },
  android: { ...config.android, package: id },
  runtimeVersion: { policy: 'fingerprint' },
  updates: { url: 'https://u.expo.dev/<project-id>' },
  experiments: { typedRoutes: true, autolinkingModuleResolution: true },
});
```

Vary at minimum: `name`, `ios.bundleIdentifier`, `android.package`, `icon`, `scheme`. Distinct bundle IDs are what let all three variants sit on one device at once.

Set `APP_VARIANT` per profile in `eas.json` (`env`) and in local scripts:

```json
{ "scripts": { "dev": "APP_VARIANT=development expo start --dev-client" } }
```

Source: [tutorial/eas/multiple-app-variants](https://docs.expo.dev/tutorial/eas/multiple-app-variants/)

Caveat: the experimental `EXPO_UNSTABLE_DEPLOY_SERVER=1` auto-deploy for expo-router servers **does not support `app.config.js` / `app.config.ts`**. If you need app variants, deploy the server manually and set the expo-router plugin `origin` yourself.

## EAS Update

Source: [eas-update/how-it-works](https://docs.expo.dev/eas-update/how-it-works/)

- A **branch** is server-side storage holding an ordered list of updates; the most recent is active.
- A **channel** is baked into the build (`"channel": "production"` in the profile).
- Channels map to same-named branches by default. Remap with `eas channel:edit production --branch version-2.0`.

**Three conditions, all required, for a build to receive an update:**

1. Platform matches exactly (iOS vs Android).
2. The build's channel is linked to a branch containing the update.
3. `runtimeVersion` of the build and the update **match exactly**.

### `runtimeVersion` policies

Set at `expo.runtimeVersion`, or per-platform at `expo.ios.runtimeVersion` / `expo.android.runtimeVersion`. Either a literal string or `{ "policy": "..." }`.

| Policy | Behaviour |
|---|---|
| `fingerprint` | **Recommended.** Hashes everything affecting the native runtime; changes automatically when native inputs change. |
| `appVersion` | Runtime version tracks the user-facing `version`. **Named footgun.** |
| `nativeVersion` | Tracks `version` + build number. Every build gets a new runtime — OTA becomes near-useless. |
| `sdkVersion` | Tracks the Expo SDK version. Too coarse: misses your own native changes. |
| literal string | Full manual control, full manual discipline. |

```json
{ "expo": { "runtimeVersion": { "policy": "fingerprint" } } }
```

**Why `appVersion` is the footgun.** Bump `version` from `1.4.0` to `1.4.1` to ship a JS-only fix, publish the update, and every installed build (runtime `1.4.0`) reports **"no compatible update found"** — the update targets a runtime that no shipped binary has. It also fails the other way: a native change without a version bump serves JS to a binary that lacks the native code, producing a crash instead of a clean rejection. `fingerprint` makes both impossible.

```sh
eas update --branch production --environment production --message "fix: checkout crash"
eas channel:list
eas branch:list
eas update:list --branch production
```

Since **SDK 55, `eas update` requires `--environment`.** Any script or CI job omitting it fails.

## EAS Workflows

YAML in `.eas/workflows/*.yml`. Scaffold with `eas workflow:create --template <name>`; run with `eas workflow:run <file>`. Triggers: GitHub `push` / `pull_request` (repo must be linked), plus App Store Connect state events (e.g. `ready_for_review`). Job `type`s include `build`, `submit`, `update`, `maestro`, `slack`, and custom functions. `needs:` orders the DAG; interpolate with `${{ needs.X.outputs.build_id }}` and `${{ env.VAR }}`.

Source: [eas/workflows/get-started](https://docs.expo.dev/eas/workflows/get-started/), [syntax](https://docs.expo.dev/eas/workflows/syntax), [e2e example](https://docs.expo.dev/eas/workflows/examples/e2e-tests/)

Why Workflows over hand-rolled Actions: it **fingerprints the project and builds natively only when native inputs changed, otherwise publishes an OTA**. Reimplementing that in Actions means reimplementing fingerprinting.

```yaml
# .eas/workflows/deploy.yml
name: deploy
on:
  push:
    branches: ['main']

jobs:
  fingerprint:
    type: fingerprint

  build_ios:
    needs: [fingerprint]
    type: build
    params:
      platform: ios
      profile: production
      fingerprint_hash_source: { type: job, id: fingerprint }

  build_android:
    needs: [fingerprint]
    type: build
    params:
      platform: android
      profile: production
      fingerprint_hash_source: { type: job, id: fingerprint }

  publish_update:
    needs: [fingerprint]
    type: update
    params:
      branch: production
      environment: production

  submit_ios:
    needs: [build_ios]
    type: submit
    params:
      build_id: ${{ needs.build_ios.outputs.build_id }}
      profile: production
```

The `fingerprint` job emits a hash EAS compares against the last build; when it is unchanged the build jobs are skipped and only `publish_update` runs. [UNVERIFIED: exact `fingerprint_hash_source` parameter spelling — validate with `eas workflow:validate .eas/workflows/deploy.yml` before committing.]

E2E, from the official example:

```yaml
# .eas/workflows/e2e-test-android.yml
name: e2e-test-android
on:
  pull_request:
    branches: ['*']
jobs:
  build_android_for_e2e:
    type: build
    params: { platform: android, profile: e2e-test }
  maestro_test:
    needs: [build_android_for_e2e]
    type: maestro
    params:
      build_id: ${{ needs.build_android_for_e2e.outputs.build_id }}
      flow_path: ['.maestro/home.yml', '.maestro/checkout.yml']
```

### What stays on GitHub Actions

Split by cost. EAS minutes are expensive; Actions minutes are not.

| GitHub Actions (every PR, ~2 min) | EAS Workflows |
|---|---|
| `turbo lint typecheck test` | `type: build` (any native build) |
| `npx expo-doctor@latest` | `type: maestro` (E2E on real artifacts) |
| `npx expo install --check` | `type: update` (OTA publishing) |
| Web build / Vercel preview | `type: submit` (store submission) |
| Dependency audit, changeset checks | Fingerprint-conditional release pipeline |

## EAS Submit

```sh
eas submit --platform ios --profile production --latest
eas submit --platform android --profile production --latest
```

iOS needs `appleId`, `ascAppId` (App Store Connect app ID), `appleTeamId`. Prefer an App Store Connect API key over an Apple ID password — store it as an EAS **secret**, not a repo file.

Android needs a Google Play service-account JSON. `serviceAccountKeyPath` points at a gitignored local file for manual submits; in CI, put the JSON in an EAS secret file variable and let EAS mount it. `track` is one of `internal`, `alpha`, `beta`, `production`; `releaseStatus` `draft` on the first submission of a new app (Play requires the first release to be promoted by hand).

`"promptToConfigurePushNotifications": false` under `cli` stops the interactive prompt from hanging non-interactive CI.

# Expo SDK Versions and Upgrade Planning

Verified 29 August 2026. This is the fastest-ageing file in the plugin — check every version against the live registry with `npx expo install --check` and the SDK changelog before installing: https://expo.dev/changelog

## Version table (SDK 57, current)

| Package | Pinned version | Source |
|---|---|---|
| `expo` | `57.0.18` (dist-tag `latest`) | npm registry |
| `expo-router` | `57.0.17` — version-locked to the SDK since SDK 55 | npm registry |
| `expo-updates` | `57.0.19` | npm registry |
| `expo-dev-client` | `57.0.16` | npm registry |
| `@expo/metro-config` | `57.0.12` | npm registry |
| `@expo/cli` | `57.0.20` | npm registry |
| `jest-expo` | `57.0.5` | npm registry |
| `eslint-config-expo` | `57.0.2` | npm registry |
| `eas-cli` | `23.0.0` | npm registry |
| `expo-doctor` | `1.20.4` | npm registry |
| `react-native` | **`0.86`** (patch `0.86.3`) | [versions/latest](https://docs.expo.dev/versions/latest/) |
| `react` / `react-dom` | **`19.2.3`** | same |
| `react-native-web` | **`0.21.0`** (npm latest `0.21.2`) | same |

Supporting libs currently sanctioned by SDK 57: `react-native-reanimated@4.5`, `react-native-worklets@0.10`, `react-native-gesture-handler@2.32` ([changelog/sdk-57](https://expo.dev/changelog/sdk-57)).

Adjacent (not Expo-versioned): `next@16.3.3`, `turbo@2.10.12`, `pnpm@11.24.0`, `bun@1.4.0`, `nx@23.1.2`, `eslint@10.9.1`, `prettier@3.9.6`, `typescript@7.0.2` (see caveat below).

### Rule: never install `react-native@latest`

`react-native` npm `latest` is **`0.87.1`** as of today — one minor ahead of what SDK 57 supports. RN ships ~6 releases/year; Expo targets exactly one RN version per SDK. Installing `latest` produces a tree Expo's autolinking, prebuild templates, and `expo-modules-core` were never built against.

Always install via the Expo resolver, never npm directly:

```sh
npx expo install react-native            # resolves to the SDK-correct version
npx expo install --check                 # report drifted packages
npx expo install --fix                   # rewrite package.json to SDK ranges
```

The same rule applies to `react`, `react-dom`, `react-native-web`, `react-native-reanimated`, `react-native-screens`, `react-native-safe-area-context`, and every `expo-*` package.

### TypeScript caveat

npm `latest` for `typescript` is `7.0.2` (the native/Go compiler). SDK 56 shipped on TS `6.0.3`. Pin TS 6.x per workspace until `typescript-eslint` and `eslint-config-expo` confirm TS 7 support. [UNVERIFIED: current `typescript-eslint` TS 7 compatibility status]

## Toolchain and platform minimums

| SDK | RN | React | RNW | Node min | iOS min | Xcode min | Android | compileSdk / targetSdk |
|---|---|---|---|---|---|---|---|---|
| 57 | 0.86 | 19.2.3 | 0.21.0 | **22.13.x** | 16.4+ | **26.4+** | 7+ | 36 / 36 |
| 56 | 0.85 | 19.2.3 | 0.21.0 | 20.19.x | 16.4+ | 26.4+ | 7+ | 36 / 36 |
| 55 | 0.83 | 19.2.0 | 0.21.0 | 20.19.x | 15.1+ | 26.2+ | 7+ | 36 / 36 |
| 54 | 0.81 | 19.1.0 | 0.21.0 | 20.19.x | 15.1+ | 16.1+ | 7+ | 36 / 36 |

Source: [docs.expo.dev/versions/latest](https://docs.expo.dev/versions/latest/)

The Node bump to 22.13.x in SDK 57 and the Xcode bump to 26.x in SDK 55 are the two most common cause of "worked yesterday, broken after upgrade" on developer machines and self-hosted CI. Pin Node in `.nvmrc`, in `eas.json` (`"node": "22.13.0"` per profile), and in the GitHub Actions `setup-node` step so all three agree.

## New Architecture mandate

**From SDK 55, the New Architecture is always on and cannot be disabled.** `newArchEnabled: false` in app config is silently ignored — remove it to avoid confusion. RN 0.82 was the first release to remove the opt-out; SDK 55 (RN 0.83) inherits it. SDK 54 is the **last** SDK where the legacy architecture is available. The legacy architecture was frozen in June 2025 — no new features, no bugfixes. Expo Go has only ever supported New Arch.

Source: [guides/new-architecture](https://docs.expo.dev/guides/new-architecture/)

Practical consequence for scaffolding: there is no legacy-arch escape hatch. If a dependency is New-Arch-incompatible, the options are (a) upgrade it, (b) replace it, (c) stay on SDK 54 — which is now a dead end. Check compatibility before committing to a library:

```sh
npx expo-doctor@latest     # cross-checks deps against React Native Directory
```

Exclude known-fine packages from the Directory check in `package.json`:

```json
{ "expo": { "doctor": { "reactNativeDirectoryCheck": { "exclude": ["react-redux", "/^@myorg\\/.*/"] } } } }
```

Known replacements for New-Arch-incompatible libraries: `react-native-fs` → `expo-file-system`; `rn-fetch-blob` → `react-native-blob-util`; `react-native-geolocation-service` → `expo-location`; `@react-native-community/masked-view` → `@react-native-masked-view/masked-view`; `@react-native-community/clipboard` → `@react-native-clipboard/clipboard`; `react-native-datepicker` → `@react-native-community/datetimepicker`. `react-native-maps` works via the interop layer; `expo-maps` is the alternative if you can require iOS 17+.

## Support window

Expo ships three SDKs per year. Each SDK targets exactly one RN version. EAS Build and EAS Update support the current SDK and a trailing window of older ones; older SDKs stop receiving patch releases well before EAS drops them.

Last publish dates (npm) as a proxy for maintenance: SDK 52 `52.0.49` (31 Jan 2026), SDK 53 `53.0.27` (10 Feb 2026), SDK 54 `54.0.37` (17 Aug 2026), SDK 55 `55.0.30`, SDK 56 `56.0.21`, SDK 57 `57.0.18`.

Treat **SDK 52 and 53 as end-of-life**. SDK 54 is still receiving patches but is the last legacy-arch SDK and is a migration dead end. Scaffold new projects on **SDK 57**. Plan upgrades one SDK at a time — never skip two — and run `npx expo install --fix && npx expo-doctor@latest` between each hop. Walkthrough: [workflow/upgrading-expo-sdk-walkthrough](https://docs.expo.dev/workflow/upgrading-expo-sdk-walkthrough/)

Pre-release channels for testing an upcoming SDK: `npm install expo@canary && npx expo install --fix` (canary = `main` snapshot, e.g. `58.0.0-canary-20260812-27f94d4`), or the `beta` npm tag before each SDK release.

## What broke, per SDK

Use this to plan an upgrade path. Each entry is a thing you must actively fix, not a nice-to-have.

### SDK 55 — released 25 Feb 2026 (RN 0.83, React 19.2)

- **Legacy Architecture removed entirely.** `newArchEnabled: false` is a no-op.
- **`notification` config field removed from app.json.** Migrate to `expo-notifications` plugin config.
- **`eas update` now requires the `--environment` flag.** Every OTA script and CI job that omits it fails.
- `expo-av` removed from Expo Go. Migrate to `expo-audio` / `expo-video`.
- Push notifications in Expo Go on Android now **throw**. (Support was *removed* in SDK 53; SDK 55 only changed the failure from a warning to a hard throw. Expo Go has not been a valid way to test remote push since 53 — use a development build.)
- Edge-to-edge is mandatory on Android 16+ — expect layout regressions under the status/nav bars.
- Minimum Xcode 26.
- `expo-navigation-bar` and `expo-status-bar` background/styling APIs became no-ops.
- Deprecated: `expo-video-thumbnails` (use `expo-video`), `removeSubscription` across modules.
- New: Hermes v1 opt-in, Hermes bytecode diffing (~75% smaller updates), `expo-brownfield`, `expo-widgets` (alpha), Expo Router Colors API / Apple zoom transitions / `Stack.Toolbar` (iOS) / experimental SplitView.
- Expo Go on the App Store / Play Store stayed on SDK 54; SDK 55 Expo Go was CLI / TestFlight / `eas go` only.

Source: [changelog/sdk-55](https://expo.dev/changelog/sdk-55)

### SDK 56 — released 21 May 2026 (RN 0.85, React 19.2)

The heaviest upgrade of the recent three.

- **`expo-router` no longer depends on React Navigation.** A codemod is provided; run it. Any third-party library importing `@react-navigation/*` internals (custom navigators, header libs, tab-bar packages) will break at runtime or type-check.
- **`expo/fetch` is now the default `globalThis.fetch`.** Opt out with `EXPO_PUBLIC_USE_RN_FETCH=1`. Watch for behavioral differences in streaming, `FormData`, and abort semantics.
- **`expo-file-system` `copy()` and `move()` are now async.** Sync variants: `copySync()`, `moveSync()`.
- **`@expo/dom-webview` replaces `react-native-webview`** as the default for DOM components.
- **The `expo` package no longer depends on `@expo/vector-icons`** — add it explicitly if you use it. `@expo/vector-icons` is itself being superseded by scoped `@react-native-vector-icons/*` packages.
- Deprecated: original `expo-calendar`, `expo-contacts`, `expo-media-library` APIs, all superseded by redesigned versions.
- Minimum Xcode 26.4; minimum iOS/tvOS 16.4; macOS 13.4. TypeScript bumped to 6.0.3. Node pre-20.19.4 dropped.
- **Expo Go for SDK 56 was never published to the App Store or Play Store.** TestFlight / `eas go` / CLI only.
- Known regression: Hermes v1 memory issue with `react-native-worklets` / `react-native-reanimated` — **fixed in SDK 57**, which is a reason to skip straight past 56 if you are on 55.
- Wins: precompiled Expo XCFrameworks (~16% faster clean iOS builds), optional Android precompiled headers via `expo-build-properties` (up to 2.81× CMake speedup), Metro crawl 6× faster, 20–50% faster cold bundling, prebuilt artifacts for `react-native-reanimated` / `react-native-screens`. Expo Router gained streaming SSR + `generateMetadata` and `SuspenseFallback`.

Source: [changelog/sdk-56](https://expo.dev/changelog/sdk-56)

### SDK 57 — released 30 Jun 2026 (RN 0.86, React 19.2.3)

Explicitly a **no-breaking-change** release ("the easiest Expo SDK upgrade you've ever made" — no breaking changes from RN 0.85).

- Fixes the SDK 56 Hermes v1 / worklets memory regression.
- `expo-router`: `Stack.Toolbar.Badge` in header placements; Android toolbar menu icons.
- `expo-dev-client`: iOS launcher setting (auto-launch vs. show launcher).
- `expo-image`: `writeToCacheAsync`, `readFromCacheAsync`.
- `expo-navigation-bar`: `setStyle` / `setHidden` now work with RN `<Modal>` on Android.
- Node minimum raised to 22.13.x — the one thing that will bite CI.
- Expo is exploring a faster release cadence, shipping non-breaking RN versions as optional upgrades.

Source: [changelog/sdk-57](https://expo.dev/changelog/sdk-57)

## Upgrade checklist

```sh
npx expo install expo@^57.0.0
npx expo install --fix
npx expo-doctor@latest
npx expo prebuild --clean          # only if you commit ios/ and android/
npx expo start --clear
```

Then: re-read the changelog entries above for every SDK you crossed, run the SDK 56 React Navigation codemod if you crossed 56, grep for `newArchEnabled`, `notification` in app config, `expo-av`, `FileSystem.copy(`, `FileSystem.move(`, and `eas update` invocations missing `--environment`.

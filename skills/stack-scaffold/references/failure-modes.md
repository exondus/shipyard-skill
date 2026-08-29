# Failure Modes: Symptom-to-Cause Triage

Verified 29 August 2026. This is the fastest-ageing file in the plugin — check every version against the live registry with `npx expo install --check` and the SDK changelog before installing: https://expo.dev/changelog

## Triage table

| Symptom you arrived with | Likely cause | Section |
|---|---|---|
| `Unable to resolve module "@repo/ui"` | Stale Metro cache, hand-written Metro config, or `main` → missing `dist/` | 1 |
| `Invalid hook call. Hooks can only be called...` | Two copies of `react` in the tree | 2 |
| `Cannot read property 'X' of undefined` from a mounted provider | Two copies of the package creating the context | 2 |
| Native build fails on a module that installed clean | Isolated install — package reaching an undeclared dep | 3 |
| `Script '/…/node_modules/react-native/react.gradle' does not exist` | Library hardcodes a hoisted `node_modules` path | 4 |
| `No podspec found for 'X' in …` / `Podfile` require fails | Same, iOS side | 4 |
| `expo-doctor` reports mismatches; crash on launch after install | Version drift off SDK-sanctioned ranges | 5 |
| Pod install fine but crash at startup, or plugin change has no effect | Stale `ios/`, or committed native dirs bypassing CNG | 6 |
| Works in Expo Go, `undefined is not a function` in a build | Native module present in one environment, not the other | 7 |
| `EXPO_PUBLIC_*` is `undefined`/wrong in a build, fine locally | Inlined at bundle time from a different environment | 8 |
| `No compatible update found` / device never receives an OTA | runtimeVersion, channel→branch, or platform mismatch | 9 |
| `Cannot find module '@react-navigation/native'` after SDK 56+ | expo-router no longer depends on React Navigation | 10 |

---

## 1. `Unable to resolve module`

**Presents as:** `Unable to resolve module "@repo/ui" from "app/_layout.tsx"` on the Metro red screen or in the terminal. Three causes, in order.

**a. Stale Metro cache.** Cheapest to rule out: `npx expo start --clear`.

**b. Hand-written Metro monorepo config.** From SDK 52, `expo/metro-config` auto-detects the workspace, and legacy manual config now fights it. In `apps/mobile/metro.config.js`, delete `watchFolders`, `resolver.nodeModulesPath(s)`, `resolver.extraNodeModules`, and `resolver.disableHierarchicalLookup`, then `npx expo start --clear` once. If it works afterwards it is a plain Node monorepo needing no special config ([guides/monorepos](https://docs.expo.dev/guides/monorepos/)). The correct config is `getDefaultConfig(__dirname)` plus your own additions only.

**c. Package `main` points at a nonexistent build output** — `"main": "./dist/index.js"` with no build step, or a `dist/` from two commits ago. Make the package source-only; Metro and Next both transpile TS directly, which eliminates the whole class:

```json
{ "main": "./src/index.ts", "types": "./src/index.ts", "exports": { ".": "./src/index.ts" } }
```

The Next.js mirror image is `Cannot use import statement outside a module` at build time: an RN-ecosystem package missing from `transpilePackages`. Find it in the stack trace, add it, restart.

---

## 2. Duplicate `react` / `react-native` and `Invalid hook call`

**Presents as:** `Invalid hook call. Hooks can only be called inside the body of a function component.` on mount; a context consumer reading `undefined` under a visibly mounted provider; or `ExpoModulesCore` symbol/link errors at native build time.

The rules, per [guides/monorepos](https://docs.expo.dev/guides/monorepos/): duplicate `react-native` versions in one monorepo are **not supported**; duplicate `react` versions in one app **cause runtime errors**; duplicate Turbo/Expo module versions cause runtime or build errors; a duplicated native module is fatal (only one version compiles into a build); and non-native packages that create a React context break too.

**Diagnose** — read the output for two distinct version strings, e.g. `react-native@0.83.10` and `react-native@0.86.3`:

```sh
pnpm why --depth=10 react-native      # or: npm why / yarn why / bun pm why
pnpm why --depth=10 react
```

**Fix, in order of preference:**

1. Align declared versions. Usually a workspace package listed `react`/`react-native` in `dependencies` instead of `peerDependencies` — shared packages must use `peerDependencies` only.
2. If a third party's peer deps are wrong and unfixable, force a root resolution:

```json
{ "resolutions": { "react": "19.2.3", "react-dom": "19.2.3", "react-native": "0.86.3" } }
```

pnpm/Yarn/Bun read `resolutions`; **npm uses `overrides`** with the same shape.

3. Enable `{ "expo": { "experiments": { "autolinkingModuleResolution": true } } }` so Metro's JS resolution matches what autolinking links natively. Available from SDK 54; **automatic for monorepo apps from SDK 55**.

Delete `node_modules` at every level and reinstall after any of these.

---

## 3. Isolated-install native build failures

**Presents as:** `pnpm install` is clean and JS resolves fine, then `eas build` or `npx expo run:ios` fails on a module — missing header, unresolved import inside a dependency, a Gradle task that cannot find a sibling package.

**Cause:** pnpm's (and Bun's) default **isolated** linker does not hoist; packages reach only what they explicitly declared. Expo supports isolated installs **from SDK 54**, but many RN libraries under-declare, and that surfaces only at native build time.

**Fix:** switch to the hoisted strategy — supported and expected, not a last resort. Set `nodeLinker: hoisted` in `pnpm-workspace.yaml`, then:

```sh
rm -rf node_modules apps/*/node_modules packages/*/node_modules
pnpm install && npx expo start --clear
```

On SDK 53 specifically, Expo recommends disabling isolated dependencies outright.

**The cost of hoisting:** you can now import packages you never declared, which breaks silently on a future upgrade. Add `pnpm dedupe --check` to CI.

---

## 4. Hardcoded `node_modules` paths in a library

**Presents as:**
- Android: `Script '/Users/you/repo/node_modules/react-native/react.gradle' does not exist.`
- iOS: `Podfile` `require_relative` failure, or `No podspec found for 'X'`.

**Cause:** RN libraries ship JS *and* native files, and the native build files often hardcode `../../node_modules/react-native/...`. That path is wrong in a monorepo — hoisting puts `node_modules` elsewhere, and Gradle/CocoaPods do not use Node module resolution.

**The correct pattern** — resolve through Node. All Expo SDK modules and templates already do this:

```groovy
// android/app/build.gradle
apply from: new File(
  ["node", "--print", "require.resolve('react-native/package.json')"].execute(null, rootDir).text.trim(),
  "../react.gradle"
)
```

```ruby
# ios/Podfile
require File.join(File.dirname(`node --print "require.resolve('react-native/package.json')"`), "scripts/react_native_pods")
```

**Fix for a third-party library:** edit `node_modules/<lib>` to use `require.resolve`, run `npx patch-package <lib>`, commit `patches/<lib>+x.y.z.patch`, add `"postinstall": "patch-package"`, and open an issue upstream. Reference: [guides/monorepos § Script does not exist](https://docs.expo.dev/guides/monorepos/)

---

## 5. Version drift

**Presents as:** `expo-doctor` listing packages outside their expected ranges; a crash at launch right after adding a dependency; a native build failing on a module you did not touch.

**Cause:** a package version the SDK was never built against — usually `npm install react-native` or a transitive bump. npm `latest` for `react-native` is `0.87.1` today; SDK 57 targets `0.86`.

**Standing workflow.** Always add RN-ecosystem packages with `npx expo install <pkg>`, never `npm install <pkg>`:

```sh
npx expo install --check       # report drifted packages, no writes
npx expo install --fix         # rewrite package.json to SDK-sanctioned ranges
npx expo-doctor@latest         # deeper: also checks React Native Directory
```

`expo-doctor` also flags unmaintained libraries and New-Arch incompatibility via React Native Directory. Tune in `package.json` (override with `EXPO_DOCTOR_ENABLE_DIRECTORY_CHECK=0|1`):

```json
{ "expo": { "doctor": { "reactNativeDirectoryCheck": {
  "enabled": true, "exclude": ["react-redux", "/^@myorg\\/.*/"], "listUnknownPackages": false
} } } }
```

Run both `--check` and `expo-doctor` on every PR in GitHub Actions — they are seconds, not EAS minutes.

---

## 6. iOS pod issues

**Presents as:** `pod install` succeeds but the app crashes at startup; a config-plugin change has no visible effect; duplicate symbol errors; `Sandbox: rsync ... deny file-write-create`.

**Cause:** a stale `ios/` that no longer reflects the app config, or committed native dirs that make config plugins a no-op.

**Procedure.** Start with `npx expo prebuild --clean`. If that is not enough:

```sh
rm -rf apps/mobile/ios/Pods apps/mobile/ios/Podfile.lock
rm -rf ~/Library/Caches/CocoaPods ~/Library/Developer/Xcode/DerivedData
npx expo prebuild --clean
cd apps/mobile/ios && pod install
```

Only then blame the library. Also confirm Xcode: SDK 57 requires **26.4+**, SDK 55 required 26; an old Xcode produces confusing pod and compile errors.

**Prefer CNG:** gitignore `ios/` and `android/` and let every build regenerate them from `app.config.ts` and config plugins. If they are committed, `npx expo prebuild` will not overwrite your changes and plugin edits silently do nothing — exactly the "my plugin config has no effect" symptom.

---

## 7. Works in Expo Go, fails in a build

**Presents as:** `undefined is not a function`, `Native module cannot be null`, or `TurboModuleRegistry.getEnforcing(...): 'X' could not be found` — but only in the dev/preview build, or only in Expo Go.

**Cause:** Expo Go ships a **fixed** native binary. Config plugins, custom native modules, and any library outside Expo Go's bundled set do not exist inside it — and conversely it bundles libraries your build lacks unless you installed them, so code can work there and fail in a real build.

This is now worse than theoretical: SDK 55's store Expo Go stayed on **SDK 54** (CLI / TestFlight / `eas go` only for 55), and SDK 56's Expo Go was **never published** to either store. Expo Go supports only the New Architecture.

**Fix — the rule, not a patch:** never let Expo Go be the acceptance environment. Scaffold to a development build from day one (`eas build --profile development --platform ios`, then `npx expo start --dev-client`).

If a library worked in Expo Go and vanishes in a build, you either forgot `npx expo install <pkg>` or forgot to rebuild after adding native code. Any new native dependency requires a **new native build** — an OTA update cannot deliver it.

---

## 8. `EXPO_PUBLIC_*` differs between dev server and EAS build

**Presents as:** `process.env.EXPO_PUBLIC_API_URL` is `undefined` in a TestFlight build but correct on the local dev server; or the app points at staging in production.

**Cause:** `EXPO_PUBLIC_*` values are **statically substituted into the bundle at build time** from whatever environment produced it — locally `.env`/`.env.local`, on EAS the environment bound via `"environment"` plus the profile's `env` block. If the variable exists only in your local `.env`, the EAS bundle has nothing to substitute and the reference collapses to `undefined`.

**Fix:**

1. `eas env:create --environment production --name EXPO_PUBLIC_API_URL --value "https://api.acme.com"`.
2. Confirm the profile binds it: `"environment": "production"` in `eas.json`.
3. Sync `.env.local` from EAS rather than hand-maintaining it: `eas env:pull --environment development`.
4. Validate at boot with a zod schema in `packages/config` so a missing var fails the build, not the user's session.

**Security corollary:** `EXPO_PUBLIC_*` is plain text in the shipped IPA/APK. Anything secret must be read only in server code — `+api.ts` routes and `packages/api` see **all** env vars, not just prefixed ones. EAS **secret**-visibility variables protect job execution, not values compiled into client code ([eas/environment-variables](https://docs.expo.dev/eas/environment-variables/)).

---

## 9. `No compatible update found`

**Presents as:** the device silently never updates, or `expo-updates` logs "No compatible update found".

An update is delivered only when **all three** conditions hold ([eas-update/how-it-works](https://docs.expo.dev/eas-update/how-it-works/)). Check in this order.

**1. `runtimeVersion` matches exactly** — overwhelmingly the most common cause. Compare the build's runtime version (on the EAS build page) with the update's target (`eas update:list --branch production`). The classic trigger is the `appVersion` policy: bump `version` `1.4.0` → `1.4.1` for a JS-only fix, publish, and every installed build (runtime `1.4.0`) is excluded. Switch to `{ "expo": { "runtimeVersion": { "policy": "fingerprint" } } }` — fingerprint hashes everything affecting the native runtime, so it changes exactly when it should, and it also prevents the inverse bug of serving JS to a binary lacking the native code.

**2. Channel is linked to a branch containing the update.** Channels map to same-named branches by default. A common miss: the profile sets `"channel": "production"` but nobody ever published to a `production` branch.

```sh
eas channel:list && eas branch:list
eas channel:edit production --branch version-2.0   # remap if needed
```

**3. Platform matches.** iOS updates are not served to Android builds; a platform-filtered export easily leaves you with only one.

Also: since **SDK 55, `eas update` requires `--environment`** — a CI job missing it fails rather than publishing.

```sh
eas update --branch production --environment production --message "fix: checkout crash"
```

---

## 10. React Navigation internals breakage (SDK 56+)

**Presents as:** after upgrading to SDK 56 or 57 — `Cannot find module '@react-navigation/native'`, type errors in a custom navigator, a header or tab-bar library rendering nothing, or `useNavigation` returning `undefined` inside a library component.

**Cause:** **SDK 56 removed expo-router's dependency on React Navigation** ([changelog/sdk-56](https://expo.dev/changelog/sdk-56)). Expo Router has its own navigation core now, so any library importing `@react-navigation/*` internals — custom navigators, header libs, tab-bar packages, navigation-state utilities — no longer finds them hoisted, or finds a version the router no longer uses.

**Fix:**

1. Run the codemod Expo ships with SDK 56 for your own code.
2. Audit every navigation-adjacent dependency for a release supporting the decoupled core; upgrade or replace it.
3. If a library genuinely needs React Navigation, install `@react-navigation/native` as an explicit direct dependency — but verify the library works against router 57 before shipping.
4. `withLayoutContext` is the supported extension point for custom navigators; prefer it over reaching into internals.

While upgrading past SDK 56, grep for the other breaking changes in that release: `FileSystem.copy(` / `FileSystem.move(` (now async — use `copySync`/`moveSync`), `react-native-webview` in DOM components (now `@expo/dom-webview`), `@expo/vector-icons` (no longer a dependency of `expo`), and reliance on RN's `fetch` (`expo/fetch` is now the default `globalThis.fetch`; opt out with `EXPO_PUBLIC_USE_RN_FETCH=1`).

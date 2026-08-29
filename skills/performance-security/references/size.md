# App Binary Size

Time-sensitive: store limits, Android Gradle Plugin flag names and Expo config keys change between SDK releases. Verify build-config keys against the current Expo and Android docs before editing a project.

Size matters commercially, not just aesthetically: install conversion drops as download size rises, and Apple enforces a cellular-download threshold above which users get a "connect to Wi-Fi" prompt at the exact moment they decided to try your app.

## What actually makes an RN binary large

In rough descending order of typical contribution:

1. **Native code from dependencies.** Every autolinked native module ships its own compiled code and any bundled frameworks. A maps SDK, a video player, an ML runtime or an analytics vendor with a fat framework each add megabytes. This dominates; JS is rarely the problem.
2. **Uncompressed assets.** PNG splash screens and hero images at 3× density, unsubsetted font families with weights you never use, bundled video, Lottie files exported without optimisation.
3. **Architecture slices.** Shipping arm64-v8a *and* armeabi-v7a *and* x86_64 in one artifact multiplies native code size.
4. **Hermes bytecode.** The `.hbc` file is typically *larger on disk* than the equivalent minified JS — this is a deliberate trade: precompiled bytecode removes parse/compile time at startup. Do not "optimise" it away; you would trade size for a slower cold start.
5. **Icon sets and locales.** A full icon font for six glyphs; forty locale bundles from a dependency for an app shipped in two languages.
6. **Debug symbols and dSYMs** left in the shipped artifact.
7. **Duplicated assets** — the same image bundled both in the native asset catalog and in the JS bundle via `expo-updates`.

## How to measure

**iOS — App Store Connect App Size Report.** This is the only measurement that matches what Apple enforces and what users see. Go to your app → the build → App Size Report; it breaks out **download size vs. install size per device class**. Local `.ipa` file size is misleading because it precedes App Store thinning and re-encryption. You need a build uploaded to App Store Connect (TestFlight is enough) to get real numbers.

**Android — analyze the `.aab`/`.apk`.**

```bash
# Android Studio: Build > Analyze APK...  (drop in the .aab or .apk)

# CLI: what a specific device actually downloads
bundletool build-apks --bundle=app.aab --output=app.apks
bundletool get-size total --apks=app.apks

# Quick look at what's inside
unzip -l app.aab | sort -k1 -n -r | head -40
```

APK Analyzer gives a per-entry breakdown (native libs by ABI, resources, DEX, assets) and can diff two builds — use the diff to catch the dependency that added 4MB last sprint.

**Track size in CI as a budget.** Record the artifact size per build and fail or flag on a threshold increase. Size regressions arrive one dependency at a time and are invisible without a trend line.

## Reduction levers, in order

### 1. Ship an Android App Bundle (`.aab`), not a universal APK
Play generates per-device splits by ABI, screen density and language, so a user downloads only their slice. This is the largest single Android win and it is free — EAS builds `.aab` for the `production` profile by default. Verify: an `app-universal.apk` in your release pipeline means you are shipping every architecture to every device.

### 2. Enable minification and resource shrinking
R8 (which replaced ProGuard) strips unused classes and shrinks/renames code; resource shrinking removes unreferenced resources.

```js
// app.json -> expo-build-properties plugin
["expo-build-properties", {
  "android": {
    "enableProguardInReleaseBuilds": true,
    "enableShrinkResourcesInReleaseBuilds": true
  }
}]
```

**Gotcha — symptom: the release build crashes or a native module silently stops working, but debug is fine.** R8 stripped a class reached only via reflection. Fix with `-keep` rules in `proguard-rules.pro` for the offending library; do not disable R8 wholesale. Always smoke-test a release build after enabling this, because the failure appears only in release.

### 3. Trim dependencies
Audit every native module against actual use. Each one costs binary size permanently, plus build time and upgrade risk.

- Remove libraries kept "just in case" or left behind after a feature was cut.
- Prefer one library that does three things over three that each do one.
- Replace heavy vendor SDKs with a thin HTTP call where the SDK exists only to POST events.
- Check for two libraries solving the same problem (two date libraries, two icon sets, two image caches).

Use APK Analyzer's native-lib view to attribute megabytes to specific `.so` files, which maps back to specific packages.

### 4. Fix the asset pipeline
- **Images:** WebP (or AVIF where supported) instead of PNG/JPEG; typically 25–50% smaller at equal quality [UNVERIFIED — depends heavily on content].
- **Icons:** SVG or a subsetted icon font. Never bundle a 900-glyph icon font for a dozen icons.
- **Fonts:** subset to the character ranges you ship, and bundle only the weights you actually render. Four weights × two families is often three quarters of your font payload wasted.
- **Don't bundle what you can stream.** Video, large illustration sets and onboarding imagery should be remote and cached via `expo-image`, not shipped in the binary — with a small embedded fallback.
- Only ship the densities you need; a single well-chosen 2× asset often beats 1×/2×/3× triplicates.

### 5. Strip locales and unused resources
Restrict Android resource configurations to your supported languages so dependency locale strings don't ride along:

```gradle
android { defaultConfig { resConfigs "en", "es" } }
```

Same principle on iOS: remove unused `.lproj` directories contributed by dependencies.

### 6. Handle symbols correctly
Upload dSYMs/symbol files to Sentry rather than leaving debug symbols in the shipped artifact. You keep readable crash reports without carrying the symbols in every user's download.

## Realistic size ranges

**Observed ranges for typical consumer RN apps, not official targets or vendor-published figures. [UNVERIFIED] — measure your own artifact rather than quoting these.**

| | Download size | Notes |
|---|---|---|
| iOS | ~30–60 MB | Post-thinning, per App Store Connect |
| Android | ~15–40 MB | Per-device split from an `.aab` |
| Universal APK | often 2–3× the split size | Which is why you never ship one |

A media-heavy or ML-containing app will exceed these legitimately. What matters is that you know your number, know what's in it, and catch regressions.

Apple's cellular-download limit has been raised repeatedly over the years — **check the current threshold in Apple's developer documentation rather than trusting a remembered figure** [UNVERIFIED]. Staying comfortably under whatever it currently is protects install conversion.

## Quick triage

When asked "why is this app 90MB?", in order:
1. Run APK Analyzer / check the App Size Report — get the actual breakdown before theorising.
2. Look at native `.so` sizes by ABI → is it a universal APK, or one heavy SDK?
3. Look at assets → images and fonts, then video.
4. Confirm R8 and resource shrinking are on in release.
5. Diff against the last known-good build to find what changed.

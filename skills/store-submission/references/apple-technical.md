# Apple Technical Requirements (2026)

Verified 29 August 2026. Guideline numbering, SDK floors, deadlines and asset specs change — verify against [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) and the [Play policy centre](https://support.google.com/googleplay/android-developer/topic/9858052) before submitting.

Authoritative source for dates: [Apple upcoming requirements](https://developer.apple.com/news/upcoming-requirements/).

---

## 1. Xcode / SDK floor for uploads

| Requirement | Since | Applies to |
|---|---|---|
| Built with **Xcode 26 or later** using the **iOS 26 / iPadOS 26 / tvOS 26 / visionOS 26 / watchOS 26 SDK** | **28 April 2026** | Every upload to App Store Connect, including TestFlight-only builds |

**Failure mode.** The upload is rejected by App Store Connect (not by App Review) with:

```
ERROR ITMS-90725: "SDK Version Issue. This app was built with the iOS <n> SDK.
All iOS apps submitted to the App Store must be built with the iOS 26 SDK or later,
included in Xcode 26 or later."
```

You get this from `eas submit`, Transporter, and `xcrun altool` alike. It is a hard upload gate — no binary reaches TestFlight.

**Preemptive fix for Expo.** Ensure the EAS Build image resolves to Xcode 26. Pin it explicitly rather than relying on the default:

```json
{ "build": { "production": { "ios": { "image": "latest" } } } }
```

Check `eas build:inspect` or the build log's "Xcode version" line before submitting. An old `expo` SDK that cannot compile against iOS 26 headers is the real blocker — upgrade the Expo SDK, don't just bump the image. Note that the SDK floor is independent of `deploymentTarget`: you can still support older iOS versions at runtime while building against the 26 SDK.

---

## 2. Privacy manifests (`PrivacyInfo.xcprivacy`)

Required since **1 May 2024** for apps and for the SDKs they embed.

The manifest declares four keys: `NSPrivacyTracking` (bool), `NSPrivacyTrackingDomains` (array), `NSPrivacyCollectedDataTypes`, and `NSPrivacyAccessedAPITypes`.

### Required-reason APIs and their approved reason codes

| API category (`NSPrivacyAccessedAPIType`) | Common approved reasons | Typical RN trigger |
|---|---|---|
| `NSPrivacyAccessedAPICategoryUserDefaults` | `CA92.1` (access only your app's own data), `1C8F.1` (app group, same team), `C56D.1` (third-party SDK on behalf of host app) | `@react-native-async-storage/async-storage`, almost every SDK |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | `C617.1` (display to user), `DDA9.1` (inside app container/group/CloudKit), `3B52.1` (user-initiated file access), `0A2A.1` (third-party SDK for host app) | `expo-file-system`, image caches |
| `NSPrivacyAccessedAPICategorySystemBootTime` | `35F9.1` (measure elapsed time) | Crash/perf SDKs, Sentry, Firebase |
| `NSPrivacyAccessedAPICategoryDiskSpace` | `E174.1` (check availability before write), `85F4.1` (user-initiated), `7D9E.1` (third-party SDK) | download/cache managers |
| `NSPrivacyAccessedAPICategoryActiveKeyboards` | `3EC4.1` (custom keyboard app), `54BD.1` (per user request) | rare |

Any use with **no** declared reason triggers an automated email from App Store Connect within minutes of upload ("ITMS-91053: Missing API declaration") and eventually blocks the submission.

### Expo configuration

Set `expo.ios.privacyManifests` in app config — the prebuild step writes `PrivacyInfo.xcprivacy` ([Expo docs](https://docs.expo.dev/guides/apple-privacy/)):

```json
{
  "expo": {
    "ios": {
      "privacyManifests": {
        "NSPrivacyAccessedAPITypes": [
          { "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryUserDefaults",
            "NSPrivacyAccessedAPITypeReasons": ["CA92.1"] },
          { "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategoryFileTimestamp",
            "NSPrivacyAccessedAPITypeReasons": ["C617.1"] },
          { "NSPrivacyAccessedAPIType": "NSPrivacyAccessedAPICategorySystemBootTime",
            "NSPrivacyAccessedAPITypeReasons": ["35F9.1"] }
        ]
      }
    }
  }
}
```

### The static-pod caveat

Apple does **not** reliably parse `PrivacyInfo.xcprivacy` files shipped inside statically-linked CocoaPods — which is how most React Native dependencies build under `use_frameworks! :linkage => :static` and under Expo's default autolinking. The practical consequence: a dependency can be fully compliant on its own and you still get ITMS-91053.

**Preemptive fix.** After adding any native dependency, run `grep -r "NSPrivacyAccessedAPIType" node_modules/*/ios ios/Pods` and hoist every distinct category/reason pair you find into your app-level `privacyManifests` block. Over-declaring a reason you legitimately qualify for is safe; under-declaring is not. Verify by uploading a build to TestFlight — Apple emails the missing-declaration list within ~15 minutes, which is the fastest available validator.

---

## 3. Third-party SDK privacy manifest + signature requirement

Apple maintains a list of **87 SDKs** that must ship both a privacy manifest and, when used as a **binary** dependency, a signature Xcode can validate across versions ([official list](https://developer.apple.com/support/third-party-SDK-requirements/)). The signature check ensures a new version is signed by the same developer as the previous one.

RN/Expo-relevant entries from the list:

`hermes` · `Alamofire` · `AppAuth` · `BoringSSL/openssl_grpc` · `OpenSSL` · `Charts` · `FBAEMKit` · `FBLPromises` · `FBSDKCoreKit` · `FBSDKCoreKit_Basics` · `FBSDKLoginKit` · `FBSDKShareKit` · `FirebaseABTesting` · `FirebaseAuth` · `FirebaseCore` · `FirebaseCoreExtension` · `FirebaseCoreInternal` · `FirebaseCrashlytics` · `FirebaseDynamicLinks` · `FirebaseFirestore` · `FirebaseInstallations` · `FirebaseMessaging` · `FirebaseRemoteConfig` · `GoogleDataTransport` · `GoogleSignIn` · `GoogleToolboxForMac` · `GoogleUtilities` · `grpcpp` · `GTMAppAuth` · `GTMSessionFetcher` · `IQKeyboardManager(Swift)` · `Kingfisher` · `leveldb` · `Lottie` · `nanopb` · `OneSignal`, `OneSignalCore`, `OneSignalExtension`, `OneSignalOutcomes` · `OrderedSet` · `Promises` · `Protobuf` · `Reachability` · `RxCocoa`, `RxRelay`, `RxSwift` · `SDWebImage` · `SnapKit` · `Starscream` · `SVProgressHUD` · `SwiftyGif` · `SwiftyJSON` · `Toast` · `UnityFramework`.

**What to do.** Keep these dependencies on recent versions — the manifest/signature support was added to each of them in a specific release, and pinning an old version reintroduces the failure. If you vendor a prebuilt `.xcframework` of any of these, confirm it is signed.

---

## 4. Export compliance

Set once in app config so every build and every TestFlight upload stops asking:

```json
{ "expo": { "ios": { "config": { "usesNonExemptEncryption": false } } } }
```

This writes `ITSAppUsesNonExemptEncryption` into `Info.plist` ([Expo config reference](https://docs.expo.dev/versions/latest/config/app/)).

- `false` is correct if you use only HTTPS/TLS and the OS-provided crypto (CryptoKit, CommonCrypto, Keychain) — the standard exemption.
- If you implement or bundle **proprietary or non-standard** encryption, leave it unset/`true` and complete the annual self-classification report; you may need a CCATS/ERN.
- Symptom of omitting it: every build sits in TestFlight as "Missing Compliance" and cannot be distributed until you answer the questionnaire by hand.

---

## 5. `NS*UsageDescription` audit

Every permission your binary can request needs a purpose string that "clearly and completely" describes the use (5.1.1(ii)). Generic strings ("This app needs camera access") get rejected.

Audit list — check each against the generated `ios/<App>/Info.plist`, not against app.json:

| Key | Present only if |
|---|---|
| `NSCameraUsageDescription` | camera capture |
| `NSPhotoLibraryUsageDescription` / `NSPhotoLibraryAddUsageDescription` | read / write-only to library |
| `NSMicrophoneUsageDescription` | audio recording, video with sound |
| `NSLocationWhenInUseUsageDescription` | foreground location |
| `NSLocationAlwaysAndWhenInUseUsageDescription` | background location (needs strong justification) |
| `NSContactsUsageDescription` | contacts |
| `NSCalendarsFullAccessUsageDescription` / `NSRemindersFullAccessUsageDescription` | calendar/reminders (iOS 17+ key names) |
| `NSFaceIDUsageDescription` | biometrics |
| `NSMotionUsageDescription` | pedometer/CoreMotion |
| `NSBluetoothAlwaysUsageDescription` | BLE |
| `NSLocalNetworkUsageDescription` | mDNS/local discovery |
| `NSSpeechRecognitionUsageDescription` | speech |
| `NSUserTrackingUsageDescription` | **only if you actually call ATT** |

### The config-plugin trap

Expo config plugins inject `Info.plist` keys and `UIBackgroundModes` on your behalf. `expo-image-picker` adds camera and photo strings; `expo-location` can add the "Always" key; `expo-notifications`, `expo-av`, `expo-camera` and `react-native-maps` all contribute. A plugin you installed for one feature can declare a permission you never use — and reviewers reject unused permission declarations under 5.1.1(iii) data minimisation.

**Preemptive fix.** Run `npx expo prebuild --clean --platform ios` and diff the generated `Info.plist` against your intended list. Suppress unwanted keys by passing plugin options (e.g. `["expo-image-picker", { "photosPermission": false }]` where supported) or by overriding with `expo.ios.infoPlist`. Do the same audit for `UIBackgroundModes` — an unused `location` or `audio` mode invites a 2.5.4 rejection.

---

## 6. Age ratings (overhauled 2025)

Tiers are now **4+, 9+, 13+, 16+, 18+** — 13+/16+/18+ replaced the old 12+/17+ ([Apple news, ks775ehf](https://developer.apple.com/news/?id=ks775ehf)).

New required questionnaire sections: **in-app controls**, **capabilities**, **medical or wellness topics**, and **violent themes**. Apps with AI assistant or chatbot functionality must be assessed for how frequently they can surface sensitive content — an unfiltered LLM surface pushes the rating up.

You may set a rating **higher** than Apple's computed value if your app requires a higher minimum age.

**Deadline: 31 January 2026.** Responses to the updated questions were mandatory for every app; without them, submitting an update in App Store Connect is interrupted. Ratings align to the new system automatically on iOS 26 and later. If you are working on an app that hasn't shipped since 2025, expect the questionnaire to block your first submission until answered — do it before you build.

Guideline 2.3.6 requires honest answers; a mismatch between rating and observed content is a rejection and, repeated, an account issue.

---

## 7. Age assurance laws — current, uncertain state

Texas **SB2420** (App Store Accountability Act) was to take effect **1 January 2026**, requiring age category signals, parental consent for downloads and IAP, re-consent on significant app changes, and consent revocation handling.

Status: Apple **paused implementation** on **23 December 2025** after a district court enjoined the law ([Apple news, 8jzbigf4](https://developer.apple.com/news/?id=8jzbigf4)). The Fifth Circuit subsequently stayed that injunction. **[UNVERIFIED: whether Texas enforcement is live as of 29 August 2026 — check developer.apple.com/news before relying on either answer.]** Equivalent Utah and Louisiana statutes take effect during 2026; **[UNVERIFIED: their exact current effective dates and litigation status.]**

APIs Apple provides, available worldwide today on iOS/iPadOS/macOS 26+:

| API | Purpose |
|---|---|
| [Declared Age Range](https://developer.apple.com/documentation/declaredagerange/) | Returns a privacy-preserving **age category**, never a birthdate. Requires user/parent sharing. |
| [PermissionKit `SignificantAppUpdateTopic`](https://developer.apple.com/documentation/PermissionKit/SignificantAppUpdateTopic) | Invokes the system parental re-consent flow when your app materially changes |
| [StoreKit `AppStore.ageRatingCode`](https://developer.apple.com/documentation/storekit/appstore/ageRatingCode) | Reads your app's effective age rating at runtime |
| App Store Server Notifications | Signals parental consent revocation |

**Preemptive posture.** Adopt Declared Age Range now if your app has any age-varying content, ads, chat, or UGC — it is cheap, is required by guideline 4.7.5 for mini-app hosts regardless of state law, and de-risks whichever way the litigation lands. Do not build a birthdate collection screen as a substitute: collecting a minor's date of birth creates COPPA/GDPR exposure that the age-category API is designed to avoid.

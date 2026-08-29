# Google Play Requirements

Verified 29 August 2026. Guideline numbering, SDK floors, deadlines and asset specs change — verify against [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) and the [Play policy centre](https://support.google.com/googleplay/android-developer/topic/9858052) before submitting.

Play review is mostly automated policy scanning plus a light human pass. Anything checkable statically — manifest permissions, SDK inventory, declared forms, target SDK — is checked *every time*, and mismatches are near-certain rejections. Behavioural nuance is checked less often but enforced retroactively via app removal.


## 1. Target API level

| Requirement | Deadline |
|---|---|
| New apps **and updates** must target **Android 16 (API level 36)** or higher | **31 August 2026** |
| Extension available on request via Play Console → Policy status | to **1 November 2026** |
| Wear OS / Android Automotive OS | API 35 |
| Android TV / Android XR | API 34 |
| (previous cycle) API 35 deadline | 31 August 2025 |

Source: [Target API level requirements](https://support.google.com/googleplay/android-developer/answer/11926878).

**Miss it and** new uploads are blocked at the Play Console upload step with an explicit target-SDK error; already-published apps stay installable for existing users but become invisible to new users on newer Android versions.

**Expo fix.** Set it in `expo-build-properties` and rebuild:

```json
["expo-build-properties", { "android": { "compileSdkVersion": 36, "targetSdkVersion": 36, "buildToolsVersion": "36.0.0" } }]
```

Then test the API 36 behaviour changes — predictive back, edge-to-edge enforcement and stricter foreground-service rules break RN apps at runtime, not at build time.


## 2. Data safety form

Declared on Play Console → **App content → Data safety**. Source: [Provide information for Data safety](https://support.google.com/googleplay/android-developer/answer/10787469).

Per data type you declare: **collected**, **shared**, **processed ephemerally**, collection **optional**, the **purposes**, and whether data is **encrypted in transit** and **deletable on request**.

**How Google cross-checks it.** The form is validated against Google's SDK Index inventory of libraries detected in your AAB, plus static analysis of the manifest and code paths. A form saying "no data collected" while the bundle contains Firebase Analytics, Sentry, AdMob, Branch or an attribution SDK is flagged automatically — one of the most common Play rejections and one of the easiest to avoid.

**Preemptive fix.** Before filling the form, enumerate every third-party SDK in the release AAB (`./gradlew :app:dependencies`, or the Play Console SDK inventory after your first upload). Most major SDKs publish an official Data-safety mapping — copy it verbatim rather than guessing. Declare **device or other IDs** if any analytics or ads SDK is present, and **crash logs**/**diagnostics** if you ship Crashlytics or Sentry. Keep the answers in version control beside your privacy policy so they update when a dependency is added.

The form must also match the **privacy policy URL**, separately required for all apps.


## 3. Account deletion

Source: [App account deletion requirements](https://support.google.com/googleplay/android-developer/answer/13327111). Enforced since **31 May 2024** (initial deadline 7 December 2023 plus extension); non-compliant apps are removed. Two independent obligations if your app supports account creation:

**(a) In-app deletion path.** Must be prominent — account settings or equivalent — and intuitive. Non-mobile form factors (Android TV, Wear OS) are exempt from the in-app path but still need the web resource.

**(b) Web deletion URL**, declared in the designated field in the Data safety form. Google actually loads this URL during review. It must be:

| Requirement | What that means in practice |
|---|---|
| **Functional** | Loads over HTTPS without errors, redirects, or a login wall that blocks the instructions |
| **Relevant** | The deletion path is prominently featured and easily discoverable on the page itself — not buried in a privacy policy |
| **Identifiable** | The page **references your app name or developer name exactly as it appears on the store listing** |

A generic `/support` or `/contact` page fails all three. Prerequisites ("cancel your subscription first") must be stated on the page. The channel may be a form, mailto link or support email. Declare in the same form whether deletion removes **all** data or only the account, and what is retained and why (legal/fraud retention is fine if disclosed).


## 4. Closed testing requirement (personal accounts)

Source: [App testing requirements for new personal developer accounts](https://support.google.com/googleplay/android-developer/answer/14151465).

| Item | Current value |
|---|---|
| Applies to | **Personal** Play Console accounts created after **13 November 2023** |
| Testers required | **12** (reduced from the earlier 20) |
| Duration | **continuously opted in for at least 14 days** |
| Then | Apply for production via Dashboard → "Apply for production" |
| Application review | usually ≤7 days, occasionally longer |

Testers who opt in, test briefly, then opt out **do not count** — the 14 days is measured on continuous opt-in.

The production application has three parts: (1) the closed test — recruitment, engagement, a summary of feedback; (2) the app — target audience, value proposition, projected install range; (3) readiness — what you changed based on testing and how you concluded it was ready. Thin answers are rejected and cost another cycle.

**Plan for it.** From a cold start a personal account needs roughly 3–4 weeks before public launch. Recruit testers early, use a Google Group as the tester list so membership is stable, and ship real updates during the 14 days so there is genuine feedback to describe.

**Organisation accounts** skip the 12-tester requirement but require verification: a **D-U-N-S number** matching the legal entity, plus verification of the organisation's website, email and, in some cases, a phone number and address. D-U-N-S issuance from Dun & Bradstreet can take days to weeks — start it first. Google's broader developer verification programme extends identity verification obligations further through 2026; **[UNVERIFIED: precise scope and dates of the 2026 verification mandate for sideloaded/non-Play distribution.]**


## 5. Sensitive permission declarations

Source: [Permissions and APIs that access sensitive information](https://support.google.com/googleplay/android-developer/answer/16585319).

Each requires a **Permissions declaration form** in Play Console (App content), a written justification, and usually an unlisted-YouTube **demo video** of the in-app flow needing it.

| Permission / API | Rule |
|---|---|
| `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO` | Broad photo/video access is restricted to apps whose **core purpose** is photo/video. Everyone else must use the **Android Photo Picker** (`ACTION_PICK_IMAGES`), which needs no permission at all. Declaration required since the [Photo & Video Permissions policy, 22 January 2025](https://support.google.com/googleplay/android-developer/answer/15800983). |
| `ACCESS_BACKGROUND_LOCATION` | Requires declaration + demo video + a feature that genuinely needs location when the app is closed. Must be requested separately from foreground location, after foreground is granted. |
| `MANAGE_EXTERNAL_STORAGE` (All files access) | Restricted to file managers, backup/restore, anti-virus, document management. Otherwise use SAF or scoped storage. |
| `QUERY_ALL_PACKAGES` | Restricted; declare specific packages in `<queries>` instead. RN libraries sometimes pull this in transitively — check the merged manifest. |
| SMS / Call Log | Restricted to default handler apps and a narrow list of use cases. |
| `foregroundServiceType` | Every foreground service must declare a type in the manifest **and** be declared in Play Console with a justification and video. Types: `camera`, `connectedDevice`, `dataSync`, `health`, `location`, `mediaPlayback`, `mediaProjection`, `microphone`, `phoneCall`, `remoteMessaging`, `shortService`, `specialUse`, `systemExempted`. `dataSync` and `specialUse` get the most scrutiny. |
| `SCHEDULE_EXACT_ALARM` | Restricted to alarms/calendars/timers; otherwise use `setExactAndAllowWhileIdle` alternatives or `USE_EXACT_ALARM` only if eligible. |

**Preemptive fix for Expo.** Run `npx expo prebuild --clean --platform android` and read `android/app/src/main/AndroidManifest.xml` plus the **merged** manifest (`android/app/build/intermediates/merged_manifests/release/AndroidManifest.xml`). Config plugins and transitive AARs add permissions silently. Remove unwanted ones with `expo.android.blockedPermissions` in app config, or `tools:node="remove"`.


## 6. Families policy

Applies if your target audience declaration (App content → Target audience and content) includes anyone **under 13** (or the local equivalent age).

Requirements: an age-neutral age screen where relevant; ads and analytics SDKs limited to the **Families self-certified ads SDK** list; no collection of personal or sensitive data from children; no third-party analytics that isn't certified; no ads that are disruptive/interstitial in the wrong places; compliance with COPPA and, in the EU, GDPR-K. Content must match the declared audience.

Note the asymmetry: declaring a mixed audience (children *and* adults) still pulls you into Families obligations for the child-facing experience. If children are not your audience, say so explicitly and make sure no listing copy, artwork or content suggests otherwise.


## 7. Release mechanics

**Pre-launch report.** Generated automatically for internal, closed, open and (optionally) production tracks. Google runs your AAB on a set of physical devices with a crawler and reports: crashes and ANRs per device/API level, performance/startup metrics, accessibility issues (touch target size, contrast, missing labels), security vulnerabilities detected in your code and dependencies, and screenshots per screen. **Read it before promoting a build.** It is the cheapest way to catch a crash on an OEM device or an old API level you don't own.

**Staged rollout.** Available on closed, open and production tracks. You choose the percentage (commonly 1 → 5 → 10 → 20 → 50 → 100), and you can **halt** a rollout to stop it reaching new users; already-updated users are not rolled back. Combine with Android vitals thresholds (crash rate, ANR rate) as your promotion gate.

**Review timing.** First-time submissions can take several days; updates from an established account are faster. **[UNVERIFIED: current published median review times.]** Budget a week for a first Play submission.

**Versioning.** `android.versionCode` must be a positive integer that increases with every upload ([Expo config reference](https://docs.expo.dev/versions/latest/config/app/)). Use EAS remote versioning (`"autoIncrement": true` in the build profile) rather than hand-editing, and never reuse a version code — Play rejects the upload permanently.

**App signing.** Enrol in Play App Signing (default for new apps). Let EAS manage the upload key; export a backup via `eas credentials` and keep it somewhere you will still have it in three years.

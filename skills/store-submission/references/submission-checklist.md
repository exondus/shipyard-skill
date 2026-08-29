# Pre-Submission Checklist

Verified 29 August 2026. Guideline numbering, SDK floors, deadlines and asset specs change — verify against [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) and the [Play policy centre](https://support.google.com/googleplay/android-developer/topic/9858052) before submitting.

Work top to bottom against the **release build on a physical device** — not a dev client, not the simulator. Every item passes or fails; if you cannot demonstrate it, it fails.


## A. Account and reviewer access

- [ ] A demo account exists, and you signed into it from a freshly-installed release build **today**.
- [ ] The demo account has **no expiry** and no automatic deactivation for inactivity.
- [ ] The demo account has **no 2FA / SMS OTP / email magic link**, or you have a documented static bypass code and it works.
- [ ] The demo account is **not rate-limited** and is not shared with a load-tested staging tier.
- [ ] The demo account is seeded so that **no screen the reviewer can reach is empty** — feed, history, notifications, saved items, purchase history.
- [ ] The demo account can reach **every feature named in the listing description**, including paid tiers (grant entitlements server-side).
- [ ] The build points at **production** backends; staging URLs, debug menus and `__DEV__` panels are compiled out.
- [ ] Backend services will stay up for the whole review window; no scheduled maintenance in the next 5 days.
- [ ] Region-locked features: the demo account bypasses geo-restriction, or the notes explain it and Apple's testing region is covered.

## B. Legal and privacy

- [ ] Privacy policy URL loads over HTTPS, returns 200, and is **also linked from inside the app** (Apple 5.1.1(i)).
- [ ] Privacy policy states what is collected, why, retention, how to delete, how to withdraw consent.
- [ ] Terms of Use / EULA URL is live and is linked **from the paywall** (Apple 3.1.2(c)); Apple's standard EULA is acceptable.
- [ ] Support URL is live and offers a real contact method (form or email), not a marketing page.
- [ ] **Account deletion works end-to-end**: new account → Settings → Delete → confirm → gone → the same email can register again, ≤3 taps from Settings.
- [ ] Play **web deletion URL** is live, names the app or developer as it appears on the listing, and prominently shows the deletion path.
- [ ] Apple Privacy Nutrition Label matches actual runtime behaviour and matches `PrivacyInfo.xcprivacy`.
- [ ] Play Data safety form matches the SDK inventory of the release AAB (analytics, crash, ads, attribution all declared).
- [ ] If the label declares tracking, the **ATT prompt fires** before any IDFA read; if not, the label says so and `NSUserTrackingUsageDescription` is removed.
- [ ] Age rating questionnaire answered in App Store Connect (mandatory since **31 January 2026**) and Play's content rating questionnaire completed.
- [ ] If any data goes to a third-party AI/LLM provider, it is disclosed in the privacy policy and the label (Apple 5.1.2(i)).

## C. Technical

- [ ] iOS build compiled with **Xcode 26 / iOS 26 SDK** (mandatory since **28 April 2026**) — confirm in the EAS build log.
- [ ] Android build targets **API 36** (mandatory **31 August 2026**).
- [ ] Cold-start launch is crash-free on the **oldest OS version you declare support for**, on a physical device.
- [ ] `PrivacyInfo.xcprivacy` covers every required-reason API in the app **and** its static pods; TestFlight upload produced no ITMS-91053 email.
- [ ] `usesNonExemptEncryption` is set in app config so no build stalls on "Missing Compliance".
- [ ] Every `NS*UsageDescription` in the generated `Info.plist` is specific, with **no strings for permissions you don't use** (config-plugin injection).
- [ ] `UIBackgroundModes` and Android `foregroundServiceType` entries correspond to real, declared behaviour.
- [ ] Merged Android manifest contains no unintended permissions (`QUERY_ALL_PACKAGES`, `ACCESS_BACKGROUND_LOCATION`, `MANAGE_EXTERNAL_STORAGE`, `READ_MEDIA_*`).
- [ ] App works on an **IPv6-only** network (Apple 2.5.5) — test via a NAT64 hotspot; no IPv4 literals in config.
- [ ] Every permission can be **denied** and the app still functions with a graceful fallback.
- [ ] **Airplane mode**: no infinite spinners; every screen shows a readable offline state with a retry.
- [ ] Every list, search result and inbox has a designed **empty state**.
- [ ] `apple-app-site-association` served at `https://<domain>/.well-known/`, `application/json`, no redirect, correct Team ID + bundle ID.
- [ ] App Links: `assetlinks.json` at `https://<domain>/.well-known/assetlinks.json` with the **Play App Signing** SHA-256 fingerprint (not the upload key's).
- [ ] Deep links open the right screen from a **cold start**, not only when the app is already running.
- [ ] Push notification registration succeeds on a production APNs build and on FCM.
- [ ] Version numbers: `ios.buildNumber` / `android.versionCode` are unique and higher than anything previously uploaded.

## D. Metadata

- [ ] App name ≤30 characters; no keyword stuffing in name or subtitle (Apple 2.3.7).
- [ ] Screenshots show the app **in use**, not splash or login screens (Apple 2.3.3).
- [ ] **No mention of Android, Google Play, the Play Store, "web version", or cross-platform pricing** anywhere in the description, release notes, screenshots, preview video, or in-app copy (Apple 2.3.10). Grep the listing text and the app's string files.
- [ ] "What's New" describes the actual changes (Apple 2.3.12).
- [ ] Correct primary category; content rating matches observed content.
- [ ] Play feature graphic (1024 × 500) uploaded — listing will not publish without it.
- [ ] No placeholder text, "TODO", or lorem ipsum anywhere in the listing.

## E. Purchases

- [ ] Every digital unlock goes through StoreKit / Play Billing; no web checkout links outside the US storefront exception.
- [ ] A **Restore Purchases** control exists and is reachable **without logging in**.
- [ ] Paywall shows, on one screen: product name, subscription period, price per period, what's included, **Terms link**, **Privacy link** (Apple 3.1.2(c)).
- [ ] Sandbox purchase completes and the entitlement persists across reinstall and across devices on the same Apple ID.
- [ ] IAP products are in "Ready to Submit" state and attached to the version being submitted.
- [ ] Purchased credits or currency do not expire (Apple 3.1.1).
- [ ] If you sell physical goods or real-world services, the review notes say so explicitly.

## F. Platform-specific

**Apple**
- [ ] If a social/third-party login is the primary auth, **Sign in with Apple** (or an equivalent private-relay alternative) is offered at least as prominently (4.8).
- [ ] If the app has no significant account features, a **guest/browse mode** exists (5.1.1(v)).
- [ ] UGC apps ship **report content**, **block user**, a filter, an EULA with a zero-tolerance clause, and published contact info (1.2).
- [ ] Interstitial ads have a large, easily-tappable close control and users can report ads (2.5.18).
- [ ] Build uploaded to **TestFlight and tested via an external group** (Beta App Review) before the production submission.

**Google Play**
- [ ] Closed test ran with **12 testers continuously opted in for 14 days** (personal accounts created after 13 Nov 2023), with substantive production-application answers.
- [ ] **Pre-launch report** reviewed: zero crashes/ANRs across the device matrix; security warnings triaged.
- [ ] Sensitive permission declaration forms submitted with demo videos where required.
- [ ] Target audience declaration is accurate; Families policy obligations met if under-13 is included.
- [ ] Staged rollout configured (start at 5–10%) with a halt plan tied to Android vitals.


## Review notes template

Paste into App Store Connect → App Review Information → Notes. Replace every `<…>`, delete what doesn't apply, keep it under ~400 words.

```
DEMO ACCOUNT
Email: <review@example.com>
Password: <StaticPassword2026!>
This account does not expire, has no 2FA, and is pre-populated with sample data.
<If OTP is unavoidable:> Any 6-digit code entered as 000000 is accepted for this account.

HOW TO REACH THE MAIN FEATURES
1. <Feature name> — Home tab > <button> > <screen>
2. <Feature name> — Profile tab > Settings > <row>
3. Account deletion — Profile tab > Settings > Account > Delete Account > type DELETE > Confirm.
   This permanently deletes the account and all associated data server-side.

IN-APP PURCHASES
Products in this build: <Pro Monthly (com.example.pro.monthly)>, <Pro Yearly (…)>.
The paywall appears at <Home > Upgrade> and also at <…>.
Restore Purchases is at <Settings > Restore Purchases> and works without signing in.
The demo account already has <no entitlement / a Pro entitlement> so you can test <both paths>.

PERMISSIONS AND WHY
Camera: used only in <Add Photo> to <…>. The app is fully usable if declined.
Location (when in use): used only in <Nearby> to <…>. Manual entry is available if declined.
<ATT:> We <do / do not> track users. <If we do:> The ATT prompt appears after <the explainer on first launch of the Feed>.

NEW IN THIS VERSION
<Specific description of each new feature and where to find it — not "bug fixes and improvements".>

USER-GENERATED CONTENT (if applicable)
Report content: long-press any post > Report. Block user: profile > ⋯ > Block.
Content is screened by <automated filter> and reviewed by a human within 24 hours.
Our EULA with the zero-tolerance clause for objectionable content is at <URL>.

OTHER
Backend is production and will remain available throughout review.
Contact for questions during review: <name, email, phone>.
```

For Google Play, put the equivalent credentials in **App content → App access** ("All or some functionality is restricted") with one instruction row per gated area, and attach demo videos to any sensitive-permission declaration.

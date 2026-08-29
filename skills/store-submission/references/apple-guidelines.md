# Apple App Review Guidelines: The Sections That Cause Rejections

Verified 29 August 2026. Guideline numbering, SDK floors, deadlines and asset specs change — verify against [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) and the [Play policy centre](https://support.google.com/googleplay/android-developer/topic/9858052) before submitting.


## 2.1 App Completeness

**Rule.** Final build only: no placeholder text, empty websites, temporary content or broken URLs. Backends live for the whole review window. If login is required, supply a demo account or a pre-approved demo mode. 2.1(b) extends this to every IAP.

**Reviewer.** Opens the app on a physical device, taps through from cold start, tries to reach every feature the metadata describes, pastes your credentials. A failed login, permanent spinner or 404 stops review with "2.1 – Information Needed".

**Fix.** A review account that never expires, has no rate limit and no 2FA/OTP (or a disclosed static bypass), pre-seeded so no reachable screen is empty. Verify from a clean device the day you submit; point the build at production, not staging.


## 2.3 Accurate Metadata

| # | Rule | Reviewer check / preemptive fix |
|---|---|---|
| 2.3.1(a) | New functionality described *with specificity* in Notes for Review; generic descriptions rejected | List every feature by name with its tap-path |
| 2.3.2 | IAPs visible in description, screenshots, previews | Any paywall shown must be disclosed |
| 2.3.3 | Screenshots show the app **in use** — not splash, login or title art | Capture populated post-login screens; overlays allowed |
| 2.3.4 | Previews are screen captures of the app; narration/overlays fine, b-roll not | See `assets.md` |
| 2.3.7 | Name ≤30 chars, unique; no prices, irrelevant or trademarked terms | Stuffing is caught by automated scanning |
| 2.3.8 | Metadata 4+ appropriate regardless of rating | "For Kids" reserved for the Kids Category |
| **2.3.10** | **Do not promote other mobile platforms** | The most common self-inflicted rejection: "Android", "Google Play", "web version" in description, release notes, screenshots or in-app copy; Play badges; Android device frames. Grep listing copy, screenshot sources and app strings |
| 2.3.12 | "What's New" describes real changes | Generic text only for bug-fix-only releases |


## 3.1.1 In-App Purchase

**Rule.** Unlocking any feature, content, subscription, currency or level requires StoreKit; license keys, QR codes, website-redeemed promo codes and crypto wallets are prohibited. IAP credits **may not expire** and must be restorable. Since the May 2025 Epic anti-steering injunction, **US storefront apps may include external purchase links with no entitlement or commission** ([summary](https://mjtsai.com/blog/2025/05/02/app-review-guidelines-updated-for-epic-anti-steering/)); elsewhere link-outs still need the External Purchase Link entitlement.

**Reviewer / fix.** The reviewer buys in sandbox, hunts for links routing to web checkout, looks for Restore Purchases, and checks a purchase survives reinstall. Route every digital unlock through StoreKit (RevenueCat, `expo-in-app-purchases`); add **Restore Purchases** reachable *without logging in*; strip "manage your subscription on our website" copy outside the US. If you sell physical goods or real-world services, say so in the notes — reviewers otherwise assume digital (3.1.3(e)/3.1.5).


## 3.1.2 Subscriptions

**Rule.** Auto-renewables must deliver ongoing value, last **≥7 days**, work on all the user's devices, and (3.1.2(c)) describe what the user gets and for what price before purchase. Don't remove functionality existing users already paid for.

**Reviewer / fix.** The reviewer looks for six things on the paywall screen: title, period length, price per period, what's included, Terms of Use (EULA) link, Privacy Policy link. Missing Terms/Privacy links is a routine rejection. Use Apple's standard EULA (`https://www.apple.com/legal/internet-services/itunes/dev/stdeula/`) if you have none, and set it in App Store Connect's License Agreement field. Verify an iPhone purchase unlocks on iPad.


## 4.2 Minimum Functionality

**Rule.** Must elevate beyond a repackaged website with lasting entertainment value or adequate utility. 4.2.2 rejects apps that are primarily marketing material, ads, web clippings, aggregators or link collections; 4.2.3(i) requires standalone operation; 4.2.6 rejects template/app-generator output unless submitted by the content provider.

**Reviewer / fix.** Reviewers judge whether the app is meaningfully more than your website in a WebView; single-`WebView` Expo wrappers are the highest-risk category on the store. Ship real native surfaces — push, offline caching, camera/photos, share sheet, biometrics, widgets, native navigation — then name them and their locations in the review notes.


## 4.7 Mini Apps, HTML5, Chatbots, Plug-ins

**Rule.** You are responsible for all embedded third-party software: follow 5.1 privacy rules, include filtering/reporting/blocking, use IAP for digital goods (3.1), don't expose native APIs without permission (4.7.2), don't share data or permissions with individual mini-apps without per-instance consent (4.7.3), provide a software index with universal links (4.7.4), and gate by declared or verified age (4.7.5). Applies to any app rendering remote JS or embedding chatbot widgets: keep an index endpoint, gate by Declared Age Range, never silently pass camera/location permission to embedded content.


## 4.8 Login Services

**Rule.** If a third-party or social login (Google, Facebook, X, LinkedIn, Amazon, WeChat…) is the **primary** account setup, you must also offer an equivalent alternative that (1) limits collection to name and email, (2) offers a **private/relay email** option at signup, and (3) does not track interactions for advertising without consent.

**Not required if:** you use only your own account system; you're an alternative marketplace; you're an education/enterprise/business app using pre-existing institutional credentials; you use a government or industry-backed citizen ID; or the app is a client for a specific third-party service users sign into directly.

**Reviewer / fix.** Reviewers count the buttons on your sign-in screen; a social button plus plain email/password with no relay option can still fail. Add `expo-apple-authentication`, shown at least as prominently — it satisfies all three conditions. Persist the user's name on *first* authorization; Apple returns it only once.


## 5.1.1 Data Collection and Storage

- **(i)** Privacy policy linked in App Store Connect metadata **and** inside the app; states what is collected and why, confirms third parties give equal protection, explains retention, deletion and consent revocation.
- **(ii)** Consent before collection, including "anonymous" analytics; purpose strings fully describe the use. **Paid functionality may not be conditioned on data access.** **(iv)** Never trick or force consent; the app stays usable when a permission is denied (manual address entry instead of Location).
- **(iii)** Data minimisation — prefer out-of-process pickers and share sheets over full-library access. **(x)** Basic contact info only if optional and not a condition of using features.
- **(v)** No significant account-based features → users must be able to use the app **without an account**. Offer account creation → you must offer **in-app account deletion**, not deactivation and not an email to support. Personal info only where core-functionality-relevant or legally mandated; social graph access is explicitly not core functionality. Users must be able to revoke social credentials in-app; don't store social tokens off-device.

**Reviewer.** Creates an account, hunts Settings for a delete path, expects the account gone. Checks whether a login wall blocks a browsing-only feature. Denies each permission and keeps going.

**Fix.** Settings → Account → Delete Account → typed confirmation → server-side purge, ≤3 taps, path stated in the notes. Add guest/browse mode if content is viewable without identity. Test with every permission denied.


## 5.1.2 Data Use and Sharing / ATT

**Rule.** No sharing personal data without permission; sharing with third parties — **including third-party AI services** — must be disclosed and consented. Tracking across apps/sites owned by other companies, and any IDFA access, needs **AppTrackingTransparency** permission. You may **not** require push, location or tracking to be enabled to access functionality, content or compensation (gift cards, codes).

**Reviewer / fix.** Reviewers cross-reference your Privacy Nutrition Label against runtime behaviour: label says "Data Used to Track You" but no ATT prompt appears → 5.1.2, or a 2.1 asking where it is. Call `requestTrackingPermissionsAsync()` (`expo-tracking-transparency`) after a neutral explainer with a genuine decline, before any IDFA read or attribution SDK init. If you don't track, align the label and delete the ATT usage string. Disclose LLM data flows in policy and label.


## 1.2 User-Generated Content

**Rule.** UGC and social apps must include **all four**: (a) filtering of objectionable material before posting, (b) a report mechanism with timely responses, (c) blocking of abusive users, (d) published contact information. Apps used primarily for pornography, random/anonymous chat, objectification of real people, threats or bullying are removed without notice.

**Reviewer / fix.** Reviewers long-press a post looking for Report and open a profile looking for Block; either missing is an immediate rejection. Ship report (with reason picker), block, mute, an EULA with a zero-tolerance clause, and a stated **24-hour** moderation SLA, with report/block in the post overflow menu and on the profile. Describe the moderation pipeline in the notes; this applies to AI-generated surfaces too.


## 2.5 Software Requirements

| # | Rule | Reviewer check / preemptive fix |
|---|---|---|
| 2.5.1 | Public APIs only; runs on the currently shipping OS | Static analysis at upload; audit native deps for private selectors |
| 2.5.2 | Self-contained bundle; **may not download code that changes app features** | The OTA boundary |
| 2.5.4 | Background modes only for their declared purpose (VoIP, audio, location, task completion) | Reviewer compares `UIBackgroundModes` to behaviour; remove unused modes |
| 2.5.5 | Must work on **IPv6-only** networks | Apple's review network is IPv6-only. Remove IPv4 literals; test over NAT64 |
| 2.5.13 / 2.5.14 | Face recognition via LocalAuthentication, alternate path for under-13s; recording needs consent **and** a visible/audible indicator | |
| 2.5.18 | Ads in the main binary only (not widgets, extensions, App Clips, notifications); must suit the age rating; interstitials need large close buttons; users must be able to report ads | Reviewers tap the close button — a 12pt corner X fails |

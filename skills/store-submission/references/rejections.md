# Common Rejections, Ranked — and How to Answer Them

Verified 29 August 2026. Guideline numbering, SDK floors, deadlines and asset specs change — verify against [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) and the [Play policy centre](https://support.google.com/googleplay/android-developer/topic/9858052) before submitting.

Ordering reflects observed frequency for small-team Expo/React Native submissions. **[UNVERIFIED: neither store publishes per-guideline rejection statistics; the ranking is judgement. The guideline numbers, triggers and fixes are verified.]** Binary vs metadata determines turnaround: a metadata-only fix is edited in App Store Connect and re-reviewed with no rebuild; a binary fix costs a full build + upload + review cycle.


## 1. Guideline 2.1 — Information Needed / App Completeness

**Triggered by:** demo credentials that don't work, expired or 2FA-gated review accounts, a backend that was down or rate-limited, a feature the reviewer couldn't find, vague review notes, or a nutrition label declaring tracking with no visible ATT prompt.

**Fix:** verify credentials from a clean install the same day; disable 2FA or supply a static bypass; rewrite notes with the literal tap-path to each feature; attach a screen recording.

**Cost:** usually **metadata-only** — reply in Resolution Center and the same build is re-reviewed. Binary only if a feature genuinely doesn't work.

## 2. Guideline 5.1.1(v) — Account deletion

**Triggered by:** no in-app deletion path; a "Delete Account" that only deactivates or logs out; deletion requiring an email to support; the path buried too deep.

**Fix:** Settings → Account → Delete Account → typed confirmation → server-side purge; state the path in the review notes. On Play, also supply the web deletion URL naming your app.

**Cost:** **new binary.**

## 3. Guideline 4.2 — Minimum Functionality

**Triggered by:** a thin WebView wrapper; an app that is essentially the website; mostly links, feeds or marketing material (4.2.2); requiring a companion app (4.2.3(i)); template/generator output (4.2.6).

**Fix:** add genuine native capability — push, offline cache, camera/photos, share sheet, biometrics, widgets, native navigation — then list those features and where to find them. Appeals on 4.2 rarely succeed without a product change.

**Cost:** **new binary**, usually substantial. Prevent this one; don't plan to fix it.

## 4. Guideline 3.1.1 — In-App Purchase

**Triggered by:** a digital unlock routed to web checkout (outside the US-storefront exception from the May 2025 anti-steering ruling); license-key or promo-code redemption for digital content; missing Restore Purchases; expiring IAP credits; a "manage your plan on our site" link.

**Fix:** move every digital unlock to StoreKit; add Restore Purchases reachable without login; remove out-links in non-US storefronts or get the External Purchase Link entitlement.

**Cost:** **new binary.**

## 5. Guideline 2.3.3 / 2.3.10 — Metadata

**Triggered by:** screenshots of the splash or login screen; Android device frames; a Play badge; "Android", "Google Play" or "web version" in the description, release notes, screenshots or in-app copy.

**Fix:** re-capture in-use screenshots at 1320 × 2868; grep every listing and app string for platform names.

**Cost:** **metadata-only** if the offending text is in the listing; **new binary** if it's in-app copy.

## 6. Guideline 5.1.1(i)/(ii) — Privacy policy and purpose strings

**Triggered by:** privacy policy in App Store Connect but not in the app; a policy silent on retention/deletion/third parties; generic `NS*UsageDescription` strings; a permission string for a permission you never request.

**Fix:** add an in-app Privacy link; rewrite each purpose string to name the feature and use ("Photos are used only to attach an image to a support ticket"); delete strings for unused permissions injected by config plugins.

**Cost:** **new binary** for strings; **metadata-only** if only the ASC URL was wrong.

## 7. Guideline 4.8 — Login Services

**Triggered by:** Google/Facebook/X sign-in as the primary auth without an equivalent alternative offering a private-email option.

**Fix:** add `expo-apple-authentication` and show Sign in with Apple at least as prominently. Remember Apple returns the user's name only on first authorization — persist it then.

**Cost:** **new binary.**

## 8. Guideline 5.1.2 — Data use / ATT

**Triggered by:** reading the IDFA or initialising an attribution SDK before the ATT prompt; a label declaring tracking while no prompt appears; a pre-permission screen whose only option is "Allow"; gating content or rewards on enabling push/location/tracking.

**Fix:** call `requestTrackingPermissionsAsync()` after a neutral explainer with a real decline, before any tracking SDK init; align the label to reality; remove "enable notifications to unlock" mechanics.

**Cost:** **new binary** (label edits alone are metadata, but the mismatch usually needs code).

## 9. Guideline 1.2 — User-Generated Content

**Triggered by:** a social/UGC/AI-content app without in-app report, block, a content filter, an EULA with a zero-tolerance clause, or published contact info.

**Fix:** ship all four, put report on the post overflow menu and block on the profile, state a 24-hour moderation SLA in the review notes.

**Cost:** **new binary.**

## 10. Guideline 3.1.2(c) — Subscription disclosure

**Triggered by:** a paywall missing price-per-period, subscription length, what's included, or the Terms/Privacy links.

**Fix:** put all six elements on the paywall screen itself; add Apple's standard EULA URL to App Store Connect's License Agreement field.

**Cost:** **new binary.**

## 11. Technical: upload and runtime

| Symptom | Guideline / code | Fix | Cost |
|---|---|---|---|
| `ITMS-90725` SDK version issue | Xcode 26 / iOS 26 SDK floor, since **28 April 2026** | Upgrade Expo SDK + EAS build image | binary |
| `ITMS-91053` missing API declaration | Privacy manifest, since **1 May 2024** | Add required-reason entries, including those hoisted from static pods | binary |
| Crash on launch on the reviewer's device | 2.1 | Test the release build on the oldest supported OS on a physical device | binary |
| Fails on reviewer's network | 2.5.5 IPv6-only | Remove IPv4 literals; test over NAT64 | binary |
| Build stuck "Missing Compliance" | export compliance | Set `ios.config.usesNonExemptEncryption` | binary (or answer the ASC questionnaire once) |

## 12. Google Play equivalents

| Rejection | Trigger | Fix | Cost |
|---|---|---|---|
| Invalid Data safety form | Form contradicts the SDK inventory in the AAB | Re-declare per SDK using each vendor's published mapping | metadata-only |
| Account deletion URL invalid | Page 404s, is behind login, or doesn't name the app | Publish a dedicated page naming the app with a visible deletion path | metadata-only |
| Permission declaration missing | `READ_MEDIA_*`, background location, all-files, `QUERY_ALL_PACKAGES`, foreground service type | Submit the declaration + demo video, or switch to the Android Photo Picker / scoped storage | metadata-only if the permission is justified; binary if you must remove it |
| Target API level | Below API 36 after **31 Aug 2026** | Rebuild at `targetSdkVersion: 36` | binary |
| Deceptive behaviour / OTA | Undisclosed behaviour change delivered over the air | Ship the change in a store build | binary |


## Resolution Center etiquette (Apple)

The Resolution Center thread is attached to the submission; replying re-opens review on the **same build**. You only need a new binary if the fix is in code.

1. **Read the citation, not the summary.** The message names guideline numbers; address each separately, in order, with a heading per number.
2. **Reply once, completely.** Each round trip adds a review cycle. Put credentials, explanation and evidence in one reply.
3. **Attach evidence.** Screenshots and a short screen recording of the fixed flow are the fastest way to close a "we couldn't find X" rejection.
4. **Say whether a new build is coming.** "Metadata correction; please re-review build 142" versus "build 143 is uploading with the fix" tells the reviewer what to wait for.
5. **Be factual.** Don't argue precedent ("app X does this"), cite revenue impact, or ask for a call.
6. **If the reviewer misread the app**, show the disproof: "Account deletion is at Settings → Account → Delete Account; recording attached." Misreads are common and usually close on the first reply.
7. **If you cannot comply**, ask a narrow question: "Which of the three conditions in 4.8 does our email/password flow fail?" A narrow question gets a narrow answer.

## Appeals

If the rejection misapplies the guidelines rather than misunderstanding the app, escalate to the **App Review Board** via the appeal link in Resolution Center or App Store Connect. Use it when the cited guideline does not describe your app, the rejection contradicts a previously approved build with no relevant change, or you have clarified twice without progress. Submit a factual, numbered rebuttal with evidence. Do not appeal 4.2 or 1.2 without changing the app — those are judgement calls the board rarely overturns. A separate channel exists for **guideline change requests**; don't conflate it with an appeal.

## Expedited review

Request via the Apple Developer "Request an Expedited App Review" form. Legitimate grounds: a critical bug affecting shipped users, a security fix, or a time-sensitive event tied to a fixed external date. State the specific harm and date. Grants are discretionary and tracked against your account; repeated marginal requests reduce future grants. **[UNVERIFIED: current published review-time medians.]** Google Play has no expedite path — the mitigations are **staged rollout with a halt** and Play's policy appeal form.

## Phased release (Apple)

After approval you can ramp over **7 days**: 1% → 2% → 5% → 10% → 20% → 50% → 100% ([App Store Connect help](https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases/)). You may pause for up to **30 days total**, unlimited times, resuming where you left off, or hit **Release to All Users** at any point. Manual downloads always get the newest version, so phased release limits automatic-update exposure only. Pair it with crash monitoring and an EAS Update rollback path for the JS layer.

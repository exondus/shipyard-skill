# External Payments and Store Rules, by Region

Verified 29 August 2026. **This is the most volatile file in the skill.** App Store payment rules changed at least five times between January 2024 and August 2026 and are under active US litigation with a Supreme Court petition pending; the EU terms are scheduled to be replaced on 1 October 2026. Re-read the live guidelines and Apple/Google support pages before writing a single line of link-out code, and put the verification date in your PR description.

## One-paragraph answer

As of today: **in the United States you may put a real button in your iOS app that opens your own web checkout, with no entitlement and no Apple commission.** In the **EU** you may link out under an entitlement, paying a fee stack that changes on 1 October 2026. **Everywhere else, including South Africa, you may not** — no buttons, no links, no calls to action, not even copy saying "cheaper on our website". Google Play has made a parallel US change with fees phasing in from 1 October 2026.

## If your storefront does not allow link-outs (South Africa and most of the world)

Be blunt about what a web checkout is worth to you. **It earns nothing from app traffic**, because no app surface may point at it. Its only customers are people who arrive from channels outside the app: search, ads, your landing page, an email to existing users, a creator link, a referral. If those channels are not yet sending meaningful traffic, a web checkout converts approximately nobody, and **building it before launch is a misallocation** — it is days of Stripe/Paystack work, webhook plumbing, tax registration and a second entitlement source, bought for a funnel that does not exist yet.

The correct order for a ZA-based, mobile-first product: ship IAP through RevenueCat, launch, get non-app acquisition working, *then* add the web checkout when you can name the channel that will feed it. Keep the entitlement schema multi-source from day one (`entitlements.md`) so adding it later is an insert, not a migration — but do not build the checkout itself on spec. The exception that justifies building early: you are selling to a market where card-on-file IAP conversion is poor and a local rail (EFT, Capitec Pay, M-PESA) is the *only* way many users can pay at all — and even then the app still cannot mention it.

## United States — iOS

### Current guideline text

**3.1.1(a) — Link to Other Purchase Methods**:

> "Developers may apply for entitlements to provide a link in their app to a website the developer owns… **These entitlements are not required for developers to include buttons, external links, or other calls to action in their United States storefront apps.** … In all other storefronts, **except for the United States storefront, where this prohibition does not apply**, apps and their metadata may not include buttons, external links, or other calls to action that direct customers to purchasing mechanisms other than in-app purchase."

**3.1.3 — Other Purchase Methods**:

> "Apps in this section cannot, within the app, encourage users to use a purchasing method other than in-app purchase, **except for apps on the United States storefront** and as set forth in 3.1.1(a) and 3.1.3(a)."

**3.1.1** is otherwise unchanged: unlocking features, subscriptions, in-game currency, levels or premium content inside the app still requires IAP. The NFT clause carries the same US carve-out. Source: https://developer.apple.com/app-store/review/guidelines/

### Litigation timeline (dates matter — each one changed what was allowed)

| Date | Event |
|---|---|
| Sept 2021 | Original *Epic v. Apple* injunction. Apple complied narrowly: link entitlement + 27% commission. |
| **30 Apr 2025** | N.D. Cal. finds Apple in **civil contempt**; bars any commission on link-outs plus scare screens and formatting rules, US storefront. |
| **1 May 2025** | Apple adds the US carve-out to the Review Guidelines. https://developer.apple.com/news/?id=9txfddzf |
| **11 Dec 2025** | Ninth Circuit (No. 25-2935) **upholds contempt** but **reverses the blanket commission ban**, remanding to set a lawful rate. https://law.justia.com/cases/federal/appellate-courts/ca9/25-2935/25-2935-2025-12-11.html |
| **29 Apr 2026** | Epic gets Apple's stay lifted; policy must change. |
| **4 / 21 May 2026** | Apple seeks a SCOTUS stay, then certiorari on contempt and injunction scope. https://9to5mac.com/2026/05/21/apple-seeks-supreme-court-review-of-contempt-finding-and-injunction-scope-in-epic-games-case/ |
| **12 Aug 2026** | Justice Kagan grants a short **administrative stay**. https://9to5mac.com/2026/08/12/apple-wins-temporary-supreme-court-pause-in-epic-games-proceedings/ |
| **13 Aug 2026** | Apple files its **proposed** link-out commission schedule; Epic opposes anything above 0%. https://9to5mac.com/2026/08/13/apple-proposes-commissions-of-up-to-15-for-off-app-store-purchases-in-the-us/ |

### Apple's proposed US link-out commission — **not in force**

| Tier | Proposed rate |
|---|---|
| Standard apps (those on 30% IAP) | **15%** |
| Video / News / Mini Apps Partner Programs, and subscription **renewals** | **10%** |
| Small Business Program members | **5%** |

Status 29 Aug 2026: **proposed only**, filed under court order, contested by Epic, subject to the pending SCOTUS application. Apple's filing concedes that under the Ninth Circuit's "necessary costs" definition the rate would be 0%. https://appleinsider.com/articles/26/08/13/apples-latest-commission-rates-for-external-app-store-purchases-havent-satisfied-epic

**Engineering implication:** the US link-out is free today, but assume a 5–15% commission and transaction reporting will arrive. Do not price the web checkout at exactly `IAP price minus 30%` — keep it a configurable value, not a constant, or the margin inverts overnight.

### What you may actually ship in the US today

Allowed: a button, a link, a QR code, a call to action, arbitrary placement and styling, your own landing page, your own price. Apple's scare-sheet and single-static-URL rules were the specific things held in contempt.

Still prohibited regardless of storefront: misleading marketing, scams, or fraud in connection with a link ("your app will be removed from the App Store and you may be removed from the Apple Developer Program").

This is a *storefront* carve-out, not an account-level one, and your binary is global. **Gate the CTA on `SKStorefront.countryCode` (`'USA'`), not on locale or IP** — locale is user-changeable and wrong for expats. [UNVERIFIED — confirm the current Expo/RN surface for reading it; RevenueCat also exposes storefront data.] Showing the CTA in ZA or JP is a 3.1.1(a)/3.1.3 rejection and, repeated, a program-removal risk.

## European Union — iOS

Link-out is permitted under the **StoreKit External Purchase Link (EU) Entitlement** or the Alternative Terms Addendum. Links may be actionable (tappable/clickable/scannable), carry parameters and redirects, target your site, another app or an alternative marketplace, and render in-app via web view or native UI — but an **actionable** link requires `ExternalPurchaseCustomLink.showNotice()` to display the system disclosure. https://developer.apple.com/support/communication-and-promotion-of-offers-on-the-app-store-in-the-eu/

### Current EU fee stack (in force until 30 Sept 2026)

**StoreKit External Purchase Link (EU) Entitlement Addendum** — Initial Acquisition Fee 2% (0% SBP) + Store Services Fee 5% (Tier 1) or 13% / 10% SBP (Tier 2) + Core Technology Commission 5%. The **Alternative Terms Addendum** swaps the CTC for the **Core Technology Fee, €0.50 per first annual install** above the threshold.

Windows: initial acquisition fee within 6 months of first install; store services and CTC within 12 months of the most recent install/update/reinstall. Neither applies to auto-renewals begun before you adopted the entitlement, nor to out-of-app transactions with no actionable link.

### Scheduled change — 1 October 2026

Apple replaces the above with unified EU terms:

| Channel | Standard | Reduced (SBP, partner programs, subs after year 1) |
|---|---|---|
| Apple IAP | 26% | 15% |
| Alternative payment processing **in-app** | 20% | 10% |
| **Store services commission on out-of-app offers** | 15% | 10% |

The store services commission on link-outs applies to sales **within 7 days of the link tap**. Initial Acquisition Fee and Core Technology Commission are not named in the new structure. https://developer.apple.com/support/payment-options-on-the-app-store-in-the-eu/

[UNVERIFIED] Whether CTF/CTC survive in any form, and whether the 1 Oct 2026 date holds — DMA deadlines have slipped before. Check that page before building EU fee logic.

## Rest of world, including South Africa

**No link-outs. None.** 3.1.1(a) and 3.1.3 prohibit buttons, external links and calls to action in every storefront other than the US (and the EU / reader / music-streaming entitlement carve-outs). For a ZA-based developer this is the operative rule at home: a ZA user on the ZA storefront must be sold through IAP, full stop.

What you *may* still do everywhere:

- Sell on the web to users who arrive via the web. The prohibition is on in-app steering, not on having a website.
- Email your existing user base about web pricing. 3.1.3: "Developers can send communications outside of the app to their user base about purchasing methods other than in-app purchase."
- Honour a web-purchased subscription inside the app under **3.1.3(b) Multiplatform Services** — content and subscriptions acquired elsewhere may be accessed in-app, *provided those items are also available as in-app purchases within the app*. This is the legal basis for the cross-platform entitlement architecture: web checkout exists, IAP also exists, the app never points at the web one.
- **3.1.3(f) Free Stand-alone Apps**: a free companion to a paid web tool needs no IAP — but only if there is *no purchasing inside the app and no call to action for purchase outside it*. Viable for a B2B tool; not for a consumer app with a paywall.
- Physical goods and real-world services (3.1.3(e)) must *not* use IAP. Person-to-person real-time services (3.1.3(d)) may use other payment methods.

## Google Play

**United States.** Since **9 Dec 2025**, following the Epic settlement, "Google will not require the use of Google Play Billing in apps distributed on the Google Play Store, or prohibit the use of in-app payment methods other than Google Play Billing." Three pathways: the Payments Policy, the Alternative Billing Program, and the External Content Links Program. https://support.google.com/googleplay/android-developer/answer/15582165

**From 1 October 2026**, developers enrolled in the external-links and alternative-billing programs must report transactions and successful downloads and pay applicable service fees. [UNVERIFIED] Those percentages are not published as of 29 Aug 2026 — verify before modelling margin.

Easy to miss: Google began sharing Play listings with third-party Android app stores on **22 July 2026** unless the developer opted out by that date.

**Outside the US**, Play Billing remains required for digital goods, with the existing user-choice-billing pilots (Korea, EEA, India, Japan, Brazil, others). [UNVERIFIED — list changes; check Play Console policy.]

## Decision table

| Storefront | In-app IAP | In-app link-out CTA | Web checkout honoured in-app |
|---|---|---|---|
| US (iOS) | Required for in-app unlocks | **Yes, free today**, commission likely 5–15% soon | Yes (3.1.3(b)) |
| EU (iOS) | Yes | Yes, under entitlement, fee stack applies; changes 1 Oct 2026 | Yes |
| ZA / UK / JP / AU / rest (iOS) | **Required** | **No** | Yes, silently |
| US (Android) | Optional since 9 Dec 2025 | Yes | Yes |
| Rest (Android) | Required | Generally no | Yes |

Implement one flag, `link_out_allowed(storefront, platform)`, fed by remote config you can flip without an app release. When the SCOTUS ruling lands or the EU terms turn over on 1 Oct 2026, that flag should be the only thing you need to change.

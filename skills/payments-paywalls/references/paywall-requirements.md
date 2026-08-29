# Paywall Requirements and Conversion Evidence

Verified 29 August 2026. The disclosure rules under Guideline 3.1.2 are stable, but reviewer strictness fluctuates and the conversion benchmarks are from RevenueCat's 2026 report (2025 data) — re-check both before treating any figure as current.

## Mandatory disclosures — App Store Review Guideline 3.1.2

Guideline 3.1.2(c) *Subscription Information* says: "Before asking a customer to subscribe, you should clearly describe what the user will get for the price. Ensure you clearly communicate the requirements described in **Schedule 2 of the Apple Developer Program License Agreement**." https://developer.apple.com/app-store/review/guidelines/

In practice, reviewers check for all of the following **on the screen carrying the purchase button**, visible without scrolling or tapping:

| # | Element | Detail |
|---|---|---|
| 1 | Subscription **name** | e.g. "Pro Annual" — must match the App Store Connect product name |
| 2 | **Duration** of a subscription period | "1 year", "1 month" — not just "annual plan" |
| 3 | **Price** and the **units it bills in** | "$59.99 / year". If you display a derived figure ("$4.99/mo"), the actual billed amount and period must also be visible |
| 4 | **Trial** length and **post-trial price** | "7 days free, then $59.99/year" |
| 5 | **Terms of Use (EULA)** link | Must open **in-app**. Apple's standard EULA URL is acceptable |
| 6 | **Privacy Policy** link | Must open **in-app** |
| 7 | **Restore Purchases** control | Visible on the paywall, not buried in settings |

Also enforced by 3.1.2(a): the subscription period must be **at least 7 days**, must work on **all the user's devices**, and must deliver **ongoing value** — a one-off unlock sold as a subscription is rejected under "ongoing value", as is a subscription gating content the user already paid for.

Google Play's equivalent (Subscriptions / Deceptive Behavior policies) requires the same price, period, trial terms and cancellation instructions before purchase. Satisfy Apple and you satisfy Play, plus a clear path to cancel.

## Ranked rejection causes and their fixes

Ordered by how often they appear in practice. Sources: https://revenueflo.com/blog/common-ios-paywall-rejections-and-the-fixes-that-work and https://www.revenuecat.com/blog/growth/the-ultimate-guide-to-app-store-rejections

**1. Terms of Use / Privacy Policy links missing or not in-app** — *Guideline 3.1.2*
Symptom: rejection says the links are missing even though they exist on your site and in the App Store listing.
Fix: two tappable links on the paywall opening an in-app browser or native screen. App Store Connect metadata and your marketing site do **not** count. Developer forums are full of repeat rejections where the links exist but are low-contrast, below the fold, or inside a collapsed section — put them in the default viewport.

**2. Free-trial toggle that hides the real price** — *Guideline 3.1.2 / 3.1.2(c)*
Symptom: "the app's binary contains a subscription that does not clearly disclose the terms."
Fix: the toggle pattern is not banned, but the **default state must show price, period and post-trial price**. Do not reveal price only after the switch is flipped.

**3. Displayed price does not match the billed price** — *Guideline 3.1.2*
Symptom: rejected for showing "$4.99/month" on a SKU that charges $59.99 once a year.
Fix: show both. The per-month figure may be the visual hero; the billed figure must be legible in the same block.

**4. No Restore Purchases** — *Guideline 3.1.1 / 3.1.2*
Symptom: "we were unable to restore previously purchased content."
Fix: a Restore control on the paywall calling `Purchases.restorePurchases()`, plus one in settings. Handle "nothing to restore" with a message, not a silent no-op — reviewers test it on a fresh account.

**5. Paywall blocks the reviewer entirely** — *Guideline 2.1 / 3.1.2*
Symptom: "we were unable to review your app because it requires a subscription."
Fix: supply a sandbox account that already holds the entitlement, and say so in App Review notes.

**6. "Free" applied to a paid trial, or exaggerated claims** — *Guideline 3.1.2(a) / 2.3*
Symptom: flagged as misleading. 3.1.2(a): apps that "trick users into purchasing a subscription under false pretenses… will be removed from the App Store and you may be removed from the Apple Developer Program."
Fix: only call it free if no charge occurs. Drop "guaranteed", "#1", unverifiable outcome claims.

**7. Dark-pattern close button** — *Guideline 3.1.2 / 4.0*
Symptom: reviewer cannot dismiss the paywall, or the X is invisible/delayed.
Fix: visible dismiss from the first frame on any soft paywall. A hard paywall may omit dismiss but must offer sign-in and restore.

**8. Steering to external payment outside the permitted storefronts** — *3.1.1(a) / 3.1.3*
Fix: gate the CTA on device storefront. See `store-rules.md` — US and (under entitlement) EU only.

**9. Subscription lacks ongoing value** — *Guideline 3.1.2(a)*
Symptom: a utility with a one-time output sold as a recurring plan.
Fix: reframe as a non-consumable unlock, or add recurring delivery (updates, content, sync).

## Conversion evidence

All figures from RevenueCat *State of Subscription Apps 2026* (115,000+ apps, ~$16B annual revenue), published 2026: https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026

| Question | Finding |
|---|---|
| Hard paywall vs freemium | **Day-35 conversion 10.7% median (hard) vs 2.1% (freemium)** — ~5×. **Day-60 revenue per install $3.09 vs $0.38** — ~8×. |
| Does the hard paywall churn worse? | No. Both models retain **~27–28%** of yearly subscribers at 12 months. |
| Trial length | **17–32 day trials: 42.5% median trial→paid. Under 4 days: 25.5%.** ~70% better. Yet **46.5% of apps ship trials ≤4 days**, up from 42.1% in 2025 — the market is moving the wrong way. |
| When do trial users quit? | **55.4% of all 3-day-trial cancellations happen on day 0**; **84% by day 1**. Day-0 was ~51% in 2025 and is worsening. |
| Annual churn shape | **~35% of annual cancellations occur in month 1**; **~72% of annual subscribers cancel within year 1** (up from ~56% in 2025). Months 2–11 run 3–10%. |
| Involuntary churn | Billing failures cause **31% of Google Play cancellations vs 14% on the App Store** (Play worsened from 28.2% in 2025). |
| Category effect | AI apps show **41% higher year-1 realised LTV** ($30.16 vs $21.37 median) but AI monthly plans retain **36% worse** over 12 months. |

Reading the numbers into decisions:

- **Hard paywall after onboarding is the default** for a consumer subscription app, not freemium — 5× conversion at equal retention.
- **Day-0 activation is the single highest-leverage surface.** Get the user to the value moment inside the first session, and send the trial-reminder push before hour 24, not at hour 60.
- **Dunning matters more on Android** than iOS by roughly 2×.

### Trial length: ship 7 days

**Default to a 7-day free trial.** Do not treat this as a range to tune before launch; pick 7, ship, then test.

The store floors, which are two different numbers and are routinely conflated:

| Floor | Value |
|---|---|
| Minimum **subscription period** — Guideline 3.1.2(a): "the subscription period must last at least seven days" | **7 days** |
| Minimum **introductory free trial** (an introductory offer on that subscription, configured in App Store Connect) | **3 days** |

So a 3-day free trial is entirely legal on both stores; 7 days is a product decision, not a compliance one. [UNVERIFIED — App Store Connect's selectable introductory-offer durations (3 days, 1/2 weeks, 1/2/3/6 months, 1 year) and Google Play's 3-day floor; confirm in the consoles before configuring.]

Why 7 and not 3: trials of 17–32 days convert to paid at **42.5%** median versus **25.5%** under 4 days — roughly 70% better — while **46.5% of apps now ship trials of ≤4 days**, up from 42.1% in 2025. **The near-ubiquitous 3-day trial is the worst-supported choice in the data and is getting more common anyway.** 7 days is the defensible default: it clears the sub-4-day cliff, it gives the user a weekend inside the window, and it is short enough that the annual charge still lands while intent is warm.

The 17–32 day figures are the reason to **test longer**, not the reason to launch at 30. Run 7 as the control and 14 or 30 as the variant in RevenueCat Experiments once you have volume. If a business constraint forces 3 days, accept that **55.4% of those cancellations land on day 0** and treat the first session as the entire funnel.

### Multi-page paywalls

RevenueCat's aggregate does not isolate multi-page versus single-screen layouts, and I found no defensible 2026 figure for it or for price-anchoring lift specifically. Treat "multi-page paywalls convert better" as **one vendor's aggregate worth testing, not established** — the report's own framing is that paywall *model* (hard vs soft) and *trial length* dominate layout effects. Test it with Experiments; don't assume it.

**The hard rule that resolves this regardless of which layout wins:** whichever page carries the purchase CTA must carry **every** required disclosure from the table above, visible without scrolling or tapping. A value-recap first page with the price on page three is the single most common 3.1.2 rejection — the reviewer sees a "Continue" button with no price attached and stops there. If you run a multi-step flow, the disclosure block travels with the button, on every step that can start a transaction.

## The safe pattern

A single paywall screen that satisfies 3.1.2 and reflects the evidence:

```
┌──────────────────────────────────────────────┐
│  ✕                              Restore      │  ← dismiss (soft) + Restore, both visible
│                                              │
│         [ value moment / 3 benefit lines ]   │  ← shown AFTER onboarding's payoff
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ ● Annual        BEST VALUE  Save 62%   │  │  ← default-selected; anchor
│  │   $59.99/year  ·  just $4.99/month     │  │  ← billed amount AND derived rate
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │ ○ Weekly            $2.99/week         │  │  ← the anchor, not the pitch
│  └────────────────────────────────────────┘  │
│                                              │
│  7 days free, then $59.99/year. Cancel       │  ← trial length + post-trial price,
│  anytime in Settings.                        │     in the DEFAULT state
│                                              │
│        [   Start 7-day free trial   ]        │
│                                              │
│    Terms of Use   ·   Privacy Policy         │  ← in-app links, above the fold
└──────────────────────────────────────────────┘
```

Rules encoded in that layout:

1. Every 3.1.2 element is on one screen in the default state — nothing behind a toggle, a scroll or a tap.
2. Weekly exists to make annual look cheap; annual is pre-selected. Per-week/per-month framing appears **alongside** the billed total, never instead of it.
3. **Trial is 7 days** — settled above, not a range to pick from at build time.
4. Restore and dismiss are both reachable in the first frame.
5. Ship the whole thing as a **RevenueCat Paywalls v2** template so copy, price emphasis and trial length are remote-configurable and A/B-testable without an app release — and so a rejection is fixable in minutes rather than a review cycle.
6. Gate any "subscribe on the web" CTA on storefront (`store-rules.md`). Never render it by default.

Before submitting: run through the seven mandatory elements as a literal checklist against a screenshot, on the smallest supported device, in the largest Dynamic Type setting. Most 3.1.2 rejections are elements that exist but fall below the fold at accessibility text sizes.

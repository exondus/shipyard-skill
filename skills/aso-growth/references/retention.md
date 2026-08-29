# Ratings, Reviews and Retention

Verified August 2026. Store field limits, ranking behaviour, benchmarks and tool pricing change — verify before acting on numbers here.

## Retention benchmarks

From AppsFlyer *State of App Marketing 2025*, Adjust *Mobile App Trends 2026* and data.ai *State of Mobile 2026*, compiled by [UXCam](https://uxcam.com/blog/mobile-app-retention-benchmarks/) (updated April 2026).

**Strong performers — approximately 75th percentile, not averages:**

| Category | D1 % | D7 % | D30 % |
|---|---|---|---|
| Overall | 30–40 | 10–15 | 5–8 |
| Social | 50–60 | 25–30 | 15–20 |
| Streaming & media | 45–55 | 20–28 | 10–15 |
| Productivity | 40–50 | 22–28 | 12–18 |
| Gaming | 40–50 | 12–18 | 5–8 |
| Fintech | 35–45 | 18–25 | 10–15 |
| Health & fitness | 35–45 | 15–22 | 8–12 |
| Ecommerce | 25–30 | 8–12 | 3–6 |

**Median across all categories: D1 25%, D7 8%, D30 4%.** Typical apps lose ~75% of installs within three days.


[UNVERIFIED] Second-hand aggregations of three vendor datasets with different "install" definitions, cohort windows and geographic mixes. The 75th-percentile framing means most apps sit well below.

**Do not treat these as targets.** Orientation only. Three failure modes: **comparing across definitions** (vendor A counts D1 as "opened within 24h of install", vendor B as "opened on calendar day 1", your analytics tool has a third — compare your app only to its own prior cohorts); **comparing across acquisition mix** (organic search installs retain far better than paid-social, so a blended number hides everything — always cohort by source); and **optimising the number instead of the product** (D1 is trivially inflatable with a day-one push or a forced tutorial; D30 is not — watch D7 and D30).

The only benchmark that matters operationally is your own trend across releases.

## In-app review prompts

### Apple

Verbatim from [Apple's StoreKit documentation](https://developer.apple.com/documentation/storekit/requestreviewaction):

> If the person hasn't rated or reviewed your app on this device, StoreKit displays the ratings and review request **a maximum of three times within a 365-day period**.
>
> If the person has rated or reviewed your app on this device, StoreKit displays the ratings and review request **if the app version is new, and if more than 365 days have passed** since the person's previous review.

Additional documented behaviour:

- **The prompt may not appear at all.** Apple: "Because this API may not present an alert, don't call it in response to a button tap or other user action." A user who taps "Rate us" and sees nothing concludes the app is broken.
- **Always fires in development builds** (so local testing says nothing about production frequency) and is a **no-op in TestFlight**.
- Use `AppStore.requestReview(in:)` or the SwiftUI `\.requestReview` environment action (iOS 16+); `SKStoreReviewController.requestReview()` is deprecated.
- You cannot read whether the user rated or whether the prompt showed. Any "did they rate?" logic is guessing.

### Google Play

The In-App Review API (`ReviewManager` / `launchReviewFlow`) is also quota-limited; Google does not publish the quota [UNVERIFIED — no documented number]. Policy states:

- **Must not be triggered by a button or any explicit user action.**
- **Must not be sentiment-gated** — you may not ask "do you like the app?" and route only happy users to the prompt. Both stores prohibit this; it is an enforcement risk, not just bad practice.
- No callback indicates whether the flow displayed or what the user did.

### Correct trigger moments

Fire **after a success the user caused**, never during friction: a task completed, a goal hit, a streak milestone, an export finished, a subscription first delivering value (not the purchase), on the third or later session after activation. Never during onboarding or before activation; after a crash, error, failed payment or permission denial; after a paywall dismissal; or on app launch.

Because you get roughly **three prompts per user per year**, gate the call behind your own check: `sessions >= 3 && activated && !erroredRecently && daysSinceLastPrompt >= 90`. Track your attempt count so the budget goes to the highest-signal moments.

### The user-initiated path

An explicit "Rate this app" button in Settings is legitimate — a link, not the API, so the button rule does not apply. Use Apple's documented persistent deep link:

```
https://apps.apple.com/app/id<YOUR_APP_ID>?action=write-review
```

`action=write-review` opens the App Store page with the review composer open. Play's equivalent is `.../details?id=<PACKAGE>&showAllReviews=true` [UNVERIFIED — Play's review deep-link parameters have changed historically].

## Review replies

Google states that **responding to a negative review increases that review's rating by an average of +0.7 stars** ([BrandBastion, summarising Google's guidance](https://blog.brandbastion.com/impact-of-replying-to-app-reviews/)). Appbot data in the same piece shows ~18% of 1–2 star reviews get a reply versus ~9% of 4–5 star — effective and under-done.

Apple publishes no equivalent figure, and **any claim that replying directly boosts search ranking on either store is [UNVERIFIED]**. The reliable mechanism is indirect and sufficient: replies raise the visible star average, which drives conversion.

Reply rules: within 48 hours, name the specific problem back to the user, say what you will do and by when, follow up in the same thread when the fix ships. Never argue, never blame, never paste a template. Both stores let you edit a reply later.

## Bad-review recovery procedure

1. **Stop prompting immediately** — every prompt during a spiral spends your three-per-year budget on angry users. Disable the call behind a remote flag.
2. **Read them all and cluster.** Usually 80% of the damage traces to one or two causes: a crash on a specific OS/device, a bait-and-switch paywall, or data loss.
3. **Fix the top cause and ship.** Nothing else here works before this step.
4. **Reply to every negative review**, older ones included, naming the fix and version number.
5. **Re-enable prompting for the fixed cohort only** — users on the new build who hit the success moment after the fix, never users still on the broken version.
6. **Reset the rating, once.** App Store Connect lets you reset to the current version. One-shot lever: it discards good reviews too, so use it only after a genuine turnaround.
7. **Watch Android vitals on Play** — a crash spiral there is simultaneously a ranking demotion.

## Push notifications

### Opt-in figures

Median opt-in: **iOS ~51%** (range 29–73%), **Android ~81%** (49–95%). Android by industry: finance ~96%, education and medical ~94%. Reaction rates: Android ~4.6%, iOS ~3.4%. Source: [Business of Apps, citing Airship](https://www.businessofapps.com/marketplace/push-notifications/research/push-notifications-statistics/).

**[UNVERIFIED / STALE] This dataset is from H1 2021.** Five years of provisional authorisation and changed norms sit between it and now. Treat iOS ~51% as a *floor* for a well-primed app. Airship publishes a 2026 edition behind a form ([landing page](https://www.airship.com/resources/mobile-app-push-notification-benchmarks-2026/)) — get current numbers there before quoting any figure.

### Provisional authorisation

Request `UNAuthorizationOptions.provisional` (alongside `.alert`, `.badge`, `.sound`) and iOS grants delivery **with no permission prompt at all**. Notifications arrive quietly in Notification Center — no banner, no sound, no lock-screen alert — each carrying "Keep" / "Turn Off" controls, so the user decides on a real notification rather than an abstract prompt.

Why it is usually the right default: you cannot be denied at the moment of asking, because you do not ask; you cannot burn your one shot (a hard `requestAuthorization` denial is near-permanent, recoverable only by walking the user into Settings); and the user judges your actual notifications, not your promise. Trade-off: provisional notifications are quiet, so time-critical alerts do not interrupt. Go provisional first, then request full authorisation at a moment where the interruption is obviously valuable.

### Priming and content

If you use the hard prompt, prime it: an in-app screen explaining the specific value, offering "Not now" as a real non-punishing option, shown *only after* activation — never on first launch. Users who decline a primer never cost you a system-level denial.

Content: personal, timely, about the user's own data beats broadcast marketing on every metric. Cap frequency, respect quiet hours, deep-link every notification to the exact screen, and give in-app per-category toggles — a user who can turn off one category will not turn off all of them at OS level.

## Streaks and habit loops, done responsibly

Streaks work when they represent a habit the user chose to build. They are manipulative when the streak is the product rather than a measure of it.

Construct them responsibly: **track a real goal the user set**, not app-opening (a meditation streak counts sessions meditated, not launches); **ship streak freezes/repairs from day one**, since one missed day destroying a 90-day streak produces churn rather than motivation; **cap the guilt** at one reminder at a user-chosen time, no 11pm loss-framing push and no escalating badges; **let users pause** via vacation mode or a weekly target; **never gate core functionality on a streak**; and **no dark patterns** — no paid streak restores, no countdown timers, no shaming copy.

The honest test: if the user stopped wanting the underlying habit, would your mechanic help them leave gracefully? If it would trap them, it is not retention — it is deferred churn.

## Instrumentation

Minimum viable measurement:

| Metric | Definition to fix in writing |
|---|---|
| Activation | One precise event meaning "got the value" |
| Time-to-activation | Install → activation, median and p90 |
| D1 / D7 / D30 | Cohorted by install date **and** source |
| Paywall funnel | Paywall view → trial → paid conversion → renewal |
| Notification opt-in | By prompt variant and timing |

Tooling: **Firebase/GA4** (free, adequate funnels), **PostHog** or **Amplitude** free tiers, **TelemetryDeck** (privacy-first, no IDFA), **RevenueCat** (free below roughly $2.5k monthly tracked revenue — verify — with cohorted subscription retention built in). Pick one product-analytics tool and one revenue tool. Instrument activation **before launch**; retrofitting makes your early cohorts unmeasurable forever.

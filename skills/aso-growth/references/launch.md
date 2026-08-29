# Launch Playbook and Attribution

Verified August 2026. Store field limits, ranking behaviour, benchmarks and tool pricing change — verify before acting on numbers here.

## Countdown

Dates are relative to your public launch date. Pull everything earlier if App Review has ever surprised you.

### T-minus 10 weeks — Play closed testing (personal accounts: the real start date)

**For a solo developer on a personal Play Console account this is usually the binding constraint on the whole launch date**, and it is routinely discovered far too late. A **personal** account created after **13 November 2023** cannot ship to production until it has run a closed test with **12 testers continuously opted in for at least 14 days**, then applied for production and passed a review that usually takes **≤7 days** ([App testing requirements for new personal developer accounts](https://support.google.com/googleplay/android-developer/answer/14151465)).

The 14 days is measured on *continuous* opt-in — testers who join, poke around and leave do not count — so the path is recruitment (the slow part), 14 clean days, then the application. **Budget 3–4 weeks from a cold start**, and start at T-10 so a rejected application still leaves room for a second cycle. Use a Google Group as the tester list so membership is stable, and ship real updates during the 14 days so the application's feedback summary describes something real. Organisation accounts skip the 12-tester rule but need a D-U-N-S number with its own multi-week lead time. Full requirement and the production-application structure: `store-submission` → `references/play.md` §4.

### T-minus 8 weeks — foundations

Finalise keyword research (see `keywords.md`) — name and subtitle freeze here. Instrument the activation event and D1/D7/D30 cohorts **before any real user installs**; retrofitting leaves your launch cohort permanently unmeasurable. Reserve the app name in App Store Connect and the package name on Play. Secure the domain, your social handle, and a support email.

### T-minus 6 weeks — TestFlight opens

TestFlight limits: **100 internal testers**, **10,000 external testers**, **100 builds**, **30 devices per tester**. The **first external build must be approved by App Review**; later builds go to review automatically. A **public link** can be shared anywhere and can filter enrolment ([Apple](https://developer.apple.com/testflight/)).

Run it as a community, not a QA queue: use the public link as the CTA on your landing page and in build-in-public posts; put testers in a Discord; ship weekly. The review prompt API is a **no-op in TestFlight**.

Play's **internal** track runs in parallel for your own builds; the **closed** track should already be running from T-10.

### T-minus 5 weeks — pre-order decision

Set a release date **between 2 and 180 days in the future**. At release, "customers receive a notification, and the app automatically downloads to the device used for pre-ordering." Paid apps are not charged until release day. Unavailable for bundles and IAPs; once released in a region an app cannot return to pre-order there ([App Store Connect](https://www.developer.apple.com/help/app-store-connect/manage-your-apps-availability/publish-for-pre-order)).

Take the pre-order if you have any audience: accumulated pre-orders **land as a single-day install spike**, and install velocity is a ranking input on both stores. Play's equivalent is **pre-registration**, which also lets you target a custom store listing at pre-registered users.

### T-minus 4 weeks — assets and pages

Screenshots and captions finished (see `store-page.md`), frames 1–3 getting the design time. Custom Product Pages built, one per intent cluster, each with a unique keyword subset — they need App Review approval, so they go in now. Play Custom Store Listings too.

Press kit live at a stable URL (see `web.md`): app name; one-line and 50-word descriptions; 1024px icon; 5 screenshots; a 30-second video if you have one; founder name, photo, bio; store links; contact email; promo codes for reviewers; and a "what's genuinely new here" paragraph. One page, no gate.

### T-minus 3 weeks — featuring nomination (hard deadline)

Apple requires the featuring nomination at least **3 weeks before your planned publication date** ([App Store Connect](https://developer.apple.com/help/app-store-connect/manage-featuring-nominations/nominate-your-app-for-featuring/)) — a hard floor; Apple recommends earlier.

Pick one nomination type: **App Launch** (launch or pre-order of a new app), **App Enhancements** (new features or a significant update), or **New Content** (offers or events inside an existing app).

The form takes: a **nomination name**; a **description** (what the update is and why); a **publication date** (specific day or range, device timezone); **related apps**, up to **10**; **platforms**; **countries/regions** and **localizations**, pre-filled and editable; **In-App Events**, attached early; **supplemental materials**, up to **5 URLs**; and **helpful details** on accessibility or anything unique. Nominations save as editable drafts; **bulk CSV import submits immediately**.

What Apple's editors reward: **platform-native design**; **day-one adoption of new OS features** — the current release's APIs, widgets, Live Activities, App Intents, watchOS/visionOS support, the strongest signal and why launches timed to a new OS release get featured disproportionately; **accessibility** (VoiceOver, Dynamic Type, contrast — Apple asks explicitly, so state what you support); **a clear, specific story**; and **a firm date** with correct regional targeting.

No equivalent form exists for Play featuring; Play editorial runs on category performance, vitals, and (for larger developers) an account manager. Clean Android vitals is the accessible lever.

### T-minus 2 weeks — submit for review

Submit with **"manually release this version"** selected, so approval does not publish you early. Approval in hand two weeks out is the difference between a launch and a scramble. Prepare launch-day assets now: Product Hunt gallery and maker comment, Reddit draft, 3–5 videos scheduled, and the email to your TestFlight community.

### T-minus 1 week — warm-up

Tell the TestFlight community the date and ask them, once, to be around. Post the "shipping next week" content. Verify every press-kit and CPP deep link.

### Launch day

Release manually in the morning of your primary market. Then: email the beta list, post the Product Hunt launch, post to the one subreddit you have standing in, publish the video, and reply to every comment and review for 48 hours. Do not launch on more than two channels — thin attention across five produces five failures.

### T-plus 14 days

Wait two full weeks before judging keyword performance. Then read App Store Connect → App Analytics → *Search terms* and Play Console's acquisition reports, and begin the one-field-per-release loop.

## Realistic expectations

Say this plainly; the alternative is a developer who quits at day 30.

- **Most indie launches see double-digit day-one downloads.** A few hundred is a good day.
- **Product Hunt is not an acquisition channel.** A backlink and a spike; rarely sustained installs.
- **Featuring is not a plan.** It is a lottery you enter by submitting the form. Submit, then act as though it will not happen.
- **The compounding asset is ASO plus one content channel**, measured over 90 days, not 7.
- **Launch day is a data point, not a verdict.** D7/D30 retention tells you whether you have a product; day-one downloads tell you how many people you told.

## Channel notes

**Product Hunt.** Launch Tuesday–Thursday at 12:01am PT (the leaderboard resets then). Write the maker comment in advance — why you built it, not a feature list. Reply to every comment within minutes. **Do not ask for upvotes**; against the rules and detectable. Yield: a few hundred to a few thousand visits and a permanent backlink.

**Reddit.** Converts *only* if you have participated in the subreddit for months first. Read the rules — many subs ban self-promotion outright. Lead with the problem; put the link last or in a comment. A post that reads as an ad is removed within minutes and can get you banned. Yield: zero, or your best day ever, mostly a function of standing.

**Short-form video (TikTok / Reels / Shorts).** Highest-yield free channel for consumer apps in 2026. Formats that work: build-in-public, problem-demo (the annoying thing then the fix, under 15 seconds), founder talking-head. Post 3–5×/week. **Expect 20+ videos before one carries** — power-law distribution, and consistency is the only input you control. Point the link at a channel-specific CPP/CSL URL to measure it.

**Other:** an email list from a pre-launch landing page is the only audience you own (`web.md`).

## Zero-budget attribution stack

Framework status: **SKAdNetwork is not deprecated**, and **AdAttributionKit is fully interoperable with it**. AAK adds alternative-marketplace support (DMA), genuine **re-engagement** attribution, view-through and custom-creative types, universal-link deep linking, and a developer mode that removes postback randomisation ([Singular](https://www.singular.net/blog/adattributionkit-the-new-skadnetwork/)). Implement AAK if you implement either. Both only matter once you run paid ads.

The stack for someone spending nothing:

| Component | What it tells you | Cost |
|---|---|---|
| **AdServices** (`AAAttribution` token → Apple's Attribution API) | Deterministic Apple Ads attribution to campaign/keyword, independent of ATT consent | Free |
| **App Store campaign links** (`?pt=&ct=`) | Per-channel organic attribution, no SDK — see `web.md` | Free |
| **Play Install Referrer API** | Android referrer string; carries UTM parameters | Free |
| **App Store Connect → App Analytics source types** | Search / Browse / Web Referrer / App Referrer — is ASO or content working | Free |
| **Play Console acquisition reports** | Play's equivalent, plus search terms | Free |
| **Firebase/GA4, PostHog or TelemetryDeck** | In-app funnels, activation, retention cohorts | Free tier |
| **RevenueCat** | Subscription revenue cohorted by install date and source | Free below ~$2.5k MTR |

**The rule: do not build an MMP before you have paid acquisition.** AppsFlyer, Adjust and Branch solve cross-network paid attribution and deduplication. At zero paid spend they measure nothing the free stack does not, while costing money, adding an SDK and expanding your privacy-manifest surface.

The corollary: the free stack cannot tell you what *seeded* an "App Store Search" install. Accept the ambiguity — at indie scale the answer is almost always the content channel you are actively working; stop for two weeks and watch the trend.

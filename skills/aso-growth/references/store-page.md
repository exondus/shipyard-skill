# Store Page Conversion

Verified August 2026. Store field limits, ranking behaviour, benchmarks and tool pricing change — verify before acting on numbers here.

## First-impression anatomy

What a search-result visitor sees before any scroll or tap:

| Surface | Apple | Play |
|---|---|---|
| Icon | Always | Always |
| App name | 30 chars, truncates ~23 in results | 30 |
| Subtitle / short description | Subtitle, 30 chars | Short description, 80 chars |
| Above-fold media | ~2.5 portrait screenshots, or 1 landscape | Feature graphic + ~2 screenshots |
| Autoplaying media | App preview, muted, first slot | Promo video, tap-to-play |
| Rating | Star average + count | Star average + count |

Dwell data: median time on a product page is around **7 seconds**, and roughly **half of visitors never scroll past the second image** ([Screenhance](https://screenhance.com/blog/state-of-app-store-screenshots-2026)) [UNVERIFIED — vendor aggregate, methodology not published].

The rule that follows: **screenshots 1–3 do essentially all the work.** Frames 4–10 are read by a small, already-converting minority. Do not spend design time evenly across ten frames.

Reported lift from a strong screenshot set is ~20–35% install conversion, with video adding a further 16–35% where it fits [UNVERIFIED — vendor aggregate of case studies, not a controlled study]. Use these to justify doing the work, never as a forecast.

## Screenshot and caption conventions

**Caption-first layout.** Large benefit text in the top third; device frame secondary and often cropped. The caption is the message, the UI screenshot is evidence. A bare, unannotated UI screenshot is the most common indie mistake — at thumbnail size it is unreadable noise.

Conventions that hold up:

- **One idea per frame.** If a caption needs a comma and a conjunction, it is two frames.
- **Frame 1 is the whole pitch.** State the outcome, not the feature. "Never argue about rent again" beats "Automatic expense splitting".
- **Frames 2–3 are the supporting proofs.** Frame 2 handles the objection, frame 3 the differentiator.
- **Readable at thumbnail.** Shrink your export to 120px wide; if the caption is illegible the font is too small — typical minimum 60–80pt on a 1320px canvas.
- **Consistent background system.** One colour or gradient family reads as a designed set; ten backgrounds read as amateur.
- **No fake-looking data.** Realistic names, amounts and dates. `Lorem ipsum` or `$1,234,567` destroys trust instantly.
- **Portrait unless motion is the product.** Landscape shows one frame above the fold instead of ~2.5.
- **Social proof in frame 1 or 2** if you have it. Do not fabricate it.

Play: the **feature graphic (1024×500)** sits above screenshots and acts as the promo video's poster. Not indexed, but the first pixel most Play visitors see.

Apple asset sizes: iPhone 6.9" is **1320 × 2868**, iPad Pro 13" is **2064 × 2752**; up to 10 screenshots per device family [UNVERIFIED — confirm required device families in App Store Connect before generating assets; this changes most years].

## The video trade-off

On Apple, the app preview **autoplays muted in the first media slot**, displacing screenshot 1 from the most valuable position. That is the trade: you swap your strongest static claim for 30 seconds of motion that most viewers abandon in 3.

Take the trade when the value is inherently motion (games, video/photo editors, drawing, AR) or the core interaction must be *seen* to be understood. Skip it when the value is a static promise (a tracker, a reader, a utility) — a caption states it in 1 second, a video takes 8 — or when you cannot afford a well-produced one, since a bad video converts worse than none.

If you ship one: the **first 3 seconds carry it**, it must read with sound off (burn in captions), keep it 15–20s not the full 30, and choose the poster frame deliberately. On Play the promo video is tap-to-play, so shipping one costs far less.

## Localised screenshots

Apple states localised listings can drive 2–3× downloads in non-English markets [UNVERIFIED — marketing claim, no published methodology]; case studies report 15–40% conversion improvement ([Screenhance](https://screenhance.com/blog/state-of-app-store-screenshots-2026)).

**Adapt, do not translate.** A translated caption in an English layout overflows (German runs ~30% longer), and the *claim* often needs to change — a Japanese user's objection is not a US user's. Localise in this order: caption copy → in-screenshot UI language → imagery → the claim itself.

With limited capacity, localise only for storefronts already sending meaningful impressions (App Store Connect → App Analytics by territory), not every locale you support.

## Apple Custom Product Pages

Up to **70 custom product pages per app**. Each can vary:

- Screenshots
- App previews
- Promotional text (170 chars)
- **Its own keywords**
- Deep links into the app (iOS 18 / iPadOS 18+; universal links or custom URLs, approved separately)
- Localisations

Source: [App Store Connect help](https://developer.apple.com/help/app-store-connect/create-custom-product-pages/configure-multiple-product-page-versions/), [Apple overview](https://developer.apple.com/app-store/custom-product-pages/).

Mechanics worth knowing:

- Each page gets a unique URL of the form `<default-url>?mt=8&pageId=<id>`.
- **With keywords assigned and the page approved and set to visible, a CPP surfaces directly in App Store search results** — not only via its URL. Without keywords it is link-only. This is the significant recent change and the most under-used indie lever.
- CPP keywords are assigned **from your latest approved app version's keyword set**, so plan the app-level field and the CPP allocation together.
- Metrics appear in App Analytics after **5+ first-time downloads** on that page.
- Requires Ready for Distribution in at least one region. Changes go through App Review.

**Structure one CPP per intent cluster** — same app, different opening claim. For an expense splitter: one page for "roommate rent" intent, one for "group trip", one for "restaurant bill". Give each a *unique, non-overlapping* keyword subset so Apple can pick the right page; overlapping sets make the choice arbitrary. Reuse the URLs as a UTM substitute for external channels.

## Google Play Custom Store Listings

Up to **50 custom store listings per app** across all types. Targeting dimensions ([AppTweak](https://www.apptweak.com/en/aso-blog/custom-store-listings)):

| Type | Targets on |
|---|---|
| Country | Different pages for markets sharing a language |
| Install state | Pre-registered users; inactive/lapsed users |
| Google Ads campaign | Specific ad-group click-through |
| **Keyword** | The search query that led the user to your listing |
| URL | A dedicated link for influencers, email, affiliates |

CSLs can vary app name, icon, descriptions, screenshots, feature graphic and promo video. They cannot vary ratings or the app itself.

Play's **keyword-targeted** CSL is the closest analogue to Apple's CPP-in-search, and Play's **install-state** targeting has no Apple equivalent — a dedicated re-engagement page for lapsed users is free conversion Apple does not offer.

## Apple Product Page Optimization (A/B tests)

Source: [Apple](https://developer.apple.com/app-store/product-page-optimization/).

| Parameter | Value |
|---|---|
| Treatments | Up to **3**, plus the original |
| Concurrent tests | **1 at a time** |
| Maximum duration | **90 days** |
| Testable | **Icon, screenshots, app previews** |
| Not testable | Name, subtitle, description, price |
| Icon constraint | Every variant icon must already ship inside the published binary |
| Traffic | You set the % exposed; e.g. 40% with 2 treatments = 20% each + 60% original |
| Consistency | A given user sees the same treatment for the whole test |
| Localisation | All supported languages or a chosen subset — more locales means slower significance |
| Editing | **Cannot modify a running test**; all new metadata passes App Review |
| Decision threshold | Apple recommends **≥90% confidence** before applying a treatment |
| Result metrics | Impressions, conversion rate, % improvement vs baseline, confidence |

Applying a treatment ends the test.

## Google Play store listing experiments

| Parameter | Value |
|---|---|
| Variants | Up to **3** against the current listing |
| Testable | Icon, feature graphic, screenshots, **short description, full description** |
| Minimum duration | **7 days** (covers day-of-week effects); 14 typical; up to 28 for low traffic |
| Traffic split | You choose; 50/50 for two-variant tests |
| Decision threshold | **≥90% confidence**; 95% for high-stakes changes like the icon |

Source: [PressPlay](https://www.pressplay.run/blog/google-play-store-listing-experiments-guide-2026) [UNVERIFIED on thresholds — Play Console reports its own confidence interval; 90/95% is practitioner convention, not a Google rule].

**The key platform difference: Play lets you A/B test text. Apple does not.** If your positioning question is "which claim converts", you can answer it on Play and then port the winner to Apple's subtitle by inference.

## The low-traffic problem

Both platforms compute significance from impressions and conversions. An app with 200 product-page views a day converting at 3% generates ~6 installs/day; split three ways against a control, a 10% relative lift is undetectable inside 90 days.

Rough guide: you need **thousands of impressions per variant** to resolve a 10% relative change. Below roughly 1,000 daily product-page views, treat store-native A/B tests as unusable for small deltas.

**Therefore: test whole concepts, not increments.** Do not test button colours, a font change, or reordering screenshots 4 and 5 — you cannot resolve those and will burn 90 days learning nothing. Test:

- Two fundamentally different **positioning claims** in frame 1 ("save money" vs "stop arguing")
- **Video vs no video**
- A **different visual system** entirely (illustrated vs device-frame)
- A **different icon concept**, not a shade of the same icon

Large swings produce large effects, and large effects resolve at low traffic. When traffic is too thin even for that, substitute cheaper evidence: paid off-store creative tests, five-second tests with real users, or shipping the better-reasoned design and watching the conversion trend across a version boundary — weaker evidence, but honest about it.

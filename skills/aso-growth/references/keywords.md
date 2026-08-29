# Keyword Research and Store Indexing

Verified August 2026. Store field limits, ranking behaviour, benchmarks and tool pricing change — verify before acting on numbers here.

## Indexed fields, exact limits

### Apple App Store (per locale)

| Field | Limit | Indexed | Notes |
|---|---|---|---|
| App Name | 30 | Yes — heaviest weight | Rejected if it reads as keyword stuffing |
| Subtitle | 30 | Yes — near-equal to name | Changeable only with a new binary |
| Keyword field | 100 | Yes — hidden from users | Syntax below |
| Description | 4,000 | **No** | Conversion only on iOS |
| Promotional text | 170 | **No** | Editable without a build |
| IAP display name | 30 | Yes (iOS 11+) | Free extra indexed surface |
| In-app event name | 30 | Yes (iOS 15+) | Events expire; keywords go too |
| In-app event short description | 50 | Yes | |
| Developer name | ~50 | Yes | Branded queries |
| Primary / secondary category | picklist | Yes | Gates category browse |
| Screenshots, app preview | n/a | **No** [UNVERIFIED] | Vendor blogs claim OCR caption indexing since June 2025; no Apple confirmation |

Total indexable characters per locale: **160** (30 + 30 + 100). Sources: [indexed-field reference](https://appscreenshotstudio.com/tools/app-store-indexed-fields), [keyword field guide](https://itsyconnect.com/guides/app-store-keyword-optimization).

### Google Play

| Field | Limit | Indexed | Notes |
|---|---|---|---|
| App title | 30 | Yes — highest weight | |
| Short description | 80 | Yes — high weight, high conversion impact | Above the fold |
| Full description | 4,000 | **Yes** | The big difference from Apple |
| Developer name | — | Yes | |
| Screenshot captions | n/a | No | |
| Hidden keyword field | — | Does not exist | Visible text only |

Source: [Play Console store-listing best practices](https://support.google.com/googleplay/android-developer/answer/13393723).

## Apple keyword field syntax, with reasoning

1. **Comma-separated, no space after the comma.** A space is a billed character that buys nothing. `budget,tracker,expense`, not `budget, tracker, expense`.
2. **Single words, not phrases.** Apple recombines tokens across name + subtitle + keyword field to match multi-word queries. `budget` and `tracker` already cover "budget tracker"; the phrase spends 14 chars for what 13 bought and blocks the tokens from recombining elsewhere.
3. **Never repeat a word already in the name or subtitle.** Those fields are indexed; repetition is not reinforcement, just wasted characters with no known ranking multiplier.
4. **Skip plurals where the singular exists.** Apple stems singular→plural reliably; the reverse is weaker [UNVERIFIED]. Default to singular, storing the plural only if it is the dominant query.
5. **Drop stop words.** `a`, `the`, `and`, `for`, `with`, `of` are ignored at match time. Also drop your category name if it duplicates the picklist.
6. **No competitor brand names.** Guideline 2.3.7 rejection risk, and Apple filters them from ranking anyway. Two losses, no upside.
7. **You cannot force phrase-match.** Everything tokenises, proper nouns included.
8. **Re-check popularity before every submission.** Demand is live and per-storefront.

## Locale pooling

Apple indexes the keyword field of *every locale served to a storefront*, additively. On the US storefront `en-US` and `es-MX` are both live, so filling both gives **320 indexable characters** instead of 160. Similar pairs exist elsewhere (`en-GB` + `en-AU`); check the storefront's served locales first.

Caveats, all load-bearing:

- The secondary locale's **name, subtitle and screenshots also go live** for users with that language set. Fill them properly or you damage conversion for that segment.
- **Never translate a keyword list across markets.** German users do not search German translations of your English terms. Rebuild from that market's autocomplete and popularity data.
- Locale availability changes. Verify in App Store Connect, not in a blog.

## How Play differs

Play weights **title > short description > long description** and reads visible text only. Guidance converged on **~2–3% density** for your top 2–3 terms across the long description, in natural prose ([AppFollow](https://appfollow.io/blog/google-play-aso-keywords)). Google penalises keyword blocks: "repeating the same phrase twenty times does not create twenty times the relevance."

Play also weights **behavioural inputs Apple largely does not**: install volume and velocity, install recency, retention and engagement, update frequency, ratings, and **Android vitals** (crash rate, ANR rate) ([AppTweak](https://www.apptweak.com/en/aso-blog/google-play-ranking-factors)). Bad-behaviour thresholds are commonly cited as user-perceived crash rate 1.09% and ANR rate 0.47% [UNVERIFIED — confirm in Play Console].

The consequence: **on Play, fixing crashes is keyword work.** An app over the vitals threshold is demoted in search and ineligible for some promotional surfaces regardless of metadata. Check vitals before starting a Play keyword sprint; over threshold, that is the higher-ROI task.

## The semantic-search shift

Apple changed US relevance visibly around **5 June 2025**: broad queries began returning apps spanning multiple *intents* rather than one dominant interpretation. Play added **Guided Search** in 2025, walking users from a broad query into a narrower intent ([AppTweak](https://www.apptweak.com/en/aso-blog/ai-reshaping-app-store-relevance)).

- Optimise **intent clusters**, not isolated exact-match tokens.
- Broad head terms split traffic across intents. A generic term you "rank" for may deliver near-zero taps because your app is not the intent served.
- Metadata, screenshots and review language must describe the same thing. Mismatched signals dilute inferred intent.
- Semantic neighbours of your term carry some weight even when not literally present [UNVERIFIED as to magnitude].

## Seven-step research procedure

Run in order. Record the artefacts named — later steps consume them.

**1. Seed from user language.** Read your support inbox, competitors' 1–3 star reviews, and the subreddit/Discord where the problem is discussed. Extract the problem phrases people actually type ("split the bill", "track macros"), not your feature names.
*Record:* 20–40 seed phrases with the source quote for each.

**2. Autocomplete harvest.** Type each seed into App Store and Play search — the suggestion list is real query data. Do a–z suffix expansion on the top 5 seeds.
*Record:* deduplicated candidates, tagged by which store suggested them.

**3. Competitor teardown.** Pick 8–12 competitors, two of them beatable. Log name, subtitle, short description, apparent keyword targets, rating count, top-10 queries.
*Record:* competitor × keyword × rating count. Terms where all top-5 results have >50k ratings are closed to a new app.

**4. Get volume ground truth from Apple Ads.** Sign in at ads.apple.com with App Store Connect credentials, start a campaign, read the **Search Popularity** score in the keyword planner. **No payment method or spend required.** The UI shows a 1–5 bar; the underlying index is 5–99, exposed by third-party tools ([Marteso](https://www.marteso.com/blog/apple-ads-search-popularity-keyword-research)). Per-storefront, live.
*Record:* popularity per candidate, per storefront, with date checked.

**5. Score difficulty against volume.** Zero-authority apps target popularity **5–25 on the 5–99 index** (2–3 bars), 3+ words. Win ~30 long-tail terms first; the resulting install velocity earns a shot at mid-tail. Head terms on launch week return zero.
*Record:* ranked shortlist, win/lose call, one-line reason each.

**6. Validate with a tiny ASA campaign.** **Exact-match** ad groups, $10–20/day, one per intent cluster, 7–14 days. Gives real impressions, tap-through and install rate per keyword — the closest proxy for organic demand *and* intent fit. Paid ASA spend has **no documented organic ranking effect**.
*Record:* impressions, TTR, CR per keyword. Kill terms with impressions but dead TTR.

**7. Ship, wait, iterate.** Submit, wait **14 days**, then read App Store Connect → App Analytics → *Search terms*. Change **one field per release** so movement is attributable.
*Record:* pre/post rank per target term and release version, in a running log.

## Tools

| Tool | Cost | Actually good for |
|---|---|---|
| Apple Ads keyword planner | Free, no spend | Only free first-party volume signal; ground truth for step 4 |
| Store autocomplete | Free | Real query discovery; catches phrasings tools miss |
| App Store Connect → App Analytics → Search terms | Free | Queries that drove *your* impressions. Underused. |
| Play Console acquisition reports | Free | Play search-term and conversion data |
| Google Keyword Planner | Free | Cross-check for Play; web intent proxy |
| Appfigures | ~$10–60/mo | Cheapest credible rank tracker for indies |
| AppFollow | Free tier + paid | Review management, keyword tracking, reply workflows |
| AppTweak | ~$100+/mo | Best keyword/semantic clustering; strong Play data |
| MobileAction | ~$100+/mo | ASA-adjacent keyword intelligence, competitor ad spend |
| Sensor Tower | Enterprise | Competitor download estimates; overkill for indies |
| SplitMetrics / Storemaven | Enterprise | Off-store creative testing when store tests are too slow |

Prices are indicative — verify. **Budget for exactly one paid rank tracker**; the rest of the method runs on free first-party data.

## Worked example: seed → shipped keyword field

App: a shared expense splitter. Name (24): `Splitly: Shared Expenses`. Subtitle (27): `Split bills with housemates`.

Tokens already indexed and therefore **banned from the field**: `splitly, shared, expenses, split, bills, with, housemates`.

Seeds surviving step 5, with popularity (5–99): `roommate` 34, `rent` 41, `iou` 12, `settle` 18, `trip` 22, `tab` 29, `owe` 15, `budget` 61 (unwinnable — dead), `receipt` 26, `venmo` (brand — banned), `flatmate` 19, `chore` 14, `debt` 23, `dinner` 25.

Apply the rules: singular only, no stop words, no name/subtitle duplication, drop `budget` and `venmo`. Order does not affect matching, so pack for density.

```
roommate,flatmate,rent,tab,owe,iou,settle,debt,receipt,group,trip,dinner,chore
```

That is 93 characters; the remaining 7 go to one more validated term, e.g. `,house` → 99 used.

Cross-check what recombination buys: name + subtitle + field now cover "split rent with roommates", "roommate expense tracker", "settle up with flatmates", "group trip expenses" — none of which cost a phrase in the field. Then fill `es-MX` on the US storefront with a separately researched Spanish list for another 100 characters.

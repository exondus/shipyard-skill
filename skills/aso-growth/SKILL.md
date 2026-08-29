---
name: aso-growth
description: >
  Research keywords and write the store listing that gets an app found, then plan the launch and the
  retention work that keeps it alive. Use for App Store and Play keyword research, choosing the app
  name and subtitle, writing listing copy and screenshot captions, store page conversion testing,
  custom product pages, deciding when to ask for a rating, improving day-one and day-thirty retention,
  planning a launch with no audience, submitting for App Store featuring,
  setting up attribution on no budget, or building the marketing site and its funnel into the store.
---

# Found, installed, retained

Three separate problems that get conflated. Search gets the impression, the page gets the install,
the first session gets the user. Work on them in that order and measure them separately.

## How search actually works

The two stores index differently and the difference decides where effort goes.

**Apple** indexes the app name, the subtitle, the 100-character keyword field, the developer name, and
in-app purchase and event names. **It does not index the description.** That is roughly 160 indexable
characters per locale, which is why every one of them matters.

Keyword field rules: comma separated with **no spaces after commas** (spaces cost characters and buy
nothing); single words, not phrases, because Apple recombines tokens across the name, subtitle and
keyword field to match multi-word queries; **never repeat a word already in the name or subtitle**;
skip plurals; drop stop words; and never use a competitor's brand name — it does not rank and it is a
metadata rejection risk.

The highest-leverage trick for an indie: on some storefronts, keywords from additional locales are
indexed additively alongside the primary one, roughly doubling the indexed space. Do not translate a
keyword list between markets — rebuild it, because people do not search translations of your terms.

**Google Play** indexes the title, the short description and the full description, weighted in that
order. Aim for natural placement of the top two or three terms across the long description; stuffing
is penalised. Play also weights behavioural signals Apple largely does not — install velocity,
retention, ratings, and technical vitals such as crash and ANR rates. **On Play, fixing crashes is
keyword work.**

Both stores have moved toward semantic matching, which means optimising intent clusters rather than
isolated exact-match tokens, and making the screenshots and reviews reinforce the same meaning as the
metadata.

## The keyword method

Executable in order. `references/keywords.md` has the detail.

1. **Seed from user language, not product language.** Mine competitor one-to-three star reviews, the
   subreddit where the problem is discussed, and your own support mail. Extract the problem phrases
   people actually type, not your feature names. `product-discovery` will already have some of this.
2. **Harvest autocomplete** in both stores for each seed, including a-to-z suffix expansion. The
   suggestion list is real query data.
3. **Tear down 8–12 competitors**: their name, subtitle, what they appear to target, and their rating
   count as a proxy for immovability. Terms where the top five all have tens of thousands of ratings
   are closed to a new app.
4. **Get volume ground truth from Apple's own ads keyword planner.** It is free with an App Store
   Connect login, needs no spend, is per-storefront and is live. It is the only free source of real
   Apple search volume.
5. **Choose long tail.** For a zero-authority app, take moderate-popularity, three-or-more-word terms
   and aim to rank first for thirty of them. The resulting install velocity is what earns a shot at
   mid-tail later. Chasing a one-word category term on launch week returns nothing.
6. **Validate with a small exact-match ads campaign** if there is any budget — a week or two at a few
   dollars a day returns real impression volume and intent per keyword. It is research, not a ranking
   hack; paid spend has no documented organic ranking effect.
7. **Ship, wait two weeks, measure, iterate — changing one field per release** so movement can be
   attributed.

Keep the working set in `docs/app/research/keywords.md` with the date and the source of every volume
figure.

## The store page

Most visitors decide in a few seconds and about half never scroll past the second image. The first
impression is the icon, the name, the subtitle, and the first two or three screenshots, plus the
preview video if there is one, which autoplays muted and consumes the first slot.

Screenshot conventions that convert: caption first with the benefit in large text in the top third and
the device frame secondary; one idea per screenshot; the strongest outcome claim first; readable at
thumbnail size. Show the app in use — a splash or login screen in the first slot is both a wasted slot
and a guideline problem. Localise screenshots by adapting rather than translating.

Video is a genuine trade-off: it lifts conversion for apps whose value is motion and hurts apps whose
value is a static promise. Test it rather than assuming.

**Custom product pages are the most under-used lever available.** Apple allows a large number of them,
each with its own screenshots, promotional text and its own keywords, and they can now surface directly
in search. One page per intent cluster is a materially different strategy from one page for everyone.
Play's equivalent is custom store listings, targetable by country, install state or search keyword.

For A/B testing: Apple allows a few treatments against the original for up to about 90 days; Play
allows text testing, which Apple does not. Run at least a week to avoid day-of-week effects, decide at
high confidence, and **test whole concepts, not button colours** — a low-traffic app cannot reach
significance on a small change, so the choice is between testing something big and not testing.

`store-submission` owns the exact asset dimensions and the metadata rules that cause rejections.

## Ratings

The in-app review prompt is rate-limited by the OS to a small number of showings per year and **may be
silently ignored**, which is precisely why both platforms forbid triggering it from a button. Budget
those showings: trigger after a success moment the app can detect — a task completed, a streak hit, an
export finished — and after at least a couple of sessions. Never during onboarding, never after an
error, and never gated on sentiment.

Reply to negative reviews. Google reports that replying raises that review's own rating by roughly
0.7 stars on average, and on Play the ratings feed the ranking directly. Ship the fix, name it in the
reply, then let the prompt fire for the fixed cohort.

## Retention

What moves it is not a growth tactic. It is time to first value in the first session, a reason to
return that is the user's own data, and notification permission earned rather than demanded — which
is `onboarding-flow`'s territory.

Rough benchmarks to calibrate against, not to target: median day-one retention around 25%, day-seven
around 8%, day-thirty around 4%, with strong consumer apps roughly 30–40 / 10–15 / 5–8 and social and
productivity apps higher. Most apps lose about three quarters of installs in three days. Verify current
figures before quoting them to anyone.

Streaks work when they represent a habit the user chose, and need a repair or freeze mechanic so a
single miss does not end the relationship. Loss-framed push to lapsed users is a short-term number and
a long-term uninstall.

## Launching with no audience

Realistic expectation first: most indie launches see double-digit day-one downloads. The compounding
assets are ASO and one content channel measured over 90 days, not launch day.

- **Pre-orders** accumulate into a single-day install spike at release, which is a genuine ranking
  signal. Set the date well ahead.
- **TestFlight as a community, not a QA queue.** A public link works as a landing-page call to action,
  and the group becomes the first review cohort.
- **Featuring nominations**: submit at least three weeks before the publication date, with a date, a
  story, and the supplemental assets. Apple's editors reward platform-native design, day-one adoption
  of new OS features, and accessibility — which is a reason to take `premium-ui`'s accessibility
  section seriously beyond compliance.
- Product Hunt is a backlink and a few hundred visits, not a business. Reddit converts only if you have
  been in the community for months. Short-form video is currently the highest-yield free channel for
  consumer apps, and it takes twenty-odd posts before one carries.
- A **press kit** page: name, one-line and 50-word descriptions, icon, five screenshots, a short video,
  bio, link, contact.

## Attribution on no budget

Do not build a paid-acquisition attribution stack before there is paid acquisition. The free stack is
enough to answer "is ASO or the video channel working": the platform attribution frameworks for ads
you do run, the install referrer on Android, App Store Connect's own source-type analytics, product
analytics for in-app funnels, and revenue cohorts from the payment provider. A per-channel custom
product page or custom store listing URL works as a poor developer's UTM, splitting traffic by page
with no SDK at all.

## Reference files

- `references/keywords.md` — field limits, syntax rules, the research method, tools and what each is for
- `references/store-page.md` — screenshot and caption conventions, custom product pages, testing rules
- `references/retention.md` — benchmarks, rating prompt quotas, opt-in and priming evidence, streaks.
  Cadence, copy and the send mechanics belong to `push-engagement`
- `references/launch.md` — the launch sequence, featuring nomination, press kit, channel notes
- `references/web.md` — the marketing site: what it is for, the store-to-web funnel, app-site SEO

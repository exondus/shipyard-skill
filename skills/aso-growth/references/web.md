# The Marketing Site

Verified August 2026. Store field limits, ranking behaviour, benchmarks and tool pricing change — verify before acting on numbers here.

The default stack pairs an Expo app with a Next.js site, and the site is usually an afterthought. It has five jobs, in this order of actual value.

## 1. What the site is for, ranked

**1. Install referrals into the stores.** Every off-store channel — TikTok bio, Reddit comment, newsletter, podcast mention — needs one URL that survives being pasted anywhere and routes each visitor to the right store. The site's highest-value function, and the only one that compounds.

**2. A landing page for paid and social traffic.** One page per campaign or intent, so a visitor arriving from a specific promise sees that promise. Cheaper and more flexible than a Custom Product Page because you change it without App Review.

**3. The press kit.** A stable, ungated URL with what a journalist, YouTuber or Apple editor needs. Linkable from featuring nominations (up to 5 supplemental URLs — see `launch.md`).

**4. The legal pages the stores require.** Non-negotiable, and a real rejection cause:

| Page | Required by | Notes |
|---|---|---|
| Privacy policy | **Both stores, all apps**, no exceptions | Must be a live HTTPS URL, must match your Data Safety / Privacy Nutrition Label declarations |
| Terms of service | Effectively required if you have accounts or subscriptions | Apple checks EULA presence for subscription apps |
| **Account-deletion URL** | Google Play, if your app supports account creation | See below |
| Support URL | Both stores | Must resolve and be about your app |

Play's account-deletion URL has three tests Google applies by actually loading the page: **functional** (HTTPS, no errors, no redirect chain, no login wall blocking the instructions), **relevant** (the deletion path prominent on that page, not buried in the privacy policy), and **identifiable** (the page **references your app name or developer name exactly as it appears on the store listing**). A generic `/support` page fails all three. Full requirement, including the separate in-app deletion path: `store-submission` → `references/play.md` §3.

**5. Support.** A FAQ and a contact route. Deflects one-star "nobody answers" reviews.

Build these as static routes. Do not put legal pages behind a CMS you might stop paying for — the stores load them during review.

## 2. The store↔web funnel

**Smart App Banner (iOS Safari).** One meta tag in `<head>`; Safari renders a native banner that opens the App Store or, if installed, the app:

```html
<meta name="apple-itunes-app" content="app-id=123456789, app-argument=https://you.com/path, affiliate-data=pt=123456&ct=web-home">
```

`app-argument` deep-links into the app when installed; `affiliate-data` carries campaign tokens ([Apple](https://developer.apple.com/documentation/webkit/promoting-apps-with-smart-app-banners)). Safari-only — Chrome on iOS and Android browsers ignore it, so ship your own banner component as the fallback. Android's equivalent is a plain link to your Play listing; Chrome's older native app-install banner behaviour is [UNVERIFIED] for current versions, so do not depend on it.

**Badges and link conventions.** Use the official artwork and follow the layout/clear-space rules — both stores enforce them and reviewers notice: [Apple marketing guidelines](https://developer.apple.com/app-store/marketing/guidelines/), [Google Play badges](https://play.google.com/intl/en_us/badges/). Canonical URLs: `https://apps.apple.com/app/id<APP_ID>` (Apple auto-redirects each visitor to their local storefront regardless of the region code in the path) and `https://play.google.com/store/apps/details?id=<PACKAGE>`.

**Attribution without an MMP.** This is the practical payoff of owning the site.

- **Apple: campaign links.** Append `?pt=<provider token>&ct=<campaign token>&mt=8`. Impressions, downloads, sales and subscriptions then split by campaign in App Store Connect → Analytics. Campaign tokens are up to **30 characters**; data appears after **24 hours**; metrics are suppressed below **5**; a first-time download counts if it happens within **24 hours** of the click; on multiple clicks the **most recent** link wins. No SDK, no MMP — but the Campaigns tab appears only once your app has analytics data ([Apple](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/)).
- **Play: install referrer.** Append URL-encoded `&referrer=utm_source%3Dtiktok%26utm_medium%3Dbio`. Read it once on first launch via the Play Install Referrer Library ([Android docs](https://developer.android.com/google/play/installreferrer/library)); the value persists 90 days and does not change unless reinstalled. It also surfaces in Play Console acquisition reports.
- Give every channel its own `ct` / `utm_source`. Two links cost nothing and answer "which channel actually installs" for free.

**Deferred deep linking** — visitor clicks a content link, installs, lands on that content — is *not* solved by the above. Universal Links and App Links only work if the app is already installed. Deferred linking needs a third party (Branch, AppsFlyer OneLink) or a probabilistic match that is unreliable post-ATT. **For an indie, skip it**: send new users to a first-run screen that asks what they came for.

**One direction you may not always link.** Pointing users *from the app* to web checkout is storefront-dependent. In the **US** App Store external purchase links are permitted alongside IAP; in the **EU/EEA** they require the Alternative Terms Addendum with its own fee stack; **Japan** has an MSCA-compliant programme; Play's **User Choice Billing** covers a specific country list at the standard fee minus 4% ([RevenueCat](https://www.revenuecat.com/blog/engineering/app-to-web-purchase-guidelines)). Elsewhere, linking out for digital goods is still a rejection. Web→app is always fine; app→web checkout is not. Verify per storefront.

## 3. SEO that is worth doing

Be honest about the ceiling. **The store listing will outrank your landing page for your own app name**, because Google surfaces the App Store and Play pages for branded app queries and they carry vastly more authority. Do not fight it — that traffic converts either way.

What the site can realistically win:

- **App-name-plus-modifier long tail**: "<app> review", "<app> pricing", "<app> vs <competitor>", "how to export from <app>", "<app> not syncing". Low volume, high intent, and the store has no page for most of them. One page each.
- **Problem-first queries** the store has no surface for: "how to split rent with roommates". Genuine content, not thin doorway pages.
- **Comparison and alternative pages**, which convert well and are the one place competitor names are legitimate (unlike your keyword field — see `keywords.md`).

Mechanics, all cheap:

- **Unique `<title>` and meta description per route.** App Router: export `metadata` or `generateMetadata` per page. No duplicated titles.
- **Open Graph and Twitter cards** on every page — what renders when someone pastes your link into Slack, Discord, iMessage or X, and the highest-leverage 20 lines on the site. Use the Next.js `opengraph-image` file convention or a static 1200×630 PNG.
- **`SoftwareApplication` structured data** on the home page. Required: `name`, an `offers` with `price` (`0` for free), and `aggregateRating` or `review`; recommended: `applicationCategory`, `operatingSystem`. Still supported for rich results as of the December 2025 docs update ([Google](https://developers.google.com/search/docs/appearance/structured-data/software-app)). Only mark up ratings you actually display.
- **Sitemap and robots**: `app/sitemap.ts` and `app/robots.ts` generate both. Submit the sitemap in Google Search Console — also the only free way to see which queries your site ranks for.
- **One canonical domain.** Pick `www` or apex, redirect the other, set `canonical` links.

## 4. Landing-page conversion

Above the fold, without scrolling, on a phone: **what the app does in one sentence** (a benefit, not a category), **one visual** (a single device shot or a short looping video), **the store badges**, and **social proof** if you have any real. That is all.

**Reuse the store assets.** The screenshots and captions you built for the store (`store-page.md`) are already tested and already localised — drop the same first three frames in. Same for the app preview video. Do not commission separate web creative; the consistency also helps, because a visitor who clicks through to the store should recognise what they see.

**One call to action, repeated.** Get the app. Not "get the app / join the newsletter / read the blog / follow us" — every extra CTA dilutes the first. On desktop, where a badge cannot install anything, the honest CTA is a QR code or an email-me-the-link field. Pre-launch, the single CTA is the TestFlight public link or an email capture — the only audience you own.

## 5. Core Web Vitals

Targets: **LCP ≤ 2.5s**, **INP ≤ 200ms** (replaced FID in March 2024), **CLS ≤ 0.1**, measured at the 75th percentile of real users ([corewebvitals.io](https://www.corewebvitals.io/core-web-vitals)). Only about 48% of mobile pages pass all three, so this is a differentiator, not table stakes.

The Next.js levers that actually move them, in order:

1. **`next/image`** with explicit `width`/`height` (kills CLS) and `priority` on the hero image (fixes LCP). Serve AVIF/WebP.
2. **`next/font`** — self-hosts and preloads the font, removing the layout shift and render-blocking request a Google Fonts `<link>` causes.
3. **Static generation.** A marketing site should be fully static or ISR. No `dynamic = "force-dynamic"` on a landing page.
4. **Cut client JS.** Keep pages as Server Components; `"use client"` only on interactive leaves. Analytics and chat widgets are the usual INP culprits — load them with `next/script` `strategy="lazyOnload"`.
5. **Reserve space** for anything that loads late (banners, embeds, cookie bars) so nothing shifts.

Measure with real-user data, not lab scores: Search Console's Core Web Vitals report and Vercel Speed Insights. Deeper performance work: `performance-security` → `references/performance.md`.

## 6. Not worth doing

- **A blog you will not maintain.** Three stale posts hurt more than no blog.
- **A separate design system for the web.** Reuse the store creative and your brand colours.
- **Deferred deep linking** at indie scale, per above.
- **An MMP for web→app attribution.** Campaign links and install referrer are free and sufficient below real paid spend (`launch.md`).
- **A cookie banner you do not need.** Ship no third-party tracking and you need no consent banner — use a cookieless analytics tool and skip the CLS and INP tax.
- **Chasing head keywords** your category leaders own.
- **A web app** built to "support" the mobile app, unless the web app is itself the product.
- **Gating the press kit** behind a form. Journalists leave.

# Vendor Free Tiers, Paid Steps and Overage Traps

> **⚠️ READ THIS FIRST. Every price and limit below WILL be out of date.** Vendors change free-tier ceilings, restructure plans and re-price overages monthly, often without announcement. These figures were checked in **August 2026** and are a starting map, not a quote. **Open the vendor's own pricing page and re-verify before you commit an architecture, quote a client a monthly cost, or promise anything stays free.** Never repeat a number from this file to a user as current fact without checking it first.

## The table

| Vendor | Free ceiling | First paid step | Unit that runs out | Specific overage trap |
|---|---|---|---|---|
| **[Sentry](https://sentry.io/pricing/)** | 5k errors, 5M spans, **50 replays**, 5GB logs, 1GB attachments, 1 cron, 1 uptime monitor, 30-day retention, **1 seat** | **Team $26/mo** (annual): 50k errors, unlimited seats, 90-day retention | Errors | One crash loop burns the month in hours. `tracesSampleRate: 1.0` copied from the docs eats 5M spans fast. 50 replays is a rounding error — error-only replay or nothing. 1 seat means a second dev forces the upgrade regardless of volume. |
| **[PostHog](https://posthog.com/pricing)** | Per product/mo: 1M events, 5k recordings, 1M flag requests, 1,500 surveys, 100k exceptions, 1M warehouse rows | Pay-as-you-go past each free allowance | Events, then recordings | Touch autocapture multiplies events 10–50×. Replay at 100% sampling exhausts 5k recordings in days. High-cardinality properties inflate storage invisibly. Server-side flag checks chew the 1M flag requests without local evaluation. |
| **[RevenueCat](https://www.revenuecat.com/pricing/)** | ≤ **$2,500 monthly tracked revenue** | **1% of tracked revenue** above $2.5k MTR | Your own revenue | The only line item that scales with success rather than usage. Trivial pre-launch, a real percentage later — model it into unit economics early rather than discovering it at scale. |
| **[Clerk](https://clerk.com/pricing)** | **50,000 MRU** (Hobby) | **Pro $20/mo** (annual), 50k MRU included, then ~$0.02/MRU in the 50k–100k band | Monthly retained users | "MRU" counts a user **retained when they return 24h+ after signing up** — not a raw MAU, so the count behaves unlike other vendors'. Production-grade features (SAML, advanced MFA, some org features) are priced as add-ons on top of the base. |
| **[Supabase](https://supabase.com/pricing)** | 500MB DB, 1GB file storage, 5GB egress + 5GB cached egress, 50k MAU, **2 active projects** | **Pro from $25/mo**: 8GB DB, 100GB storage, 250GB egress, 100k MAU, 7-day backups, $10 compute credit | Egress, then DB size | **Free projects pause after 1 week of inactivity** — this kills demos and side projects without warning. On Pro, **compute is billed separately** from the $25 base (only $10 credit included), so the real floor is above $25. Egress $0.09/GB: serving images from Storage instead of a CDN is the classic bill shock. |
| **[Neon](https://neon.com/pricing)** | 0.5 GB storage/project, **100 CU-hours/project**, 100 projects, 10 branches/project, scale-to-zero after 5 min | **Launch**: usage-based, no minimum — $0.106/CU-hour, $0.35/GB-month, 500GB egress/project then $0.10/GB | Compute hours | Compute-hours from branches **left running**. Scale-to-zero saves you only if connections actually idle — a health check or a long-lived pooler keeps compute warm 24/7 and silently drains CU-hours. Branch-per-PR sprawl multiplies this. |
| **[Expo EAS](https://expo.dev/pricing)** | 15 iOS + 15 Android builds/mo, 1 concurrency, 45-min timeout, **1,000 EAS Update MAUs**, 100 GiB bandwidth, 20 GiB storage, low-priority queue | **Starter $19/mo**: $45 build credit, 3,000 Update MAUs, then usage-based | Update MAUs, then build minutes | **1,000 Update MAUs is nothing at launch** — a modest launch week blows through it. Additional build **concurrency is $50 each** (up to 5), which is what you actually want when CI queues. Update bandwidth $0.10/GiB, storage $0.05/GiB. Low-priority queue means 45+ min waits at peak. |
| **[Vercel](https://vercel.com/pricing)** | Hobby: 100GB fast data transfer, 1M function invocations, 5k image transformations, 300k image cache reads — **personal, non-commercial use only** | **Pro $20/user/mo** with $20 usage credit: 10M edge requests, 1TB transfer, 1M function invocations | Seats, then transfer/invocations | **Hobby forbids commercial use** — shipping a revenue app on Hobby is a ToS violation, not a clever saving. Pro is **per user**, so team size drives cost more than traffic early on. Overages: $0.15/GB transfer, $0.60/1M invocations, image transforms from $0.05/1k, ISR reads from $0.40/1M. |
| **[Cloudflare](https://developers.cloudflare.com/workers/platform/pricing/)** | Workers/Pages free tier generous for daily request volume; Pages static hosting effectively unmetered bandwidth | **Workers Paid $5/mo** | Worker CPU time | **R2 has zero egress fees** — the single biggest structural cost advantage in this stack, and the reason to put R2+CDN in front of Supabase/S3 storage. Watch Workers CPU-time limits per request; long-running work belongs elsewhere. [UNVERIFIED — Cloudflare figures not re-checked this session; verify before quoting.] |

## Which cost explodes first

For a small consumer app, in the order it actually happens:

1. **EAS Update MAUs.** 1,000 free MAUs is hit within days of any real launch. It's first because it triggers on *success*, arrives without warning, and OTA updates are the thing you least want to lose mid-launch.
2. **Sentry errors.** A bad release produces a crash loop; 5,000 errors evaporate in hours. Worse, you hit the cap during the exact incident you need visibility for, and Sentry goes dark until the next cycle.
3. **PostHog events.** Once autocapture and replay are both on, the 1M/5k allowances go quickly. Slower than the above but harder to walk back, because the fix (turning off autocapture) also costs you historical continuity.
4. **Supabase egress and compute.** Grows with media traffic. Serving images directly from Storage is the usual cause; the bill climbs steadily rather than spiking, so it goes unnoticed longest.
5. **Vercel seats and transfer.** Driven by team growth first, traffic second.
6. **Clerk MRU past 50k.** Genuinely far away for most apps; the 50k ceiling is generous.
7. **RevenueCat's 1%.** Last, and the only one that arrives as good news.

Note the pattern: **the first three fire on launch day, not at scale.** Configure their limits before you launch, not after.

## Controls and where to set them

| Control | Where |
|---|---|
| **Trace/replay sampling** | Sentry `Sentry.init` — `tracesSampler` (0.1 baseline, 1.0 on checkout/signup), `replaysSessionSampleRate: 0.0`, `replaysOnErrorSampleRate: 1.0` |
| **Spike protection + rate limits** | Sentry project settings → per-key rate limit and spike protection. Set both; they are the only controls that survive a bug in your own `beforeSend` |
| **Billing limits per product** | PostHog → Billing. PostHog **drops** events over the limit rather than charging. Set separate limits for analytics, replay and flags. This is the hard backstop — set it on day one |
| **Autocapture off, replay sampled** | PostHog init — `captureTouches: false`, replay sampling ≤10%, `captureScreens: true` is fine |
| **Local flag evaluation** | PostHog server SDK with a personal API key — keeps flag checks off the 1M-request meter |
| **CDN in front of object storage** | Cloudflare R2 (zero egress) or a CDN in front of Supabase Storage — the fix for egress at $0.09/GB |
| **One build per release** | EAS — use `eas update` (OTA) for JS-only changes; reserve native builds for native changes. Don't build per commit |
| **No idle preview environments** | Neon — delete PR branches on merge; confirm scale-to-zero actually engages (no health check keeping compute warm). Supabase — don't hold open free projects you're not using, they pause anyway |
| **Noise filtering** | Sentry `ignoreErrors` + `denyUrls` in init, inbound filters in project settings; PostHog internal-traffic cohort filter |
| **Environment separation** | Never point dev/preview builds at production analytics or error projects — dev noise consuming production quota is a common and entirely avoidable cause of overage |
| **Size/volume budgets in CI** | Track bundle size and event volume per release so regressions surface as diffs, not invoices |

## Rules of thumb

- **Sample from day one.** Retrofitting sampling after a bill is painful and loses the comparability of your historical data.
- **Set hard caps everywhere they exist** (PostHog billing limits, Sentry spike protection). Prefer dropping data to an unbounded invoice at this stage.
- **A free tier that pauses or throttles is a production risk, not a saving.** Supabase free-project pausing and EAS low-priority queues are fine for prototypes and wrong for anything with users.
- **Model the whole stack monthly before launch.** The realistic pre-revenue floor for a serious consumer app is roughly $50–100/mo once you leave the free tiers that matter (EAS Starter, Sentry Team, Supabase Pro) [UNVERIFIED — an estimate from the figures above, not a vendor quote].
- Re-verify this table quarterly, and always before quoting a number to anyone.

---
name: cost-control
description: >
  Keep the running cost of an app near zero before it has revenue, and know which line will grow first
  when it does. Use before adding any paid service, when comparing hosting, database, auth, analytics
  or build vendors, when a bill is unexpectedly high, when deciding whether a free tier will survive
  launch, or when someone asks what this app costs to run. Also use to set spend caps and billing
  limits before launch rather than after the first surprise invoice.
---

# Cost control

The goal is not to be cheap. It is to make the bill predictable and to know, before launch, which
number grows first — because the way small apps get expensive is never the line anyone watched.

## Before adding any paid service

Four questions, answered in writing in `docs/app/stack.md`:

1. **What is the free ceiling, in the unit that will actually run out?** Not "generous free tier" —
   the number, and which metric it counts. Monthly active users, events, errors, build minutes and
   gigabytes of egress all behave differently.
2. **What happens at the ceiling?** Some vendors stop accepting data, some charge overage, some
   suspend the project. These are wildly different outcomes and only one of them is safe to discover
   in production.
3. **What is the first paid tier, and what triggers it?** For several services the trigger is a
   *feature* — removing branding, multi-factor auth, an extra environment — not volume, and paying for
   a plan when one feature was the reason is a common waste.
4. **What does leaving cost?** Auth and database migrations are the expensive ones. Analytics and error
   tracking are nearly free to swap. Weight the lock-in accordingly and be willing to pick the
   stickier vendor deliberately.

## The order costs explode

For a small consumer app on the default stack, in the order it usually happens:

1. **Over-the-air update active users.** The free allowance is small and launch week eats it. This is
   the surprise more often than anything else.
2. **Error tracking quota** on a bad release. A crash loop can consume a month of error quota in hours,
   which is why spike protection and inbound filters go in before launch, not after.
3. **Product analytics events**, once autocapture and session replay are both on. The multiplier is
   large and it compounds with user growth.
4. **Database egress and compute** as media traffic grows. Serving images and video directly from
   object storage to a mobile app is the classic way to turn a $25 bill into a $200 one.
5. **Auth monthly active users**, once past a large free ceiling.
6. **The revenue share on payments** — the only one that arrives as good news.

## The controls that actually work

Set these before launch. Afterwards is a conversation about a bill that already exists.

- **Sample from day one.** Traces and profiles at a low rate, session replay error-triggered only,
  touch autocapture off. Retrofitting sampling after a bill is the same work done under pressure.
- **Set hard billing limits and spend caps** in every vendor console that offers one. Prefer a vendor
  that drops overage data over one that silently bills for it, and know which you have.
- **Put a CDN in front of user-facing media** rather than serving it from the database platform's
  storage, and never select whole wide rows for a list view.
- **One build per release, not per commit.** Use over-the-air updates for JavaScript-only changes and
  keep native builds for native changes; the fingerprint runtime policy makes this safe.
- **Do not leave preview environments running.** Per-branch databases that scale to zero are cheap;
  ones that do not are a standing charge for something nobody is looking at.
- **Filter known noise** out of error tracking — network aborts, cancelled requests, injected WebView
  scripts. It is quota and it is also signal-to-noise.

## The realistic floor

A pre-revenue app on the default stack runs at roughly **$50–100 a month** once you leave the free
tiers that actually bind — see the per-vendor table in `references/tiers.md`, which is the authority on
the number. Below that is possible pre-launch and not after it. What takes it to several hundred is
almost always media egress or an unsampled analytics and replay setup, not the number of users.

`references/tiers.md` has the per-vendor table — free ceiling, first paid tier, and the specific
overage trap for each — as of August 2026. **Prices and limits change constantly; verify before
quoting a number to anyone or making a decision on it.**

## When to accept a cost

Cheap is not the objective, and three costs are worth paying early:

- **A paid tier that removes a launch blocker** — a branding removal requirement, an environment you
  actually need, a build concurrency that unblocks a release.
- **Anything that buys back a day of your time per month.** At the scale of a solo build, engineering
  time is the scarce resource, not money.
- **Error tracking and analytics quota sufficient to see the launch.** Being blind during the week
  that matters most is the most expensive saving available.

The corresponding waste: paying for a plan tier to get one feature without checking whether an add-on
exists; paying for observability on a pre-launch app with no users; and building an in-house version
of a cheap service to save a small monthly fee, which costs a week and then needs maintaining forever.

## Reference files

- `references/tiers.md` — per-vendor free ceilings, first paid tiers and overage traps, with the
  caveat that every number needs re-checking before use

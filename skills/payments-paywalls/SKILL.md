---
name: payments-paywalls
description: >
  Design and wire monetisation — in-app purchases, subscriptions, entitlements, paywall screens and web
  checkout — across RevenueCat, Apple and Google in-app purchase, Stripe and Paystack. Use when adding
  payments or a paywall, choosing a pricing model, building the entitlement architecture, handling
  purchase webhooks, reconciling a user who paid on the web with their mobile access, dealing with
  trials, grace periods, refunds or restore purchases, or answering whether an app may link out to a
  web checkout. Use it for subscription churn too — why people cancel, dunning and failed payments,
  win-back offers and downgrade paths. Also use for paywall rejections and for choosing a processor for
  a South African or African business.
---

# Money

Three things must be true before any purchase code is written, and getting them wrong is expensive to
undo:

1. **Your database is the source of truth for access**, not a payment SDK. Every server-side
   authorisation reads your own `entitlements` table.
2. **You gate on entitlement keys, never on product IDs.** Product IDs multiply — platforms, regions,
   experiments, legacy SKUs — and every `if productId === …` becomes a bug the day pricing changes.
3. **Webhooks are verified over the raw request body, deduplicated, and treated as unordered.** All
   three providers sign the bytes; parsing and re-serialising before verifying breaks the signature,
   which is the single most common integration failure.

## The architecture

Apple and Google purchases go through RevenueCat. Web purchases go through Stripe or Paystack. Both
paths write into one table you own:

```
entitlements(user_id, entitlement_key, source, status, current_period_end,
             grace_until, store_txn_id, raw_event_id, updated_at)
```

Effective access is a single predicate over that row — active, in grace, or in billing retry. The
mobile app may read the RevenueCat customer info for instant UI, because waiting on a round trip to
show a locked screen feels broken, but **no server-side gate ever calls a payment provider in a
request path.** Add a nightly reconcile over rows expiring within 48 hours, because webhooks do fail.

`references/entitlements.md` has the schema, the state machine and the reconcile job.

## RevenueCat

The object model is products → packages → offerings → entitlements. Offerings and paywalls are
configured remotely, which means pricing and paywall layout can change without a release — a
significant part of why it is worth the dependency.

Things that reliably go wrong:

- **It cannot run in Expo Go.** It needs a development build. Newer SDKs mock the paywall UI in Expo
  Go so layout work is possible, but no transaction is real.
- **Log the user in with your own user ID before showing a paywall** whenever you can. Anonymous
  purchases get aliased on later login, and a user who buys anonymously, reinstalls and signs in on a
  second device produces alias chains and transfer events that turn into support tickets.
- **A cancellation event means auto-renew was turned off, not that access ends.** Keep the entitlement
  until expiry. Conversely, an expiry timestamp in the past does not mean access ended — grace period
  and billing retry keep the user entitled while the card is retried. Trust the entitlement state, not
  a date comparison. The one event that does revoke immediately is a refund or support-initiated
  cancellation.
- **Restore purchases must be reachable**, and reachable without being signed in. Its absence is a
  routine rejection.

## What you may charge, where

This is the most volatile area in the whole plugin and it has changed repeatedly. **Verify the current
position before implementing a link-out, and record the date you checked in `docs/app/entitlements.md`.**

The shape as of August 2026:

- **Any digital unlock inside the app uses the store's in-app purchase.** No license keys, no external
  checkout, no crypto. This has not changed.
- **United States storefront**: following the 2025 injunction, apps may include buttons and external
  links to a web checkout. Apple proposed a commission on those link-outs in August 2026; it was not in
  force at the time of writing and is contested. Build the link-out so a commission can be absorbed
  rather than assuming zero forever.
- **European Union**: link-outs are permitted under entitlement programmes with their own fee
  structures, and the terms were scheduled to change materially on 1 October 2026.
- **Everywhere else, including South Africa**: no link-outs, no buttons, no "subscribe on our website"
  copy inside the app. You may email existing users about web pricing. Shipping a link-out to a
  non-permitted storefront is a rejection, and repeated offences escalate.

Google Play made a parallel change for the US in late 2025 with reporting and service fees phasing in
during 2026.

`references/store-rules.md` has the guideline numbers, the dates and the sources. It ages fast — treat
it as a starting point for verification, not as authority.

## Web: Stripe or Paystack

**Stripe does not onboard South African entities.** A ZA-registered business realistically chooses
Paystack, a local gateway, or a merchant-of-record such as Paddle if it needs global VAT handled.
Record the decision in `docs/app/stack.md`; it changes the schema of nothing but the plumbing of
everything.

**Stripe**, where available: hosted Checkout for subscriptions unless there is a real reason to own
the UI, the customer portal for cancel/upgrade/card changes rather than rebuilding it, and the
idempotency pattern of granting on checkout completion for instant UX while letting the invoice event
set the authoritative period end. Both writes are upserts keyed on the subscription, so order does not
matter. Apple and Google act as merchant of record and remit tax; Stripe does not unless you use its
managed-payments product, so tax registration is your problem.

**Paystack**, for South Africa and West/East Africa: initialise, redirect or open the inline popup,
and then **verify server-side before granting anything** — the callback URL is not proof of payment.
Webhooks are signed with SHA-512 over the raw body, from a fixed set of IPs.

Its subscription limitations are real and shape the product: a subscription needs a card
authorisation, so the cheapest local channels — instant EFT and bank-app pay — cannot back a recurring
plan; **a failed subscription charge is not retried**, so you write your own dunning; and there is no
proration or plan change, so an upgrade is a cancel and re-subscribe with the credit handled by you.
Design around these before promising an upgrade flow.

## The paywall screen

`onboarding-flow` decides where it goes. This skill decides what is on it.

Mandatory, or the app is rejected: product name and duration, price **and** billing period, the
post-trial price and trial length, functional **in-app** links to terms of use and privacy policy —
links on the App Store listing do not count — and a restore purchases affordance.

The common rejections are all versions of hiding the price: a free-trial toggle whose default state
conceals what is billed, a monthly-equivalent price shown for a yearly SKU, or the word "free" applied
to a paid trial.

Within those constraints: anchor weekly against annual and show the annual plan's per-week equivalent,
default-select annual, and put social proof on the screen immediately before. Default to a **7-day
trial** and test longer — the evidence favours much longer trials and almost nobody ships them.

Where the paywall sits in the flow, and the evidence on hard against freemium paywalls, is decided at
the product level by `onboarding-flow`, not on this screen. One hard constraint crosses both: if the
paywall spans multiple pages, **the page carrying the purchase button carries every disclosure**,
visible without scrolling or tapping. Price on page three is the top paywall rejection.

## Costs

RevenueCat is free below a monthly tracked-revenue threshold and then takes a percentage of tracked
revenue. Apple and Google take 30%, or 15% under their small-business programmes and on subscriptions
after twelve months — enrol in the small business programme on day one, it is free money and people
forget. Stripe and Paystack charge per transaction with a fixed component that matters at low prices.
`cost-control` has the table.

## Reference files

- `references/entitlements.md` — the table, the state machine, webhook handling, the reconcile job
- `references/revenuecat.md` — SDK setup, offerings, identity, offline entitlements, event semantics
- `references/store-rules.md` — external purchase rules by region, with dates and sources
- `references/stripe.md` — Checkout, portal, webhook idempotency, tax and merchant of record
- `references/paystack.md` — initialise/verify, webhooks, subscription limitations, ZA specifics
- `references/paywall-requirements.md` — the mandatory disclosures and the common rejections
- `assets/entitlements-template.md` — copy into `docs/app/entitlements.md` and fill it in

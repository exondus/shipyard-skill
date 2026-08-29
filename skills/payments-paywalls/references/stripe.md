# Stripe for the Web Half

Verified 29 August 2026. Stripe pricing and the Managed Payments (merchant-of-record) product changed in a June 2026 refresh; API versions pin behaviour, so check `https://stripe.com/pricing` and the current API changelog before quoting numbers or relying on webhook payload shapes.

## Availability caveat first

Stripe does **not** onboard South Africa-registered entities. `https://stripe.com/global` lists South Africa under **"extended network"** and links to Paystack rather than Stripe signup. If the business is ZA-registered, everything in this file applies only if you have an offshore entity (US/UK/EU/DE) with a real bank account and address; otherwise go to `paystack.md`. Do not architect around Stripe and discover this at onboarding.

## Checkout vs Payment Element vs Billing

| | Use when | Cost of ownership |
|---|---|---|
| **Checkout** (hosted, `stripe.checkout.sessions.create`) | Default for subscriptions. Hosted page or embedded component. SCA/3DS, Apple Pay/Google Pay, Link, tax, promo codes, address collection, localisation all handled. | Lowest. One API call, one redirect, one webhook. |
| **Payment Element** | You need the payment form inside your own multi-step flow, custom branding beyond Checkout's appearance API, or a non-standard money flow. | High: you own SCA handling, payment-method availability by country, error states, retries. Budget weeks, not days. |
| **Billing** | Not an alternative — the layer underneath. Products, prices, subscription schedules, proration, trials, dunning/Smart Retries, invoices, revenue recognition. | 0.7% of billing volume PAYG, or from ~$620/mo annual. |

Default recommendation: **Checkout in subscription mode, backed by Billing, with the Customer Portal for management.** Reach for Payment Element only when a concrete requirement forces it.

```ts
const session = await stripe.checkout.sessions.create({
  mode: 'subscription',
  line_items: [{ price: PRICE_ID, quantity: 1 }],
  customer: stripeCustomerId,             // create/reuse one per user_id — never per checkout
  client_reference_id: user.id,           // your uuid, echoed back on the webhook
  subscription_data: {
    trial_period_days: 14,
    metadata: { user_id: user.id, entitlement_key: 'pro' },
  },
  payment_method_collection: 'if_required', // card-less trial
  allow_promotion_codes: true,
  automatic_tax: { enabled: true },
  success_url: `${APP_URL}/welcome?session_id={CHECKOUT_SESSION_ID}`,
  cancel_url: `${APP_URL}/pricing`,
});
```

Put `user_id` in **both** `client_reference_id` and `subscription_data.metadata`. The first is only on the session; the second rides on every subsequent subscription and invoice event, which is what you actually need at renewal time three months later. Symptom of omitting it: renewal webhooks that you cannot map to a user without an extra API round-trip.

## The webhook set that matters

| Event | Do |
|---|---|
| `checkout.session.completed` | Provision immediately for UX. Treat as *intent* — for async payment methods the money may still fail. Check `payment_status === 'paid'` or `mode === 'subscription' && status === 'complete'`. |
| `invoice.paid` | **Authoritative.** Sets `current_period_end`, flips `trialing → active`. Every renewal comes through here. |
| `invoice.payment_failed` | → `billing_retry`. Keep access; Smart Retries are running. |
| `customer.subscription.updated` | Status transitions (`trialing`, `active`, `past_due`, `unpaid`, `canceled`, `paused`), plan changes, `cancel_at_period_end`. |
| `customer.subscription.deleted` | Access truly ends. |
| `customer.subscription.trial_will_end` | Fires ~3 days out. Your card-less-trial conversion hook. |
| `charge.refunded` / `charge.dispute.created` | → `refunded`. Revoke now. |
| `invoice.payment_action_required` | SCA needed — email the hosted invoice URL. |

Ignore `payment_intent.*` for subscriptions; the invoice events supersede them and subscribing to both produces double-processing.

## Grant-on-checkout, authoritative-on-invoice

Both handlers write the **same upsert keyed on the subscription id**, so order and duplication are irrelevant.

```ts
export async function POST(req: Request) {
  const raw = await req.text();                        // raw bytes — required
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      raw, req.headers.get('stripe-signature')!, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch { return new Response('bad signature', { status: 400 }); }

  await db.transaction(async (tx) => {
    // idempotency inside the same transaction as the write
    const seen = await tx.query(
      `INSERT INTO processed_events (source, event_id) VALUES ('stripe', $1)
       ON CONFLICT DO NOTHING RETURNING 1`, [event.id]);
    if (seen.rowCount === 0) return;                   // replay

    switch (event.type) {
      case 'checkout.session.completed': {
        const s = event.data.object as Stripe.Checkout.Session;
        if (s.mode !== 'subscription') break;
        const sub = await stripe.subscriptions.retrieve(s.subscription as string);
        await upsertEntitlement(tx, {
          userId: s.client_reference_id!,          // or sub.metadata.user_id
          source: 'stripe',
          providerSubId: sub.id,                   // ← the upsert key
          status: sub.status === 'trialing' ? 'trialing' : 'active',
          currentPeriodEnd: new Date(sub.current_period_end * 1000),
          autoRenew: !sub.cancel_at_period_end,
          lastEventAt: new Date(event.created * 1000),
        });
        break;
      }
      case 'invoice.paid': {
        const inv = event.data.object as Stripe.Invoice;
        if (!inv.subscription) break;
        const sub = await stripe.subscriptions.retrieve(inv.subscription as string);
        await upsertEntitlement(tx, {
          userId: sub.metadata.user_id,
          source: 'stripe',
          providerSubId: sub.id,                   // same key → idempotent
          status: 'active',
          currentPeriodEnd: new Date(sub.current_period_end * 1000),
          autoRenew: !sub.cancel_at_period_end,
          lastEventAt: new Date(event.created * 1000),
        });
        break;
      }
      // ...payment_failed → billing_retry, deleted → expired, refunded → refunded
    }
  });
  return new Response('ok');
}
```

Two guards that are not optional. First, the upsert must carry `WHERE entitlements.last_event_at < EXCLUDED.last_event_at` — Stripe delivers concurrently and `invoice.paid` frequently lands before `checkout.session.completed`. Second, re-retrieve the subscription rather than trusting the event payload for period boundaries; the payload is a snapshot from event time.

Also set an **idempotency key** on outbound writes (`stripe.subscriptions.create(params, { idempotencyKey })`) so a retried request from your own server does not create two subscriptions.

## Customer portal

```ts
const portal = await stripe.billingPortal.sessions.create({
  customer: stripeCustomerId,
  return_url: `${APP_URL}/account`,
});
```

Do not rebuild cancel / upgrade / downgrade / update-card / invoice-history. Configure the portal in the Dashboard (which plans are switchable, whether cancellation is immediate or at period end, whether a cancellation survey shows). Portal actions produce the same `customer.subscription.updated` webhooks, so your pipeline needs no special handling.

## Trials without a card

`payment_method_collection: 'if_required'` plus `trial_period_days` starts a trial with no card on file. Conversion mechanics:

- The subscription enters `trialing`; write status `trialing` and grant access.
- `customer.subscription.trial_will_end` fires ~3 days before. Email a Checkout/portal link to add a card.
- If no card by trial end, Stripe applies `trial_settings.end_behavior.missing_payment_method` — set it to `cancel` (clean) or `pause` (keeps the record). Default is `create_invoice`, which leaves an unpayable open invoice; set it explicitly.
- Card-less trials raise trial starts and lower trial→paid conversion. The mobile evidence is that *longer* trials convert better regardless (42.5% at 17–32 days vs 25.5% under 4 days — 2026 State of Subscription Apps), so pair card-less with a longer window rather than a 3-day one.

## Tax and merchant of record

This is the structural difference between web and mobile revenue, and it is a compliance obligation, not an accounting detail.

- **Apple and Google are merchant of record.** They collect and remit VAT/GST/sales tax worldwide, handle invoicing and refunds. You receive net proceeds and have no registration duty in the buyer's country. This is a large part of what the 15–30% buys.
- **Stripe is a payment processor, not MoR.** On a Stripe web sale *you* are the seller of record. You must register for VAT/GST where you cross thresholds (EU OSS, UK, ZA, AU, etc.), charge the right rate, and remit. **Stripe Tax** (0.5% per transaction, or Tax Complete from ~$90/mo) calculates and reports; it does not register or remit for you.
- **Stripe Managed Payments** is Stripe's MoR product (post-Lemon-Squeezy acquisition), separated from PSP fees in the June 2026 refresh. It adds **+3.5%** on top of standard fees — **6.4% + $0.30** domestic US, roughly 8.9–10% all-in international with FX. It covers indirect tax in 80+ countries and 35 product categories, plus disputes and transaction-level support. **Not available in most of Africa, most of Asia, or Latin America outside Mexico and Brazil.** https://stripe.com/pricing

So the naive "web checkout saves 30%" is wrong once tax is priced in: 2.9% + 0.30 + 0.7% Billing + 0.5% Tax ≈ 4.1% plus your own registration and filing cost, or ~6.4% under Managed Payments — still cheaper than 30%, roughly level with Apple's 15% SBP rate once accounting overhead is counted.

## Reconciling a web subscriber with mobile entitlements

Two viable routes:

**A. RevenueCat as the aggregator (recommended for mobile-first products).** Either use **RevenueCat Web Billing** for the web checkout, or keep Stripe and use RevenueCat's Stripe integration, which imports subscriptions created directly in Stripe as *external purchases* so they grant RC entitlements. Trials and coupons carry through to RC charts and events; you can configure whether the subscription registers at invoice creation or after payment. Not supported through RC web flows: tiered pricing, usage-based pricing, customer-chooses pricing. Web purchases redeem into the app via a one-click deep link or QR, emitting `WEB_PURCHASE_REDEEMED`. https://www.revenuecat.com/docs/web/integrations/stripe

**B. Your own table as the aggregator (recommended when Paystack is in the mix, which it is for ZA).** Stripe webhooks write `source='stripe'` rows; RevenueCat webhooks write `app_store`/`play_store` rows; Paystack writes `paystack` rows. `has_entitlement()` unions them. RevenueCat then only ever sees mobile revenue, which also keeps your MTR — and therefore your RevenueCat bill — down.

Either way, the mobile client must refresh after a web purchase: `customerInfo` is cached for 5 minutes and RevenueCat does not push. After returning from a web checkout, call your own `/me/entitlements` endpoint (authoritative) and `Purchases.getCustomerInfo()` (for RC-backed UI), and re-render on both.

Finally: never show a "subscribe on the web" CTA inside the iOS app outside the US and EU carve-outs (see `store-rules.md`). Web subscribers arriving from the web, email, or a browser are fine everywhere; the restriction is on in-app steering.

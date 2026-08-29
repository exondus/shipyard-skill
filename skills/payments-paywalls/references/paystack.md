# Paystack, and the South Africa Context

Verified 29 August 2026. Paystack's channel availability, pricing and country coverage change without notice; the subscription limitations below have been stable for years but confirm against https://paystack.com/docs before designing recurring billing on top of them.

## Why this file exists: Stripe is not available to ZA entities

`https://stripe.com/global` lists South Africa under **"extended network"**, and the link goes to Paystack rather than Stripe signup. A South Africa-registered company cannot open a standard Stripe account. Practical options for a ZA business:

| Option | Shape | Use when |
|---|---|---|
| **Paystack** | Local acquiring, ZAR settlement, Stripe-owned | Default. Best local conversion (EFT, Capitec Pay), real ZAR settlement. |
| **Peach Payments** | ZA PSP, broad local method coverage | You need debit orders / DebiCheck or enterprise ZA rails. |
| **Yoco** | ZA SME, card-present + online | Small merchant, in-person component. |
| **Ozow / Capitec Pay** | Instant-EFT rails, usually via a PSP | Cheapest per-transaction channel; **cannot back a subscription** (see below). |
| **Paddle / Lemon Squeezy / Polar** | Merchant of record | Selling globally to consumers/SaaS and you want VAT/GST registration and remittance handled. Accepts ZA-based sellers. |
| **Offshore entity + Stripe** | UK/US/EE company | Only if you genuinely need Stripe Billing's proration, usage billing, or Managed Payments. Real cost: incorporation, banking, transfer pricing, SARS exchange-control paperwork. |

For a mobile-first product where the majority of revenue is IAP, the pragmatic ZA stack is **RevenueCat for Apple/Google + Paystack for the ZA/Africa web checkout**, with a MoR only if a large share of web revenue is EU/UK consumer.

## Availability and channels

| Country | Channels | Currency |
|---|---|---|
| **South Africa** | Card (Visa/Mastercard/Amex), **EFT**, **QR code**, **Capitec Pay** | ZAR |
| **Nigeria** | Card (Visa/Mastercard/Verve/Amex), Bank account, Pay with Transfer, USSD, Mobile money, **Direct Debit** | NGN |
| **Ghana** | Card, Mobile money, Pay with Transfer | GHS |
| **Kenya** | Card, Mobile money (**M-PESA**), Pay with Pesalink | KES |
| **Côte d'Ivoire** | Card, Mobile money | XOF (varies by channel) |

Cards work on every account; other channels require the account to be in that country and sometimes explicit enablement (Pesalink, Capitec Pay). Source: https://paystack.com/docs/payments/payment-channels/

**There is no mobile money in South Africa.** If you are reasoning by analogy from Nigeria or Kenya, EFT and Capitec Pay are the ZA equivalents and they behave very differently — see subscriptions.

## ZA pricing

| | Rate |
|---|---|
| Local card | **2.9% + R1** (ex VAT); the R1 is waived under R10 |
| **Capitec Pay / Ozow EFT** | **2% flat, no fixed fee** |
| International card | **3.1% + R1** (ex VAT), settled in ZAR by default |
| Bank transfer (payout instruction) | R3 per transfer, success or failure |
| Settlement | **T+2 working days**; payouts free; no setup or monthly fee |

Source: https://paystack.com/za/pricing

## Payment flow: initialize → redirect or inline → **server-side verify**

```ts
// 1. Server: initialize
const res = await fetch('https://api.paystack.co/transaction/initialize', {
  method: 'POST',
  headers: { Authorization: `Bearer ${SECRET_KEY}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: user.email,
    amount: 19900,                 // ← CENTS. R199.00 = 19900. NOT 199.
    currency: 'ZAR',
    reference: ourReference,       // your idempotent id — store it BEFORE calling
    callback_url: `${APP_URL}/pay/return`,
    channels: ['card', 'eft', 'qr'],
    metadata: { user_id: user.id, entitlement_key: 'pro' },
    // plan: 'PLN_xxxx'            // ← adding a plan turns this into a subscription
  }),
});
const { data } = await res.json();  // { authorization_url, access_code, reference }
```

**The unit trap:** `amount` is in the currency's minor unit — kobo for NGN, **cents for ZAR**, pesewas for GHS. Passing `199` charges R1.99. There is no validation that catches this; the symptom is a successful transaction for 1/100th of the price, discovered at settlement. Wrap it: `const toMinor = (rands: number) => Math.round(rands * 100);` and never pass a raw number.

Two front ends from the same `access_code`:

- **Redirect**: send the browser to `data.authorization_url`. Simplest, works everywhere, required for some channels.
- **Inline / popup**: `PaystackPop.setup({ key: PUBLIC_KEY, access_code })` keeps the user on your page. Better conversion on desktop web. In an Expo app use a `WebBrowser.openAuthSessionAsync` on the authorization URL rather than embedding the popup script.

```ts
// 3. Server: verify. This is the ONLY thing that authorises a grant.
const v = await fetch(`https://api.paystack.co/transaction/verify/${reference}`,
  { headers: { Authorization: `Bearer ${SECRET_KEY}` } }).then(r => r.json());
if (v.data.status === 'success' && v.data.amount === expectedMinorUnits
    && v.data.currency === 'ZAR') { grant(); }
```

**The `callback_url` is not proof of payment.** It is a browser redirect that a user can hit by typing the URL. Always verify server-side, and always check the amount and currency against what you expected — not just `status === 'success'`. Symptom of trusting the callback: free subscriptions handed out to anyone who inspects the return URL.

Store the transaction row with your `reference` *before* initializing, so an abandoned or duplicated attempt is reconcilable.

## Webhooks

- Header: **`x-paystack-signature`**
- Algorithm: **HMAC-SHA512** over the **raw request body**, keyed with your **secret key**
- Allowlist source IPs: `52.31.139.75`, `52.49.173.169`, `52.214.14.220` (same in test and live)
- Retries — **live**: every 3 minutes ×4, then hourly for a total of 72 hours. **Test**: hourly for 10 hours, 30s timeout per attempt.
- Return **200 immediately**; do the work asynchronously or fast.

```ts
import crypto from 'node:crypto';
const hash = crypto.createHmac('sha512', SECRET_KEY).update(raw).digest('hex');
if (hash !== req.headers.get('x-paystack-signature')) return new Response(null, { status: 401 });
```

Events you care about: `charge.success`, `subscription.create`, `subscription.disable`, `subscription.not_renew`, `subscription.expiring_cards` (monthly digest), `invoice.create`, `invoice.update`, `invoice.payment_failed`, `refund.processed`, `charge.dispute.create|remind|resolve`. Source: https://paystack.com/docs/payments/webhooks/

Paystack event payloads do not carry a stable top-level event id in the way Stripe does; key your `processed_events` row on `(source='paystack', event_id = data.reference ?? data.id ?? sha256(raw))` so replays are still idempotent.

## Subscription limitations — read every line

Source: https://paystack.com/docs/payments/subscriptions/ and https://paystack.com/docs/payments/recurring-charges/

1. **An authorization is mandatory, and only cards and Nigerian Direct Debit produce one.** "Paystack uses card and direct debit authorizations to charge customers, so there needs to be an existing authorization to charge." **EFT, Capitec Pay, Ozow, QR, USSD and Pay-with-Transfer cannot back a subscription.** This is the single biggest ZA design constraint: your cheapest channel (2% flat) is one-off only, and recurring billing forces card at 2.9% + R1. If your ZA users prefer EFT, either sell annual one-off payments over EFT and handle renewal as a fresh charge, or accept card-only for subscribers.
2. **A failed subscription charge is not retried.** "If a subscription charge fails, we don't retry it." There is no dunning, no Smart Retries, no grace period. You build it (see below) or you silently lose the customer.
3. **No proration and no plan change.** There is no upgrade/downgrade API. To change plan you disable the subscription and create a new one on the existing authorization, and you compute and apply any credit yourself.
4. **Month-end renewal dates collapse.** Monthly subscriptions created on or before the 28th renew on that date; those created on the **29th, 30th or 31st renew on the 28th**. Your `current_period_end` must come from Paystack's next payment date, not from `dateAdd(start, 1 month)`.
5. Intervals: hourly, daily, weekly, monthly, quarterly, biannually, annually.
6. Cancellation emits `subscription.not_renew`, then `subscription.disable` at period end. Only `disable` ends access.
7. Customers with multiple authorizations: specify which to charge, or Paystack picks one — which may be an expired card.
8. `subscription.expiring_cards` arrives monthly with cards expiring soon. This is your only advance warning; wire it to an email.
9. Currency: international cards settle to ZAR by default. If you price in USD you carry FX on settlement.

## Write your own dunning

Because Paystack does not retry, the retry loop is yours. Minimum viable implementation:

- **Trigger** on `invoice.payment_failed` / `charge.failed` for a subscription reference. Move to `billing_retry` with `grace_until = now() + 14 days` and **keep access**. Revoking on first failure destroys recoverable revenue.
- **Retry** via `POST /transaction/charge_authorization` with the stored `authorization_code`: days 1, 3, 5, 7, 10, 14. Randomise the hour — issuers decline repeat attempts at identical times.
- **Stop early** on hard declines (invalid `authorization_code`, card lost/stolen, repeated "do not honour") and go straight to the update-card email.
- **Communicate** at failure, day 3 and day 10: in-app banner plus a one-tap "update card" link that runs a fresh `transaction/initialize` for a R1 authorisation charge, then swaps the stored `authorization_code`.
- **Expire** at `grace_until`; **recover** on any `charge.success` for that subscription (back to `active`, extend `current_period_end`, clear `grace_until`).
- **Pre-empt** using `subscription.expiring_cards` — email 30 days out. Cheaper than any retry.

Log every attempt with `reference`, `gateway_response` and the HTTP body; Paystack decline reasons are terse and you will need the history for support tickets.

## Do not

- Do not use `callback_url` as authorisation. Verify.
- Do not pass rands where cents are expected.
- Do not offer EFT/Capitec on a page that creates a subscription — it will succeed once and never renew, and the symptom is a cohort of "subscribers" whose second month never arrives.
- Do not assume mobile money exists in ZA.
- Do not build proration logic against the API; it isn't there.
- Do not skip the IP allowlist — the HMAC is your real defence, but the allowlist is free.

# Entitlement Storage, Webhooks and Reconciliation

Verified 29 August 2026. The schema and patterns here are stable engineering practice; the provider-specific field names and webhook retry schedules change — verify against RevenueCat, Stripe and Paystack docs before implementing.

## Principle

Your Postgres row is the only thing your API is allowed to authorise against. RevenueCat's `customerInfo`, Stripe's subscription object and Paystack's transaction record are *inputs*. Never call a provider API inside a request-path authorisation check: it adds 100–800ms, it fails when the provider does, and it makes your access rules untestable.

## DDL

```sql
CREATE TYPE entitlement_source AS ENUM
  ('app_store','play_store','stripe','rc_web','paystack','promo','admin');

CREATE TYPE entitlement_status AS ENUM
  ('trialing','active','grace','billing_retry','paused',
   'cancelled','expired','refunded');

CREATE TABLE entitlements (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            uuid NOT NULL REFERENCES users(id),
  entitlement_key    text NOT NULL,               -- 'pro', 'team'. Matches RC entitlement id.
  source             entitlement_source NOT NULL,
  status             entitlement_status NOT NULL,
  product_id         text,                        -- store SKU / Stripe price / Paystack plan code
  -- subscription identity within that source. The upsert key.
  provider_sub_id    text NOT NULL,               -- original_transaction_id | sub_xxx | subscription_code
  period_start       timestamptz,
  current_period_end timestamptz,                 -- may be in the PAST while status='grace'
  grace_until        timestamptz,
  trial_end          timestamptz,
  auto_renew         boolean NOT NULL DEFAULT true,
  environment        text NOT NULL DEFAULT 'production',  -- 'sandbox' rows must never grant
  last_event_at      timestamptz NOT NULL,        -- provider event timestamp, NOT now()
  raw                jsonb NOT NULL DEFAULT '{}',
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source, provider_sub_id)
);

CREATE INDEX ON entitlements (user_id, entitlement_key)
  WHERE status IN ('trialing','active','grace','billing_retry');
CREATE INDEX ON entitlements (current_period_end)
  WHERE status IN ('trialing','active','grace','billing_retry');

CREATE TABLE processed_events (
  source     entitlement_source NOT NULL,
  event_id   text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (source, event_id)
);
```

`UNIQUE (source, provider_sub_id)` is what makes replayed and out-of-order webhooks safe: every write is an upsert on that key, so a duplicate `RENEWAL` is a no-op rather than a second row granting a second month.

## Effective access is a predicate over your row

```sql
CREATE OR REPLACE FUNCTION has_entitlement(p_user uuid, p_key text)
RETURNS boolean LANGUAGE sql STABLE AS $$
  SELECT EXISTS (
    SELECT 1 FROM entitlements
    WHERE user_id = p_user
      AND entitlement_key = p_key
      AND environment = 'production'
      AND (
        status IN ('trialing','active')
        OR (status IN ('grace','billing_retry')
            AND coalesce(grace_until, current_period_end + interval '16 days') > now())
      )
  );
$$;
```

Note what is **not** in the predicate: `current_period_end > now()`. During Apple/Google billing retry and grace, the period end is in the past and the user is still entitled. If you gate on the date you will lock out every user whose card bounced, which is 14% of App Store cancellations and 31% of Google Play ones (https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026, 2026 report).

## Status state machine

```
                 ┌──────────┐  trial converts   ┌────────┐
  purchase ─────▶│ trialing │──────────────────▶│ active │◀──── renewal
                 └────┬─────┘                   └──┬──┬──┘
                      │ trial cancelled            │  │ auto-renew off
                      ▼                            │  ▼
                 ┌─────────┐                       │ ┌───────────┐  period end
                 │ expired │◀──────────────────────┼─│ cancelled │────────────▶ expired
                 └─────────┘        period end     │ └───────────┘
                      ▲                            │ payment fails
                      │ grace/retry exhausted      ▼
                      │                    ┌───────────────┐  card recovers
                      └────────────────────│ grace /       │──────────────▶ active
                                           │ billing_retry │
                                           └───────────────┘
  any state ── refund / revoke ──▶ refunded   (immediate loss of access)
  active ──── Google pause ──────▶ paused     (no access, resumes later)
```

Rules that trip people up:

| Transition | Reality |
|---|---|
| `cancelled` | Auto-renew turned off. **Access continues to `current_period_end`.** Do not revoke. |
| `grace` / `billing_retry` | `current_period_end` is in the past. Access continues to `grace_until`. Apple grace is 16 days for monthly+, 6 days for weekly [UNVERIFIED — confirm current App Store Connect values]; Google's grace + account-hold window is configurable per app. |
| `refunded` | The only status that revokes immediately. Sources: RevenueCat `CANCELLATION` with `cancel_reason: CUSTOMER_SUPPORT`, Stripe `charge.refunded`, Apple `REFUND` notification. |
| `paused` | Google Play pause only. No access, but do not delete the row — a `RESUME`/`RENEWAL` follows. |

## Webhook handling

Three rules, applied identically to RevenueCat, Stripe and Paystack.

**1. Verify over the raw body.** All three sign the exact bytes. Reading `req.body` after a JSON body-parser and re-serialising changes whitespace and key order, and the HMAC will never match. Symptom: signature verification fails 100% of the time in production while your unit test passes.

```ts
// Next.js App Router — route handlers give you the raw body via req.text()
export async function POST(req: Request) {
  const raw = await req.text();                       // raw bytes, do not parse first
  const sig = req.headers.get('x-paystack-signature'); // or stripe-signature
                                                       // or x-revenuecat-webhook-signature
  if (!verify(raw, sig)) return new Response('bad signature', { status: 401 });
  const event = JSON.parse(raw);
  ...
}
```

Algorithms differ: Stripe `stripe-signature` = HMAC-SHA256 over `t.payload` with timestamp tolerance; RevenueCat `X-RevenueCat-Webhook-Signature` = timestamp + SHA256 HMAC over raw body (https://www.revenuecat.com/docs/integrations/webhooks); Paystack `x-paystack-signature` = HMAC-SHA512 over the raw body with your **secret key** (https://paystack.com/docs/payments/webhooks/).

**2. Idempotency inside the same transaction as the write.** Insert the event id first; a unique-violation means you have already processed it and should return 200 immediately.

```ts
await db.transaction(async (tx) => {
  const ins = await tx.query(
    `INSERT INTO processed_events (source, event_id) VALUES ($1,$2)
     ON CONFLICT DO NOTHING RETURNING 1`, [source, eventId]);
  if (ins.rowCount === 0) return;            // duplicate delivery, already applied
  await applyEntitlement(tx, event);
});
```

Doing the dedupe check *before* the transaction, or in Redis, reintroduces the race: two concurrent retries both read "not seen" and both grant.

**3. Delivery is unordered. Guard on the provider's event timestamp, not `now()`.** RevenueCat explicitly makes no ordering guarantee, and cancellations can lag ~2 hours while renewals arrive in seconds — so a stale `CANCELLATION` routinely lands *after* the `RENEWAL` that superseded it.

```sql
INSERT INTO entitlements AS e (user_id, entitlement_key, source, status, provider_sub_id,
                               current_period_end, grace_until, auto_renew, last_event_at, raw)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
ON CONFLICT (source, provider_sub_id) DO UPDATE SET
  status             = EXCLUDED.status,
  current_period_end = EXCLUDED.current_period_end,
  grace_until        = EXCLUDED.grace_until,
  auto_renew         = EXCLUDED.auto_renew,
  last_event_at      = EXCLUDED.last_event_at,
  raw                = EXCLUDED.raw,
  updated_at         = now()
WHERE e.last_event_at < EXCLUDED.last_event_at;   -- stale event: no-op
```

Symptom if you omit the `WHERE`: users randomly lose access minutes after a successful renewal, and it is unreproducible locally.

## Nightly reconcile

Webhooks are lossy. RevenueCat retries 5 times (5/10/20/40/80 minutes) then gives up; Paystack retries for 72 hours; a deploy during that window silently drops events. Run a job that re-pulls state for every row whose period is about to end or has just ended.

```sql
SELECT id, user_id, source, provider_sub_id, status, current_period_end
FROM entitlements
WHERE environment = 'production'
  AND (
       (status IN ('trialing','active','grace','billing_retry')
        AND current_period_end < now() + interval '48 hours')
    OR (status IN ('grace','billing_retry') AND grace_until < now() + interval '24 hours')
    OR updated_at < now() - interval '30 days'      -- drift sweep
  )
ORDER BY current_period_end
LIMIT 5000;
```

For each row, fetch authoritative state and apply the same upsert with `last_event_at = now()`:

- `source IN ('app_store','play_store','rc_web')` → RevenueCat `GET /v1/subscribers/{app_user_id}` (or v2 `/projects/{id}/customers/{id}`). RevenueCat's own docs recommend this follow-up read after webhooks rather than trusting the payload alone.
- `source = 'stripe'` → `stripe.subscriptions.retrieve(provider_sub_id)`.
- `source = 'paystack'` → `GET /subscription/:code`.

Alert if the job flips more than ~1% of rows in a run; that means webhook delivery is broken, not that users churned.

## One user, two providers

A user subscribing on iOS and later on web is common (they forget, or they want the web price). Your unique key is `(source, provider_sub_id)`, so both rows coexist — this is correct and intentional. `has_entitlement` is an `EXISTS`, so access is the union.

Handle it explicitly:

1. **Detect at write time.** After upserting, count other active rows for the same `(user_id, entitlement_key)` from a different `source`. If >1, write a `duplicate_entitlement` record for support.
2. **Never auto-cancel the store subscription.** You cannot cancel an Apple or Google subscription from your server; only the user can, in system settings. Attempting to "clean up" by revoking access instead just breaks a paying customer.
3. **Do cancel the one you control.** If the newer purchase is Apple/Google and the older is Stripe or Paystack, cancel the Stripe/Paystack subscription and refund the unused portion — that is the one you can actually stop.
4. **Show it in the UI.** On the account screen, render the *managing* source ("You're subscribed via the App Store — manage in Settings") derived from the row with the latest `period_start`, and surface the duplicate with a support link.
5. **RevenueCat `TRANSFER` events** move transactions between app user IDs and will change which `user_id` an `app_store` row belongs to. Handle `TRANSFER` by re-reading the subscriber and rewriting `user_id` on the affected row — do not create a second row.

Also guard `environment`: sandbox and TestFlight purchases arrive as real webhooks with `environment: SANDBOX`. Store them, never let them satisfy `has_entitlement` in production. Symptom if ignored: reviewers and internal testers appear as paying customers and your MRR chart is wrong.

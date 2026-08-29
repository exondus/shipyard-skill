# Entitlements — <app name>

Written <date>. Last verified against live store rules <date>.

The one file that answers "what does this user get, and who says so". Every payments change edits this
file in the same commit. Store payment rules change every few months — the decisions log at the bottom
exists so the next person can tell a current answer from a stale one.

**Source of truth:** the `entitlements` table in Postgres. RevenueCat, Stripe and Paystack are inputs.
No request-path authorisation calls a payment provider.

---

## Products

One row per store SKU. Prices are the tier at time of writing, not a contract.

| Product | Apple product ID | Google product ID / base plan | Stripe price ID | Paystack plan code | Price | Period |
|---|---|---|---|---|---|---|
| <Pro Annual> | <com.x.pro.annual> | <pro / annual> | <price_...> | <PLN_...> | <> | 1 year |
| <Pro Monthly> | | | | | | 1 month |
| <Pro Weekly> | | | | | | 1 week |

**Introductory offer:** <7-day free trial on annual only> — configured in App Store Connect and Play
Console per product. Trial length lives in the store, not in code.

## Offerings

RevenueCat offerings are remotely configurable. Record which is live so a dashboard change is traceable.

| Offering ID | Packages | Current? | Audience / experiment | Set by | Date |
|---|---|---|---|---|---|
| `default` | `$rc_annual`, `$rc_weekly` | ✅ | all | | |
| <`winback`> | | | <Targeting: lapsed> | | |

## Entitlements

The identifiers the code checks. **Gate on these, never on product IDs.**

| Key | Unlocks | Granted by |
|---|---|---|
| `<pro>` | <the specific features, listed> | all Pro products, any source |
| | | |

Feature flags that are *not* entitlements (free-tier limits, kill switches) live in <remote config>, not here.

## Source of truth

`entitlements` table — see the `payments-paywalls` skill's `references/entitlements.md` for the DDL.

| Column | Notes for this project |
|---|---|
| `user_id` | <Clerk user id / internal uuid>. Also the RevenueCat `appUserID`. |
| `entitlement_key` | matches the table above |
| `source` | `app_store` · `play_store` · `stripe` · `rc_web` · `paystack` · `promo` · `admin` |
| `provider_sub_id` | Apple `original_transaction_id` · Stripe `sub_...` · Paystack `subscription_code` |
| `status` | `trialing` `active` `grace` `billing_retry` `paused` `cancelled` `expired` `refunded` |
| `environment` | sandbox rows exist and must never grant in production |

Access predicate: `has_entitlement(user_id, key)` in <schema/file>. It must **not** compare
`current_period_end` to `now()` — grace and billing retry run past the period end.

## Webhooks

| Provider | Endpoint | Signature | Secret location |
|---|---|---|---|
| RevenueCat | `<POST /api/webhooks/revenuecat>` | HMAC-SHA256 `X-RevenueCat-Webhook-Signature` over raw body | `<RC_WEBHOOK_SECRET>` in <1Password / EAS secrets / Vercel env> |
| Stripe | `<POST /api/webhooks/stripe>` | `stripe-signature`, `constructEvent` over raw body | `<STRIPE_WEBHOOK_SECRET>` |
| Paystack | `<POST /api/webhooks/paystack>` | HMAC-SHA512 `x-paystack-signature` over raw body, keyed with the **secret key** | `<PAYSTACK_SECRET_KEY>` |

Every handler: raw body → verify → insert event id into `processed_events` inside the write
transaction → upsert on `(source, provider_sub_id)` guarded by `last_event_at`.

**Paystack IP allowlist:** `52.31.139.75`, `52.49.173.169`, `52.214.14.220`.

**Reconcile job:** `<name>`, runs `<0 3 * * *>`, re-pulls provider state for rows ending within 48h.
Alerts if it flips more than `<1%>` of rows.

## Trial and grace configuration

| Setting | Value | Where it is set |
|---|---|---|
| Free trial length | <7 days> | App Store Connect + Play Console, per product |
| Apple billing grace period | <on / 16 days> | App Store Connect → Subscriptions |
| Google grace period | <on / 7 days> | Play Console → Subscription settings |
| Google account hold | <30 days> | Play Console |
| Stripe dunning | <Smart Retries, 4 attempts / 21 days> | Stripe Dashboard → Billing → Revenue Recovery |
| Paystack dunning | **you build it** — <days 1/3/5/7/10/14 via `charge_authorization`> | `<file>` |
| `grace_until` default when a provider sends none | <14 days> | `<file>` |

Paystack does not retry failed subscription charges. If the row above is empty, ZA card churn is silent.

## Regional payment posture

Verified <date>. Re-verify before every release — see `references/store-rules.md`.

| Storefront | IAP | In-app link-out CTA | Web processor for that region |
|---|---|---|---|
| US (iOS) | required in-app | **allowed**, currently 0% commission — assume 5–15% lands | <Stripe> |
| EU (iOS) | required in-app | allowed under entitlement; terms change 1 Oct 2026 | <Stripe> |
| ZA / rest (iOS) | **required** | **prohibited** | <Paystack>, non-app traffic only |
| US (Android) | optional since 9 Dec 2025 | allowed; fees phase in 1 Oct 2026 | <Stripe> |
| Rest (Android) | required | prohibited | <Paystack> |

**Link-out gate:** `<flag name>`, read from <remote config>, keyed on `SKStorefront.countryCode`
(**not** locale, **not** IP). Default off. Flipping it must not require an app release.

**Merchant of record:** Apple and Google remit tax on IAP. On <Stripe / Paystack> we are the seller of
record and owe VAT/GST registration in <list jurisdictions and thresholds>. Owner: <name>.

## Decisions log

| Date | Decision | Why | Source checked |
|---|---|---|---|
| <2026-08-29> | <Paystack for web, no Stripe> | <ZA-registered entity; Stripe lists SA as "extended network"> | <https://stripe.com/global> |
| | | | |

## Verify before each release

- [ ] `has_entitlement` does **not** compare `current_period_end` to `now()`; grace and retry still grant
- [ ] Sandbox / TestFlight rows cannot grant in production (`environment` filter present and tested)
- [ ] All three webhook handlers verify over the **raw** body; a re-serialised-body test fails as expected
- [ ] `processed_events` insert is inside the same transaction as the entitlement write
- [ ] Upsert carries the `last_event_at` staleness guard (replay an old `CANCELLATION` after a `RENEWAL`)
- [ ] Reconcile job ran in the last 24h and flipped < `<1%>` of rows
- [ ] Restore Purchases works on a fresh device, signed in, with nothing to restore (shows a message)
- [ ] Paywall carries every 3.1.2 disclosure on the page with the CTA, at largest Dynamic Type
- [ ] Link-out CTA renders **only** where the table above says it may; verified by switching storefront
- [ ] Store rules re-read and the "Last verified" date at the top of this file updated
- [ ] Trial, grace and account-hold settings in App Store Connect / Play Console match this file
- [ ] Paystack dunning schedule is live (or web billing is card-only and that is a deliberate decision)

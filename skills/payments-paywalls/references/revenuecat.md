# RevenueCat in Expo / React Native

Verified 29 August 2026. SDK versions move weekly — re-check npm before pinning. Feature availability (Virtual Currencies, Funnels, Web Billing MoR) changed materially in the June 2026 release and will change again.

## Packages and build requirement

| Package | Version | Notes |
|---|---|---|
| `react-native-purchases` | **10.8.1** (2026-08-27) | Core SDK. `hotfix` dist-tag pins the 8.12.0 line. |
| `react-native-purchases-ui` | **10.8.1** (2026-08-27) | Paywalls v2 renderer. Optional but required for remote paywalls. |

Source: `https://registry.npmjs.org/react-native-purchases`. Install with `npx expo install react-native-purchases react-native-purchases-ui` so Expo picks the SDK-compatible range.

Both ship an Expo config plugin, so no manual native edits — but they contain native modules, which means **a development build (`expo-dev-client`) or a production build. Purchases cannot execute in Expo Go.** Recent SDKs add a *Preview API Mode*: the SDK detects Expo Go and swaps native calls for JS mocks so a paywall renders for layout work. It returns fake data; no transaction occurs, no entitlement is granted. https://www.revenuecat.com/docs/getting-started/installation/expo

Symptom if you skip the rebuild after installing: `TypeError: null is not an object (evaluating 'RNPurchases.setupPurchases')` — hot reload does not link new native code. Rebuild, don't debug.

## Object model

```
Store product (com.app.pro.annual, price, duration)
   └─ Package        ($rc_annual / $rc_monthly / custom id) — one product per platform
        └─ Offering  ("default", "black_friday") — the set of packages you show
             ↓ grants
        Entitlement  ("pro") — the thing your code checks
```

**Gate on entitlement identifiers, never product IDs.** `customerInfo.entitlements.active['pro']` survives you adding a new price point, running an experiment, launching on a new store, or grandfathering a legacy SKU. `productIdentifier === 'com.app.pro.annual'` breaks on all five. Offerings are remotely configurable, so pricing changes ship without an app release; entitlement identifiers are the stable contract between the dashboard and your code.

## Configure and identity

```ts
import Purchases, { LOG_LEVEL } from 'react-native-purchases';

if (__DEV__) Purchases.setLogLevel(LOG_LEVEL.DEBUG);

Purchases.configure({
  apiKey: Platform.select({ ios: RC_IOS_KEY, android: RC_ANDROID_KEY })!,
  appUserID: session?.userId ?? null,   // null → anonymous
});

// after sign-in
const { customerInfo, created } = await Purchases.logIn(user.id);
// after sign-out
await Purchases.logOut();
```

Configure once, at module scope or in a root effect. Use your own stable user UUID as `appUserID` — not an email, not a phone number (PII in RevenueCat's dashboard and webhooks), not a device id.

### The anonymous-alias problem, concretely

If `appUserID` is null, RevenueCat mints `$RCAnonymousID:9f3c…`. Concrete failure:

1. User buys annual before signup. Purchase attaches to `$RCAnonymousID:A`.
2. They sign up; `logIn('user-123')` aliases `A → user-123`. Fine.
3. They reinstall. New anonymous id `B`. They tap Restore *before* signing in — the Apple receipt attaches the transaction to `B`.
4. They sign in. `user-123` and `B` both claim the same `original_transaction_id`. RevenueCat **transfers** it and fires `TRANSFER`; depending on your project's transfer-behaviour setting, the other id loses the entitlement.
5. Your Postgres `app_store` row now points at whoever lost the race. The user emails support saying they paid and have nothing.

Mitigations: require sign-in before the paywall where the funnel tolerates it; always `logIn` before `purchasePackage` and `restorePurchases`; handle `TRANSFER` by re-reading the subscriber and rewriting `user_id` rather than inserting; and set transfer behaviour (keep-with-original vs transfer-to-new) deliberately. https://www.revenuecat.com/docs/customers/user-ids

## customerInfo, caching, offline

```ts
const info = await Purchases.getCustomerInfo();
const isPro = typeof info.entitlements.active['pro'] !== 'undefined';

Purchases.addCustomerInfoUpdateListener((info) => { /* re-render */ });
```

- Cache TTL is **5 minutes**. The SDK refreshes when you call `getCustomerInfo()`, complete a purchase, or restore — and it refreshes on app foreground, so calling `getCustomerInfo()` frequently is cheap and usually hits cache.
- The listener is *not* a push channel. "CustomerInfo updates are not pushed to your app from the RevenueCat backend; updates can only happen from an outbound network request to RevenueCat." A web purchase completed in Safari will not appear on the phone until the app makes a request — foreground the app or call `getCustomerInfo()` after returning from a web checkout.
- **Offline Entitlements**: if RevenueCat's servers are unreachable, the SDK verifies the Apple/Google/Amazon purchase locally and grants the entitlement temporarily, automatically. Limits: subscriptions only (not consumables or non-consumables), only for purchases made on that device/store, and **cross-platform purchases are invisible offline** — a user who bought on web will appear unentitled during an RC outage. Everything syncs on recovery. https://www.revenuecat.com/docs/customers/customer-info

Do not persist `customerInfo` yourself as a substitute for your server. Use it for instant UI only; the server gate is your Postgres row.

## Restore purchases

```ts
const info = await Purchases.restorePurchases();
```

Required by Apple (see `paywall-requirements.md`): a visible "Restore Purchases" control on the paywall and in settings. With a real `appUserID` it is mostly redundant — entitlements follow the user — but its absence is a routine 3.1.2 rejection. Restore also triggers the alias/transfer machinery above, so call it only after `logIn`.

## Feature surface (as of the June 2026 release)

| Feature | What it is |
|---|---|
| **Paywalls v2** | Remote, native, versioned paywall templates rendered by `react-native-purchases-ui`. GA. Ship copy/layout/price changes without an app release. Adds an **AI Editor** (conversational paywall authoring) and **Paywall Rules** (conditional component visibility on preset/custom variables). https://www.revenuecat.com/blog/growth/announcing-revenuecat-paywalls-v2 |
| **Targeting** | Map an audience (country, app version, attributes) to a specific offering. Deterministic, not an experiment. |
| **Experiments** | A/B tests on offerings/paywalls. Now reports **pLTV winner predictions with credible intervals** and one-click rollout. Fires `EXPERIMENT_ENROLLMENT` webhooks. |
| **Virtual Currencies** | GA. Server-held balances for coins/credits, with `VIRTUAL_CURRENCY_TRANSACTION` webhooks on purchase and refund. |
| **Funnels** | Hosted multi-step web onboarding with A/B testing — the web-to-app funnel pattern. |
| **Web Billing** | RevenueCat's own web checkout: hosted paywalls, Apple/Google Pay express checkout, discount codes, invoicing, and a Stripe **Managed Payments** merchant-of-record option that handles tax. Web purchases redeem into the app in one click via deep link or QR (`WEB_PURCHASE_REDEEMED`). https://www.revenuecat.com/billing |
| **Stripe integration** | Imports subscriptions created directly in Stripe as *external purchases*, so they grant RC entitlements. Trials and coupons carry over. Not supported through RC web flows: tiered pricing, usage-based pricing, customer-chooses pricing. https://www.revenuecat.com/docs/web/integrations/stripe |

Pricing: free to **$2,500 monthly tracked revenue**, then **1% of MTR**; Enterprise is custom. https://www.revenuecat.com/pricing/

## Webhook events

Source: https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields

| Event | Meaning / trap |
|---|---|
| `INITIAL_PURCHASE` | First purchase of a subscription. |
| `RENEWAL` | Successful renewal, including recovery after a billing issue. |
| `CANCELLATION` | **Auto-renew turned off — NOT loss of access.** Access runs to `expiration_at_ms`. Check `cancel_reason`: `UNSUBSCRIBE`, `BILLING_ERROR`, `CUSTOMER_SUPPORT` (refund — revoke now), `PRICE_INCREASE`, `DEVELOPER_INITIATED`. Can arrive ~2 hours late. |
| `UNCANCELLATION` | User re-enabled auto-renew before expiry. |
| `NON_RENEWING_PURCHASE` | Consumable / non-consumable / non-renewing sub. |
| `SUBSCRIPTION_PAUSED` | Google Play pause. No access, resumes later — do not delete the row. |
| `EXPIRATION` | Access actually ends. `expiration_reason` mirrors the cancel reasons plus `SUBSCRIPTION_PAUSED`, `UNKNOWN`. |
| `BILLING_ISSUE` | Payment failed; store is retrying. Carries nullable `grace_period_expiration_at_ms`. **Keep the entitlement** until that passes. |
| `PRODUCT_CHANGE` | Upgrade/downgrade/crossgrade. Update `product_id`, keep the same `provider_sub_id`. |
| `SUBSCRIPTION_EXTENDED` | Store-granted extension (e.g. Apple outage credit). |
| `REFUND_REVERSED` | A refund was reversed — re-grant. |
| `INVOICE_ISSUANCE` | Invoice generated (web/Stripe paths). |
| `TRANSFER` | Transactions moved between app user IDs. Rewrite `user_id`; do not insert. |
| `TEMPORARY_ENTITLEMENT_GRANT` | RC granted access during a store outage. Treat as active but expect a correcting event. |
| `VIRTUAL_CURRENCY_TRANSACTION` | Balance adjustment from purchase or refund. |
| `EXPERIMENT_ENROLLMENT` | Experiment assignment. |
| `WEB_PURCHASE_REDEEMED` | Web purchase linked to an app user. |
| `PRICE_INCREASE_CONSENT` | User accepted/declined a price increase. |
| `TEST` | Dashboard test event — must not grant. |
| `SUBSCRIBER_ALIAS` | Deprecated. |

Universal fields: `api_version`, `type`, `id`, `event_timestamp_ms`, `app_id`. Subscriber fields: `app_user_id`, `original_app_user_id`, `aliases[]`, `subscriber_attributes`. Subscription fields: `expiration_at_ms`, `purchased_at_ms`, `product_id`, `entitlement_ids[]`, `store` (`APP_STORE` | `PLAY_STORE` | `STRIPE` | `RC_BILLING` | …), `environment` (`SANDBOX` | `PRODUCTION`), `transaction_id`, `original_transaction_id`.

Use `original_transaction_id` as `provider_sub_id`; `transaction_id` changes every renewal.

### "expiration_at_ms is in the past but the user is still entitled"

This is grace period or billing retry. Apple and Google keep the entitlement live while re-attempting the card, so RevenueCat's `entitlements.active` map still contains the key while the raw expiry date has passed. Authorise from the status + `grace_until`, never from `expiration_at_ms > now()`. Involuntary churn is 31% of Google Play cancellations vs 14% on the App Store (2026 State of Subscription Apps), so this path is high-traffic on Android.

### Verification, retries, ordering

- Verify the **HMAC-SHA256 `X-RevenueCat-Webhook-Signature`** (timestamp + hash) computed over **raw request body bytes, exactly as received** — re-serialising after JSON parse breaks it. A shared-secret `Authorization` header is the weaker legacy alternative.
- Retries: 5 attempts at **5, 10, 20, 40, 80 minutes** on any non-200, then it stops. Manual replay exists in the dashboard.
- Typical latency 5–60s; `CANCELLATION` up to ~2h.
- **No ordering guarantee.** Guard writes with `WHERE last_event_at < EXCLUDED.last_event_at`.
- RevenueCat's own docs recommend following a webhook with `GET /v1/subscribers/{app_user_id}` to resolve authoritative state rather than trusting the payload alone. Do this for any event that grants or revokes.

Underneath, RevenueCat is consuming **App Store Server Notifications V2** and **Google Play Real-Time Developer Notifications** and normalising them. You do not need to configure those feeds yourself when using RevenueCat, but knowing they exist explains the latency and the vocabulary (grace period, billing retry, account hold).

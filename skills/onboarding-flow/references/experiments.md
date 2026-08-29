# Onboarding Experiments, Teardowns and Limits

Time-sensitive: every effect size here is dated and vendor-sourced, and the regulatory section describes a rulemaking in flight. Re-verify figures against the current [RevenueCat State of Subscription Apps](https://www.revenuecat.com/state-of-subscription-apps) and the FTC status against the docket.

## The metric rule

**Primary metric: retained paid revenue at day 30 per user entering onboarding.** Not trial starts. Not paywall conversion rate.

Why optimising trial starts degrades revenue: the levers that most efficiently raise trial starts reduce the user's understanding of what they agreed to — burying price, shortening the trial, softening renewal language, a `$0.00` CTA with no terms nearby, dismissal-blocking design. Each moves trial starts up and downstream conversion down; the effects cancel or invert. The decision comes almost immediately — **55.4% of 3-day trial cancellations happen on Day 0, 84% by Day 1** ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026)) — so a misunderstood trial start costs you acquisition spend plus refund and review risk.

Setup: one primary metric, two guardrails (D1 retention, refund/chargeback rate), one diagnostic (step-level drop-off). Ship on the primary; block on a guardrail regression even if the primary is up. D30 is a compromise for iteration speed — check D90 and 12-month on winners before institutionalising, since roughly **72% of annual subscribers cancel within year one**, 35% of those in month one.

## Assignment

Assign on a **stable install-scoped ID generated before the first onboarding screen renders** — not user ID (it does not exist yet; account creation is late, see `sequence.md`) and not advertising ID (ATT-dependent, null for most iOS users).

```ts
// generated on first launch, persisted, immutable
const installId = await getOrCreateInstallId();   // SecureStore / AsyncStorage
const variant = flags.getExperiment('onboarding_paywall_pages', { unit: installId });
track('experiment_exposed', { experiment, variant, install_id: installId });
```

Rules:
- Cache the variant for the whole flow — never re-evaluate mid-flow, or users cross variants.
- Emit `experiment_exposed` at the first screen the variant affects; analyse on exposure, not assignment, or unexposed users dilute the effect.
- Carry `variant` on every downstream event (`paywall_viewed`, `checkout_started`, and the webhook-emitted `subscription_started`) so revenue attributes without a third-system join. Event names come from `observability-analytics/references/event-spec.md`.
- On account creation, backfill `install_id → user_id`.
- Tooling: PostHog or Statsig for flags; Superwall or RevenueCat Experiments for paywall tests — they own the purchase event, removing the hardest attribution join.

## Sample size and duration

For a small app this is the binding constraint, not idea supply.

| Baseline install→paid | Detectable lift | Users per arm (approx) |
|---|---|---|
| 10% | +20% relative | ~4,000 |
| 10% | +10% relative | ~15,000 |
| 3% | +20% relative | ~15,000 |
| 3% | +10% relative | ~57,000 |

Two arms, 80% power, 95% confidence, binary metric. Revenue metrics have higher variance and need more. **[UNVERIFIED as exact figures — order-of-magnitude anchors; compute against your own baseline.]**

Consequences for a small app:
- At 500 installs/day, ~2–8 weeks per two-arm test. **Two arms only**; multi-arm is unaffordable.
- **Test big swings first.** A 5% copy tweak is undetectable at your volume; screen order, paywall structure and trial length are not.
- Run full weeks (day-of-week effects are large) and never stop on a peek — peeking inflates false positives badly at these sizes.
- Below ~200 installs/day, stop A/B testing: sequential before/after over a long window, plus qualitative testing. Pretending to run underpowered experiments is worse than not running them.
- Do not test during a UA spike or feature launch — the population shifts underneath you.

## Test order

Highest expected effect first — you can only afford a few.

| # | Test | Expected effect | Evidence |
|---|---|---|---|
| 1 | Hard paywall vs freemium | Very large. 10.7% vs 2.1% median D35 install→paid; $3.09 vs $0.38 D60 RPI; 12-mo retention ~equal | [RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026) |
| 2 | Trial length: 7-day default vs 14 or 30 | Large. 17–32 day 42.5% vs <4 day 25.5% trial→paid | [RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026) |
| 3 | Multi-page vs single-page onboarding paywall | **Unestablished.** One vendor's aggregate: 12.41% vs 9.07% (+37% rel.), 40M opens Feb–May 2026. Uncontrolled; `payments-paywalls` calls it folklore pending your own test | [Superwall](https://superwall.com/blog/new-postmulti-page-onboarding-paywalls-convert-37-better-than-single-page-heres-why) — [UNVERIFIED] |
| 4 | Reveal screen present vs absent | Expected large; no published effect size | [UNVERIFIED] |
| 5 | Personalisation length (6 vs 14 questions) | Moderate, non-monotonic — longer often wins when each answer visibly does something | [UNVERIFIED] |
| 6 | Permission soft-ask timing/copy | Moderate on opt-in (2–3× vs cold prompt); downstream revenue effect unmeasured | [Plotline](https://www.plotline.so/blog/how-to-improve-push-notification-opt-in-rates) — [UNVERIFIED methodology] |
| 7 | Annual-vs-monthly default and price anchoring | Moderate | [UNVERIFIED] |
| 8 | Paywall CTA copy | Small individually; Cal AI ran 61 paywall experiments to find theirs | [Cal AI](https://tasu.ai/library/cal-ai) |
| 9 | Social proof placement and format | Small | [UNVERIFIED] |

One variable per experiment. If you cannot afford to isolate, ship the redesign as a single arm and accept you will not learn which part worked — a legitimate low-volume trade, as long as you are honest that you made it.

## Teardowns

| App | Mechanism worth copying | How it works |
|---|---|---|
| **Cal AI** (32 screens, [teardown](https://tasu.ai/library/cal-ai)) | Live-updating personalisation | Every input animates the calorie target changing. The user watches a plan build itself around them — data entry becomes a payoff loop. |
| **Cal AI** | Rating ask before the paywall — **do not copy** | Cal AI fires the review prompt mid-onboarding at peak sentiment. This plugin recommends against it: iOS allows roughly **three prompts per user per year**, and one spent pre-activation buys a rating from someone who has not used the product, against both stores' guidance. Correct gate: `sessions >= 3 && activated && !erroredRecently && daysSinceLastPrompt >= 90` (`aso-growth/references/retention.md`). |
| **Cal AI** | `Try for $0.00` CTA | Found across 61 paywall experiments; "$0.00" removes the purchase-decision weight "free trial" retains. Defensible only with terms plainly on the same screen. |
| **Cal AI** | Referral code entry mid-onboarding | At peak engagement, not buried in Settings; also signals a community exists. |
| **Duolingo** (38 screens, [teardown](https://tasu.ai/library/duolingo)) | Full first lesson before account or paywall | Turns both asks from cold to warm — the user has evidence before either friction point. |
| **Duolingo** | Explicit daily-goal commitment | "5 min/day" is a self-consistency contract the streak enforces. Not data collection. |
| **Duolingo** | Notification re-ask after a streak exists | First "no" treated as "not yet"; by the second ask the value is self-evident. |
| **Duolingo** | Four plans, half of them family | Reframes personal spend as household value, raising the acceptable price. |
| **Superhuman** | 1:1 human onboarding | Makes the user articulate their workflow aloud — personalisation plus reciprocity. Transferable piece: make them *state* a goal, not pick one. |
| **Headspace / Gentler Streak** | Intent echo | "What brings you here?" quoted back verbatim in later screens and notifications. Cheap, high perceived fidelity. |

Common thread: by the time the paywall appears the user holds something — a plan, a streak, a completed lesson — that leaving forfeits. Every screen increases what they have built or what they would lose.

## Dark patterns to avoid

Each raises trial starts and lowers D30 retained revenue; several are enforcement exposure.

- Fake or resetting countdown timers; false scarcity.
- A close button that is invisible, delayed, tiny, or disguised (an X that opens a second paywall).
- Confirmshaming decline copy ("No thanks, I don't want to get healthier").
- Price in tiny grey text, or absent until the purchase sheet.
- A trial not stating length, converted price and renewal date on the CTA's own screen.
- Pre-selected expensive plans where the CTA does not name the price it will charge.
- Cancellation harder than signup: more steps, email-only, a phone call, an unskippable retention gauntlet.
- Silent renewal price increases.
- Rating prompts gated on a positive answer first ("Enjoying the app?" → 5 stars only if yes). Against both stores' rules.
- Permission asks that block core functionality when declined (see `permissions.md`).

Safe default: **"7 days free, then $29.99/year — cancel anytime in Settings"** at body-text size adjacent to the CTA and visible without scrolling, a same-weight "Not now", in-app Terms and Privacy links, Restore Purchases, and a reminder before the trial converts.

**Trial length: 7 days is the default here, not 3.** Three days is the market's most common choice and its worst-supported one — 17–32 day trials convert at 42.5% vs 25.5% under four days, so test 14 and 30 upward from 7. Apple imposes **no 7-day floor on free trials**: introductory offers can be 3 days. The 7-day minimum applies to the *subscription period*, not the trial — a common conflation; see `payments-paywalls/references/paywall-requirements.md` for the disclosure rules that follow from it.

**Multi-page paywalls:** whichever page carries the purchase CTA must carry every 3.1.2 disclosure — name, period, price and billing units, trial length, post-trial price, in-app Terms and Privacy links — in the default state, without scrolling or tapping. A value-recap first page with the price on page three is the top paywall rejection cause.

## Regulatory status — dated, and uncertain

**United States.** The FTC's Negative Option Rule ("click-to-cancel") was **vacated by the Eighth Circuit in July 2025** on procedural grounds. Rulemaking restarted: draft ANPRM to OIRA **30 January 2026**, ANPRM announced **11 March 2026**, comments due **13 April 2026** ([Gibson Dunn](https://www.gibsondunn.com/ftc-restarts-negative-option-rulemaking-after-eighth-circuit-vacatur-enforcement-under-rosca-continues/), [Latham](https://www.lw.com/en/insights/eighth-circuit-vacates-ftc-click-to-cancel-rule-days-before-compliance-deadline)). **The scope of any replacement rule is genuinely unknown as of August 2026** — do not assume the vacated specifics return.

Binding regardless: **ROSCA** (clear and conspicuous disclosure of material terms, express informed consent before charging, simple online cancellation) and **FTC Act §5**. Enforcement did not pause — $60M and $7.5M settlements over enrolment and cancellation practices post-date the vacatur. State auto-renewal laws in **California, Colorado, Minnesota and New York** exceed the federal floor; California's is the practical compliance target.

**European Union.** The Consumer Rights Directive and UCPD already prohibit misleading trial framing and require clear pre-contractual information and a straightforward withdrawal path. The **Digital Fairness Act**, targeting dark patterns, addictive design and subscription traps, is in the legislative process. **[UNVERIFIED — status and final text as of August 2026 not confirmed here; check the current stage before treating any provision as binding.]** Design as though it lands; nothing expected of it conflicts with the safe pattern above.

**App stores.** Apple Guideline **3.1.2** requires the paywall to state subscription title, duration, price, inclusions and renewal terms, with working Terms and Privacy links — the most common subscription rejection. Google Play mirrors this plus an unambiguous cancellation path. **[UNVERIFIED as to exact wording — read the live guideline before submission; both are revised without notice.]**

Net: the safe pattern is identical under every regime and also maximises D30 retained revenue. There is no trade-off between compliance and the metric that matters — only between compliance and the metric that does not.

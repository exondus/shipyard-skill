# Onboarding Screen Sequence

Time-sensitive: every conversion figure here is dated and vendor-sourced. Re-verify against the current [RevenueCat State of Subscription Apps](https://www.revenuecat.com/state-of-subscription-apps) before quoting a number to a user or making a pricing decision.

**The event vocabulary is owned by the `observability-analytics` skill** (`references/event-spec.md`). This file *uses* those names; it does not define them. If a screen needs an event the spec lacks, add it to the spec and to `docs/app/analytics-spec.md` in the same PR, in `object_action` past-tense snake_case, with variance in properties rather than the name.

## The template

Order matters more than screen count. Top performers run long — Cal AI 32 screens, Duolingo 38 — and still convert, because each screen asks one thing and pays it back immediately ([Cal AI teardown](https://tasu.ai/library/cal-ai), [Duolingo teardown](https://tasu.ai/library/duolingo)).

| # | Screen | Purpose | Mechanism | Must show | Event |
|---|---|---|---|---|---|
| 1 | **Hook / demo** | Answer "will this work?" before asking anything | Show-don't-tell removes the largest pre-commitment doubt | A 3–6s loop of the core feature working on a recognisable real example. No copy about the company. | `onboarding_started {variant}` |
| 2 | **Intent** ("what brings you here?") | Segment + set up the echo | Self-identification; the answer is quoted back later verbatim | 3–5 options, one tap, no "other" free text | `onboarding_step_completed {step_index, step_name:'intent', variant}` |
| 3–5 | **Identity questions** | Easy wins, build momentum | Sequential commitment — small yeses beget larger ones | One question per screen, large tap targets, visible progress bar | `onboarding_step_completed {step_index, step_name:'profile', variant}` |
| 6–14 | **Plan inputs** | Collect only what the personalised output needs | Investment/sunk cost; the plan is *earned* | Each answer visibly changes something on screen — a number ticking, a curve moving. Cal AI animates the calorie target updating per input. | `onboarding_step_completed {step_index, step_name:'goal', variant}` |
| 15 | **Social proof** | Pre-empt "is this legit?" | Consensus, immediately before the ask | Rating, install count, 2–3 short specific testimonials, before/after if the product has one | `onboarding_step_viewed {step_index, step_name:'social_proof', variant}` |
| 16 | **The reveal** | Deliver value before charging | Loss aversion via specificity — a plan with your name and a date is costly to abandon | User's name, the concrete numbers, a projected outcome with a date, animated assembly | `onboarding_reveal_viewed {variant, seconds_to_reveal, reveal_type}` | |
| 17 | **Permission soft-ask** | Earn the OS prompt | Contextual framing; the OS prompt is one-shot (see `permissions.md`) | Framed around the plan the user has just been shown, not the abstract capability | `permission_softask_shown {permission, placement:'onboarding_post_reveal', variant}`, `permission_softask_answered {accepted}`; then **only if `accepted`** `permission_prompt_requested`, `permission_prompt_answered {result}` |
| 18–20 | **Paywall** | Convert | Splitting value / expectations / price across screens may reduce the pile-up on one page — unestablished, see below | Value recap, then what happens and when, then plans + CTA. **Whichever page carries the CTA carries every 3.1.2 disclosure.** | `paywall_viewed {placement:'onboarding', variant, offering_id, trigger}`, `checkout_started`, then `subscription_started {is_trial:true}` **server-side from the RevenueCat webhook** |
| 21 | **Account creation** | Persist what now exists | Endowment — there is now something to lose | Apple/Google sign-in first, email second. Never a password on the first pass. | `signup_started {method, entry_point:'onboarding'}`, `signup_completed {method, seconds_since_started}` |
| 22 | **Activation** | The aha, immediately | Time-to-value | Drop straight into the first real action, pre-filled from onboarding answers | `onboarding_completed {duration_seconds, steps_skipped, variant}`, then `activation_completed {time_to_activate_seconds, activation_path}` |

Emit `onboarding_step_viewed {step_index, step_name, variant}` on every screen as well as `onboarding_step_completed`. Viewed-minus-completed per screen is what localises the drop-off; a single screen usually owns most of the loss.

Every event named in this table is defined in `observability-analytics/references/event-spec.md` with its full property list. Use the names and properties exactly as that file writes them; if a screen needs something it lacks, add it there first.

Two spec rules this flow depends on. **Revenue events are server-side only** — never emit `subscription_started` from the client; it double-counts on retry, misses renewals and refunds, and is spoofable. And **propagate the funnel discriminators** (`variant`, `placement`, `offering_id`) through every step including the webhook-emitted revenue event, or you can measure overall conversion and nothing else.

## Placement rules and why

**The reveal goes immediately before the paywall.** The paywall converts against a specific thing the user now has. Reversed, you are asking someone to pay for a hypothesis. This is the whole architecture — everything before the reveal exists to make the reveal feel specific and earned.

**The paywall goes after the reveal, before first real use.** Hard paywall (no free tier) shows a median Day-35 install-to-paid of **10.7% vs 2.1% for freemium** and Day-60 RPI of **$3.09 vs $0.38**, with 12-month retention essentially identical (27% vs 28%) — which defeats the usual "freemium retains better" defence ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026)).

**Multi-page paywall: worth testing, not established.** One vendor's aggregate reports **12.41% vs 9.07%** for multi-page over single-page across 40M opens Feb–May 2026 ([Superwall](https://superwall.com/blog/new-postmulti-page-onboarding-paywalls-convert-37-better-than-single-page-heres-why)), and the mechanism is plausible: one page otherwise carries value proposition, objection handling, pricing and payment at once. But it is uncontrolled, and `payments-paywalls/references/paywall-requirements.md` treats it as folklore until you A/B test it with RevenueCat Experiments. Paywall *model* and *trial length* dominate layout effects. Test it; do not assume it.

**Hard constraint if you do split it:** whichever page carries the purchase CTA must also carry **every** Guideline 3.1.2 disclosure — subscription name, period, price and billing units, trial length and post-trial price, and in-app Terms and Privacy links — visible in the default state without scrolling, tapping or flipping a toggle. A value-recap first page with the price on page three is the top paywall rejection cause. Splitting the *pitch* is fine; splitting the *disclosure away from the CTA* is a rejection.

**Trial length: 7 days is the default.** Prefer 7 over the 3 days most apps ship — the most common choice and the worst-supported one — and test 14 or 30 upward: 17–32 day trials converted at **42.5%** vs **25.5%** under four days ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026)). Regardless of length, **55.4% of 3-day trial cancellations happen on Day 0** and 84% by Day 1 — value must land in the first session. Apple imposes **no 7-day floor on free trials**; introductory offers can be 3 days. The 7-day minimum applies to the *subscription period*, not the trial.

**No rating ask during onboarding.** Tempting — sentiment peaks after the reveal and before price, and Cal AI does exactly this. Still wrong, and `aso-growth/references/retention.md` is the authority: iOS allows roughly **three prompts per user per year**, and spending one pre-activation buys a rating from someone with no experience to rate. Both stores' guidance is against prompting during onboarding or before activation, and Apple's API may silently not present at all. Correct trigger is after a user-caused success, gated on roughly `sessions >= 3 && activated && !erroredRecently && daysSinceLastPrompt >= 90`. Keep it out of this flow entirely.

**Permission soft-ask goes after the reveal, never before it.** The soft ask must be able to name a concrete thing the user has already been shown — "we'll remind you at 8am about *this* plan" — and before the reveal there is no plan to point at. The OS prompt is one-shot, so an ask made a screen too early permanently costs the permission. Same rule stated in `permissions.md`; if you reorder this flow, the soft ask moves with the reveal.

**Referral ask mid-flow, not in Settings.** Cal AI puts referral-code entry inside onboarding at peak engagement; in Settings it is dead weight. It also signals that a community exists.

**Account creation after the paywall, not before.** Duolingo runs an entire first lesson before requiring an account. Use an anonymous device-scoped ID from screen 1, attach everything to it, and convert to an account when there is something worth saving. Signup-before-value is the single most expensive ordering mistake — it front-loads the highest-friction step against the lowest motivation.

**Personalisation questions work through the mechanism, not the data.** Their function is sequential micro-commitment, making the reveal feel earned, and segmentation for later messaging. A question whose answer visibly changes nothing on screen is theatre and costs you a drop-off point. Test: if you deleted the question, would the reveal look different? If no, delete the question.

## Variants by product shape

**Habit / tracker (fitness, nutrition, sleep, finance)** — the canonical shape above. Longest personalisation block (10–20 inputs), strongest reveal (a numeric plan with a projected date), notification permission load-bearing because the product *is* the reminder loop. Ask for the goal *and* the deadline — a target date makes the projection concrete. Activation = first log.

**Content / subscription (news, courses, audio, video)** — 3–5 taste questions, and the reveal is a *populated library*, not a plan: the mechanism is abundance ("142 pieces matched to you"), not projection. Deliver one complete piece free before the paywall — the content is the demo. Activation = first item finished, not started.

**Social / network** — value is other people, so the reveal must be *people*: contacts already here, or an active feed. Never ask for contacts permission before showing why (see `permissions.md`). The paywall usually moves later or disappears — monetising before network value exists suppresses the network. Activation = first outbound interaction, not first session.

**Tool / utility (scanner, editor, converter, single-shot AI)** — 5–10 screens. The user has a job right now; personalisation is friction. Let them complete one real task end-to-end, then paywall the *export* of that result — the half-finished artefact is the leverage. Do not build a 30-screen flow for a tool: sequential commitment needs a plan to build toward, and a tool has none. Activation = first completed task.

**AI-wrapper apps** sit between tool and tracker: demo model output on screen 1, personalise lightly, reveal a customised assistant. AI apps show ~41% higher revenue-per-user but **36% worse 12-month retention on monthly plans** ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026)) — push annual and invest in a retention loop, not just onboarding.

## Working backwards to a flow

1. **Name the aha in one sentence:** "the user has X and feels Y." That is what `activation_completed` fires on, and the spec's activation definition is not finished until you can write that sentence.
2. **List the minimum inputs** needed to deliver a *personalised* version of that aha. Everything else is cut, or moved to Settings.
3. **Order the survivors easy-to-hard.** Never open with weight, income or anything shame-adjacent — put those after commitment, with a "prefer not to say" path.
4. **Attach a visible consequence to every input.** If you cannot, cut it.
5. **Write the reveal screen first,** then work backwards to the questions that make it specific. Flows designed forward accumulate questions nobody needs.
6. **Set a time-to-value target** — activation inside the first session, ideally under three minutes — and treat any screen that endangers it as a deletion candidate.

Localisation note: onboarding is the most copy-dense surface in the app and the first thing an international user sees. Namespace it separately (`onboarding`), keep every string in ICU, and budget German at +30–40% expansion — a 32-screen flow with fixed-height cards will break. See `localization-foundation/references/ops.md`.

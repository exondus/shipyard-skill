---
name: onboarding-flow
description: >
  Design, build and improve the first-run experience of an app — the sequence from install to the
  moment the user gets value, including personalisation questions, permission priming, social proof,
  where the paywall and the account creation go, and how each step is instrumented. Use when building
  onboarding or a signup flow, converting a product idea into a first-run sequence, improving
  activation or day-one retention, deciding when to ask for notifications or other permissions, or
  when someone asks why users install and never come back, or wants to A/B test onboarding.
---

# Onboarding

Onboarding is not an introduction to the app. It is the machine that gets a stranger to the one action
that predicts them still being here in a month, and takes payment on the way. Almost everything that
determines whether an app has a business happens in these screens.

## Start from the activation event

`docs/app/brief.md` names it. If it does not, go back to `product-discovery` — an onboarding flow
designed without one is decoration.

The method, in order:

1. **Name the aha in one sentence**: "the user has X and feels Y."
2. **Work backwards to the minimum inputs** needed to deliver a *personalised* version of that. Every
   question that does not feed the personalised result is cut, however interesting the data would be.
3. **Sequence**: hook or demo (no input required) → one or two easy identity questions → the questions
   that build the plan, one per screen, each visibly changing something on screen → social proof →
   **the reveal**, the generated personalised result → permission soft-ask, pointing at the thing the
   reveal just showed → paywall → account creation → the activation event itself.

   The soft-ask goes **after** the reveal, never before it: the ask has to point at something the user
   has already seen, or it is asking for trust it has not yet earned.
4. **One ask per screen.** A screen with three fields converts worse than three screens with one.

## What the evidence supports

Cited so the reasoning can be checked, not to settle taste. Figures below are from RevenueCat's *State
of Subscription Apps 2026* and Superwall's 2026 paywall dataset; re-verify before quoting to anyone.

- **Screen count is not the enemy.** Top performers run 20–38 onboarding screens. What hurts is a
  screen that asks without giving; what works is a question whose answer visibly moves something.
- **Personalisation questions work through the mechanism, not the data.** Sequential micro-commitment,
  and making the resulting plan feel earned. A question whose answer changes nothing visible is
  theatre and users detect it.
- **Multi-page onboarding paywalls may convert better** — one vendor's aggregate puts them at around
  12.4% against 9.1% — but it is an uncontrolled comparison across different apps, and
  `payments-paywalls` treats it as untested. Worth an experiment, not a default. If you do split the
  paywall, **the page carrying the purchase button carries every required disclosure** — price,
  period, post-trial price, trial length, terms and privacy links — visible without scrolling or
  tapping. Price on page three is the top paywall rejection.
- **Longer trials convert better**: 17–32 day trials convert to paid at about 42.5% against 25.5% for
  trials under four days. Most apps ship the short one.
- **Day zero is everything.** Around 55% of three-day-trial cancellations happen on day zero and 84%
  by day one. Value must land in the first sitting, and a trial-reminder push is among the
  highest-leverage things in the app.
- **Value before signup.** Anonymous-first with a device-scoped identity, then account creation at the
  point the user has something worth saving.
- **Priming a permission ask lifts opt-in substantially** — commonly reported at two to three times a
  cold system prompt. The system prompt is one-shot per install; treat it as a resource you spend once.

## Permissions

The rule: **never fire the OS prompt until an in-app soft ask has been accepted**, and never fire it
on first launch. Ask immediately after the screen that makes the permission obviously useful, framed
in terms of what the user just set up — "remind you about *your* plan", not "we'd like to send you
notifications".

A refusal is "not yet", not "never". Ask again after the user has something to lose — a streak, a
saved plan, a scheduled item — through an in-app path that explains how to enable it in Settings.

**On iOS, provisional authorisation is usually the right first move.** Notifications go quietly to
Notification Centre with no prompt at all, so there is no one-shot to burn and the user judges your
actual notifications rather than a promise, upgrading or turning them off from the notification
itself. Then request full authorisation at a moment where the interruption is obviously worth it. The
trade-off is that provisional notifications never interrupt, so anything time-critical needs the full
grant. `aso-growth/references/retention.md` has the argument in full;
`push-engagement/references/setup.md` has the authorisation options.

Store rules constrain this: functionality, content and rewards may not be conditioned on granting a
permission, and the app must work with every permission denied. `store-submission` has the detail.

## Where the paywall goes

After the reveal, before the first real use. The user has answered questions, seen a result built from
their answers, and been shown social proof; that is the moment of highest perceived value. A paywall
before the reveal converts worse and reads as a toll booth.

The paywall itself is `payments-paywalls` — it owns the pricing presentation, the trial framing, and
the mandatory disclosures without which the app is rejected. Do not design the paywall screen here;
design the sequence that leads to it.

## Instrument it while building it

An onboarding funnel that was not instrumented while it was built cannot be diagnosed later, only
rebuilt. Every screen emits a view and a completion event carrying the same step identifier, the
variant, and a stable identity assigned before the first screen. Every permission ask emits shown and
result. The reveal, the paywall, the trial start and the activation event each emit their own.

`observability-analytics` owns the taxonomy; the rule that matters here is that every step in the
funnel carries the same discriminating property, or the funnel cannot be broken down without
re-instrumenting.

The single number to watch is step-level drop-off. One screen almost always owns most of the loss, and
it is rarely the one anyone expects.

## Testing it

One variable per experiment — sequence, question count, trial length, paywall page count, CTA copy —
keyed on a stable install ID assigned before the first screen renders, so the assignment cannot be
contaminated by the flow itself.

**The primary metric is retained paid revenue at day 30, not trial starts.** Optimising for trial
starts alone reliably degrades revenue: the easiest way to raise them is to obscure what the user is
agreeing to, and that money arrives and then leaves as refunds and chargebacks. Pre-register the
sample size and expect two to four weeks per test on a small app.

## Patterns worth stealing, with their mechanism

Copying the surface without the mechanism produces cargo cult. The mechanism is the point:

- **A demo before any question** — removes the "will this actually work for me" doubt before asking
  for effort.
- **Answers that visibly update a target in real time** — the plan is built in front of the user, so
  it feels theirs rather than issued.
- **A named, dated, specific projected outcome** — specificity creates something to lose, which is
  what carries the user across the paywall.
- **Not the rating prompt.** Several widely-copied onboarding flows ask for a rating mid-sequence, at
  peak sentiment. Do not copy it. The OS grants roughly three prompts per user per year and may
  silently ignore the call; spending one on someone who has not yet used the product is the worst
  available trade, and both platforms' guidance is against prompting before the user has experienced
  anything. `aso-growth` owns the trigger — after activation, after a success moment, from about the
  third session.
- **Referral placement mid-flow at peak engagement**, not at the end when the user is leaving.
- **A commitment question** ("what is your daily goal?") — an explicit commitment device, which
  measurably changes follow-through.
- **Echoing the user's stated intent back verbatim** in later copy and notifications — cheap
  personalisation with high perceived fidelity.

## The line you do not cross

Not only because it is wrong, but because it is now the most enforced area in consumer regulation and
in store review.

No fake countdowns. No disguised or delayed close buttons. No confirmshaming ("no thanks, I don't want
to improve"). No trial where the price and renewal date are not visible in the default state. No
cancellation flow with more steps than signup.

Store rules require the paywall to state title, duration, price per period, what is included, and
functional in-app links to terms and privacy policy — link-outs on the store listing do not satisfy
it. In the US, the FTC's specific click-to-cancel rule was vacated in 2025 and rulemaking restarted in
2026, but ROSCA and Section 5 enforcement continued throughout with substantial settlements, and
several state auto-renewal laws are stricter and in force. In the EU, existing consumer law already
bans misleading trial framing and further dark-pattern legislation is in progress. Design for the
strict case; it is also the one that produces fewer refunds.

The safe pattern, which converts fine: "3 days free, then $29.99/year, cancel anytime in Settings", a
visible same-size "Not now", and a reminder before the trial converts.

## Reference files

- `references/sequence.md` — the screen-by-screen template with the mechanism for each
- `references/permissions.md` — priming copy, timing, re-ask paths, provisional authorisation
- `references/experiments.md` — what to test, in what order, with what metric and sample size

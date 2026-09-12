---
name: visual-verification
description: >
  Run the app, drive it through a real user flow, and capture what actually rendered — screenshots,
  accessibility trees, measured contrast, logs — so claims about the interface are evidence rather
  than assertion. Use whenever a screen or flow needs checking as it renders rather than as written:
  "walk the onboarding", "check how it looks on device", "test with notifications denied", "does it
  survive 200% font scale", "is the paywall disclosure visible", "prove the contrast", "run it and
  tell me what you see". Use it automatically when `self-review` reaches the does-it-run question on
  a user-visible slice, when `premium-ui` has finished a screen and needs it checked as rendered, and
  when `preflight-audit` Phase 9 asks for a screen-reader walk, a maximum-text screenshot or a
  contrast calculation. Drives iOS simulators and Android emulators via Argent, and the web via
  Chrome DevTools MCP or Playwright. Produces evidence, not design opinions — `premium-ui` judges it.
---

# Visual verification

Everything else in this plugin reasons about the interface from source. That is fast, objective and
grep-able, and it is structurally blind to an entire class of defect: a 44pt target overlapped by a
sibling, a label clipped at maximum text size, a skeleton that does not match the layout it replaces,
real contrast after opacity and overlay compositing, focus order, an accessibility tree that reads one
row as five, a disclosure that sits below the fold on the smallest supported device.

This skill has the eyes. It runs the app, drives it, and writes down what it saw.

**It does not judge.** It reports measurements and artifacts. `premium-ui` owns whether a spacing
rhythm is right; `self-review` owns whether a slice is done; `preflight-audit` owns whether it ships.
Keeping opinion out of this skill is what stops four skills arguing about the same screen.

## The line against Maestro

They are not competing. `stack-scaffold` puts Maestro in CI as committed regression; this skill is
in-session exploration that produces evidence.

| | This skill | Maestro |
|---|---|---|
| Runs | Now, once, because someone asked a question | Every PR, forever |
| Knows the flow | Discovers it | Was told it |
| Output | Screenshots, trees, measurements, findings | Pass or fail |
| Survives a UI change | Yes — it looks again | No — it breaks and gets fixed |

**The handoff rule: any flow worth walking twice becomes a Maestro flow.** When a walk finds a real
defect, emit the Maestro flow that would have caught it, and say so in the report. A finding that is
fixed but not guarded comes back — and the guard is cheapest to write while the walk is still open.

## Before you drive

A walk that cannot be repeated is an anecdote. Four preconditions, and a walk that skips one must say
which and label everything downstream as unrepeatable.

**1. A reachable build.** A development build on a simulator, emulator or device — not Expo Go, which
has a fixed native binary and different behaviour for anything with a config plugin. For web, a dev or
preview server with a URL. Confirm the build is current: a walk against a stale binary is the most
expensive kind of wrong, because everything it reports is true of code that no longer exists.

**2. A reset to first run.** Onboarding happens once per install, so driving it repeatedly means
destroying that state on demand. This is the single most common reason a first-run walk cannot be
repeated. `references/native.md` and `references/web.md` give the mechanisms per platform. Establish
this *before* the first walk, not after the state is gone.

**3. A deterministic identity.** A seeded test account and a way to land on any screen directly — deep
links on `expo-router`, a URL on web. Walking twelve screens to reach the thirteenth wastes the budget
and introduces flake at every step. Drive the flow under test; jump to everything else.

**4. Isolation.** Read `references/safety.md` before the first walk of a project. In short: a driven
walk fires real analytics events into whatever project the build points at, and will quietly corrupt
the activation funnel `observability-analytics` depends on. It can also touch real billing, real push
tokens and real user data, and screenshots of a signed-in session are full of things that should not
be pasted into a report.

## The walk

For each stop in the flow, in this order:

1. **Act** — one interaction. Tap, type, scroll, grant, deny, background, rotate.
2. **Settle** — wait for the state to resolve rather than for a fixed duration. A screenshot taken
   mid-transition is evidence of nothing and is the usual source of "it looked broken" false findings.
3. **Capture** — screenshot, and the accessibility tree. Console and network only when the stop is
   about behaviour rather than appearance; they are large and most stops do not need them.
4. **Assert** — the specific, checkable things listed below. Name the stop, the expectation, and what
   was actually observed.

Number the stops and keep the artifacts. A walk report whose screenshots have been discarded cannot be
re-read by the next person, and `preflight-audit` reads these reports as history at intake.

### What to assert at a stop

Only what is visible at that stop. Resist the urge to re-audit the whole app at every screen.

- **Does the expected state render at all** — and for a data surface, is this the loading, empty,
  error, offline or success rendering? `premium-ui` requires all five to exist; this is where their
  existence is proved rather than claimed.
- **Is anything clipped, overlapped or off-screen** at this device size.
- **Is every interactive element reachable** — in the accessibility tree, with a role, a label and a
  state, and a hit region that is not covered by a sibling.
- **Do the measured values hold** — contrast, target size, text size. Measured, not read from tokens.
  A token says what a component asked for; the render says what it got.
- **Did anything land in the log** that should not have — a warning, a failed request, a key error.

## Driving onboarding

This is the flow the skill exists for, and the one with the most ways to go wrong. `onboarding-flow`
owns its design; this owns proving it behaves.

Walk it end to end from a genuine first run: hook, the personalisation questions, the reveal, the
permission soft-ask, the paywall, account creation, and the activation event itself. Then walk it
again down the paths nobody tests.

**The three walks that find the most.**

*The denial walk.* Refuse every permission and continue. The app must work with every permission
denied — that is a store rule, not a preference, and it is checked in review. Notifications denied,
photos denied, location denied, tracking denied. The failure mode is not a crash; it is a screen that
silently does nothing, or a button whose handler needed a grant it did not get.

*The disclosure walk.* On the **smallest supported device at the largest text size**, screenshot the
page carrying the purchase button. Price, period, post-trial price, trial length, and the terms and
privacy links must all be visible without scrolling or tapping. Price below the fold is the top
paywall rejection, and it is invisible to every static check because in source the text is right
there. This one screenshot is worth more than most of the audit.

*The interruption walk.* Background the app mid-onboarding and return. Kill it and relaunch. Go
offline at the reveal. Onboarding state that lives only in memory is extremely common and produces a
user who lands back on screen one, or worse, in the app with no plan.

**Prove the instrumentation while you are in there.** `onboarding-flow` requires every step to emit an
event with the same discriminator, and a slice is not done until the event is visible in the analytics
tool rather than present in the code. A walk is the only cheap moment to check that, because you are
generating the events anyway. Confirm arrival in the tool; do not infer it from a network request.

## Conditions

Read `references/conditions.md` for the full matrix and how to sample it. The governing rule is
`preflight-audit`'s: running everything on everything turns the review into theatre and teaches
everyone to skim the output. Pick the conditions the flow is actually exposed to, state which you
picked and which you skipped, and give a reason for each skip.

The default sample for a consumer app, which is four walks and not twenty: the smallest supported
device at default settings; the smallest supported device at maximum text size; dark mode; and offline
at the point the flow first needs the network.

## Measurement

Assertions about numbers need arithmetic, not judgement.

`scripts/contrast.py` measures real contrast from a screenshot rather than from tokens, which is the
only way to account for opacity, overlays, gradients and dimmed disabled states. It reports both WCAG
2.1 ratios and APCA Lc, and exits non-zero on failure so its output can be quoted as proof:

```
python3 scripts/contrast.py shot.png --box 24,180,320,44 --size 17 --weight 400
python3 scripts/contrast.py shot.png --pair 24,190 24,220   # explicit foreground/background points
```

Target sizes and text sizes come from the accessibility tree, which reports the rendered frame. Take
them from there, not from the style.

Measure a full-resolution screenshot. Argent downscales screenshots by default, and resampling blends
thin text into its background, so contrast measured from a scaled image reads lower than what
rendered. Mind the units: `--box` and `--pair` are image pixels, while the accessibility tree reports
frames in points — multiply by the device scale (2 or 3 on iPhones, the screen density on Android).
`--size` goes the other way: pass the text size in points or CSS pixels, not image pixels, because
the thresholds are defined in those units.

## Evidence discipline

This skill inherits `preflight-audit`'s evidence standard, and should read
`references/evidence-standard.md` from that skill when one is installed. Three rules do most of the
work here:

**Say which kind of nothing.** A walk that found no problems found nothing because nothing qualified,
because nothing was measured, or because the thing was never built. These are different results and
only the first one is good news.

**Grade your own instruments.** Automated accessibility checks catch roughly a third of real issues
and none of the ones about whether a flow makes sense. A clean tree is not a clean screen. Say what a
clean result from each instrument actually means.

**End with what you could not observe, and why.** Physical-device behaviour, real network conditions,
StoreKit outside sandbox, push delivery, OEM Android quirks, anything behind a state you could not
reach. This line is the most useful sentence in the report and the one most often left out.

## Output

Write to `docs/app/review/YYYY-MM-DD-<flow>-walk.md` using `assets/walk-report-template.md`, with
artifacts alongside it. Always write the file for a full flow walk; a single-screen check can stay in
the conversation unless it found something.

Findings use the same closure record as `self-review` and `preflight-audit`, so they carry forward
without translation:

```
FINDING:  what and where — the stop number and the file, if known
ADDED / REMOVED / WIRED / PROOF
STATUS:   CLOSED | PARTIAL | DEFERRED | NOT-A-BUG
```

For this skill, `PROOF` is the artifact: the screenshot path, the tree excerpt, the script output. Not
a description of the screenshot — the screenshot.

## Do not

- **Do not fix while walking.** Finish the walk, write the findings, then fix. A walk that stops to
  patch loses the flow state and never reaches the end, which is where the interesting failures are.
- **Do not re-verify against memory.** Re-walk against the original findings, the way
  `preflight-audit` does. An agent told something was fixed will find it fixed.
- **Do not report a screenshot as a finding.** "Here is the screen" is not a finding. A finding names
  an expectation and how the render violated it.
- **Do not walk a stale build.** Confirm the binary matches `HEAD` before starting.
- **Do not paste a signed-in screenshot without reading `references/safety.md`.**

## Reference files

- `references/native.md` — Argent: booting, resetting to first run, deep links, driving, the
  accessibility tree, logs, and the React component tree
- `references/web.md` — Chrome DevTools MCP and Playwright: when each, Lighthouse's two-tool split,
  and the web-specific interface checks a native-shaped audit misses
- `references/conditions.md` — the condition matrix and how to sample it without theatre
- `references/safety.md` — analytics pollution, billing sandboxes, secrets in screenshots, real data
- `scripts/contrast.py` — measured WCAG and APCA contrast from a rendered screenshot
- `assets/walk-report-template.md` — the report

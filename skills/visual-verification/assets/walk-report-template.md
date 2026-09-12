# Walk — <flow name>

Walked <date>. Build `<commit sha>` on `<device / browser>`. Artifacts in `./<flow>-<date>/`.

Keep this readable in two minutes. The findings and the could-not-observe line are the parts anyone
will come back for; everything else is supporting material.

---

## Result

<One line. "Onboarding completes end to end; three findings, one blocking." Not a paragraph, and not
after the context.>

## Setup

| | |
|---|---|
| Build | `<sha>` — verified current / **stale, see note** |
| Platform | iOS 18 simulator, iPhone SE (3rd gen) / Android 15 emulator, Pixel 6a / Chrome 144 |
| Reset method | `simctl uninstall` · `pm clear` · fresh browser context · in-app dev reset |
| Backend | dev / staging / **production (agreed: <what was agreed>)** |
| Analytics | isolated to `<project>` — verified at stop <n> |
| Billing | sandbox account `<id>` |
| Account | seeded test account, fake data |

```
Sampled:  <conditions actually walked>
Skipped:  <condition> (<reason>)
          <condition> (<reason>)
```

---

## Stops

One row per stop. Keep the assertion column to what was checked *at that stop*.

| # | Action | Rendered | Asserted | Artifact |
|---|---|---|---|---|
| 1 | Cold launch, first run | Hook screen | Renders; 2 controls in tree, both labelled | `01-hook.png` |
| 2 | Tap "Get started" | Question 1 of 6 | Answer visibly changes the preview | `02-q1.png` |
| … | | | | |

Note against any stop where the state took unusual time to settle, where the log carried something, or
where the render differed from what the previous walk produced.

---

## Measurements

Paste the tool output, not a description of it.

```
$ python3 scripts/contrast.py 07-paywall.png --box 24,412,327,22 --size 13
Post-trial price line
  #8a8a8e on #ffffff   13px / 400
  WCAG 2.1   3.27:1   (normal text — AA needs 4.5, AAA needs 7.0)   AA FAIL
  APCA       Lc 51.4    (small text — needs |Lc| 90)   FAIL
  FAIL
```

| Measurement | Value | Threshold | Result |
|---|---|---|---|
| Smallest touch target (`<element>`) | 38 × 38 pt | 44 pt | FAIL |
| Body contrast | 8.1:1 / Lc 78 | 4.5:1 / Lc 75 | pass |
| Paywall disclosure above fold at max text | — | all five items visible | FAIL |

---

## Findings

One closure record each. Same shape as `self-review` and `preflight-audit`, so these carry forward
without translation.

```
FINDING:  Stop 7 — post-trial price falls below the fold at max text size on iPhone SE.
          Apple 3.1.2 requires it visible without scrolling. components/Paywall.tsx:118
ADDED:    —
REMOVED:  —
WIRED:    —
PROOF:    07-paywall-maxtext.png; the price row's frame origin.y exceeds the viewport
          height in the accessibility tree dump at 07-tree.json:214
STATUS:   PARTIAL — reproduced, not yet fixed
```

---

## Confirmed healthy

Verified, not assumed. Without this section the report reads as though everything unmentioned is fine,
which is the opposite of true.

- Every permission denied and the flow still completes — walked, stops 3, 5, 9
- All five states render on the plan list — loading skeleton matches final layout
- Onboarding survives background-and-return at stop 6 and a cold kill at stop 8

---

## Could not observe

The most useful section, and the one most often left out. This is where the next walk starts.

- Physical-device behaviour — simulator only this session
- Real network failure — offline was set with a dev flag, not at the network layer, so the UI branch
  is proved and the network layer is not
- StoreKit outside sandbox
- Push delivery
- Android — iOS only this session

**Kind of nothing:** <for any axis with no findings, say whether nothing qualified, nothing was
measured, or the thing was never built.>

---

## Regression handoff

Any flow worth walking twice becomes a committed test.

- [ ] `.maestro/<flow>.yml` — covers stops 1–9, asserts the disclosure is visible at max text
- [ ] Playwright spec generated from the web walk, committed at `<path>`
- [ ] Nothing yet — say why

---

## Changelog

| Date | Walk | What changed since the last one |
|---|---|---|

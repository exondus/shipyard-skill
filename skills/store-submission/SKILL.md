---
name: store-submission
description: >
  Get an app through App Store and Google Play review the first time. Use when preparing to submit,
  building store assets — screenshots, app preview video, icon, feature graphic — writing review notes
  and setting up a demo account, filling in privacy nutrition labels, privacy manifests, the Play data
  safety form or age ratings, configuring TestFlight or staged rollout, deciding what may be changed by
  over-the-air update, or responding to a rejection. Use it for the account-level prerequisites that
  block a launch — the Paid Applications Agreement, banking and tax forms, developer verification — and
  for the privacy policy, terms of service and account-deletion page the stores require. Also use early
  in a build to check which review requirements are architectural — account deletion, restore purchases,
  report and block, permission handling — rather than paperwork.
---

# Store review

Two ideas make this cheap instead of miserable.

**Most of app review is architecture, not paperwork.** In-app account deletion, restore purchases,
report and block for user-generated content, an experience that still works when a permission is
denied, a privacy policy reachable inside the app, a paywall that discloses its price — every one is
a rejection if missing and every one is a build task, not a submission task. Read this skill in week
one, not in launch week.

**Verify the current rules before submitting.** Guideline numbering, SDK floors, target API deadlines,
required screenshot sizes, age-rating questionnaires and age-assurance obligations all changed during
2025 and 2026 and continue to. `references/` records the position as of August 2026 and is a starting
point for checking, not authority. Check `developer.apple.com/app-store/review/guidelines/` and Play's
policy pages directly.

## Before this skill, run preflight-audit

`store-submission` prepares the material. **The go/no-go gate is the `preflight-audit` skill**, and it
is a different question — not "is the paperwork complete" but "if this ships tomorrow, what breaks,
who gets hurt, and who refuses it". Run its intake if the project has never had one, then its audit,
remediate, and verify. Do not let a submission checklist stand in for it.

## The account-level blockers nobody schedules

These have nothing to do with the code and they stop a launch dead. Start them in the first fortnight;
see `ship-app/references/timeline.md` for how they interact with the rest of the schedule.

- **The Paid Applications Agreement, banking and tax forms.** Until that agreement is active and the
  bank and tax details are complete, in-app purchases do not resolve — they show as unavailable in
  sandbox and in production, and it looks like a StoreKit bug. If purchases "work in the simulator but
  the product list is empty on device", check this before debugging anything.
- **Developer verification.** Play organisation accounts need a D-U-N-S number and site and email
  verification; personal accounts face the closed-testing requirement below. Both take weeks, not days.
- **The legal pages.** A privacy policy and terms of service, live at stable HTTPS URLs, reachable
  **inside the app** and not only from the store listing — the paywall disclosure rules require the
  in-app links specifically. Plus a public account-deletion page for Play, which has its own content
  requirements. These are a real deliverable with a real deadline, and no skill in this plugin writes
  them for you; a lawyer or a reputable generator does, and the generated text still has to describe
  what your app actually collects, which means reconciling it with the privacy label, the privacy
  manifest and the data safety form.

## The requirements that are architecture

Handle these while building the feature they belong to:

| Requirement | Where it belongs |
|---|---|
| In-app account deletion that deletes, plus a public web deletion URL for Play | with auth |
| A third-party-login alternative limiting collection to name and email with a private relay option, if social login is the primary path | with auth |
| Restore purchases, reachable without signing in | with payments |
| Paywall disclosure: name, duration, price per period, post-trial price, in-app links to terms and privacy | with the paywall |
| Report, block, content filtering and an objectionable-content EULA | with any user-generated content |
| The app works with every permission denied, and no content or reward is conditioned on granting one | with each permission |
| The tracking-consent prompt, if and only if the privacy label declares tracking | with analytics |
| Privacy manifest declaring required-reason API use, matching the privacy label | with the dependency that needs it |
| The app must function on IPv6-only networks | with any hardcoded host |
| Nothing in the app or its metadata mentions another platform | with the copy |

That last one catches people every release: no "also on Android", no Play badge, no Android device
frame in a screenshot, no "cheaper on our website" in a non-permitted storefront.

## Assets

Exact current specifications are in `references/assets.md`. What matters at the planning stage:

- **Screenshots**: one phone set and one tablet set at the currently required display sizes, no alpha
  channel, showing the app in use rather than a splash or login screen. `aso-growth` owns what makes
  them convert; this skill owns whether they are accepted.
- **App preview video**: short, within a specific duration window, and — the rule people break —
  **captured from the device screen**. Marketing footage, hands, and lifestyle b-roll are rejected.
  Record on a real device, not the simulator — simulator captures have the wrong status bar and drop
  frames — then cut to the required length and check the codec and frame rate before uploading. Its first three seconds must show the core action, because
  it autoplays.
- **Icon**: square, no alpha, no pre-rounded corners.
- Localise the sets you can; a localised listing is cheap and drives installs.

## The demo account and review notes

The single most common rejection is "information needed": the reviewer could not get in, or could not
find the feature.

Provide a demo account that never expires, is not rate-limited, has **no two-factor prompt** (or a
static bypass), and is seeded with realistic data so the app is not empty. Then write review notes that
name the exact tap path to every gated feature, every in-app purchase, and every background mode, and
explain anything non-obvious. Generic notes are themselves grounds for rejection under the metadata
rules. A short screen recording attached to the notes resolves more questions than a paragraph.

## Technical gates

- The **SDK and toolchain floor** for new submissions, and Play's **target API level deadline**, both
  move annually and both hard-fail at upload rather than at review. Check them before a release branch,
  not after.
- **Privacy manifest** for required-reason APIs, plus signed third-party SDKs from the published list.
  Copy required reasons from dependency manifests up into your own where the toolchain does not.
- **Export compliance** declared in config, or every TestFlight build stalls on a questionnaire.
- **Every permission string present, specific, and matched to a capability actually used.** Config
  plugins can inject a permission you do not use, which is its own rejection — audit the generated
  native config, do not assume.
- **Age rating**: the questionnaire was overhauled and the tiers changed; unanswered questions can
  block updates entirely. Age-assurance obligations from several US states are in flux — check before
  relying on any particular position.
- **Play data safety** must match what the SDKs actually do. Google cross-checks. Enumerate every
  analytics, crash and advertising SDK and use each vendor's published guidance.
- **Play sensitive declarations**: photo and video permissions are restricted to apps whose core
  purpose requires them — use the system photo picker instead — and background location, storage,
  package queries and each foreground service type need their own declaration, often with a demo video.
- **New personal Play accounts** face a closed-testing requirement with a minimum tester count held for
  a continuous period before production access. Budget several weeks and start recruiting testers early;
  this surprises first-time publishers more than anything else.

## Over-the-air updates

Permitted, within limits both stores state in similar terms: you may fix bugs, change copy, styling,
layout and configuration, and vary existing flows. You may not add features that were not present at
review, add or remove a purchase mechanism, change how a permission is used, or change content that
affects the age rating. Keep one update channel per release and always keep the previous update
available to roll back to.

## Submission

Run an **external TestFlight round first**, always. It goes through a lighter review that catches
metadata and permission problems before the real submission, and it produces the beta cohort
`aso-growth` wants anyway.

Let the build system own build numbers and versions rather than hand-editing both, which is how
duplicate-build-number upload failures happen. Use phased release on Apple and staged rollout on Play;
read the Play pre-launch report before promoting anything.

## Rejections

Reply in the resolution centre on the same submission — do not silently resubmit. Address each cited
guideline number separately, factually, with a screenshot or screen recording of the fix, and say
whether the change is metadata-only or needs a new build. If the reviewer is genuinely wrong, appeal to
the review board rather than arguing in the resolution centre; it is a different process with a
different outcome.

Save expedited review for real emergencies. It is granted on reputation and spent permanently.

`references/rejections.md` ranks the common causes with the fix for each. Read it before submitting,
not after.

## Reference files

- `references/apple-guidelines.md` — the sections that cause rejections, with what reviewers check
- `references/apple-technical.md` — SDK floor, privacy manifests, permissions, age ratings, compliance
- `references/play.md` — target API, data safety, declarations, testing requirements, deletion URL
- `references/assets.md` — exact asset specifications and the video capture rules
- `references/submission-checklist.md` — the pre-submission run-through
- `references/rejections.md` — ranked causes and fixes

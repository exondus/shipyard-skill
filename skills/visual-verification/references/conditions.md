# Conditions

Not time-sensitive. This is a sampling method, not a fact about a vendor.

A flow can be walked under more combinations than anyone will ever run. The instinct is to enumerate
them; the result of enumerating them is that the reports get long, then get skimmed, then stop being
read at all — and the review has failed in the way `preflight-audit` warns about, by becoming a ritual
that produces a green tick.

So: sample deliberately, say what you sampled, and say what you skipped and why. A skipped condition
is a decision, and it belongs in the report where someone can disagree with it.

## The axes

| Axis | What it finds | Cheapest way to set it |
|---|---|---|
| **Screen size** | Clipping, fold position, disclosures pushed below the cut | Smallest supported device. Not the largest, not the default |
| **Text scale** | Fixed-height containers, truncated labels, buttons that stop fitting their text | Maximum, not one step up |
| **Theme** | Inverted palettes, invisible borders, shadows that vanish, unreadable disabled states | Dark mode |
| **Motion** | Animation that is load-bearing — a transition that was the only signal a state changed | Reduced motion on |
| **Network** | Spinners with no timeout, no offline state, optimistic writes with no rollback | Offline at the first network-dependent stop |
| **Permissions** | Screens that silently do nothing; store-rule violations | Every permission denied |
| **Data state** | Missing empty and error renderings; layouts that assume average content | Empty account, then a very long string |
| **Lifecycle** | State held only in memory; onboarding that restarts; lost session | Background and return, then cold kill and relaunch |
| **Locale** | Fixed-width containers, hardcoded formats, untranslated surfaces | Pseudo-locale or the most expansive shipped language |
| **CPU** | Jank, spinners that never resolve, races that only appear when slow | 4× throttle (web) or a low-end Android profile |
| **Input modality** | Keyboard traps, missing focus indicators, stuck hover states on touch | Keyboard-only pass (web) |
| **Platform** | Everything above, differently | The other one |

## Yield

Ranked by how often each turns up a real finding, from walks in practice rather than from theory:

1. **Permissions denied.** Consistently the richest, and the one with a store rule behind it. The app
   must work with every permission denied.
2. **Maximum text size on the smallest device.** The disclosure walk lives here, and so do most
   clipping defects.
3. **Lifecycle interruption.** Backgrounding mid-flow is normal user behaviour and is almost never
   tested.
4. **Empty and error data states.** `premium-ui` requires all five states; this is where the two
   nobody built are discovered.
5. **Offline.** High yield, but read the honesty caveat in `references/native.md` — what "offline"
   means varies by how you set it, and the report must say which.
6. **Keyboard-only** on web. Finds more than the rest of the web list combined.
7. **Dark mode.** Usually cheap and usually clean, because it gets looked at during development.

Motion, locale, CPU and platform-crossing are real but lower yield per walk. Rotate them rather than
running them every time.

## The default sample

For a consumer app slice, four walks:

1. Smallest supported device, default settings, happy path.
2. Smallest supported device, maximum text size.
3. Dark mode.
4. Offline at the first stop that needs the network.

Plus, for onboarding specifically, the three walks named in `SKILL.md`: denial, disclosure,
interruption. Those are not optional for a first-run flow — they are what the flow is for.

## When to widen

Widen on consequence, not on thoroughness. `preflight-audit` weights its accessibility phase by who
the users are, and the same logic applies here: where the audience has a specific reason to need a
condition — a health product used by people with impaired vision, a public-sector obligation, a tool
used one-handed in the field — that condition stops being a sample and becomes mandatory, and a
failure in it is harm rather than debt.

Widen also after a bug. A defect found under one condition is evidence that condition is untested, and
the next few walks should include it.

## Stating it

Every report carries this, in two lines:

```
Sampled:  smallest device · max text · dark · offline-at-reveal
Skipped:  locale (single-locale launch, catalogue wired but one language shipped)
          CPU throttle (native; no low-end device available this session)
          platform: Android (iOS only this session — Android walk outstanding)
```

The second block is the useful one. It is where the next walk starts.

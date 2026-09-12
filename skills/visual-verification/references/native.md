# Driving native — Argent, simulators and emulators

Written September 2026. The `simctl` and `adb` invocations below rotate with Xcode and platform-tools
releases; treat them as a place to start checking rather than as authority. Argent's own tool names
are deliberately not listed — ask the assistant **"What can Argent do?"** and it enumerates the
current set. Guessing a tool name from a blog post is how a walk stalls on its first call.

## Argent

`yarn dlx @swmansion/argent init` — the installer detects the coding agent, registers the MCP server
and configures the environment. iOS needs macOS with Xcode; Android needs `adb` on `PATH` and the
emulator package. It runs locally over MCP stdio and sends no telemetry.

What it gives a walk, in the four groups that matter here:

- **Control** — boot a simulator or emulator, launch by bundle ID, open deep links, and drive the UI
  with taps, swipes, pinches, rotation, keyboard input and hardware buttons. It talks to the simulator
  directly rather than through XCUITest, so a long walk stays fast enough to be worth doing.
- **Inspect** — the accessibility tree, the native view hierarchy, and the React component tree. The
  accessibility tree is the primary instrument for this skill: it carries roles, labels, states and
  rendered frames, which is where target sizes and clipping are actually established.
- **Debug** — console logs, and network traffic at both the JavaScript `fetch` layer and the native
  layer. Native-layer capture matters because a request made by a native module never appears in a JS
  network log, and "the event fired" is routinely asserted from the wrong layer.
- **Profile** — combined React and native profiles, UI hangs, render cascades. Out of scope for a
  verification walk; `performance-security` owns it.

Argent also drives physical devices, TVs, and Chromium/Electron apps. For a React Native project it
builds and launches without extra setup.

## Reset to first run

The precondition that most often has not been arranged. Pick one and write the choice into
`docs/app/stack.md`, because every subsequent walk depends on it.

**iOS simulator**

```sh
xcrun simctl uninstall booted <bundle-id>          # app + its data; reinstall to get first run
xcrun simctl privacy booted reset all <bundle-id>  # permission grants only, app data intact
xcrun simctl erase <device-udid>                   # nuclear: wipes the whole device
```

Uninstall is the honest reset — it clears `AsyncStorage`, MMKV, the Keychain items behind
`expo-secure-store`, and therefore the Clerk session. Resetting privacy alone is the right tool for
the denial walk, because it lets you re-arm the one-shot system prompts without losing the account.

**Android emulator**

```sh
adb shell pm clear <package>                       # data + permissions, app stays installed
adb uninstall <package>
adb shell pm reset-permissions                     # device-wide permission reset
adb shell pm revoke <package> android.permission.POST_NOTIFICATIONS
```

`pm clear` is usually enough and is much faster than a reinstall.

**The in-app debug reset.** Tempting, and fine, but it is a half-built-sweep hazard: a reset
affordance that ships is a data-loss button in production. If you add one, gate it on `__DEV__` and
grep for it during `self-review`'s "was the old thing removed" question. Note that it resets only what
it was written to reset — it will miss the Keychain item somebody added later, and a walk that trusts
it will report a clean first run that was not one.

## Landing on a screen directly

```sh
xcrun simctl openurl booted "myapp://onboarding/reveal"
adb shell am start -W -a android.intent.action.VIEW -d "myapp://onboarding/reveal" <package>
```

Argent opens deep links itself, which is the better path inside a walk. With `expo-router` every route
is already addressable, so the cost of making the flow jumpable is close to zero — and it converts a
twelve-tap approach into one call, removing eleven chances to flake.

Drive the flow under test. Jump to everything else.

## Setting the conditions

**Text size**

```sh
xcrun simctl ui booted content-size accessibility-extra-extra-extra-large
adb shell settings put system font_scale 2.0
```

Reset with `content-size medium` and `font_scale 1.0`. Maximum, not one step up — an enabled scaling
setting inside a fixed-height container clips only at the top of the range, which is exactly why
testing at default passes and real users report clipped buttons.

**Appearance**

```sh
xcrun simctl ui booted appearance dark
adb shell cmd uimode night yes
```

**Reduced motion.** Android reads the transition scale:

```sh
adb shell settings put global transition_animation_scale 0
```

iOS has no reliable `simctl` equivalent — drive the Settings app with Argent to toggle Accessibility →
Motion → Reduce Motion, and say in the report that this was set by hand. Do not assert reduced-motion
behaviour you did not actually set; an unverified reduced-motion claim is worse than an absent one.

**Offline.** The weakest spot in the toolchain and worth being honest about. The Android emulator can
be taken off the network:

```sh
adb shell svc wifi disable && adb shell svc data disable
```

The iOS simulator shares the host's network and has no per-app toggle, so offline there means a host
level Network Link Conditioner profile, a proxy, or a dev-only flag in the app. Whichever is used, say
which — "offline behaviour verified" means something different for each, and a flag-based offline test
proves the UI branch exists without proving the network layer fails the way the UI expects.

**Locale and expansion.** Launch under a pseudo-locale if the project has one wired —
`localization-foundation` explains why this matters even for a single-locale launch. Text expansion
finds fixed-width containers that no English walk will ever reveal.

## Reading the accessibility tree

This is the instrument, not a formality. From it, take:

- **Roles, labels and states** on every interactive element. An icon-only control with no label is a
  finding. A compound row that appears as five separate nodes is a finding — a screen reader will read
  it as five items.
- **Rendered frames**, which give real target sizes. Compare against 44pt on iOS and 48dp on Android,
  and check the frame is not covered by a later sibling. A control styled at 44pt inside a clipping
  parent is smaller than it claims.
- **Traversal order**, by walking it in order rather than reading it as a set. Order defects are
  invisible in a screenshot and obvious in the tree.
- **Focus**, on sheet open and close. `premium-ui` requires focus to move in and return to the
  trigger; the tree is where that is proved.

What it will not tell you: whether the flow makes sense, whether a label is accurate rather than
merely present, or whether the reading order is sensible rather than merely defined. Those need the
screenshots and a person.

## Logs

Capture console output across the whole walk rather than per stop, and read it at the end. Things that
only show up in the log: a swallowed promise rejection, a failed image fetch that renders as an empty
box, a `key` warning that becomes a list reorder bug, a permission API returning `denied` where the UI
proceeds as though it were `granted`.

A stop that renders correctly while logging an error is a finding, not a pass.

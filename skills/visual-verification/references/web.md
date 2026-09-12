# Driving web — Chrome DevTools MCP, Playwright, and the checks a mobile-shaped audit misses

Written September 2026. Tool names and flags rotate; verify against each project's README before
depending on a specific one.

## Which tool

Both, for different jobs. Neither replaces the other.

**Chrome DevTools MCP** (`chrome-devtools-mcp`, maintained by the Chrome team) controls and inspects a
live Chrome over CDP. It is the *inspection* tool: screenshots, console with source-mapped stack
traces, network requests, the accessibility tree, Lighthouse, and performance traces. Chrome stable or
Chrome for Testing only — other Chromium browsers are not supported. From Chrome 144 it can attach to
an existing authenticated session, which removes most of the login problem. A slim mode reduces it to
navigate, evaluate and screenshot when the full tool surface is more than the task needs.

**Playwright MCP** (`npx @playwright/mcp@latest`) is the *driving* tool. Better at multi-step flows,
better at authenticated runs via saved storage state, and — the reason it earns its place here — a
session can be turned into durable Playwright test code. That is the web half of the handoff rule in
`SKILL.md`: a flow worth walking twice becomes a committed test, and on web the walk can write it.

Rough split: Playwright drives the flow, Chrome DevTools MCP measures the stops.

**One caution on Lighthouse.** Its audit covers accessibility, SEO and best practices and does **not**
include performance. Core Web Vitals come from a separate performance trace. A report claiming "we ran
Lighthouse, performance is fine" from the audit tool alone is a false clean, and it is a common one.
Performance tooling may also send trace URLs to Google's CrUX API for field data; disable that flag on
anything unreleased or internal.

## Reset to first run

Web is the easy platform here, and the advantage is worth using deliberately. A fresh browser context
is a fresh install: no cookies, no `localStorage`, no `sessionStorage`, no IndexedDB, no service
worker. Playwright gives one per context, so every walk starts clean without a teardown step.

Two things survive a naive reset and quietly break first-run walks: a registered **service worker**
holding a cached shell, and **server-side state** keyed to the test account — an onboarding-complete
flag in Postgres does not care that the browser forgot. For a true first run, reset the account too,
or seed a new one per walk.

## Setting the conditions

Everything in `references/conditions.md` is available through CDP or Playwright: device and viewport
emulation, `prefers-color-scheme`, `prefers-reduced-motion`, `forced-colors`, locale and timezone,
network throttling, and CPU throttling. CPU throttling is the one people skip and the one that
reproduces the most real reports — a mid-range Android at 4× slowdown is the actual condition most
users are in, and it is where a spinner that never resolves finally shows itself.

Test **browser zoom at 200%** as well as font scale. They are different failure modes: zoom reflows
the layout, text-only scaling breaks fixed-height containers. `premium-ui`'s accessibility floor is
written mobile-first, so the zoom case has no equivalent there and is easy to leave unchecked.

## The web-specific checks

`premium-ui`'s accessibility floor — 44pt targets, dynamic type, VoiceOver and TalkBack labelling — is
native-shaped and correct for native. Web has its own list, and a walk that only applies the native
one will pass a page that is genuinely broken for keyboard users.

Vendor a pinned copy of the Web Interface Guidelines into the project rather than fetching them at
review time. The upstream rules change without notice, and the three files that repository publishes do
not agree with each other — the command sheet most agents fetch is missing the hit-target and mobile
input-size rules that the `AGENTS.md` version carries, along with most of the design section. Pin a
copy, diff upstream deliberately, and the review becomes reproducible.

The checks that need a *driven* browser rather than a grep:

**Keyboard.** Tab through the entire flow without touching the mouse. Every interactive element
reachable, in an order that matches the visual one, with a **visible** focus indicator at every stop.
Focus moves into a dialog on open and returns to the trigger on close. No keyboard trap. This single
pass finds more real defects than any other web check, and it is invisible to static analysis.

**Forms.** Every control has a label, and clicking the label focuses the control. Enter submits when a
text input is the only control; in a `textarea`, ⌘/⌃+Enter submits and Enter inserts a newline. Submit
stays enabled until submission starts, then disables with a spinner for the in-flight request — and
the request carries an idempotency key, which the network panel will show you. Double-submit by
hammering the button; a form that creates two records is a finding you will not get any other way.

**Targets and text.** Hit targets at least 24px, 44px on touch. Inputs at least 16px on mobile, or iOS
Safari zooms the page on focus — a jarring defect that never reproduces on desktop and is therefore
almost never caught.

**Content resilience.** Drive the page with a very long string, a missing image, a four-digit count
and an empty list. Layouts that assume average content are the norm, and the render is the only place
it shows.

**Locale.** Formats follow the user's locale, derived from `Accept-Language` or `navigator.languages`
and never from IP or GPS. Switch the browser locale and re-walk one stop; dates and currency should
move.

**Anchors.** Linked headings need `scroll-margin-top` or they land under a sticky header. Click every
in-page anchor rather than reading the CSS.

## Capture

Same protocol as native: act, settle, capture, assert. Two differences worth noting.

Take the **accessibility tree**, not just the DOM. The DOM says what was written; the tree says what
assistive technology will receive, after ARIA, after `aria-hidden`, after whatever a component library
did on your behalf. Decorative elements should be hidden from it and named elements should have
accurate names, and only the tree shows either.

Read the **console with source maps enabled**. A minified stack in a walk report is evidence nobody can
act on, and Chrome DevTools MCP will map it for you.

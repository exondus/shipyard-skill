# Store Listing Asset Specifications

Verified 29 August 2026. Guideline numbering, SDK floors, deadlines and asset specs change — verify against [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) and the [Play policy centre](https://support.google.com/googleplay/android-developer/topic/9858052) before submitting.

Sources: [Apple screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/) · [Apple app preview specifications](https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications/) · [Play graphic assets](https://support.google.com/googleplay/android-developer/answer/9866151).

---

## iOS screenshots

Apple reduced the mandatory sets. You now need **one iPhone set and, if the app supports iPad, one iPad set**. Everything else is scaled automatically.

| Display | Portrait px | Landscape px | Status |
|---|---|---|---|
| iPhone **6.9″** | 1320 × 2868 · 1290 × 2796 · 1260 × 2736 | 2868 × 1320 · 2796 × 1290 · 2736 × 1260 | **Preferred.** Providing this makes 6.5″ optional |
| iPhone **6.5″** | 1284 × 2778 | 2778 × 1284 | Required only if 6.9″ is not provided |
| iPad **13″** | 2064 × 2752 | 2752 × 2064 | **Required if the app runs on iPad** |
| iPad **12.9″** | 2048 × 2732 | 2732 × 2048 | Accepted in place of 13″ |

| Rule | Value |
|---|---|
| Count per set | **1–10** |
| Formats | `.png`, `.jpg`, `.jpeg` |
| Alpha / transparency | **Not allowed** — flatten onto an opaque background |
| Colour | RGB; sRGB or P3 |
| Orientation | Portrait or landscape; all shots in a set should share one orientation |
| Localisation | Per-language sets; if a language has none it falls back to the primary language's set |

**Guideline 2.3.3:** screenshots must show the app **in use** — not the splash screen, not the login screen, not pure title art. Text overlays, captions and device frames are permitted.

## iOS app preview video

| Property | Value |
|---|---|
| Duration | **15–30 seconds** |
| Count | Up to **3** per localisation |
| Max file size | **500 MB** |
| Codec | H.264, progressive, up to High Profile Level 4.0 — or ProRes 422 HQ |
| Bitrate | H.264 **10–12 Mbps**; ProRes ~220 Mbps VBR |
| Frame rate | **≤30 fps** |
| Container | `.mov`, `.m4v`, `.mp4` (ProRes: `.mov` only) |
| Audio | **Stereo only**, 256 kbps AAC (or PCM 16/24/32-bit for ProRes), 44.1 or 48 kHz, all tracks enabled |
| Poster frame | Defaults to **5 s**; choose it deliberately in App Store Connect |
| iPhone 6.9″ resolution | 886 × 1920 portrait / 1920 × 886 landscape |
| iPhone 6.1″ | 886 × 1920 / 1920 × 886 |
| iPad 13″ | 1200 × 1600 portrait / 1600 × 1200 landscape |

**Guideline 2.3.4 — device-capture only.** The preview must consist of video screen captures of the app itself. Narration and text/graphic overlays are permitted. Marketing b-roll, filmed hands on a phone, lifestyle footage, actors, and animated logo stings that aren't app UI will be rejected. A short branded end-card is generally tolerated but is not worth risking on a first submission.

## iOS app icon

| Property | Value |
|---|---|
| Size | **1024 × 1024** px |
| Format | PNG or JPEG, flattened |
| Alpha | **No alpha channel, no transparency** |
| Corners | Square — do **not** pre-round; the system masks it |
| Other | No overlaid text claiming price/rank; must match the in-app icon |

## iOS text metadata

App name ≤30 characters (guideline 2.3.7) · subtitle ≤30 · promotional text ≤170 (editable without review) · description ≤4000 · keywords ≤100 characters total, comma-separated, no spaces · What's New ≤4000.

---

## Google Play assets

| Asset | Spec |
|---|---|
| App icon | **512 × 512** px, 32-bit PNG **with alpha**, ≤1024 KB |
| Feature graphic | **1024 × 500** px, JPEG or 24-bit PNG, **no alpha** — mandatory for every listing |
| Phone screenshots | **2–8** per device type, 320–3840 px on any side, 16:9 or 9:16, JPEG or 24-bit PNG no alpha. 1920 × 1080 minimum recommended for featured placements |
| Tablet / Chromebook screenshots | **Minimum 4**, 1080–7680 px, 16:9 or 9:16 |
| Wear OS | ≥1 screenshot, ≥384 × 384, 1:1, app interface only |
| Promo video | **YouTube URL**, public or unlisted, **ads disabled**, no age restriction. Aim for ≥80% of the runtime to be actual app usage |
| Short description | ≤**80** characters |
| Full description | ≤**4000** characters |
| App title | ≤**30** characters |

Note the alpha asymmetry: Play's **icon requires** alpha, Play's **feature graphic and screenshots forbid** it, and Apple forbids it everywhere. Exporting one 1024 icon for both stores without checking will fail one of them.

---

## Producing the assets

### Capturing clean device recordings

1. **Use a real device, not the simulator, for previews.** Simulator recordings have wrong status bars and drop frames; Apple's specified preview resolutions (886 × 1920) don't correspond to any simulator output, so you will be scaling anyway — start from a genuine 1290 × 2796 or 1320 × 2868 capture and downscale.
2. **Fix the status bar.** For screenshots, use `xcrun simctl status_bar <device> override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3`. For device recordings, enable Do Not Disturb, charge to 100%, and full signal — or crop the status bar out entirely.
3. **Record.** iOS: connect the device to a Mac and use QuickTime → File → New Movie Recording → select the device (gives clean H.264 at native resolution). Android: `adb shell screenrecord --bit-rate 12000000 --size 1920x1080 /sdcard/demo.mp4` then `adb pull`.
4. **Seed the data first.** Empty lists, "Lorem ipsum", test emails and `user_12345` in a screenshot are visible to reviewers under 2.3.9 (display fictional but plausible account data) and read as unfinished to users.
5. **Slow your interactions down.** Tap, pause ~800 ms, then let the animation finish. Fast native transitions are unreadable at 30 fps in a 15-second cut.

### Cutting to spec

```bash
# Trim to 28s, force ≤30fps, H.264 High L4.0 at 11 Mbps, stereo AAC 256k @48kHz
ffmpeg -i raw.mov -t 28 -vf "scale=886:1920,fps=30" \
  -c:v libx264 -profile:v high -level 4.0 -b:v 11M -maxrate 12M -bufsize 24M \
  -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 -ac 2 preview.mp4
```

App Store Connect rejects previews for: mono audio, >30 fps, missing audio track, wrong resolution, and duration outside 15–30 s. If you have no narration, add a silent stereo AAC track rather than omitting audio — `-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000`.

For screenshots, generate all sizes from one source with a deterministic script rather than hand-resizing. Strip alpha explicitly: `magick in.png -background white -alpha remove -alpha off -strip out.jpg`.

### The first screenshot

Most users see only the first two or three, and Apple auto-plays the preview above them. Rules that hold up:

- **One benefit headline**, ≥60 px cap-height, above the device frame — a verb phrase describing an outcome, not a feature name.
- Show the **core screen after the user has value**, never onboarding or an empty state.
- Portrait, high contrast, legible at thumbnail scale. Test by shrinking to 150 px wide and asking whether the headline is still readable.
- Keep the headline consistent in position and typography across all shots so the set scans as a sequence.
- **Guideline 2.3.10:** no Android device frames, no Google Play badge, no "also on Android/web" copy in any screenshot destined for the App Store.

### Pre-upload checklist

- [ ] No alpha channel on any Apple asset or Play screenshot/feature graphic; alpha present on the Play icon
- [ ] Exact pixel dimensions match a listed size — not "close enough"
- [ ] Preview duration between 15 and 30 s, ≤30 fps, stereo audio present
- [ ] No competitor names, no platform names (2.3.10), no prices baked into artwork
- [ ] No placeholder/lorem/test-account data visible
- [ ] Status bar consistent across the set
- [ ] Localised sets uploaded for every language you list, or a sensible fallback language chosen
- [ ] Play feature graphic present (listing cannot publish without it)
- [ ] Play promo video is unlisted-or-public, ads disabled

#!/usr/bin/env python3
"""Measure text contrast from a rendered screenshot.

Tokens say what a component asked for. This says what it got, after opacity,
overlays, gradients, dimmed disabled states and whatever the theme actually
resolved to at runtime.

Two modes:

  --box X,Y,W,H     Crop a region around some text. The script picks the
                    background (most common colour) and the foreground (the
                    colour furthest from it in luminance that still covers a
                    meaningful share of the crop, so antialiasing fringes are
                    not mistaken for the text colour).

  --pair X,Y X,Y    Sample two explicit points: foreground first, then
                    background. Use this when the crop is busy or when the
                    automatic pick reports a share that looks wrong.

Reports WCAG 2.1 ratios and APCA Lc. Exits 1 if anything fails, so the output
can be quoted as proof rather than described.

Usage:
  contrast.py shot.png --box 24,180,320,44 --size 17
  contrast.py shot.png --box 24,180,320,44 --size 15 --weight 700
  contrast.py shot.png --pair 40,196 40,230
  contrast.py shot.png --box 24,180,320,44 --json
"""

import argparse
import json
import sys
from collections import Counter

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: python3 -m pip install Pillow")


# ---------------------------------------------------------------- WCAG 2.1

def _srgb_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb) -> float:
    r, g, b = (_srgb_to_linear(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def wcag_ratio(fg, bg) -> float:
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def wcag_thresholds(size_px: float, weight: int):
    """WCAG 'large text' is >=24px, or >=18.66px when bold (>=700)."""
    large = size_px >= 24 or (weight >= 700 and size_px >= 18.66)
    return (3.0, 4.5, "large") if large else (4.5, 7.0, "normal")


# ------------------------------------------------------------------- APCA
# APCA-W3 0.1.9. Lc is signed: positive for dark text on light, negative for
# light text on dark. Compare the absolute value against the thresholds.

_MAIN_TRC = 2.4
_S_TRC = (0.2126729, 0.7151522, 0.0721750)
_NORM_BG, _NORM_TXT = 0.56, 0.57
_REV_TXT, _REV_BG = 0.62, 0.65
_BLK_THRS, _BLK_CLMP = 0.022, 1.414
_SCALE_BOW, _SCALE_WOB = 1.14, 1.14
_LO_BOW_OFFSET, _LO_WOB_OFFSET = 0.027, 0.027
_DELTA_Y_MIN, _LO_CLIP = 0.0005, 0.1


def _apca_y(rgb) -> float:
    y = sum(co * (v / 255.0) ** _MAIN_TRC for co, v in zip(_S_TRC, rgb))
    return y + (_BLK_THRS - y) ** _BLK_CLMP if y < _BLK_THRS else y


def apca_lc(fg, bg) -> float:
    y_txt, y_bg = _apca_y(fg), _apca_y(bg)
    if abs(y_bg - y_txt) < _DELTA_Y_MIN:
        return 0.0
    if y_bg > y_txt:  # dark text on light background
        sapc = (y_bg ** _NORM_BG - y_txt ** _NORM_TXT) * _SCALE_BOW
        out = 0.0 if sapc < _LO_CLIP else sapc - _LO_BOW_OFFSET
    else:             # light text on dark background
        sapc = (y_bg ** _REV_BG - y_txt ** _REV_TXT) * _SCALE_WOB
        out = 0.0 if sapc > -_LO_CLIP else sapc + _LO_WOB_OFFSET
    return out * 100.0


def apca_threshold(size_px: float, weight: int):
    """Simplified reading of the APCA readability criterion. The real font
    lookup table is two-dimensional across size and weight; these bands take
    its body-text minimums (Lc 75 from 18px/400 or 14px/700, Lc 90 below that)
    and never relax further. Under 14px the table can ask for more than Lc 90,
    so check the full table for anything marginal."""
    bold = weight >= 700
    if size_px >= 36 or (bold and size_px >= 24):
        return 45.0, "large display text"
    if size_px >= 24 or (bold and size_px >= 18):
        return 60.0, "large text"
    if size_px >= 18 or (bold and size_px >= 14):
        return 75.0, "body text"
    return 90.0, "small body text"


# --------------------------------------------------------------- sampling

def sample_box(img, box, min_share: float):
    x, y, w, h = box
    if w <= 0 or h <= 0:
        sys.exit("error: the box is empty — W and H must both be positive")
    if x < 0 or y < 0 or x + w > img.width or y + h > img.height:
        sys.exit(
            "error: the box {},{},{},{} runs outside the {}x{} image. Pillow pads "
            "out-of-bounds pixels with black, which would be measured as text. Box "
            "coordinates are image pixels — on a 3x screenshot, multiply points by 3."
            .format(x, y, w, h, img.width, img.height)
        )
    crop = img.crop((x, y, x + w, y + h))
    total = crop.size[0] * crop.size[1]

    counts = Counter({colour: n for n, colour in crop.getcolors(maxcolors=total) or []})
    if not counts:
        sys.exit("error: could not read colours from the box")
    bg, bg_count = counts.most_common(1)[0]
    bg_lum = relative_luminance(bg)

    floor = max(2, int(total * min_share))
    candidates = [(c, n) for c, n in counts.items() if n >= floor and c != bg]
    if not candidates:
        sys.exit(
            "error: no second colour covers at least {:.1%} of the box. The crop is "
            "probably a flat surface with no text in it, or the text is thinner than "
            "the threshold — widen the box, or use --pair.".format(min_share)
        )

    fg, fg_count = max(candidates, key=lambda cn: abs(relative_luminance(cn[0]) - bg_lum))
    return {
        "fg": fg, "bg": bg,
        "fg_share": fg_count / total,
        "bg_share": bg_count / total,
        "distinct_colours": len(counts),
    }


def sample_pair(img, fg_pt, bg_pt):
    for x, y in (fg_pt, bg_pt):
        if not (0 <= x < img.width and 0 <= y < img.height):
            sys.exit("error: point {},{} is outside the {}x{} image".format(
                x, y, img.width, img.height))
    return {
        "fg": img.getpixel(tuple(fg_pt)),
        "bg": img.getpixel(tuple(bg_pt)),
        "fg_share": None, "bg_share": None, "distinct_colours": None,
    }


def hexs(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# ------------------------------------------------------------------- main

def parse_box(s):
    parts = [int(p) for p in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box wants X,Y,W,H")
    return parts


def parse_point(s):
    parts = [int(p) for p in s.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--pair points want X,Y")
    return parts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--box", type=parse_box, help="X,Y,W,H region around the text")
    ap.add_argument("--pair", type=parse_point, nargs=2, metavar=("FG", "BG"),
                    help="explicit foreground and background points, each X,Y")
    ap.add_argument("--size", type=float, default=16.0, help="rendered text size in px (default 16)")
    ap.add_argument("--weight", type=int, default=400, help="font weight (default 400)")
    ap.add_argument("--min-share", type=float, default=0.005,
                    help="minimum share of the box a colour must cover to count as the "
                         "foreground, which keeps antialiasing out (default 0.005)")
    ap.add_argument("--label", default=None, help="what this measurement is of, for the report")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if bool(args.box) == bool(args.pair):
        ap.error("give exactly one of --box or --pair")

    img = Image.open(args.image).convert("RGB")
    s = sample_box(img, args.box, args.min_share) if args.box else sample_pair(img, *args.pair)

    ratio = wcag_ratio(s["fg"], s["bg"])
    aa, aaa, wcag_class = wcag_thresholds(args.size, args.weight)
    lc = apca_lc(s["fg"], s["bg"])
    lc_min, apca_class = apca_threshold(args.size, args.weight)

    passes_aa = ratio >= aa
    passes_aaa = ratio >= aaa
    passes_apca = abs(lc) >= lc_min
    ok = passes_aa and passes_apca

    result = {
        "image": args.image,
        "label": args.label,
        "foreground": hexs(s["fg"]),
        "background": hexs(s["bg"]),
        "foreground_share": s["fg_share"],
        "background_share": s["bg_share"],
        "text_px": args.size,
        "font_weight": args.weight,
        "wcag": {"ratio": round(ratio, 2), "class": wcag_class,
                 "aa_threshold": aa, "aaa_threshold": aaa,
                 "passes_aa": passes_aa, "passes_aaa": passes_aaa},
        "apca": {"lc": round(lc, 1), "class": apca_class,
                 "threshold": lc_min, "passes": passes_apca},
        "verdict": "PASS" if ok else "FAIL",
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.label:
            print(args.label)
        print(f"  {hexs(s['fg'])} on {hexs(s['bg'])}   {args.size:g}px / {args.weight}")
        if s["fg_share"] is not None:
            print(f"  sampled from {s['distinct_colours']} distinct colours — "
                  f"foreground {s['fg_share']:.1%} of box, background {s['bg_share']:.1%}")
        print(f"  WCAG 2.1   {ratio:.2f}:1   ({wcag_class} text — AA needs {aa}, AAA needs {aaa})   "
              f"{'AA pass' if passes_aa else 'AA FAIL'}"
              f"{', AAA pass' if passes_aaa else ''}")
        print(f"  APCA       Lc {lc:.1f}    ({apca_class} — needs |Lc| {lc_min:g})   "
              f"{'pass' if passes_apca else 'FAIL'}")
        print(f"  {result['verdict']}")
        if s["fg_share"] is not None and s["fg_share"] < 0.02:
            print("  note: the foreground covers under 2% of the box. Check the picked colour "
                  "is the text and not a fringe; use --pair if it is not.")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10", "matplotlib", "requests"]
# ///
"""Project 4 starter: generate a colour pictogram in ARASAAC's own style.

ARASAAC's colour pictograms -- 'black' is id 2886 -- are a single flat colour on
a transparent background: a silhouette. So a pictogram for any colour the
wordnet has but ARASAAC lacks can be *generated*: keep that silhouette (its
alpha channel) and refill it with the colour's hex value from the xkcd colour
survey, which matplotlib ships offline. The result sits in the same visual
family as the real pictograms it will be matched alongside.

Licence: ARASAAC pictograms are CC BY-NC-SA 4.0 (Government of Aragon), so a
recoloured one inherits that -- credit ARASAAC and keep the licence.

Run:  uv run colour_swatch.py chestnut                 # -> chestnut.png
      uv run colour_swatch.py "burnt orange" out.png
"""
import sys
from pathlib import Path

import requests
from matplotlib.colors import XKCD_COLORS  # 949 named colours, offline
from PIL import Image, ImageColor

HERE = Path(__file__).resolve().parent
TEMPLATE_ID = 2886                                   # ARASAAC 'black' (colour)
TEMPLATE_URL = f"https://static.arasaac.org/pictograms/{TEMPLATE_ID}/{TEMPLATE_ID}_500.png"
TEMPLATE = HERE / f"arasaac_{TEMPLATE_ID}_black.png"  # cached, not committed


def template() -> Image.Image:
    """The ARASAAC 'black' pictogram as RGBA, downloaded once and cached."""
    if not TEMPLATE.exists():
        r = requests.get(TEMPLATE_URL, timeout=30)
        r.raise_for_status()
        TEMPLATE.write_bytes(r.content)
    return Image.open(TEMPLATE).convert("RGBA")


def recolour(name: str, path: str) -> str | None:
    """Refill the template silhouette with an xkcd colour; return its hex, or None if unknown."""
    hexv = XKCD_COLORS.get(f"xkcd:{name.lower()}")
    if not hexv:
        return None
    src = template()
    out = Image.new("RGBA", src.size, ImageColor.getrgb(hexv) + (0,))
    out.putalpha(src.getchannel("A"))                 # the shape is the alpha mask
    out.save(path)
    return hexv


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('usage: uv run colour_swatch.py "<xkcd colour name>" [out.png]')
    name = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else name.replace(" ", "_") + ".png"
    hexv = recolour(name, path)
    if hexv is None:
        sys.exit(f"{name!r} is not an xkcd colour name")
    print(f"{name} -> {hexv} -> {path}  (ARASAAC {TEMPLATE_ID} recoloured; CC BY-NC-SA)")


if __name__ == "__main__":
    main()

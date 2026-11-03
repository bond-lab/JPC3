#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
"""Project 4 starter: generate a colour-swatch pictogram from an xkcd colour name.

Colour terms are the clear case of a synset that will never have a drawn
pictograph and does not need one. The xkcd colour survey names 949 colours
with hex values (shipped offline in matplotlib), so for a colour synset we can
just generate a labelled swatch and attach it.

Run:  uv run colour_swatch.py chestnut                 # -> chestnut.png
      uv run colour_swatch.py "burnt orange" out.png
"""
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import XKCD_COLORS  # 949 named colours, offline


def swatch(name: str, path: str) -> str | None:
    """Write a labelled square swatch for an xkcd colour name; return its hex, or None."""
    hexv = XKCD_COLORS.get(f"xkcd:{name.lower()}")
    if not hexv:
        return None
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, color=hexv))
    ax.text(0.5, 0.08, name, ha="center", va="center", fontsize=11, color="white")
    fig.savefig(path, dpi=150, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return hexv


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('usage: uv run colour_swatch.py "<xkcd colour name>" [out.png]')
    name = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else name.replace(" ", "_") + ".png"
    hexv = swatch(name, path)
    if hexv is None:
        sys.exit(f"{name!r} is not an xkcd colour name")
    print(f"{name} -> {hexv} -> {path}")


if __name__ == "__main__":
    main()

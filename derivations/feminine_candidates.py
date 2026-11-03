#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1"]
# ///
"""Project 2 starter: crude feminine-motion candidates, by suffix.

List Czech noun lemmas where *base + a feminine suffix* is also a lemma
(ucitel -> ucitelka). This over-generates on purpose -- *past* -> *pastka* is
a mousetrap, not a feminine -- which is the point: the candidate list is
cheap, and telling real derivations from coincidences is the work. Wire in
DeriNet (https://ufal.mff.cuni.cz/derinet) for a serious candidate source.

Run:  uv run feminine_candidates.py        # all candidates
      uv run feminine_candidates.py 40     # the first N
"""
import sys
from collections.abc import Iterator
from pathlib import Path

import wn

wn.config.data_directory = Path(__file__).resolve().parent.parent / "patterns" / ".wn_data"
SUFFIXES = ("ka", "kyně", "ice", "yně")


def candidates(cs: wn.Wordnet) -> Iterator[tuple[str, str, str]]:
    """Yield (base, feminine, suffix) for every lemma pair that looks derived."""
    lemmas = {w.lemma() for w in cs.words(pos="n")}
    for base in sorted(lemmas):
        for suf in SUFFIXES:
            if base + suf in lemmas:
                yield base, base + suf, suf


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")
    n = 0
    for base, fem, suf in candidates(cs):
        print(f"{base} -> {fem}  ({suf})")
        n += 1
        if limit and n >= limit:
            break
    print(f"\n{n} candidates printed -- judge a sample by hand", file=sys.stderr)


if __name__ == "__main__":
    main()

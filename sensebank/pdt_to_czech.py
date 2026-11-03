#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
"""Project 3 starter: map a PDT (PWN 1.5) synset offset to the current Czech synset.

PDT sense tags are Princeton WordNet **1.5** offsets. The CILI project keeps a
table mapping those straight to an ILI (older-wn-mappings/ili-map-pwn15.tab),
and the Czech wordnet is keyed to ILIs. So the bridge is one hop:
offset -> ILI -> Czech synset, with no version chaining.

The interesting output is the residue: tags that reach no Czech synset.

Run:  uv run pdt_to_czech.py 00002403-a 00007846-n     # offsets as arguments
      uv run pdt_to_czech.py < tags.txt                 # one offset per line
Output, one line per tag:  offset  ili  lemmas | MISSING-SYNSET | NO-ILI
"""
import sys
from pathlib import Path

import requests
import wn

HERE = Path(__file__).resolve().parent
wn.config.data_directory = HERE.parent / "patterns" / ".wn_data"
URL = ("https://raw.githubusercontent.com/globalwordnet/cili/master/"
       "older-wn-mappings/ili-map-pwn15.tab")
TAB = HERE / "ili-map-pwn15.tab"


def pwn15_to_ili() -> dict[str, str]:
    """{ '00002403-a': 'i1', ... } from the PWN 1.5 CILI map (cached beside the script)."""
    if not TAB.exists():
        TAB.write_text(requests.get(URL, timeout=120).text, encoding="utf-8")
    out: dict[str, str] = {}
    for line in TAB.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        ili, offset, *_confidence = line.split("\t")   # three columns
        out[offset.strip()] = ili.strip()
    return out


def lookup(offset: str, mapping: dict[str, str], cs: wn.Wordnet) -> tuple[str | None, list[str]]:
    """Return (ili, Czech lemmas) for a PWN 1.5 offset; lemmas is [] if unmapped."""
    ili = mapping.get(offset)
    if not ili:
        return None, []
    return ili, [w.lemma() for s in cs.synsets(ili=ili) for w in s.words()]


def main() -> None:
    offsets = sys.argv[1:] or [ln.strip() for ln in sys.stdin if ln.strip()]
    if not offsets:
        sys.exit("usage: uv run pdt_to_czech.py <offset>... | < tags.txt")
    mapping = pwn15_to_ili()
    cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")
    counts = {"mapped": 0, "missing-synset": 0, "no-ili": 0}
    for off in offsets:
        ili, lemmas = lookup(off, mapping, cs)
        if ili is None:
            kind, show = "no-ili", "NO-ILI"
        elif not lemmas:
            kind, show = "missing-synset", "MISSING-SYNSET"
        else:
            kind, show = "mapped", "|".join(lemmas)
        counts[kind] += 1
        print(f"{off}\t{ili or '-'}\t{show}")
    print("\n" + "  ".join(f"{k}: {v}" for k, v in counts.items()), file=sys.stderr)


if __name__ == "__main__":
    main()

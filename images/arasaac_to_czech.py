#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
"""Project 4 starter: ARASAAC pictograms -> Czech synsets.

ARASAAC pictograms already carry WordNet **3.1** synset ids. Map those to an
ILI through the CILI table and look up the Czech synset, so a pictogram can be
attached to the right Czech concept -- the same bridge as project 5.

Run:  uv run arasaac_to_czech.py pes         # search ARASAAC (Czech) for a word
      uv run arasaac_to_czech.py pes 10      # the first N pictograms
Output, one line per (pictogram, synset):  id  offset  ili  lemmas  image-url
"""
import sys
from pathlib import Path

import requests
import wn

HERE = Path(__file__).resolve().parent
wn.config.data_directory = HERE.parent / "patterns" / ".wn_data"
CILI_URL = ("https://raw.githubusercontent.com/globalwordnet/cili/master/"
            "ili-map-pwn31.tab")
CILI_TAB = HERE / "ili-map-pwn31.tab"
ARASAAC = "https://api.arasaac.org/api/pictograms/cs/search/"
IMAGE = "https://static.arasaac.org/pictograms/{pid}/{pid}_300.png"


def load_cili() -> dict[str, str]:
    """{ '02086723-n': 'i46360', ... } mapping PWN 3.1 ids to ILIs (cached)."""
    if not CILI_TAB.exists():
        CILI_TAB.write_text(requests.get(CILI_URL, timeout=120).text, encoding="utf-8")
    mapping: dict[str, str] = {}
    for line in CILI_TAB.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            ili, pwn = line.split("\t", 1)
            mapping[pwn.strip()] = ili.strip()
    return mapping


def search(word: str) -> list[dict]:
    """ARASAAC pictograms whose Czech keywords match `word`."""
    r = requests.get(ARASAAC + word, headers={"accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: uv run arasaac_to_czech.py <czech word> [N]")
    word = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    pwn31_to_ili = load_cili()
    cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")
    for picto in search(word)[:limit]:
        pid = picto["_id"]
        for off in picto.get("synsets", []):             # e.g. '02086723-n'
            ili = pwn31_to_ili.get(off)
            lemmas = [w.lemma() for s in (cs.synsets(ili=ili) if ili else []) for w in s.words()]
            print(f"{pid}\t{off}\t{ili or '-'}\t{'|'.join(lemmas) or 'MISSING'}\t{IMAGE.format(pid=pid)}")


if __name__ == "__main__":
    main()

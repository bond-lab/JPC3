# Project 3 — Merging the PDT wordnet sense tags

The Prague Dependency Treebank is sense-annotated against **PWN 1.5**-era Czech
wordnet synsets. Re-anchor those tags to the current synset inventory, and
characterise the **residue** — the tags that don't carry over.

## The good news: a direct 1.5 → ILI map

CILI ships historical maps under
[`older-wn-mappings/`](https://github.com/globalwordnet/cili/tree/master/older-wn-mappings),
including `ili-map-pwn15.tab`. So the hop you feared (chaining 1.5→1.6→…→3.0)
is unnecessary: map the PDT synset offset straight to an ILI, then to Czech.

The file has **three** tab-separated columns — `ili`, `offset-pos`,
`confidence` — so parse all three (the confidence flag is itself worth
reporting on in the error analysis):

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
from pathlib import Path
import requests, wn

wn.config.data_directory = Path(__file__).resolve().parent.parent / "patterns" / ".wn_data"
URL = ("https://raw.githubusercontent.com/globalwordnet/cili/master/"
       "older-wn-mappings/ili-map-pwn15.tab")

def pwn15_to_ili() -> dict[str, str]:
    """{ '00002403-a': 'i1', ... } from the PWN 1.5 CILI map."""
    text = requests.get(URL, timeout=120).text
    out = {}
    for line in text.splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        ili, offset, *rest = line.split("\t")      # rest[0] = confidence
        out[offset.strip()] = ili.strip()
    return out

m = pwn15_to_ili()
cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")

def pdt_tag_to_czech(offset_pos: str):
    """A PDT 1.5 synset offset -> the current Czech synset(s), or []."""
    ili = m.get(offset_pos)
    return cs.synsets(ili=ili) if ili else []
```

Sanity check: of the ~87k distinct ILIs in the 1.5 map, **26 363** resolve to a
synset that exists in the Czech wordnet — so the bridge reaches a large share of
the inventory before you even look at PDT.

## What to actually build

1. Read the PDT sense tags (your input data). Each is an old synset id / offset.
2. Map offset → ILI → current Czech synset with the helper above.
3. Classify every tag:
   - **mapped** — one current synset, done.
   - **split / merged** — the old synset corresponds to several current ones, or
     several old ones collapse into one (use the confidence column and the
     English gloss to decide).
   - **renumbered** — maps via ILI but the offset changed.
   - **deleted / missing** — no ILI, or the ILI has no Czech synset.
4. Hand-categorise ~100 of the **unmapped residue** — that taxonomy is the
   deliverable. Compare against the structural-mapping approach of Daudé et al.

## Readings

Daudé, Padró & Rigau (2000) *Mapping WordNets Using Structural Information*;
Bond et al. (2016) *CILI*. See the top-level `README.md` for keys.

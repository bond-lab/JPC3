# Project 4 — ARASAAC & Global Symbols pictographs

Extend [ARAWN](https://github.com/omwn/arawn) (the existing ARASAAC wordnet):
add colour variants, match more synsets, and bring in sets from other countries
(e.g. the Bulgarian and Croatian sets on
[Global Symbols](https://globalsymbols.com/)). Watch the per-set licences — they
differ — and report them.

## Both sources have usable public APIs

**ARASAAC** pictograms already carry a WordNet synset tag (a 3.1 offset) and a
`sex` flag, so they bridge to Czech by exactly the ILI route projects 3 and 5
use:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
from pathlib import Path
import requests, wn

wn.config.data_directory = Path(__file__).resolve().parent.parent / "patterns" / ".wn_data"
CILI = ("https://raw.githubusercontent.com/globalwordnet/cili/master/"
        "ili-map-pwn31.tab")

pwn31_to_ili = dict(
    reversed(line.split("\t", 1))                       # 'i46360\t02086723-n'
    for line in requests.get(CILI, timeout=120).text.splitlines() if "\t" in line
)
cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")

r = requests.get("https://api.arasaac.org/api/pictograms/cs/search/pes",
                 headers={"accept": "application/json"}, timeout=30).json()
for picto in r[:3]:
    pid = picto["_id"]
    for off in picto.get("synsets", []):                # e.g. '02086723-n'
        ili = pwn31_to_ili.get(off)
        cz = [w.lemma() for s in (cs.synsets(ili=ili) if ili else []) for w in s.words()]
        img = f"https://static.arasaac.org/pictograms/{pid}/{pid}_300.png"
        print(pid, off, ili, cz, img)
```

(`reversed(line.split(...))` flips each `ili<TAB>offset` row into
`offset -> ili`; strip whitespace if you keep the values.)

**Global Symbols** returns an image URL and the symbol-set it came from:

```
GET https://globalsymbols.com/api/v1/symbolsets                      # list sets + licences
GET https://globalsymbols.com/api/v1/labels/search?query=dog&language=eng&symbolset=<id>
# -> [{ picto: { image_url, symbolset_id, part_of_speech, native_format }}]
```

The Bulgarian/Croatian sets are particular `symbolset` ids — list the sets
first and note each one's licence before you import its images.

## Angles for the four-part spine

- **Match more synsets.** ARASAAC's own synset tags are a starting alignment;
  for untagged pictographs match on the Czech/English keyword through the
  wordnet. Report a coverage before/after over the synset inventory (weight by
  frequency if you can).
- **Colour variants.** ARASAAC serves colour and plain versions (and skin/hair
  options) of the same pictogram id — a clean before/after figure.
- **Error analysis.** Hand-check 100 matches: is the picture a fair depiction of
  *that sense*? Group the failures (wrong sense, too abstract, culture-specific).
- **Licences.** One short table: symbol set → licence → count imported.

## Readings

Sevens (2018) *Words Divide, Pictographs Unite*; Bond & Foster (2013)
*Linking and Extending an Open Multilingual Wordnet*. Keys in the top-level
`README.md`.

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
"""Project 5 starter: Wikidata --> ILI --> Czech.

Pull Wikidata items that carry a wordnet/ILI link *and* a Czech label, resolve
them to an ILI, and check whether the Czech wordnet already covers it. Each
item is classified:

    present         Czech synset exists and already has this label as a lemma
    missing-lemma   Czech synset exists but lacks this label  -> candidate lemma
    missing-synset  ILI not in the Czech wordnet at all       -> candidate synset
    no-ili          could not resolve to an ILI (rare)

Two ways in, and we use both:
  * P5063 "Interlingual Index ID" -- the ILI directly (values look like iNNNN).
    Fewer items carry it (~20k), but no mapping is needed.
  * P8814 "WordNet 3.1 Synset ID" -- more items (~35k), but it is a WordNet
    **3.1** offset, so we map it to an ILI through the Collaborative
    Interlingual Index table `ili-map-pwn31.tab`. (Mapping through omw-en:2.0
    instead fails: it is WordNet 3.0, whose offsets differ.)
We prefer P5063 when present and fall back to P8814 -> CILI, which covers the
most items.

Run:  uv run wikidata_to_czech.py            # small demo (LIMIT 500)
      uv run wikidata_to_czech.py 5000 out.tsv

WDQS etiquette: send a real User-Agent, and for the *whole* set (~tens of
thousands of rows) page with LIMIT/OFFSET or use a Query Service dump rather
than one huge query.
"""
import sys
from pathlib import Path
import requests
import wn

HERE = Path(__file__).resolve().parent
wn.config.data_directory = HERE.parent / "patterns" / ".wn_data"   # share one DB
WDQS = "https://query.wikidata.org/sparql"
UA = "JPC3-course/0.1 (https://github.com/omwn; bond@ieee.org)"
CILI_URL = ("https://raw.githubusercontent.com/globalwordnet/cili/"
            "master/ili-map-pwn31.tab")
CILI_TAB = HERE / "ili-map-pwn31.tab"


def load_cili() -> dict[str, str]:
    """{ '02086723-n': 'i46360', ... } mapping PWN 3.1 ids to ILIs."""
    if not CILI_TAB.exists():
        CILI_TAB.write_bytes(requests.get(CILI_URL, timeout=120).content)
    mapping = {}
    for line in CILI_TAB.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            ili, pwn = line.split("\t", 1)
            mapping[pwn.strip()] = ili.strip()
    return mapping


def fetch(limit: int) -> dict[str, dict]:
    """Return {qid: {'label', 'ili', 'wn'}} for items with P5063 or P8814."""
    query = f"""
    SELECT ?item ?cs ?ili ?wn WHERE {{
      {{ ?item wdt:P5063 ?ili . }} UNION {{ ?item wdt:P8814 ?wn . }}
      ?item rdfs:label ?cs . FILTER(lang(?cs) = "cs")
    }} LIMIT {limit}
    """
    r = requests.get(WDQS, params={"query": query, "format": "json"},
                     headers={"User-Agent": UA}, timeout=120)
    r.raise_for_status()
    items: dict[str, dict] = {}
    for b in r.json()["results"]["bindings"]:
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        rec = items.setdefault(qid, {"label": b["cs"]["value"],
                                     "ili": None, "wn": None})
        if "ili" in b:
            rec["ili"] = b["ili"]["value"]      # P5063, e.g. i46360
        if "wn" in b:
            rec["wn"] = b["wn"]["value"]        # P8814, e.g. 02086723-n
    return items


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    pwn31_to_ili = load_cili()
    cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")

    items = fetch(limit)
    counts = {"present": 0, "missing-lemma": 0, "missing-synset": 0, "no-ili": 0}
    records = []
    for qid, rec in items.items():
        label = rec["label"]
        ili = rec["ili"] or pwn31_to_ili.get(rec["wn"])   # prefer P5063
        wnid = rec["wn"] or ""
        if not ili:
            kind, cs_lemmas = "no-ili", []
        else:
            cs_syns = cs.synsets(ili=ili)
            cs_lemmas = [w.lemma() for s in cs_syns for w in s.words()]
            if not cs_syns:
                kind = "missing-synset"
            elif label in cs_lemmas:
                kind = "present"
            else:
                kind = "missing-lemma"
        counts[kind] += 1
        records.append((kind, qid, wnid, ili or "", label, "|".join(cs_lemmas)))

    print(f"{len(items)} Wikidata items with P5063/P8814 + a Czech label")
    for k, v in counts.items():
        print(f"  {k:15}: {v}")
    print("\ncandidate additions (missing-lemma / missing-synset), first 15:")
    for rec in [r for r in records if r[0].startswith("missing")][:15]:
        kind, qid, wnid, ili, label, lemmas = rec
        print(f"  {kind:14} {label!r:24} ili={ili:9} cs=[{lemmas}]")

    if out:
        with out.open("w", encoding="utf-8") as fh:
            fh.write("kind\tqid\twn31\tili\twikidata_cs\tczech_lemmas\n")
            for rec in records:
                fh.write("\t".join(rec) + "\n")
        print(f"\nwrote {len(records)} rows to {out}")


if __name__ == "__main__":
    main()

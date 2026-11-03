#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1"]
# ///
"""Project 6 starter: assemble the evidence bundle an LLM judges.

Before asking a model whether a synset's lemmas are right, give it grounds:
the Czech lemmas, the English lemmas and gloss for the same concept (reached
through the shared ILI in omw-en), and -- when the project-5 run found one --
Wikidata's Czech label. This script writes one JSON record per synset, plus
the fixed answer schema the model must fill in, so its answers are scorable.

There is deliberately no API call here: this is the half you can run offline
and inspect. The call itself, and the validation of what comes back, is the
project.

Run:  uv run build_evidence.py 200 evidence.jsonl
      uv run build_evidence.py 200 evidence.jsonl ../wikidata/candidates.tsv
"""
import csv
import json
import random
import sys
from pathlib import Path

import wn

wn.config.data_directory = Path(__file__).resolve().parent.parent / "patterns" / ".wn_data"

SCHEMA = {
    "synset": "ntumc-cs-02086723-n",
    "verdict": "ok | suspect",
    "problem": "wrong-sense | missing-lemma | spurious-lemma | bad-gloss | none",
    "rationale": "one sentence, citing the evidence",
    "confidence": 0.0,
}


def wikidata_labels(tsv: Path | None) -> dict[str, str]:
    """{ili: wikidata Czech label} from a wikidata_to_czech.py TSV, if given."""
    if tsv is None or not tsv.exists():
        return {}
    with tsv.open(encoding="utf-8") as fh:
        return {row["ili"]: row["wikidata_cs"] for row in csv.DictReader(fh, delimiter="\t") if row["ili"]}


def evidence(ss: wn.Synset, en: wn.Wordnet, labels: dict[str, str]) -> dict:
    """One record: what a model needs to judge this Czech synset."""
    en_syn = en.synsets(ili=ss.ili) if ss.ili else []
    return {
        "synset": ss.id,
        "ili": ss.ili,
        "czech_lemmas": [w.lemma() for w in ss.words()],
        "english_lemmas": [w.lemma() for s in en_syn for w in s.words()],
        "gloss": next((d for s in en_syn for d in s.definitions()), None),
        "wikidata_cs": labels.get(ss.ili or ""),
    }


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("evidence.jsonl")
    tsv = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    cs = wn.Wordnet(lexicon="ntumc-cs:2026.08")
    en = wn.Wordnet(lexicon="omw-en:2.0")
    labels = wikidata_labels(tsv)

    random.seed(1)                                   # a reproducible sample
    sample = random.sample([s for s in cs.synsets(pos="n") if s.ili], n)
    with out.open("w", encoding="utf-8") as fh:
        for ss in sample:
            fh.write(json.dumps(evidence(ss, en, labels), ensure_ascii=False) + "\n")
    print(f"wrote {n} records to {out} ({sum(1 for s in sample if labels.get(s.ili))} with a Wikidata label)")
    print("answer schema the model must fill:\n" + json.dumps(SCHEMA, indent=2))


if __name__ == "__main__":
    main()

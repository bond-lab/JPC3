#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "lxml"]
# ///
"""Count 'role nouns' in the Czech WordNet.

A role noun denotes a person by the role they occupy (teacher, doctor). The
Czech WordNet has no lexicographer files and records relations one way only,
so person-ness is read off the English side: almost every Czech synset carries
an ILI, and the same ILI names the English synset in omw-en. We proxy "role
noun" two ways and report both:

  (A) English lexicographer file == noun.person
  (B) transitive hyponym of {person, individual, someone, ...}  (i35562)

Run:  uv run count_role_nouns.py
It downloads omw-en:2.0 and the Czech WordNet into ./.wn_data on first use.
"""
from pathlib import Path

import wn

HERE = Path(__file__).resolve().parent
DATA = HERE / ".wn_data"
CES = "wncze:2.2"
CES_URL = ("https://github.com/bond-lab/czech-wn/releases/download/"
           "v2.2/wncze-2.2.tar.xz")

DATA.mkdir(parents=True, exist_ok=True)
wn.config.data_directory = DATA
assert wn.config.database_path.is_relative_to(HERE), "data dir isolation failed"


def ensure_data() -> None:
    have = {lx.id for lx in wn.lexicons()}
    if "omw-en" not in have:
        wn.download("omw-en:2.0", progress_handler=None)
    if "wncze" not in have:
        wn.download(CES_URL, progress_handler=None)


def english_person_ilis(en: wn.Wordnet) -> tuple[set[str], set[str]]:
    """Return (noun.person ILIs, person-hyponym-closure ILIs)."""
    by_lexfile = {ss.ili for ss in en.synsets(pos="n")
                  if ss.ili and ss.lexfile() == "noun.person"}

    root = None
    for ss in en.synsets("person", pos="n"):
        if {"person", "individual", "someone"} & {w.lemma() for w in ss.words()}:
            root = ss
            break
    closure: set[str] = set()
    if root is not None:
        stack, seen = [root], set()
        while stack:
            cur = stack.pop()
            if cur.id in seen:
                continue
            seen.add(cur.id)
            if cur.ili:
                closure.add(cur.ili)
            stack.extend(cur.hyponyms())
    return by_lexfile, closure


def czech_counts(cs_nouns: list, target: set[str]) -> tuple[int, int, int]:
    syns = [ss for ss in cs_nouns if ss.ili in target]
    lemmas, senses = set(), 0
    for ss in syns:
        ws = ss.words()
        senses += len(ws)
        lemmas.update(w.lemma() for w in ws)
    return len(syns), len(lemmas), senses


def main() -> None:
    ensure_data()
    en = wn.Wordnet(lexicon="omw-en:2.0")
    cs = wn.Wordnet(lexicon=CES)

    person_lexfile, person_closure = english_person_ilis(en)
    cs_nouns = list(cs.synsets(pos="n"))

    print(f"Czech synsets (all POS)     : {sum(1 for _ in cs.synsets())}")
    print(f"Czech noun synsets          : {len(cs_nouns)}")
    print(f"English noun.person synsets : {len(person_lexfile)}\n")

    for label, tgt in [("noun.person lexfile", person_lexfile),
                       ("person-hyponym closure", person_closure)]:
        n_syn, n_lem, n_sense = czech_counts(cs_nouns, tgt)
        print(f"[{label}]")
        print(f"  Czech role-noun synsets         : {n_syn}")
        print(f"  distinct Czech role-noun lemmas : {n_lem}")
        print(f"  lemma-synset pairs (senses)     : {n_sense}\n")


if __name__ == "__main__":
    main()

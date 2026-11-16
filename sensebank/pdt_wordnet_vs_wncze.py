#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
"""How much of the PDT annotation wordnet is in the Czech WordNet 2.2?

The lexico-semantic annotation of PDT (2004-2011) used its own copy of the
Czech WordNet ("Czech WordNet 1.9 PDT", 23,094 synsets). It was edited
in Brno and, while annotating, at ÚFAL: new synsets for missing senses,
definitions and examples, merged and split senses for 25 hard lemmas. This
script asks what of that reached the current release, synset by synset:

  - its ILI, through the CILI map from Princeton WordNet 1.5;
  - the wncze 2.2 synset with that ILI, and which of its words are there;
  - whether its definitions, examples and hypernym links are there;
  - how many annotated words were tagged with it, so every count can be
    weighted by use.

Run:  uv run pdt_wordnet_vs_wncze.py              # summary; data/pdt_vs_wncze.tsv
It downloads the annotation and its wordnet from LINDAT (3 MB) on first use.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import wn
from pdt_sources import (
    DATA,
    HERE,
    NasSynset,
    ili_of,
    pwn15_ili,
    read_nas,
    read_tags,
    tag_index,
    tag_key,
)

wn.config.data_directory = HERE.parent / "patterns" / ".wn_data"
CES = "wncze:2.2"
CES_URL = "https://github.com/bond-lab/czech-wn/releases/download/v2.2/wncze-2.2.tar.xz"
OUT = DATA / "pdt_vs_wncze.tsv"
FACTS = HERE / "report" / "facts-compare.json"
UFAL = "bejce"   # the edit stamps of Eduard Bejček (bejce9am, bejcek); the rest are Brno's

# The 25 lemmas ÚFAL re-analysed (Bejček et al. 2006, Table 4); stát twice.
CORRECTED = ["čas", "část", "cena", "člověk", "dát", "den", "dobrý", "dostat", "fax",
             "místo", "mít", "moci", "návrh", "podnik", "práce", "právo", "řada", "říkat",
             "rok", "stát", "svět", "systém", "uvést", "vysoký"]

SLUGS = ["all", "some", "elsewhere", "gone", "absent", "noili", "newin", "newout"]
STATUSES = [
    "all words kept",
    "some words kept",
    "no word kept, words elsewhere",
    "no word kept, words gone",
    "concept not in wncze",
    "no ILI for the 1.5 offset",
    "new synset, its words in one wncze synset",
    "new synset, not in wncze",
]


@dataclass
class Row:
    """What became of one annotation synset."""

    nas: NasSynset
    status: str
    ili: str = ""
    confidence: float = 0.0
    wncze: str = ""
    kept: int = 0
    defs_kept: int = 0
    examples_kept: int = 0
    tokens: int = 0


@dataclass
class Wncze:
    """The parts of wncze 2.2 the comparison looks things up in."""

    by_ili: dict[str, wn.Synset]
    by_lemma: dict[tuple[str, str], set[str]]


def load_wncze() -> Wncze:
    """Load wncze 2.2, downloading it once, and index it.

    Returns:
        Its synsets by ILI, and (lemma, part of speech) -> synset ids
    """
    if "wncze" not in {lx.id for lx in wn.lexicons()}:
        wn.download(CES_URL, progress_handler=None)
    cs = wn.Wordnet(lexicon=CES)
    by_lemma: dict[tuple[str, str], set[str]] = defaultdict(set)
    for sense in cs.senses():
        ss = sense.synset()
        by_lemma[(sense.word().lemma(), pos(ss.pos))].add(ss.id)
    return Wncze({ss.ili: ss for ss in cs.synsets() if ss.ili}, by_lemma)


def pos(p: str) -> str:
    """Fold parts of speech to n, v, a, r.

    Args:
        p: a part of speech from either wordnet ('b' and 's' included)

    Returns:
        The folded part of speech
    """
    return {"b": "r", "s": "a"}.get(p, p)


def norm(text: str) -> str:
    """Normalise a definition or example for comparison.

    The annotation wordnet often prefixes the lemma ('cena: trofej').

    Args:
        text: a definition or example

    Returns:
        It in lower case without the prefix, quotes or final punctuation
    """
    text = re.sub(r"^[^\s:]+:\s+", "", text.strip())
    return text.strip('"„“ .').lower()


def carried(texts: list[str], into: list[str]) -> int:
    """Count the texts found, normalised, in another list.

    Args:
        texts: definitions or examples of the annotation synset
        into: those of the wncze synset

    Returns:
        How many of texts are in into, or contained in one of them
    """
    targets = [norm(t) for t in into]
    return sum(1 for t in texts if norm(t) and any(norm(t) in x for x in targets))


def classify(syn: NasSynset, cili: dict[str, tuple[str, float]], cs: Wncze) -> Row:
    """Decide what became of one annotation synset.

    Args:
        syn: the annotation synset
        cili: the CILI map from Princeton 1.5
        cs: wncze 2.2, indexed

    Returns:
        Its row, with a status from STATUSES
    """
    p = pos(syn.pos)
    if syn.pwn15 is None:
        shared = set.intersection(*(cs.by_lemma.get((w, p), set()) for w in syn.literals))
        found = "its words in one wncze synset" if shared else "not in wncze"
        return Row(syn, f"new synset, {found}", wncze=" ".join(sorted(shared)))
    hit = ili_of(syn, cili)
    if hit is None:
        return Row(syn, "no ILI for the 1.5 offset")
    ili, conf = hit
    ss = cs.by_ili.get(ili)
    if ss is None:
        return Row(syn, "concept not in wncze", ili, conf)
    words = {w.lemma() for w in ss.words()}
    kept = sum(1 for w in syn.literals if w in words)
    if kept == len(syn.literals):
        status = "all words kept"
    elif kept:
        status = "some words kept"
    elif any((w, p) in cs.by_lemma for w in syn.literals):
        status = "no word kept, words elsewhere"
    else:
        status = "no word kept, words gone"
    return Row(syn, status, ili, conf, ss.id, kept,
               carried(syn.definitions, ss.definitions()),
               carried(syn.examples, ss.examples()))


def hypernyms_kept(rows: dict[str, Row], cs: Wncze) -> tuple[int, int, int]:
    """Count the hypernym links whose both ends reached wncze, and those kept.

    Args:
        rows: every annotation synset's row, by its id
        cs: wncze 2.2, indexed

    Returns:
        (links kept, links with both ends in wncze, links lost from a wncze
        synset that has no hypernym at all)
    """
    both = kept = orphans = 0
    for row in rows.values():
        if not row.ili or not row.wncze:
            continue
        child = cs.by_ili[row.ili]
        parents = {h.id for h in child.hypernyms()}
        for target in row.nas.hypernyms:
            up = rows.get(target)
            if up and up.ili and up.wncze:
                both += 1
                kept += up.wncze in parents
                orphans += not parents
    return kept, both, orphans


def report(rows: dict[str, Row], cs: Wncze) -> None:
    """Print the summary tables.

    Args:
        rows: every annotation synset's row, by its id
        cs: wncze 2.2, indexed
    """
    by = defaultdict(list)
    for row in rows.values():
        by[row.status].append(row)
    total_tok = sum(r.tokens for r in rows.values())
    print(f"{'status':42} {'synsets':>8} {'words':>7} {'kept':>6} {'tagged':>8} {'share':>6}")
    for status in STATUSES:
        rs = by.get(status, [])
        words = sum(len(r.nas.literals) for r in rs)
        tok = sum(r.tokens for r in rs)
        print(f"{status:42} {len(rs):8} {words:7} {sum(r.kept for r in rs):6} {tok:8} "
              f"{tok / total_tok:6.1%}")
    rs = list(rows.values())
    print(f"{'total':42} {len(rs):8} {sum(len(r.nas.literals) for r in rs):7} "
          f"{sum(r.kept for r in rs):6} {total_tok:8}")

    low = Counter(r.status for r in rs if r.ili and r.confidence < 1)
    print(f"\nCILI 1.5 links below confidence 1, by status: {dict(low)}")

    for team, rows_ in (("ÚFAL (Bejček)", [r for r in rs if r.nas.stamp.startswith(UFAL)]),
                        ("Brno", [r for r in rs if r.nas.stamp
                                  and not r.nas.stamp.startswith(UFAL)])):
        print(f"\nedit stamps of {team}: {len(rows_)} synsets, {sum(r.tokens for r in rows_)} "
              f"tagged words; definitions {sum(len(r.nas.definitions) for r in rows_)}, "
              f"{sum(r.defs_kept for r in rows_)} in wncze; examples "
              f"{sum(len(r.nas.examples) for r in rows_)}, {sum(r.examples_kept for r in rows_)} "
              f"in wncze")
        print(f"  status {dict(Counter(r.status for r in rows_).most_common())}")
    defs = sum(len(r.nas.definitions) for r in rs)
    exs = sum(len(r.nas.examples) for r in rs)
    print(f"\nall definitions: {defs}, {sum(r.defs_kept for r in rs)} in wncze 2.2")
    print(f"all examples:    {exs}, {sum(r.examples_kept for r in rs)} in wncze 2.2")
    kept, both, orphans = hypernyms_kept(rows, cs)
    print(f"hypernym links with both ends in wncze: {both}, {kept} kept; "
          f"{orphans} of the rest from a wncze synset with no hypernym")

    print(f"\n{'lemma':10} {'PDT senses':>10} {'tagged':>7} {'reached':>8} {'wncze senses':>12}")
    for lemma in CORRECTED:
        mine = [r for r in rs if lemma in r.nas.literals]
        now = sum(len(cs.by_lemma.get((lemma, p), ())) for p in "nvar")
        reached = sum(1 for r in mine if r.ili in cs.by_ili
                      and lemma in {w.lemma() for w in cs.by_ili[r.ili].words()})
        print(f"{lemma:10} {len(mine):10} {sum(r.tokens for r in mine):7} {reached:8} {now:12}")


def id_check(rows: dict[str, Row], cs: Wncze) -> dict[str, int]:
    """Test whether the annotation ids could be the 2.0 offsets wncze uses.

    Args:
        rows: every annotation synset's row, by its id
        cs: wncze 2.2, indexed

    Returns:
        How many annotation offsets name a wncze synset as 2.0 ids, and how
        many of those share a word with it
    """
    synsets = {ss.id: ss for ss in cs.by_ili.values()}
    same = overlap = 0
    for row in rows.values():
        if row.nas.pwn15 is None:
            continue
        ss = synsets.get(f"wncze-{row.nas.id}")
        if ss is not None:
            same += 1
            overlap += bool(set(row.nas.literals) & {w.lemma() for w in ss.words()})
    return {"pwn15": sum(1 for r in rows.values() if r.nas.pwn15), "same": same,
            "overlap": overlap}


def facts(rows: dict[str, Row], cs: Wncze) -> dict:
    """Collect the figures the report cites.

    Args:
        rows: every annotation synset's row, by its id
        cs: wncze 2.2, indexed

    Returns:
        A nested dict of counts, keyed as the report's facts.tex expects
    """
    rs = list(rows.values())
    total = sum(r.tokens for r in rs)
    out: dict = {"total": {"synsets": len(rs), "words": sum(len(r.nas.literals) for r in rs),
                           "kept": sum(r.kept for r in rs), "tagged": total}}
    for slug, status in zip(SLUGS, STATUSES):
        sub = [r for r in rs if r.status == status]
        tagged = sum(r.tokens for r in sub)
        out[slug] = {"synsets": len(sub), "words": sum(len(r.nas.literals) for r in sub),
                     "kept": sum(r.kept for r in sub), "tagged": tagged,
                     "share": round(100 * tagged / total, 1),
                     "lowconf": sum(1 for r in sub if r.ili and r.confidence < 1)}
    for team, sub in (("ufal", [r for r in rs if r.nas.stamp.startswith(UFAL)]),
                      ("brno", [r for r in rs if r.nas.stamp
                                and not r.nas.stamp.startswith(UFAL)])):
        out[team] = {"synsets": len(sub), "tagged": sum(r.tokens for r in sub),
                     "defs": sum(len(r.nas.definitions) for r in sub),
                     "defskept": sum(r.defs_kept for r in sub),
                     "examples": sum(len(r.nas.examples) for r in sub),
                     "exampleskept": sum(r.examples_kept for r in sub),
                     "allkept": sum(1 for r in sub if r.status == STATUSES[0])}
    out["defs"] = {"total": sum(len(r.nas.definitions) for r in rs),
                   "kept": sum(r.defs_kept for r in rs)}
    out["examples"] = {"total": sum(len(r.nas.examples) for r in rs),
                       "kept": sum(r.examples_kept for r in rs)}
    new = [r for r in rs if r.nas.pwn15 is None]
    out["newsyn"] = {"synsets": len(new), "tagged": sum(r.tokens for r in new)}
    out["idcheck"] = id_check(rows, cs)
    kept, both, orphans = hypernyms_kept(rows, cs)
    out["hyper"] = {"both": both, "kept": kept, "orphans": orphans}
    out["lemma"] = {}
    for i, lemma in enumerate(CORRECTED):
        mine = [r for r in rs if lemma in r.nas.literals]
        out["lemma"][f"l{i}"] = {
            "pdt": len(mine), "tagged": sum(r.tokens for r in mine),
            "reached": sum(1 for r in mine if r.ili in cs.by_ili
                           and lemma in {w.lemma() for w in cs.by_ili[r.ili].words()}),
            "now": sum(len(cs.by_lemma.get((lemma, p), ())) for p in "nvar")}
    return out


def write_tsv(rows: dict[str, Row], path: Path) -> None:
    """Write one line per annotation synset.

    Args:
        rows: every annotation synset's row, by its id
        path: where to write
    """
    with path.open("w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh, delimiter="\t", lineterminator="\n")
        out.writerow(["pdt_synset", "status", "tagged", "ili", "cili_confidence", "wncze",
                      "words", "kept", "definitions", "defs_kept", "examples",
                      "examples_kept", "edited"])
        for r in sorted(rows.values(), key=lambda r: -r.tokens):
            out.writerow([r.nas.id, r.status, r.tokens, r.ili, r.confidence or "", r.wncze,
                          "|".join(r.nas.literals), r.kept, len(r.nas.definitions),
                          r.defs_kept, len(r.nas.examples), r.examples_kept, r.nas.stamp])


def main() -> None:
    """Compare the annotation wordnet with wncze 2.2 and report."""
    nas = read_nas()
    cs = load_wncze()
    cili = pwn15_ili()
    rows = {sid: classify(syn, cili, cs) for sid, syn in nas.items()}
    index = tag_index(nas)
    for tok in read_tags():
        if tag_key(tok.tag) in index:
            rows[index[tag_key(tok.tag)]].tokens += 1
    report(rows, cs)
    write_tsv(rows, OUT)
    FACTS.write_text(json.dumps(facts(rows, cs), indent=1) + "\n")
    print(f"\nwrote {OUT.relative_to(HERE)} and {FACTS.relative_to(HERE)}")


if __name__ == "__main__":
    main()

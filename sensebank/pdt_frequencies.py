#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests"]
# ///
"""Sense frequencies for the Czech WordNet 2.2 from the PDT annotation.

Every word the PDT annotators tagged with a synset is a count for a sense:
the PDT lemma in the wncze synset that has the tag's ILI. This script makes
those counts and says what happened to every word it could not count.

  tag -> annotation synset -> ILI (CILI map from WordNet 1.5)
      -> wncze 2.2 synset -> the sense whose lemma is the PDT lemma

The PDT lemma comes from PDT 3.0 (the annotation is stand-off). A reflexive
verb is lemmatised without se/si in PDT, and a negated word without ne-, so
those forms are tried too. Only CILI links of confidence 1 are used: the
lower ones are often wrong (dobrý 'good' maps to výborný 'excellent').

Run:  uv run pdt_frequencies.py
Writes, under data/:
  pdt_counts.tsv          wncze synset, lemma, PDT count, NTU-MC count
  pdt_set_count.jsonl     the counts as czech-wn change records (set_count)
  pdt_missing_words.tsv   tagged words the wncze synset lacks: add_sense candidates
  pdt_new_synsets.tsv    tags on synsets with no Princeton id: new-synset candidates
  pdt_exceptions.tsv      words tagged with an exception, by type and lemma
It downloads PDT 3.0 (128 MB) and the annotation from LINDAT on first use.
"""
import csv
import datetime
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import wn
from pdt_sources import (
    DATA,
    EXCEPTIONS,
    HERE,
    UNTAGGED,
    NasSynset,
    Token,
    base_lemma,
    ili_of,
    pwn15_ili,
    read_nas,
    read_tokens,
    tag_index,
    tag_key,
)
from pdt_wordnet_vs_wncze import CES, Wncze, load_wncze

MIN_CONFIDENCE = 1.0
FACTS = HERE / "report" / "facts-freq.json"
FATES = {"counted": "counted", "no agreed tag": "untagged", "exception": "exception",
         "word not in the wncze synset": "notinsynset",
         "new synset (no Princeton id)": "newsynset",
         "CILI link below confidence 1": "lowconf", "concept not in wncze": "absent",
         "no ILI for the 1.5 offset": "noili", "tag names no synset": "badtag",
         "document not in PDT 3.0": "nodoc"}
CORPUS = "PDT"
SOURCE = ("Lexico-Semantic Annotation of PDT using Czech WordNet "
          "(hdl:11858/00-097C-0000-0001-487A-4), lemmas from PDT 3.0 "
          "(JPC3 sensebank/pdt_frequencies.py)")
REASON = "how often the sense is tagged in the corpus"
USER = "fcbond"


def candidates(tok: Token) -> list[str]:
    """The lemmas a tagged word may have in the wordnet.

    Args:
        tok: an annotated word with its PDT lemma and tag

    Returns:
        The bare lemma, its reflexive forms and, if negated, its ne- form
    """
    base = base_lemma(tok.lemma)
    out = [base, f"{base} se", f"{base} si"]
    if len(tok.mtag) > 10 and tok.mtag[10] == "N":
        out.append("ne" + base)
    return out


@dataclass
class Bridge:
    """Everything needed to decide what becomes of a tagged word."""

    nas: dict[str, NasSynset]
    index: dict[str, str]
    cili: dict[str, tuple[str, float]]
    cs: Wncze
    words: dict[str, dict[str, wn.Sense]]


@dataclass
class Fate:
    """What became of one annotated word."""

    label: str
    synset: NasSynset | None = None
    ili: str = ""
    sense: wn.Sense | None = None


def load_bridge() -> Bridge:
    """Load the annotation wordnet, the CILI map and wncze 2.2.

    Returns:
        The bridge from a tag to a wncze sense
    """
    nas = read_nas()
    cs = load_wncze()
    words = {ili: {s.word().lemma(): s for s in ss.senses()} for ili, ss in cs.by_ili.items()}
    return Bridge(nas, tag_index(nas), pwn15_ili(), cs, words)


def fate(tok: Token, b: Bridge) -> Fate:
    """Decide what becomes of one annotated word.

    Args:
        tok: the word, with its PDT lemma
        b: the bridge

    Returns:
        Its fate: a label from FATES, with the annotation synset, the ILI and
        the wncze sense as far as the word got
    """
    if tok.tag == UNTAGGED:
        return Fate("no agreed tag")
    if not tok.lemma:
        return Fate("document not in PDT 3.0")
    if tok.tag in EXCEPTIONS:
        return Fate("exception")
    syn = b.nas.get(b.index.get(tag_key(tok.tag), ""))
    if syn is None:
        return Fate("tag names no synset")
    if syn.pwn15 is None:
        return Fate("new synset (no Princeton id)", syn)
    hit = ili_of(syn, b.cili)
    if hit is None:
        return Fate("no ILI for the 1.5 offset", syn)
    if hit[1] < MIN_CONFIDENCE:
        return Fate("CILI link below confidence 1", syn, hit[0])
    senses = b.words.get(hit[0])
    if senses is None:
        return Fate("concept not in wncze", syn, hit[0])
    lemma = next((c for c in candidates(tok) if c in senses), None)
    if lemma is None:
        return Fate("word not in the wncze synset", syn, hit[0])
    return Fate("counted", syn, hit[0], senses[lemma])


def write_tsv(path: Path, header: list[str], rows: list[list]) -> None:
    """Write a tab-separated file with a header.

    Args:
        path: where to write
        header: the column names
        rows: the rows
    """
    with path.open("w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh, delimiter="\t", lineterminator="\n")
        out.writerow(header)
        out.writerows(rows)


def main() -> None:
    """Count the senses, write the files and report what was left out."""
    b = load_bridge()
    nas, cs = b.nas, b.cs
    lexicon = wn.Wordnet(lexicon=CES)

    fates: Counter[str] = Counter()
    negated: Counter[str] = Counter()
    by_tag: Counter[str] = Counter()
    found: Counter[tuple[str, str]] = Counter()
    missing: Counter[tuple[str, str]] = Counter()
    new: Counter[tuple[str, str]] = Counter()
    exceptions: Counter[tuple[str, str]] = Counter()
    for tok in read_tokens():
        fates["all annotated words"] += 1
        fates["tagged with a synset"] += tok.tag not in EXCEPTIONS and tok.tag != UNTAGGED
        kind = tok.tag if tok.tag in EXCEPTIONS or tok.tag == UNTAGGED else "synset"
        by_tag[kind] += bool(tok.mtag)
        negated[kind] += tok.mtag[10:11] == "N"
        f = fate(tok, b)
        fates[f.label] += 1
        if f.label == "exception":
            exceptions[(tok.tag, base_lemma(tok.lemma))] += 1
        elif f.label == "new synset (no Princeton id)":
            new[(f.synset.id, base_lemma(tok.lemma))] += 1
        elif f.label == "word not in the wncze synset":
            missing[(cs.by_ili[f.ili].id, base_lemma(tok.lemma))] += 1
        elif f.label == "counted":
            found[(f.sense.synset().id, f.sense.word().lemma())] += 1

    total, synset_tags = fates["all annotated words"], fates["tagged with a synset"]
    report(fates, found)
    ntumc = {(s.synset().id, s.word().lemma()): sum(s.counts()) for s in lexicon.senses()
             if s.counts()}
    write_tsv(DATA / "pdt_counts.tsv", ["synset", "lemma", "pdt", "ntumc"],
              [[sid, lem, n, ntumc.get((sid, lem), "")] for (sid, lem), n in found.most_common()])
    write_records(found, DATA / "pdt_set_count.jsonl")
    write_tsv(DATA / "pdt_missing_words.tsv", ["synset", "pdt_lemma", "tagged", "synset_words"],
              [[sid, lem, n, "|".join(w.lemma() for w in lexicon.synset(sid).words())]
               for (sid, lem), n in missing.most_common()])
    write_tsv(DATA / "pdt_new_synsets.tsv", ["pdt_synset", "lemma", "tagged", "words", "definition"],
              [[sid, lem, n, "|".join(nas[sid].literals), " / ".join(nas[sid].definitions)]
               for (sid, lem), n in new.most_common()])
    write_tsv(DATA / "pdt_exceptions.tsv", ["code", "exception", "lemma", "tagged"],
              [[code, EXCEPTIONS[code], lem, n] for (code, lem), n in exceptions.most_common()])
    both = sum(1 for key in found if key in ntumc)
    print(f"\nsenses with a PDT count: {len(found)}; with an NTU-MC count already: {len(ntumc)}; "
          f"both: {both}")
    print(f"exceptions by type: { {EXCEPTIONS[c]: n for c, n in sum_by_code(exceptions).items()} }")
    FACTS.write_text(json.dumps({
        "words": total, "synsettags": synset_tags,
        "fate": {slug: fates[what] for what, slug in FATES.items()},
        "counted": {"share": round(100 * fates["counted"] / synset_tags, 1)},
        "senses": {"pdt": len(found), "ntumc": len(ntumc), "both": both},
        "exc": dict(sum_by_code(exceptions)),
        "missing": {"pairs": len(missing), "words": sum(missing.values())},
        "new": {"pairs": len(new), "words": sum(new.values())},
        "negated": {("untagged" if k == UNTAGGED else k): round(100 * negated[k] / n, 1)
                    for k, n in by_tag.items() if n},
    }, indent=1) + "\n")
    print(f"wrote {', '.join(f.name for f in sorted(DATA.glob('pdt_*')))} in "
          f"{DATA.relative_to(HERE)}/")


def sum_by_code(exceptions: Counter[tuple[str, str]]) -> Counter[str]:
    """Total the exception counts by code.

    Args:
        exceptions: (code, lemma) -> words

    Returns:
        code -> words, most frequent first
    """
    out: Counter[str] = Counter()
    for (code, _), n in exceptions.items():
        out[code] += n
    return Counter(dict(out.most_common()))


def report(fate: Counter[str], found: Counter[tuple[str, str]]) -> None:
    """Print what happened to the annotated words, and the commonest senses.

    Args:
        fate: words by what became of them, with the totals
        found: (synset, lemma) -> words counted
    """
    total, synset_tags = fate["all annotated words"], fate["tagged with a synset"]
    print(f"{'annotated words':34} {total:7}")
    for what, n in fate.most_common():
        if what in FATES:
            print(f"  {what:32} {n:7} {n / total:6.1%}")
    print(f"counted: {fate['counted'] / synset_tags:.1%} of the {synset_tags} words "
          "tagged with a synset")
    print("\ncommonest senses:")
    for (sid, lemma), n in found.most_common(12):
        print(f"  {n:5}  {lemma:14} {sid}")


def write_records(found: Counter[tuple[str, str]], path: Path) -> None:
    """Write the counts as czech-wn set_count change records.

    The ids are provisional; the maintainer numbers them into the log.

    Args:
        found: (synset, lemma) -> words counted
        path: where to write the JSON lines
    """
    date = datetime.date.today().isoformat()
    with path.open("w", encoding="utf-8") as fh:
        for i, ((sid, lemma), n) in enumerate(sorted(found.items()), 1):
            fh.write(json.dumps({
                "id": f"wncze-2.2-pdt-{i}", "action": "set_count", "lexicon": "wncze",
                "synset": sid, "lemma": lemma, "new": str(n), "corpus": CORPUS,
                "user": USER, "date": date, "source": SOURCE, "reason": REASON,
                "base": "wncze-2.2"}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

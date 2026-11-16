#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests", "openpyxl"]
# ///
"""Validation sheets for the PDT senses the Czech WordNet 2.2 lacks.

A sense here is a lemma with the synset the PDT annotators tagged it with.
This script takes the senses that are not in wncze 2.2, for four reasons:

  - the word is missing from the wncze synset for the concept: easy to fix
    by adding the word, so only a sample of QUOTA is judged, to measure how
    often adding it would be right;
  - the concept is missing from wncze;
  - the synset is one ÚFAL or Brno added with no Princeton id;
  - the 1.5 offset has no ILI.

The last three are judged in full. Each sense is judged by two of the seven
students, who decide whether it is a sense to add.

Run:  uv run new_sense_sheets.py
Writes, under data/sheets/ (git-ignored: the sentences are PDT's, CC BY-NC-SA):
  sheet-A.xlsx ... sheet-G.xlsx   one workbook per student
  items.tsv                       the key: each item, its sense, its two judges

Randomisation
-------------
Everything random is drawn from random.Random seeded with SEED and a
purpose ("assign", "order", ...), so each purpose has its own stream: the
sheets are the same on every run, and changing how examples are sampled
does not change who judges what. Change SEED only before the sheets go out;
after that, the key must stay as it is.

0. Which senses.  The QUOTA senses with a missing word are a uniform random
   sample of all of them, so the share judged right estimates the share
   right among all of them: the precision of adding them in bulk.
1. Who judges what.  Seven students make 21 pairs. Each item goes to one
   pair, so every pair shares about ten items and we get Cohen's kappa for
   every pair, not only overall, and can spot a student who reads the task
   differently. The items are dealt in frequency order, in rounds of 21,
   to the pairs in a fresh random order each round. That stratifies by
   frequency: every pair gets a mix of frequent and rare senses, so no
   pair's kappa is computed only on the easy, frequent ones. Each student
   is in six pairs, so has about 6 x 10 items.
2. Item numbers.  Items are numbered in a random order, so the number says
   nothing about frequency or about the reason the sense is missing.
3. Order on a sheet.  Each sheet is shuffled separately, so the two judges of
   an item see it at different points: tiredness and learning over the
   sheet do not hit both judgements of the same item.
4. Example sentences.  Up to EXAMPLES sentences per item, sampled at random
   from all the sentences tagged with the sense, so the frequent wording
   does not crowd out the rest. Both judges see the same sentences.

The sheets are blind: they show neither how often a sense is tagged nor why
it is missing (both are in items.tsv), and students should not compare
answers until both have finished.
"""
import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations

import wn
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation
from pdt_frequencies import Bridge, fate, load_bridge
from pdt_sources import DATA, HERE, base_lemma, read_tokens

SEED = 20261116
QUOTA = {"word not in the wncze synset": 60}
POPULATION: dict[str, int] = {}   # senses in each category, filled by collect()
EXAMPLES = 3
STUDENTS = list("ABCDEFG")
OUT = DATA / "sheets"
FACTS = HERE / "report" / "facts-sheets.json"
SLUGS = {"word not in the wncze synset": "word", "concept not in wncze": "concept",
         "new synset (no Princeton id)": "newsyn", "no ILI for the 1.5 offset": "noili"}
MISSING = {"word not in the wncze synset", "concept not in wncze",
           "new synset (no Princeton id)", "no ILI for the 1.5 offset"}
CHOICES = ["add", "already in wncze", "wrong tag", "unsure"]
INSTRUCTIONS = [
    ("Each row is a Czech word in a sense that annotators of the Prague Dependency "
     "Treebank used, but that the Czech WordNet 2.2 does not have."),
    ("Read the sentences (the word is in «»), the PDT sense, and the senses the "
     "Czech WordNet already has for the word. Then choose:"),
    "  add: a real sense of the word that the Czech WordNet is missing.",
    "  already in wncze: the Czech WordNet has this sense; give its number.",
    "  wrong tag: the sentences do not use the word in the PDT sense.",
    "  unsure: you cannot decide; say why in the comment.",
    "Work alone, and do not compare answers until everyone has finished.",
]


@dataclass
class Item:
    """One sense to judge, with the evidence for it."""

    pdt_synset: str
    lemma: str
    reason: str
    ili: str = ""
    tagged: int = 0
    sentences: list[str] = field(default_factory=list)
    number: str = ""
    judges: tuple[str, str] = ("", "")


def rng(purpose: str) -> random.Random:
    """A random stream for one purpose, fixed by SEED.

    Args:
        purpose: what the stream is for, e.g. 'assign'

    Returns:
        A seeded generator, the same on every run
    """
    return random.Random(f"{SEED}-{purpose}")


def collect(b: Bridge) -> list[Item]:
    """Find the missing senses, sampling the categories in QUOTA (point 0).

    Args:
        b: the bridge from a tag to wncze

    Returns:
        The items, most tagged first, each with all its sentences
    """
    items: dict[tuple[str, str], Item] = {}
    for tok in read_tokens():
        f = fate(tok, b)
        if f.label not in MISSING:
            continue
        key = (f.synset.id, base_lemma(tok.lemma))
        item = items.setdefault(key, Item(f.synset.id, key[1], f.label, f.ili))
        item.sentences.append(tok.sentence)
    keep = []
    r = rng("sample")
    for reason in sorted(MISSING):
        mine = sorted((i for i in items.values() if i.reason == reason),
                      key=lambda i: (i.pdt_synset, i.lemma))
        POPULATION[reason] = len(mine)
        quota = QUOTA.get(reason, len(mine))
        keep += r.sample(mine, min(quota, len(mine)))
    for item in keep:
        item.tagged = len(item.sentences)
    return sorted(keep, key=lambda i: (-i.tagged, i.pdt_synset, i.lemma))


def assign(items: list[Item]) -> None:
    """Give each item a pair of judges, stratified by frequency (point 1).

    Args:
        items: the items, most tagged first; changed in place
    """
    pairs = list(combinations(STUDENTS, 2))
    r = rng("assign")
    for start in range(0, len(items), len(pairs)):
        order = pairs[:]
        r.shuffle(order)
        for item, pair in zip(items[start:start + len(pairs)], order):
            item.judges = pair


def number(items: list[Item]) -> None:
    """Number the items in a random order (point 2).

    Args:
        items: the items; changed in place
    """
    order = items[:]
    rng("number").shuffle(order)
    for n, item in enumerate(order, 1):
        item.number = f"S{n:03d}"


def sample_sentences(items: list[Item]) -> None:
    """Keep up to EXAMPLES random sentences per item (point 4).

    Args:
        items: the items; changed in place
    """
    r = rng("examples")
    for item in items:
        item.sentences = r.sample(sorted(set(item.sentences)),
                                  min(EXAMPLES, len(set(item.sentences))))


def english(en: wn.Wordnet, ili: str) -> str:
    """The English lemmas and gloss of a concept.

    Args:
        en: the English wordnet
        ili: the concept's ILI, or ''

    Returns:
        'lemma, lemma: gloss', or '' if there is none
    """
    for ss in en.synsets(ili=ili) if ili else []:
        defs = ss.definitions()
        return f"{', '.join(ss.lemmas())}: {defs[0] if defs else ''}"
    return ""


def wncze_senses(b: Bridge, en: wn.Wordnet, lemma: str) -> list[str]:
    """The senses wncze 2.2 already has for a lemma, numbered.

    Args:
        b: the bridge
        en: the English wordnet
        lemma: the Czech lemma

    Returns:
        One line per synset holding the lemma or its reflexive forms
    """
    ids = sorted({sid for form in (lemma, f"{lemma} se", f"{lemma} si")
                  for p in "nvar" for sid in b.cs.by_lemma.get((form, p), ())})
    lines = []
    for n, sid in enumerate(ids, 1):
        ss = wn.synset(sid)
        lines.append(f"{n}. {', '.join(ss.lemmas())} | {english(en, ss.ili or '')}")
    return lines


def pdt_sense(b: Bridge, en: wn.Wordnet, item: Item) -> str:
    """Describe the PDT sense: its words, definition, examples, English.

    Args:
        b: the bridge
        en: the English wordnet
        item: the item

    Returns:
        A few lines of text
    """
    syn = b.nas[item.pdt_synset]
    lines = [", ".join(syn.literals)]
    lines += [f"definition: {d}" for d in syn.definitions]
    lines += [f"example: {e}" for e in syn.examples[:2]]
    if item.ili:
        lines.append(f"English: {english(en, item.ili)}")
    return "\n".join(lines)


def write_sheet(student: str, rows: list[list[str]]) -> None:
    """Write one student's workbook, with an instructions sheet.

    Args:
        student: the student's letter
        rows: the rows to judge, in the order to show them
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "judge"
    header = ["item", "word", "sentences", "PDT sense", "senses in the Czech WordNet",
              "decision", "number (if already in wncze)", "comment"]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row + ["", "", ""])
    for col, width in zip("ABCDEFGH", [7, 14, 60, 45, 55, 18, 12, 30]):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    choice = DataValidation(type="list", formula1=f'"{",".join(CHOICES)}"', allow_blank=True)
    ws.add_data_validation(choice)
    choice.add(f"F2:F{len(rows) + 1}")
    ws.freeze_panes = "C2"
    info = wb.create_sheet("instructions", 0)
    info.column_dimensions["A"].width = 100
    for line in [f"Sheet {student}: {len(rows)} items", "", *INSTRUCTIONS]:
        info.append([line])
    wb.save(OUT / f"sheet-{student}.xlsx")


def main() -> None:
    """Build the items, assign them, and write the sheets and the key."""
    b = load_bridge()
    en = wn.Wordnet(lexicon="omw-en:2.0")
    items = collect(b)
    assign(items)
    number(items)
    sample_sentences(items)
    OUT.mkdir(parents=True, exist_ok=True)

    sheets: dict[str, list[list[str]]] = defaultdict(list)
    for item in items:
        row = [item.number, item.lemma, "\n\n".join(item.sentences),
               pdt_sense(b, en, item), "\n".join(wncze_senses(b, en, item.lemma)) or "(none)"]
        for student in item.judges:
            sheets[student].append(row)
    for student in STUDENTS:
        rows = sheets[student]
        rng(f"order-{student}").shuffle(rows)
        write_sheet(student, rows)

    with (OUT / "items.tsv").open("w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh, delimiter="\t", lineterminator="\n")
        out.writerow(["item", "lemma", "pdt_synset", "reason", "ili", "tagged",
                      "judge1", "judge2"])
        for item in sorted(items, key=lambda i: i.number):
            out.writerow([item.number, item.lemma, item.pdt_synset, item.reason, item.ili,
                          item.tagged, *item.judges])
    per = {s: len(sheets[s]) for s in STUDENTS}
    print(f"{len(items)} senses: {dict(Counter(i.reason for i in items))}")
    print(f"items per sheet {per}")
    word = [i.tagged for i in items if i.reason == "word not in the wncze synset"]
    FACTS.write_text(json.dumps({
        "items": len(items), "students": len(STUDENTS),
        "pairs": len(list(combinations(STUDENTS, 2))),
        "perstudent": min(per.values()), "perpair": len(items) // len(list(combinations(STUDENTS, 2))),
        "tagged": sum(i.tagged for i in items), "population": sum(POPULATION.values()),
        **{slug: {"judged": sum(1 for i in items if i.reason == reason),
                  "of": POPULATION[reason]} for reason, slug in SLUGS.items()},
        "wordsample": {"once": sum(1 for n in word if n == 1),
                       "ten": sum(1 for n in word if n >= 10), "tagged": sum(word)},
    }, indent=1) + "\n")
    print(f"wrote {len(STUDENTS)} sheets and items.tsv in {OUT}, and {FACTS.name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["wn>=1.1", "requests", "openpyxl", "numpy", "statsmodels"]
# ///
"""Score the students' validation sheets against the key.

new_sense_sheets.py dealt each missing sense to two students, and wrote the
key (data/sheets/items.tsv) saying who has which item. This script reads the
returned workbooks, pairs the two answers for every item, and reports:

  - for each kind of missing sense, how many items the two judges agree
    are 'add', 'already in wncze', 'wrong tag' or 'unsure', and how many
    are split;
  - agreement as Fleiss' kappa over all items, and by kind (two judges
    per item, but not the same two, so Cohen's kappa does not apply);
  - Cohen's kappa for each pair of students, who share 10 items: too few
    for a firm figure, but enough to spot a pair that reads the task
    differently;
  - the split items, to resolve by discussion.

Agreement is on the decision; two 'already in wncze' answers that name
different senses are agreed, and listed separately.

Put the returned workbooks in data/returned/ (any name starting sheet-;
the student is read from the sheet itself), then:

Run:  uv run score_sheets.py
Writes data/scores/ (judgements.tsv, split.tsv, pairs.tsv) and
report/facts-scores.json. Sheets not yet returned are reported and left
out; items with only one answer are 'pending'.
"""
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import numpy as np
from new_sense_sheets import CHOICES, SLUGS, STUDENTS
from openpyxl import load_workbook
from pdt_sources import DATA, HERE, write_tsv
from statsmodels.stats.inter_rater import aggregate_raters, cohens_kappa, fleiss_kappa

KEY = DATA / "sheets" / "items.tsv"
RETURNED = DATA / "returned"
OUT = DATA / "scores"
FACTS = HERE / "report" / "facts-scores.json"
SPLIT = "split"
PENDING = "pending"


@dataclass
class Answer:
    """One student's answer for one item."""

    decision: str
    number: str = ""
    comment: str = ""


@dataclass
class Item:
    """One sense from the key, with the answers returned so far."""

    item: str
    lemma: str
    reason: str
    judges: tuple[str, str]
    answers: dict[str, Answer] = field(default_factory=dict)

    @property
    def outcome(self) -> str:
        """The agreed decision, 'split', or 'pending' if an answer is missing."""
        if len(self.answers) < 2:
            return PENDING
        first, second = (self.answers[j].decision for j in self.judges)
        return first if first == second else SPLIT


def read_key(path: Path = KEY) -> dict[str, Item]:
    """Read the key that new_sense_sheets.py wrote.

    Args:
        path: items.tsv

    Returns:
        item number -> Item, with no answers yet
    """
    with path.open(encoding="utf-8") as fh:
        return {r["item"]: Item(r["item"], r["lemma"], r["reason"], (r["judge1"], r["judge2"]))
                for r in csv.DictReader(fh, delimiter="\t")}


def clean(value: object) -> str:
    """A cell as tidy text: None becomes '', spaces are trimmed, case is lowered.

    Args:
        value: the cell's value

    Returns:
        the text
    """
    return "" if value is None else " ".join(str(value).split()).lower()


def read_sheet(path: Path) -> tuple[str, dict[str, Answer]]:
    """Read one returned workbook.

    The student's letter is taken from the instructions sheet ('Sheet C: 60
    items'), so it does not matter what the file was renamed to.

    Args:
        path: the workbook

    Returns:
        the student's letter, and item number -> Answer for the answered items

    Raises:
        ValueError: if the instructions sheet does not name a student
    """
    wb = load_workbook(path, read_only=True)
    found = re.match(r"Sheet ([A-Z]):", str(wb["instructions"]["A1"].value))
    if not found:
        raise ValueError(f"{path.name}: no 'Sheet X:' line in the instructions")
    answers = {}
    for row in wb["judge"].iter_rows(min_row=2, values_only=True):
        item, decision, number, comment = row[0], clean(row[5]), clean(row[6]), row[7]
        if item and decision:
            answers[str(item)] = Answer(decision, number, "" if comment is None else str(comment))
    return found[1], answers


def collect(items: dict[str, Item], folder: Path = RETURNED) -> list[str]:
    """Add the answers in every returned workbook to the items.

    Args:
        items: the key; changed in place
        folder: where the returned workbooks are

    Returns:
        problems to fix by hand: unknown decisions, items on the wrong sheet,
        unanswered items, sheets not returned
    """
    problems, returned = [], set()
    for path in sorted(folder.glob("sheet-*.xlsx")):
        student, answers = read_sheet(path)
        returned.add(student)
        mine = {i for i, item in items.items() if student in item.judges}
        for number, answer in answers.items():
            if number not in mine:
                problems.append(f"{student} {number}: not on this student's sheet")
            elif answer.decision not in CHOICES:
                problems.append(f"{student} {number}: unknown decision '{answer.decision}'")
            else:
                items[number].answers[student] = answer
        problems += [f"{student} {n}: no answer" for n in sorted(mine - set(answers))]
    problems += [f"{s}: sheet not returned" for s in STUDENTS if s not in returned]
    return problems


def fleiss(items: list[Item]) -> float | None:
    """Fleiss' kappa over items with two answers.

    Args:
        items: the items to include

    Returns:
        kappa, or None if fewer than two items have both answers
    """
    rated = [[CHOICES.index(item.answers[j].decision) for j in item.judges]
             for item in items if item.outcome != PENDING]
    if len(rated) < 2:
        return None
    table, _ = aggregate_raters(np.array(rated), n_cat=len(CHOICES))
    return round(float(fleiss_kappa(table)), 2)


def cohen(items: list[Item], pair: tuple[str, str]) -> float | None:
    """Cohen's kappa for the items one pair of students share.

    Args:
        items: all items
        pair: the two students, e.g. ('A', 'B')

    Returns:
        kappa, or None if it is undefined (no items, or both students gave
        a single answer throughout)
    """
    table = np.zeros((len(CHOICES), len(CHOICES)))
    for item in items:
        if set(item.judges) == set(pair) and item.outcome != PENDING:
            a, b = (CHOICES.index(item.answers[s].decision) for s in pair)
            table[a, b] += 1
    n = table.sum()
    if n == 0:
        return None
    chance = (table.sum(axis=1) @ table.sum(axis=0)) / n**2
    if chance == 1:
        return None
    return round(float(cohens_kappa(table).kappa), 2)


def summarise(items: list[Item]) -> dict:
    """The counts and kappa for one group of items.

    Args:
        items: the group

    Returns:
        items judged twice, each agreed decision, split, pending and kappa
    """
    outcomes = Counter(item.outcome for item in items)
    out = {"judged": sum(n for o, n in outcomes.items() if o != PENDING),
           "split": outcomes[SPLIT], "pending": outcomes[PENDING]}
    out |= {choice.split()[0]: outcomes[choice] for choice in CHOICES}
    kappa = fleiss(items)
    if kappa is not None:
        out["kappa"] = kappa
    return out


def main() -> None:
    """Score the returned sheets and write the tables and facts."""
    items = read_key()
    problems = collect(items, RETURNED)
    every = list(items.values())
    facts = {"all": summarise(every),
             **{slug: summarise([i for i in every if i.reason == reason])
                for reason, slug in SLUGS.items()}}
    pairs = {f"{a}{b}": cohen(every, (a, b)) for a, b in combinations(STUDENTS, 2)}
    facts["pairs"] = {pair: k for pair, k in pairs.items() if k is not None}
    word = facts["word"]
    if word["judged"]:
        facts["word"]["addshare"] = round(100 * word["add"] / word["judged"], 1)
    FACTS.write_text(json.dumps(facts, indent=1) + "\n", encoding="utf-8")

    OUT.mkdir(exist_ok=True)
    header = ["item", "lemma", "reason", "outcome"]
    for n in (1, 2):
        header += [f"judge{n}", f"decision{n}", f"number{n}", f"comment{n}"]
    rows = []
    for item in every:
        row = [item.item, item.lemma, item.reason, item.outcome]
        for judge in item.judges:
            a = item.answers.get(judge, Answer(""))
            row += [judge, a.decision, a.number, a.comment]
        rows.append(row)
    write_tsv(OUT / "judgements.tsv", header, rows)
    write_tsv(OUT / "split.tsv", header, [r for r in rows if r[3] == SPLIT])
    write_tsv(OUT / "pairs.tsv", ["pair", "kappa"],
              [[pair, "" if k is None else k] for pair, k in pairs.items()])

    different = [i.item for i in every if i.outcome == "already in wncze"
                 and len({a.number for a in i.answers.values()}) > 1]
    print(json.dumps(facts, indent=1))
    if different:
        print(f"agreed 'already in wncze' but on different senses: {', '.join(different)}")
    print(f"{len(problems)} problems" + "".join(f"\n  {p}" for p in problems))
    print(f"wrote {OUT.relative_to(HERE)}/ and {FACTS.relative_to(HERE)}")


if __name__ == "__main__":
    main()

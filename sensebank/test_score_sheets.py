"""Tests of score_sheets.py on small made-up workbooks (no downloads)."""
from openpyxl import Workbook
from score_sheets import Answer, Item, cohen, collect, fleiss, read_sheet


def make_sheet(path, student, answers):
    """Write a workbook laid out like new_sense_sheets.py's.

    Args:
        path: where to write it
        student: the letter on the instructions sheet
        answers: (item, decision, number) rows
    """
    wb = Workbook()
    wb.active.title = "judge"
    wb["judge"].append(["item", "word", "sentences", "PDT sense", "senses",
                        "decision", "number", "comment"])
    for item, decision, number in answers:
        wb["judge"].append([item, "w", "s", "p", "senses", decision, number, None])
    wb.create_sheet("instructions", 0)["A1"] = f"Sheet {student}: {len(answers)} items"
    wb.save(path)


def items_for(pairs):
    """A key with one item per (judge, judge) pair given.

    Args:
        pairs: e.g. [('A', 'B'), ('A', 'B')]

    Returns:
        item number -> Item
    """
    return {f"S{n:03d}": Item(f"S{n:03d}", "slovo", "concept not in wncze", pair)
            for n, pair in enumerate(pairs, 1)}


def test_read_sheet_takes_student_from_sheet_and_tidies_answers(tmp_path):
    # Arrange: the file was renamed, and one answer has stray capitals and spaces
    path = tmp_path / "sheet-C-novak.xlsx"
    make_sheet(path, "C", [("S001", " Add ", None), ("S002", None, None)])
    # Act
    student, answers = read_sheet(path)
    # Assert: the unanswered row is left out
    assert student == "C"
    assert answers == {"S001": Answer("add")}


def test_collect_reports_problems(tmp_path):
    # Arrange: A answers both items, one with a made-up decision; B is missing
    items = items_for([("A", "B"), ("A", "B")])
    make_sheet(tmp_path / "sheet-A.xlsx", "A", [("S001", "add", None), ("S002", "maybe", None)])
    # Act
    problems = collect(items, tmp_path)
    # Assert
    assert "A S002: unknown decision 'maybe'" in problems
    assert "B: sheet not returned" in problems
    assert items["S001"].outcome == "pending"


def test_outcome_and_kappa():
    # Arrange: A and B agree on three items and split on one
    items = items_for([("A", "B")] * 4)
    for (number, item), (a, b) in zip(items.items(), [("add", "add"),
                                                      ("wrong tag", "wrong tag"),
                                                      ("add", "add"),
                                                      ("add", "unsure")]):
        item.answers = {"A": Answer(a), "B": Answer(b)}
    # Act
    outcomes = [item.outcome for item in items.values()]
    pair = cohen(list(items.values()), ("A", "B"))
    overall = fleiss(list(items.values()))
    # Assert
    assert outcomes == ["add", "wrong tag", "add", "split"]
    assert 0 < pair < 1
    assert 0 < overall < 1


def test_cohen_is_undefined_without_variety():
    # Arrange: both students say 'add' to everything
    items = items_for([("A", "B")] * 3)
    for item in items.values():
        item.answers = {"A": Answer("add"), "B": Answer("add")}
    # Act / Assert: chance agreement is 1, so kappa is undefined
    assert cohen(list(items.values()), ("A", "B")) is None
    assert cohen(list(items.values()), ("C", "D")) is None

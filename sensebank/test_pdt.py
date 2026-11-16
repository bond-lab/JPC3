"""Tests of the pure helpers behind the PDT scripts (no downloads)."""
from pdt_frequencies import candidates
from pdt_sources import NasSynset, Token, base_lemma, ili_of, literal, tag_index
from pdt_wordnet_vs_wncze import carried, norm, pos


def test_base_lemma_strips_technical_suffixes():
    # Arrange
    lemmas = ["stát-2_^(státní_útvar)", "vycházet_:T", "Praha_;G", "rok", "e-mail"]
    # Act
    bases = [base_lemma(x) for x in lemmas]
    # Assert
    assert bases == ["stát", "vycházet", "Praha", "rok", "e-mail"]


def test_literal_drops_homonym_mark():
    assert literal(" vypadat ^2 ") == "vypadat"
    assert literal("horský potok") == "horský potok"


def test_pwn15_offset_and_ufal_ids():
    # Arrange
    adverb = NasSynset("00004331-b", "b", ["jen"])
    ufal = NasSynset("NAS-430683854", "v", ["mít"])
    # Act / Assert
    assert adverb.pwn15 == "00004331-r"
    assert ufal.pwn15 is None


def test_tag_index_drops_zeros_and_pos():
    # Arrange
    nas = {"01307561-v": NasSynset("01307561-v", "v", ["mít"]),
           "NAS-1": NasSynset("NAS-1", "v", ["moci"])}
    # Act
    index = tag_index(nas)
    # Assert
    assert index == {"1307561": "01307561-v", "NAS-1": "NAS-1"}


def test_ili_of_tries_satellite_for_adjectives():
    # Arrange
    cili = {"00002403-s": ("i1", 1.0)}
    syn = NasSynset("00002403-a", "a", ["schopný"])
    # Act / Assert
    assert ili_of(syn, cili) == ("i1", 1.0)


def test_candidates_cover_reflexive_and_negated_forms():
    # Arrange: tag position 11 is negation
    tok = Token("d", "m1", "123", "závislý", "AAIS1----1N----")
    # Act
    forms = candidates(tok)
    # Assert
    assert forms == ["závislý", "závislý se", "závislý si", "nezávislý"]


def test_norm_and_carried_ignore_lemma_prefix_and_case():
    # Arrange
    pdt = ["cena: Trofej."]
    wncze = ["trofej", "something else"]
    # Act / Assert
    assert norm(pdt[0]) == "trofej"
    assert carried(pdt, wncze) == 1
    assert carried(["nic"], wncze) == 0


def test_pos_folds_satellites_and_adverbs():
    assert [pos(p) for p in "nvasbr"] == ["n", "v", "a", "a", "r", "r"]


def test_assign_balances_pairs_and_is_reproducible():
    # Arrange
    from collections import Counter

    from new_sense_sheets import Item, assign
    items = [Item(f"s{i}", "x", "r") for i in range(201)]
    again = [Item(f"s{i}", "x", "r") for i in range(201)]
    # Act
    assign(items)
    assign(again)
    pairs = Counter(tuple(i.judges) for i in items)
    # Assert: 21 pairs, 9 or 10 items each, the same on every run
    assert len(pairs) == 21
    assert set(pairs.values()) <= {9, 10}
    assert [i.judges for i in items] == [i.judges for i in again]


def test_number_gives_unique_ids():
    # Arrange
    from new_sense_sheets import Item, number
    items = [Item(f"s{i}", "x", "r") for i in range(50)]
    # Act
    number(items)
    # Assert
    assert sorted(i.number for i in items) == [f"S{n:03d}" for n in range(1, 51)]


def test_detokenise_attaches_punctuation():
    from pdt_sources import detokenise
    assert detokenise(["Ahoj", ",", "světe", "(", "a", ")", "."]) == "Ahoj, světe (a)."

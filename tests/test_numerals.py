from fractions import Fraction

import pytest

from pe.corpus import load_corpus
from pe.numerals import (
    NumeralSystem,
    extract_numeral_notations,
    possible_readings,
    reading_distribution,
)


D = NumeralSystem.DECIMAL
S = NumeralSystem.SEXAGESIMAL
B = NumeralSystem.BISEXAGESIMAL
C = NumeralSystem.CAPACITY


def test_figure_2_sexagesimal_worked_example():
    readings = possible_readings(
        [(1, "N34"), (5, "N14"), (1, "N01"), (1, "N8B")]
    )
    assert readings == {S: Fraction(223, 2)}


def test_figure_2_capacity_worked_example():
    readings = possible_readings(
        [(7, "N14"), (2, "N01"), (3, "N39B")]
    )
    assert readings == {C: Fraction(223, 5)}


def test_paper_illustration_rejects_seven_n01_in_capacity():
    readings = possible_readings([(1, "N45"), (2, "N14"), (7, "N01")])
    assert readings == {S: Fraction(3627)}


def test_max_count_matches_papers_invalid_example():
    assert set(possible_readings([(10, "N01")])) == {D, S, B}
    assert possible_readings([(11, "N01")]) == {}


@pytest.fixture(scope="module")
def corpus_distribution():
    notations = extract_numeral_notations(load_corpus())
    return notations, reading_distribution(notations)


def test_current_snapshot_extraction_count(corpus_distribution):
    notations, _ = corpus_distribution
    # Revised paper: 8011 intact notations from its 2022-10-03 snapshot.
    assert len(notations) == 8008
    assert len(notations) - 8011 == -3


def test_damage_marker_after_run_discards_notation(corpus_distribution):
    notations, _ = corpus_distribution
    locations = {
        (notation.pnumber, notation.source_line, notation.raw)
        for notation in notations
    }
    assert not any(
        pnumber == "P008296" and source_line == 11
        for pnumber, source_line, _ in locations
    )
    assert (
        "P008094",
        11,
        "4(N39B) 1(N30C)#",
    ) in locations


def test_current_snapshot_table_1(corpus_distribution):
    _, distribution = corpus_distribution
    observed = {
        frozenset(): 49,
        frozenset({B}): 15,
        frozenset({C}): 1743,
        frozenset({D}): 78,
        frozenset({S}): 106,
        frozenset({B, D}): 21,
        frozenset({B, S}): 5,
        frozenset({C, D}): 46,
        frozenset({C, S}): 146,
        frozenset({B, C, S}): 177,
        frozenset({B, D, S}): 291,
        frozenset({B, C, D, S}): 5331,
    }
    assert distribution == observed

    published = {
        frozenset(): 27,
        frozenset({B}): 18,
        frozenset({C}): 1678,
        frozenset({D}): 96,
        frozenset({S}): 107,
        frozenset({B, D}): 22,
        frozenset({B, S}): 5,
        frozenset({C, D}): 49,
        frozenset({C, S}): 143,
        frozenset({B, C, S}): 185,
        frozenset({B, D, S}): 292,
        frozenset({B, C, D, S}): 5389,
    }
    assert sum(observed.values()) - sum(published.values()) == -3

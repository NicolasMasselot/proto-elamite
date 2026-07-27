from pathlib import Path

import pytest

from pe.constants import CORPUS_COMMIT
from pe.corpus import Damage, TokenKind, corpus_stats, load_corpus, parse_atf


@pytest.fixture(scope="module")
def tablets():
    return load_corpus()


@pytest.fixture(scope="module")
def stats(tablets):
    return corpus_stats(tablets)


def test_submodule_is_pinned():
    git_pointer = Path("data/pe-headers/.git").read_text().strip()
    git_dir = (Path("data/pe-headers") / git_pointer.removeprefix("gitdir: ")).resolve()
    assert (git_dir / "HEAD").read_text().strip() == CORPUS_COMMIT


def test_parses_pnumber_and_entries_in_order():
    tablet = parse_atf(Path("data/pe-headers/corpus/P008001.atf"))
    assert tablet.pnumber == "P008001"
    assert [entry.label for entry in tablet.entries[:3]] == ["1.", "2.", "3."]
    assert [token.value for token in tablet.entries[1].signs] == ["M319", "M032"]
    assert [token.value for token in tablet.entries[1].numeral_notation] == [
        "1(N14)",
        "7(N01)",
    ]


def test_damage_and_missing_are_distinct():
    tablet = parse_atf(Path("data/pe-headers/corpus/P008002.atf"))
    broken = tablet.entries[2].signs[0]
    missing_sign = tablet.entries[2].signs[1]
    missing_numeral = tablet.entries[2].numeral_notation[0]

    assert (broken.value, broken.damage) == ("M263~b", Damage.BROKEN)
    assert (missing_sign.kind, missing_sign.damage) == (
        TokenKind.UNREADABLE,
        Damage.MISSING,
    )
    assert (missing_numeral.kind, missing_numeral.damage) == (
        TokenKind.UNREADABLE,
        Damage.MISSING,
    )

    restored = parse_atf(Path("data/pe-headers/corpus/P008085.atf")).entries[0].signs[0]
    assert (restored.value, restored.damage, restored.restored, restored.uncertain) == (
        "M157~a",
        Damage.MISSING,
        True,
        True,
    )


def test_text_counts_and_published_delta(stats):
    # Born et al. 2019: 1399 texts after numeric/unreadable-only pruning.
    assert (stats.total_texts, stats.cleaned_texts) == (1467, 1398)
    assert stats.cleaned_texts - 1399 == -1
    assert stats.total_entries == 11026
    assert stats.total_entries - 11013 == 13


def test_token_inventory_and_published_deltas(stats):
    # Born et al. 2021: 33778 = 7508 unreadable + 11364 numeral + 14906 signs.
    assert (
        stats.total_tokens,
        stats.unreadable_or_missing,
        stats.numeral_tokens,
        stats.nonnumerical_tokens,
    ) == (33828, 7584, 11389, 14855)
    assert (
        stats.total_tokens - 33778,
        stats.unreadable_or_missing - 7508,
        stats.numeral_tokens - 11364,
        stats.nonnumerical_tokens - 14906,
    ) == (50, 76, 25, -51)


def test_hapax_and_published_delta(stats):
    # Born et al. 2019: 745 hapax among 1623 non-numerical sign types.
    assert (stats.nonnumerical_types, stats.nonnumerical_hapax) == (1630, 744)
    assert (stats.nonnumerical_types - 1623, stats.nonnumerical_hapax - 745) == (
        7,
        -1,
    )

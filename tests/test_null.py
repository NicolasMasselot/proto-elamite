from dataclasses import dataclass, replace
import random

import pytest

from pe.constants import NULL_SANITY_CHECK_SEEDS, PERMUTATION_SEED
from pe.null import (
    make_obverse_bundle_randomizer,
    make_tablet_notation_pool_randomizer,
    make_tablet_notation_stratified_randomizer,
    make_valid_system_randomizer,
    permutation_test,
    randomize_obverse_bundles_by_slot_count,
    randomize_tablet_notation_pool,
    randomize_tablet_notation_strata,
    randomize_valid_system_assignments,
)


@dataclass(frozen=True)
class ToyNotation:
    valid_systems: frozenset[str]
    assigned_system: str
    length: int = 1


def score_a_assignments(corpus: tuple[ToyNotation, ...]) -> int:
    return sum(item.assigned_system == "A" for item in corpus)


RANDOMIZE_TOY = make_valid_system_randomizer(
    valid_systems=lambda item: item.valid_systems,
    assign_system=lambda item, system: replace(item, assigned_system=system),
)


@pytest.mark.parametrize("seed", NULL_SANITY_CHECK_SEEDS)
def test_no_signal_has_large_upper_tail_p_value(seed):
    corpus = tuple(
        ToyNotation(frozenset({"A", "B"}), "A" if index < 10 else "B")
        for index in range(20)
    )
    result = permutation_test(
        corpus,
        score_a_assignments,
        RANDOMIZE_TOY,
        n_resamples=2_000,
        seed=seed,
    )

    assert result.observed == 10
    assert 9.75 < result.null_mean < 10.25
    assert 2.0 < result.null_std < 2.5
    assert result.p_value > 0.5


def test_obvious_signal_has_small_upper_tail_p_value():
    corpus = tuple(
        ToyNotation(frozenset({"A", "B"}), "A") for _ in range(20)
    )
    result = permutation_test(
        corpus,
        score_a_assignments,
        RANDOMIZE_TOY,
        n_resamples=5_000,
        seed=PERMUTATION_SEED,
    )

    assert result.observed == 20
    assert 9.75 < result.null_mean < 10.25
    assert 2.0 < result.null_std < 2.5
    assert result.p_value < 0.01


def test_p_value_uses_add_one_correction():
    result = permutation_test(
        1,
        lambda value: value,
        lambda _value, _rng: 0,
        n_resamples=9,
        seed=PERMUTATION_SEED,
    )
    assert result.p_value == 1 / 10


def test_valid_set_randomization_never_uses_an_invalid_system():
    corpus = (
        ToyNotation(frozenset({"A", "C"}), "A"),
        ToyNotation(frozenset({"B"}), "B"),
    )
    randomized = randomize_valid_system_assignments(
        corpus,
        random.Random(PERMUTATION_SEED),
        valid_systems=lambda item: item.valid_systems,
        assign_system=lambda item, system: replace(
            item, assigned_system=system
        ),
    )

    assert randomized[0].assigned_system in {"A", "C"}
    assert randomized[1] is corpus[1]


def test_permutation_test_reproduces_complete_null_distribution():
    corpus = tuple(
        ToyNotation(frozenset({"A", "B"}), "A") for _ in range(8)
    )
    first = permutation_test(
        corpus,
        score_a_assignments,
        RANDOMIZE_TOY,
        n_resamples=100,
        seed=PERMUTATION_SEED,
    )
    second = permutation_test(
        corpus,
        score_a_assignments,
        RANDOMIZE_TOY,
        n_resamples=100,
        seed=PERMUTATION_SEED,
    )
    assert first == second


def test_invalid_resample_count_and_empty_valid_set_are_rejected():
    corpus = (ToyNotation(frozenset({"A"}), "A"),)
    with pytest.raises(ValueError, match="n_resamples"):
        permutation_test(
            corpus,
            score_a_assignments,
            RANDOMIZE_TOY,
            n_resamples=0,
            seed=PERMUTATION_SEED,
        )

    invalid = (ToyNotation(frozenset(), "A"),)
    with pytest.raises(ValueError, match="no valid system"):
        randomize_valid_system_assignments(
            invalid,
            random.Random(PERMUTATION_SEED),
            valid_systems=lambda item: item.valid_systems,
            assign_system=lambda item, system: replace(
                item, assigned_system=system
            ),
        )


@dataclass(frozen=True)
class ToyTablet:
    obverse_entries: int
    reverse_entries: int
    obverse: tuple[ToyNotation, ...]
    reverse: tuple[ToyNotation, ...]

    @property
    def notation_count(self):
        return len(self.obverse) + len(self.reverse)

    @property
    def position_strata(self):
        return ("obverse",) * len(self.obverse) + ("reverse",) * len(
            self.reverse
        )

    @property
    def length_strata(self):
        return tuple(
            notation.length
            for notation in (*self.obverse, *self.reverse)
        )

    def replace_notations(self, notations):
        split = len(self.obverse)
        return replace(
            self,
            obverse=notations[:split],
            reverse=notations[split:],
        )

    def replace_obverse(self, notations):
        return replace(self, obverse=notations)


def test_pool_randomizer_preserves_shape_and_notation_valid_sets():
    pool = tuple(
        ToyNotation(frozenset({system}), system)
        for system in ("A", "B", "C", "D", "E")
    )
    corpus = (
        ToyTablet(3, 1, pool[:2], pool[2:3]),
        ToyTablet(2, 2, pool[3:4], pool[4:5]),
    )
    randomized = randomize_tablet_notation_pool(
        corpus,
        random.Random(PERMUTATION_SEED),
        notation_pool=pool,
        notation_count=lambda tablet: tablet.notation_count,
        replace_notations=lambda tablet, notations: tablet.replace_notations(
            notations
        ),
    )

    assert [
        (tablet.obverse_entries, tablet.reverse_entries)
        for tablet in randomized
    ] == [(3, 1), (2, 2)]
    assert [
        (len(tablet.obverse), len(tablet.reverse))
        for tablet in randomized
    ] == [(2, 1), (1, 1)]
    assert len(
        {
            notation.assigned_system
            for tablet in randomized
            for notation in (*tablet.obverse, *tablet.reverse)
        }
    ) == 5

    bound = make_tablet_notation_pool_randomizer(
        notation_pool=pool,
        notation_count=lambda tablet: tablet.notation_count,
        replace_notations=lambda tablet, notations: tablet.replace_notations(
            notations
        ),
    )
    assert bound(corpus, random.Random(PERMUTATION_SEED)) == randomized


def test_stratified_randomizer_preserves_position_composition():
    obverse_pool = tuple(
        ToyNotation(frozenset({system}), system)
        for system in ("O1", "O2", "O3")
    )
    reverse_pool = tuple(
        ToyNotation(frozenset({system}), system)
        for system in ("R1", "R2")
    )
    corpus = (
        ToyTablet(2, 1, obverse_pool[:2], reverse_pool[:1]),
        ToyTablet(1, 1, obverse_pool[2:], reverse_pool[1:]),
    )
    randomized = randomize_tablet_notation_strata(
        corpus,
        random.Random(PERMUTATION_SEED),
        notation_pools={
            "obverse": obverse_pool,
            "reverse": reverse_pool,
        },
        slot_strata=lambda tablet: tablet.position_strata,
        replace_notations=lambda tablet, notations: tablet.replace_notations(
            notations
        ),
    )

    assert [
        (tablet.obverse_entries, tablet.reverse_entries)
        for tablet in randomized
    ] == [(2, 1), (1, 1)]
    assert all(
        notation.assigned_system.startswith("O")
        for tablet in randomized
        for notation in tablet.obverse
    )
    assert all(
        notation.assigned_system.startswith("R")
        for tablet in randomized
        for notation in tablet.reverse
    )

    bound = make_tablet_notation_stratified_randomizer(
        notation_pools={
            "obverse": obverse_pool,
            "reverse": reverse_pool,
        },
        slot_strata=lambda tablet: tablet.position_strata,
        replace_notations=lambda tablet, notations: tablet.replace_notations(
            notations
        ),
    )
    assert bound(corpus, random.Random(PERMUTATION_SEED)) == randomized


def test_stratified_randomizer_preserves_each_length_stratum():
    pool = (
        ToyNotation(frozenset({"A"}), "A1", length=1),
        ToyNotation(frozenset({"A"}), "A2", length=1),
        ToyNotation(frozenset({"A"}), "A3", length=1),
        ToyNotation(frozenset({"B"}), "B1", length=2),
        ToyNotation(frozenset({"B"}), "B2", length=2),
    )
    corpus = (
        ToyTablet(2, 1, pool[:2], pool[3:4]),
        ToyTablet(1, 1, pool[2:3], pool[4:5]),
    )
    randomized = randomize_tablet_notation_strata(
        corpus,
        random.Random(PERMUTATION_SEED),
        notation_pools={
            1: tuple(item for item in pool if item.length == 1),
            2: tuple(item for item in pool if item.length == 2),
        },
        slot_strata=lambda tablet: tablet.length_strata,
        replace_notations=lambda tablet, notations: tablet.replace_notations(
            notations
        ),
    )

    assert [
        tablet.length_strata for tablet in randomized
    ] == [
        tablet.length_strata for tablet in corpus
    ]


def test_obverse_bundle_shuffle_fixes_reverse_and_slot_count():
    notations = tuple(
        ToyNotation(frozenset({system}), system)
        for system in ("A", "B", "C", "D", "E", "F", "R1", "R2", "R3")
    )
    corpus = (
        ToyTablet(2, 1, notations[0:2], notations[6:7]),
        ToyTablet(2, 1, notations[2:4], notations[7:8]),
        ToyTablet(1, 1, notations[4:5], notations[8:9]),
        ToyTablet(1, 0, notations[5:6], ()),
    )
    randomized = randomize_obverse_bundles_by_slot_count(
        corpus,
        random.Random(PERMUTATION_SEED),
        obverse_notations=lambda tablet: tablet.obverse,
        replace_obverse=lambda tablet, obverse: tablet.replace_obverse(
            obverse
        ),
    )

    assert [
        tablet.reverse for tablet in randomized
    ] == [
        tablet.reverse for tablet in corpus
    ]
    for slot_count in (1, 2):
        original_bundles = sorted(
            tuple(item.assigned_system for item in tablet.obverse)
            for tablet in corpus
            if len(tablet.obverse) == slot_count
        )
        shuffled_bundles = sorted(
            tuple(item.assigned_system for item in tablet.obverse)
            for tablet in randomized
            if len(tablet.obverse) == slot_count
        )
        assert shuffled_bundles == original_bundles

    bound = make_obverse_bundle_randomizer(
        obverse_notations=lambda tablet: tablet.obverse,
        replace_obverse=lambda tablet, obverse: tablet.replace_obverse(
            obverse
        ),
    )
    assert bound(corpus, random.Random(PERMUTATION_SEED)) == randomized

"""Reusable, deterministic permutation-test infrastructure."""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
import random
import statistics
from typing import Hashable, TypeVar

from pe.constants import PERMUTATION_SEED


CorpusT = TypeVar("CorpusT")
ItemT = TypeVar("ItemT")
SystemT = TypeVar("SystemT")


@dataclass(frozen=True)
class PermutationTestResult:
    observed: float
    null_distribution: tuple[float, ...]
    null_mean: float
    null_std: float
    p_value: float
    n_resamples: int
    seed: int


def permutation_test(
    corpus: CorpusT,
    scoring_function: Callable[[CorpusT], int | float],
    randomization_function: Callable[[CorpusT, random.Random], CorpusT],
    *,
    n_resamples: int,
    seed: int = PERMUTATION_SEED,
) -> PermutationTestResult:
    """Compute a deterministic upper-tail empirical permutation test.

    The upper-tail p-value uses the finite-sample add-one correction:
    ``(count(null >= observed) + 1) / (n_resamples + 1)``.  It therefore never
    reports literal zero.  Randomness is isolated in a local RNG, so a seed
    reproduces the complete null distribution and does not depend on or modify
    Python's module-level random state.
    """

    if n_resamples <= 0:
        raise ValueError("n_resamples must be positive")

    observed = float(scoring_function(corpus))
    rng = random.Random(seed)
    null_distribution = tuple(
        float(scoring_function(randomization_function(corpus, rng)))
        for _ in range(n_resamples)
    )
    null_mean = statistics.fmean(null_distribution)
    null_std = statistics.pstdev(null_distribution)
    p_value = (
        sum(statistic >= observed for statistic in null_distribution) + 1
    ) / (
        n_resamples + 1
    )

    return PermutationTestResult(
        observed=observed,
        null_distribution=null_distribution,
        null_mean=null_mean,
        null_std=null_std,
        p_value=p_value,
        n_resamples=n_resamples,
        seed=seed,
    )


def randomize_valid_system_assignments(
    corpus: Sequence[ItemT],
    rng: random.Random,
    *,
    valid_systems: Callable[[ItemT], Collection[SystemT]],
    assign_system: Callable[[ItemT, SystemT], ItemT],
) -> tuple[ItemT, ...]:
    """Randomize ambiguous notations within their own valid reading sets.

    This null is appropriate for a statistic evaluated on one sampled system
    assignment per notation.  It is not appropriate for an existential
    statistic which searches every valid assignment, because fixing one
    reading before scoring understates that statistic's null.  Sampling from
    all four systems would still be wrong: it would introduce readings which
    Algorithm 1 has already ruled out.  Unambiguous items remain fixed.  Items
    with no valid system are rejected because they do not belong in this
    randomization.

    System options are canonically ordered before sampling, making results
    stable even when ``valid_systems`` returns a set.
    """

    randomized: list[ItemT] = []
    for item in corpus:
        options = tuple(
            sorted(
                set(valid_systems(item)),
                key=lambda system: str(getattr(system, "value", system)),
            )
        )
        if not options:
            raise ValueError("cannot randomize an item with no valid system")
        if len(options) == 1:
            randomized.append(item)
            continue
        system = options[rng.randrange(len(options))]
        randomized.append(assign_system(item, system))
    return tuple(randomized)


def make_valid_system_randomizer(
    *,
    valid_systems: Callable[[ItemT], Collection[SystemT]],
    assign_system: Callable[[ItemT, SystemT], ItemT],
) -> Callable[[Sequence[ItemT], random.Random], tuple[ItemT, ...]]:
    """Bind item accessors into a randomizer accepted by ``permutation_test``."""

    def randomize(
        corpus: Sequence[ItemT], rng: random.Random
    ) -> tuple[ItemT, ...]:
        return randomize_valid_system_assignments(
            corpus,
            rng,
            valid_systems=valid_systems,
            assign_system=assign_system,
        )

    return randomize


def randomize_tablet_notation_pool(
    corpus: Sequence[ItemT],
    rng: random.Random,
    *,
    notation_pool: Sequence[SystemT],
    notation_count: Callable[[ItemT], int],
    replace_notations: Callable[[ItemT, tuple[SystemT, ...]], ItemT],
) -> tuple[ItemT, ...]:
    """Shuffle notation identities while preserving every tablet's shape.

    This null is appropriate for an existential statistic, such as "does any
    consistent system assignment close this tablet?", when notation
    composition is exchangeable across all slots.  Each shuffled notation
    retains its full valid-reading set, and the existential search is rerun
    after shuffling.  This measures how often tablet closure arises from
    accidental combinations of otherwise valid notations in tablets of the
    observed sizes.  It is not appropriate for a witness statistic that is
    sensitive to position- or length-specific notation composition; use
    :func:`randomize_tablet_notation_strata` for those controls.

    By contrast, :func:`randomize_valid_system_assignments` chooses one system
    per ambiguous notation before scoring.  That answers whether one sampled
    assignment closes, not whether any valid assignment closes, and therefore
    understates the null for an existential statistic.

    Sampling is without replacement from the corpus-wide pool.  The caller's
    replacement function must retain structural fields such as obverse and
    reverse entry counts; only notation slots are replaced.
    """

    counts = tuple(notation_count(item) for item in corpus)
    if any(count < 0 for count in counts):
        raise ValueError("notation counts cannot be negative")
    total = sum(counts)
    if total > len(notation_pool):
        raise ValueError("notation pool is smaller than the requested slots")

    shuffled = rng.sample(tuple(notation_pool), total)
    randomized: list[ItemT] = []
    offset = 0
    for item, count in zip(corpus, counts, strict=True):
        replacements = tuple(shuffled[offset : offset + count])
        randomized.append(replace_notations(item, replacements))
        offset += count
    return tuple(randomized)


def make_tablet_notation_pool_randomizer(
    *,
    notation_pool: Sequence[SystemT],
    notation_count: Callable[[ItemT], int],
    replace_notations: Callable[[ItemT, tuple[SystemT, ...]], ItemT],
) -> Callable[[Sequence[ItemT], random.Random], tuple[ItemT, ...]]:
    """Bind a global pool and shape accessors for ``permutation_test``."""

    def randomize(
        corpus: Sequence[ItemT], rng: random.Random
    ) -> tuple[ItemT, ...]:
        return randomize_tablet_notation_pool(
            corpus,
            rng,
            notation_pool=notation_pool,
            notation_count=notation_count,
            replace_notations=replace_notations,
        )

    return randomize


def randomize_tablet_notation_strata(
    corpus: Sequence[ItemT],
    rng: random.Random,
    *,
    notation_pools: Mapping[Hashable, Sequence[SystemT]],
    slot_strata: Callable[[ItemT], Sequence[Hashable]],
    replace_notations: Callable[[ItemT, tuple[SystemT, ...]], ItemT],
) -> tuple[ItemT, ...]:
    """Shuffle full notations within pre-specified compositional strata.

    This is the appropriate existential null when a witness statistic could
    be driven by a known compositional margin.  For the position control,
    label obverse and reverse slots separately and provide pools of notations
    attested on the corresponding surface.  For the notation-length control,
    label each slot by its number of distinct digit signs and partition the
    corpus-wide pool by the same measure.  In either use, a notation retains
    its complete valid-reading set and the scorer reruns the existential
    search.

    This differs from the unstratified pool shuffle, which treats all notation
    slots as exchangeable, and from the valid-system assignment randomizer,
    which fixes one reading before scoring.  Sampling is without replacement
    within each stratum.  Tablet order and each tablet's number and order of
    notation slots are preserved.
    """

    item_strata = tuple(tuple(slot_strata(item)) for item in corpus)
    required: dict[Hashable, int] = {}
    for strata in item_strata:
        for stratum in strata:
            required[stratum] = required.get(stratum, 0) + 1

    sampled: dict[Hashable, list[SystemT]] = {}
    for stratum, count in required.items():
        if stratum not in notation_pools:
            raise ValueError(f"missing notation pool for stratum {stratum!r}")
        pool = tuple(notation_pools[stratum])
        if count > len(pool):
            raise ValueError(
                f"notation pool for stratum {stratum!r} is smaller than "
                "the requested slots"
            )
        sampled[stratum] = rng.sample(pool, count)

    offsets = {stratum: 0 for stratum in sampled}
    randomized: list[ItemT] = []
    for item, strata in zip(corpus, item_strata, strict=True):
        replacements: list[SystemT] = []
        for stratum in strata:
            offset = offsets[stratum]
            replacements.append(sampled[stratum][offset])
            offsets[stratum] = offset + 1
        randomized.append(replace_notations(item, tuple(replacements)))
    return tuple(randomized)


def make_tablet_notation_stratified_randomizer(
    *,
    notation_pools: Mapping[Hashable, Sequence[SystemT]],
    slot_strata: Callable[[ItemT], Sequence[Hashable]],
    replace_notations: Callable[[ItemT, tuple[SystemT, ...]], ItemT],
) -> Callable[[Sequence[ItemT], random.Random], tuple[ItemT, ...]]:
    """Bind compositional strata into a randomizer for ``permutation_test``."""

    def randomize(
        corpus: Sequence[ItemT], rng: random.Random
    ) -> tuple[ItemT, ...]:
        return randomize_tablet_notation_strata(
            corpus,
            rng,
            notation_pools=notation_pools,
            slot_strata=slot_strata,
            replace_notations=replace_notations,
        )

    return randomize


def randomize_obverse_bundles_by_slot_count(
    corpus: Sequence[ItemT],
    rng: random.Random,
    *,
    obverse_notations: Callable[[ItemT], Sequence[SystemT]],
    replace_obverse: Callable[[ItemT, tuple[SystemT, ...]], ItemT],
) -> tuple[ItemT, ...]:
    """Permute whole obverse bundles among equal-slot-count tablets.

    This null is appropriate for testing whether an attested reverse summary
    has unusual existential closure compatibility with its own obverse.
    Reverse notations are never replaced, so their magnitude, ambiguity, and
    complete valid-reading sets remain exactly attested.  Whole obverse
    bundles move only among tablets with the same number of obverse notation
    slots; tablet shape and within-bundle notation order are therefore fixed.
    """

    bundles = tuple(tuple(obverse_notations(item)) for item in corpus)
    indices_by_count: dict[int, list[int]] = {}
    for index, bundle in enumerate(bundles):
        indices_by_count.setdefault(len(bundle), []).append(index)

    replacements = list(bundles)
    for indices in indices_by_count.values():
        shuffled = rng.sample(
            tuple(bundles[index] for index in indices),
            len(indices),
        )
        for index, bundle in zip(indices, shuffled, strict=True):
            replacements[index] = bundle

    return tuple(
        replace_obverse(item, replacement)
        for item, replacement in zip(
            corpus, replacements, strict=True
        )
    )


def make_obverse_bundle_randomizer(
    *,
    obverse_notations: Callable[[ItemT], Sequence[SystemT]],
    replace_obverse: Callable[[ItemT, tuple[SystemT, ...]], ItemT],
) -> Callable[[Sequence[ItemT], random.Random], tuple[ItemT, ...]]:
    """Bind obverse accessors into a randomizer for ``permutation_test``."""

    def randomize(
        corpus: Sequence[ItemT], rng: random.Random
    ) -> tuple[ItemT, ...]:
        return randomize_obverse_bundles_by_slot_count(
            corpus,
            rng,
            obverse_notations=obverse_notations,
            replace_obverse=replace_obverse,
        )

    return randomize

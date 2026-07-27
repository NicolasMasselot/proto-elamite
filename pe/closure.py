"""Deterministic baseline subset-sum closure.

This module implements only the automatic baseline described in Section 3.2
of Born et al. (arXiv:2502.00090): tablets with one or two reverse entries are
tested for a non-empty subset of obverse readings that equals a reverse
reading in one consistent numeral system.  It intentionally contains no
implicit-object inheritance or solver logic.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping

from pe.corpus import Tablet
from pe.numerals import (
    NumeralNotation,
    NumeralSystem,
    extract_numeral_notations,
    possible_readings,
)


VALUE_SCALE = 120


NotationIndex = Mapping[
    str,
    Mapping[int, tuple[NumeralNotation, ...]],
]


def order_of_magnitude(value: Fraction) -> int:
    """Return the base-10 order containing a positive exact value."""

    if value <= 0:
        raise ValueError("magnitude requires a positive value")
    order = 0
    while value >= 10:
        value /= 10
        order += 1
    while value < 1:
        value *= 10
        order -= 1
    return order


@dataclass(frozen=True)
class ClosureWitness:
    system: NumeralSystem
    value: Fraction
    summary: NumeralNotation
    components: tuple[NumeralNotation, ...]


@dataclass(frozen=True)
class EncodedNotation:
    """A notation's complete valid readings in 1/120 N01 units."""

    readings: tuple[tuple[NumeralSystem, int], ...]
    distinct_digit_sign_count: int

    @property
    def unambiguous(self) -> bool:
        return len(self.readings) == 1

    @property
    def magnitude_bucket(self) -> int:
        maximum = max(value for _, value in self.readings)
        return order_of_magnitude(Fraction(maximum, VALUE_SCALE))


@dataclass(frozen=True)
class EncodedTablet:
    pnumber: str
    obverse_entry_count: int
    reverse_entry_count: int
    obverse: tuple[EncodedNotation, ...]
    reverse: tuple[EncodedNotation, ...]

    @property
    def notation_count(self) -> int:
        return len(self.obverse) + len(self.reverse)

    @property
    def position_strata(self) -> tuple[str, ...]:
        return ("obverse",) * len(self.obverse) + ("reverse",) * len(
            self.reverse
        )

    @property
    def length_strata(self) -> tuple[int, ...]:
        return tuple(
            notation.distinct_digit_sign_count
            for notation in (*self.obverse, *self.reverse)
        )

    @property
    def position_magnitude_strata(
        self,
    ) -> tuple[tuple[str, int], ...]:
        return tuple(
            ("obverse", notation.magnitude_bucket)
            for notation in self.obverse
        ) + tuple(
            ("reverse", notation.magnitude_bucket)
            for notation in self.reverse
        )

    def replace_notations(
        self, notations: tuple[EncodedNotation, ...]
    ) -> EncodedTablet:
        if len(notations) != self.notation_count:
            raise ValueError("replacement count changes tablet shape")
        split = len(self.obverse)
        return EncodedTablet(
            pnumber=self.pnumber,
            obverse_entry_count=self.obverse_entry_count,
            reverse_entry_count=self.reverse_entry_count,
            obverse=notations[:split],
            reverse=notations[split:],
        )

    def replace_obverse(
        self, notations: tuple[EncodedNotation, ...]
    ) -> EncodedTablet:
        if len(notations) != len(self.obverse):
            raise ValueError("replacement count changes obverse shape")
        return EncodedTablet(
            pnumber=self.pnumber,
            obverse_entry_count=self.obverse_entry_count,
            reverse_entry_count=self.reverse_entry_count,
            obverse=notations,
            reverse=self.reverse,
        )


def index_notations(
    notations: Iterable[NumeralNotation],
) -> dict[str, dict[int, tuple[NumeralNotation, ...]]]:
    grouped: dict[str, dict[int, list[NumeralNotation]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for notation in notations:
        grouped[notation.pnumber][notation.source_line].append(notation)
    return {
        pnumber: {
            source_line: tuple(items)
            for source_line, items in by_line.items()
        }
        for pnumber, by_line in grouped.items()
    }


def _subset_indices(
    values: tuple[Fraction, ...],
    target: Fraction,
    *,
    marked: tuple[bool, ...] | None = None,
    require_marked: bool = False,
) -> tuple[int, ...] | None:
    """Return one deterministic non-empty subset summing to ``target``."""

    if marked is None:
        marked = (False,) * len(values)
    if len(marked) != len(values):
        raise ValueError("marked flags must align with values")

    reachable: dict[tuple[Fraction, bool], tuple[int, ...]] = {
        (Fraction(0), False): ()
    }
    for index, value in enumerate(values):
        additions: dict[tuple[Fraction, bool], tuple[int, ...]] = {}
        for (subtotal, has_marked), selected in tuple(reachable.items()):
            new_total = subtotal + value
            state = (new_total, has_marked or marked[index])
            if new_total > target or state in reachable or state in additions:
                continue
            additions[state] = selected + (index,)
        reachable.update(additions)
        states = (
            ((target, True),)
            if require_marked
            else ((target, True), (target, False))
        )
        for state in states:
            if state not in reachable:
                continue
            selected = reachable[state]
            return selected if selected else None
    return None


def is_baseline_candidate(tablet: Tablet) -> bool:
    reverse_entries = sum(entry.surface == "reverse" for entry in tablet.entries)
    return reverse_entries in {1, 2}


def baseline_witnesses(
    tablet: Tablet,
    notation_index: NotationIndex,
) -> tuple[ClosureWitness, ...]:
    """Find same-system subset sums for one baseline-candidate tablet."""

    if not is_baseline_candidate(tablet):
        return ()

    surface_by_line = {
        entry.source_line: entry.surface for entry in tablet.entries
    }
    obverse: list[
        tuple[NumeralNotation, dict[NumeralSystem, Fraction]]
    ] = []
    reverse: list[
        tuple[NumeralNotation, dict[NumeralSystem, Fraction]]
    ] = []

    for source_line, notations in notation_index.get(
        tablet.pnumber, {}
    ).items():
        surface = surface_by_line.get(source_line)
        if surface not in {"obverse", "reverse"}:
            continue
        destination = obverse if surface == "obverse" else reverse
        for notation in notations:
            readings = possible_readings(notation.digits)
            if readings:
                destination.append((notation, readings))

    witnesses: list[ClosureWitness] = []
    for summary, summary_readings in reverse:
        for system, target in summary_readings.items():
            eligible = tuple(
                (notation, readings[system])
                for notation, readings in obverse
                if system in readings
            )
            values = tuple(value for _, value in eligible)
            selected = _subset_indices(
                values,
                target,
            )
            if selected is None:
                continue

            # Prefer a witness carrying the paper's evidentiary condition when
            # one exists, while preserving the raw closure if it does not.
            if len(summary_readings) != 1:
                supported = _subset_indices(
                    values,
                    target,
                    marked=tuple(
                        len(readings) == 1
                        for _, readings in obverse
                        if system in readings
                    ),
                    require_marked=True,
                )
                if supported is not None:
                    selected = supported
            witnesses.append(
                ClosureWitness(
                    system=system,
                    value=target,
                    summary=summary,
                    components=tuple(eligible[index][0] for index in selected),
                )
            )
    return tuple(witnesses)


def witness_has_unambiguous_component(witness: ClosureWitness) -> bool:
    """Whether a witness contains the paper's intrinsic system evidence."""

    return any(
        len(possible_readings(notation.digits)) == 1
        for notation in (witness.summary, *witness.components)
    )


def baseline_closure_counts(
    tablets: Iterable[Tablet],
) -> tuple[int, int]:
    """Return raw and unambiguous-component-supported candidate counts."""

    tablets = tuple(tablets)
    notation_index = index_notations(extract_numeral_notations(tablets))
    raw_count = 0
    supported_count = 0
    for tablet in tablets:
        witnesses = baseline_witnesses(tablet, notation_index)
        if not witnesses:
            continue
        raw_count += 1
        if any(witness_has_unambiguous_component(item) for item in witnesses):
            supported_count += 1
    return raw_count, supported_count


def _encode_notation(notation: NumeralNotation) -> EncodedNotation | None:
    readings = possible_readings(notation.digits)
    if not readings:
        return None
    encoded: list[tuple[NumeralSystem, int]] = []
    for system, value in readings.items():
        scaled = value * VALUE_SCALE
        if scaled.denominator != 1:
            raise ValueError(f"cannot encode value {value} at scale {VALUE_SCALE}")
        encoded.append((system, scaled.numerator))
    return EncodedNotation(
        readings=tuple(encoded),
        distinct_digit_sign_count=len(
            {digit.sign for digit in notation.digits}
        ),
    )


def build_encoded_position_pools(
    tablets: Iterable[Tablet],
) -> dict[str, tuple[EncodedNotation, ...]]:
    """Return full-corpus notation pools partitioned by tablet surface."""

    tablets = tuple(tablets)
    surface_by_location = {
        (tablet.pnumber, entry.source_line): entry.surface
        for tablet in tablets
        for entry in tablet.entries
    }
    pools: dict[str, list[EncodedNotation]] = {
        "obverse": [],
        "reverse": [],
    }
    for notation in extract_numeral_notations(tablets):
        encoded = _encode_notation(notation)
        if encoded is None:
            continue
        surface = surface_by_location.get(
            (notation.pnumber, notation.source_line)
        )
        if surface in pools:
            pools[surface].append(encoded)
    return {
        surface: tuple(notations)
        for surface, notations in pools.items()
    }


def group_notations_by_length(
    notations: Iterable[EncodedNotation],
) -> dict[int, tuple[EncodedNotation, ...]]:
    """Partition notations by their number of distinct digit signs."""

    grouped: dict[int, list[EncodedNotation]] = defaultdict(list)
    for notation in notations:
        grouped[notation.distinct_digit_sign_count].append(notation)
    return {
        length: tuple(items)
        for length, items in grouped.items()
    }


def group_position_notations_by_magnitude(
    position_pools: Mapping[str, Iterable[EncodedNotation]],
) -> dict[tuple[str, int], tuple[EncodedNotation, ...]]:
    """Partition surface-specific pools by maximum-reading magnitude."""

    grouped: dict[
        tuple[str, int], list[EncodedNotation]
    ] = defaultdict(list)
    for position, notations in position_pools.items():
        for notation in notations:
            grouped[(position, notation.magnitude_bucket)].append(notation)
    return {
        stratum: tuple(items)
        for stratum, items in grouped.items()
    }


def build_encoded_baseline_corpus(
    tablets: Iterable[Tablet],
) -> tuple[tuple[EncodedTablet, ...], tuple[EncodedNotation, ...]]:
    """Build the 425 fixed-shape candidates and corpus-wide notation pool."""

    tablets = tuple(tablets)
    extracted = extract_numeral_notations(tablets)
    encoded_by_location: dict[
        tuple[str, int], list[EncodedNotation]
    ] = defaultdict(list)
    notation_pool: list[EncodedNotation] = []
    for notation in extracted:
        encoded = _encode_notation(notation)
        if encoded is None:
            continue
        encoded_by_location[
            (notation.pnumber, notation.source_line)
        ].append(encoded)
        notation_pool.append(encoded)

    candidates: list[EncodedTablet] = []
    for tablet in tablets:
        if not is_baseline_candidate(tablet):
            continue
        obverse: list[EncodedNotation] = []
        reverse: list[EncodedNotation] = []
        for entry in tablet.entries:
            if entry.surface not in {"obverse", "reverse"}:
                continue
            destination = obverse if entry.surface == "obverse" else reverse
            destination.extend(
                encoded_by_location.get(
                    (tablet.pnumber, entry.source_line), ()
                )
            )
        candidates.append(
            EncodedTablet(
                pnumber=tablet.pnumber,
                obverse_entry_count=sum(
                    entry.surface == "obverse" for entry in tablet.entries
                ),
                reverse_entry_count=sum(
                    entry.surface == "reverse" for entry in tablet.entries
                ),
                obverse=tuple(obverse),
                reverse=tuple(reverse),
            )
        )
    return tuple(candidates), tuple(notation_pool)


def _encoded_subset_exists(
    terms: tuple[tuple[int, bool], ...],
    target: int,
    *,
    require_marked: bool,
) -> bool:
    """Fast bitset subset sum, optionally requiring a marked component."""

    if target <= 0:
        return False
    mask = (1 << (target + 1)) - 1
    unmarked = 1
    marked = 0
    for value, is_marked in terms:
        if value <= 0 or value > target:
            continue
        if is_marked:
            marked |= (unmarked | marked) << value
        else:
            unmarked |= unmarked << value
            marked |= marked << value
        unmarked &= mask
        marked &= mask
        if require_marked:
            if (marked >> target) & 1:
                return True
        elif ((unmarked | marked) >> target) & 1:
            return True
    return False


def encoded_tablet_closes(
    tablet: EncodedTablet,
    *,
    require_unambiguous_witness: bool,
) -> bool:
    """Re-run existential same-system closure on one encoded tablet."""

    obverse_maps = tuple(dict(notation.readings) for notation in tablet.obverse)
    for summary in tablet.reverse:
        for system, target in summary.readings:
            terms = tuple(
                (readings[system], notation.unambiguous)
                for notation, readings in zip(
                    tablet.obverse, obverse_maps, strict=True
                )
                if system in readings
            )
            require_marked = (
                require_unambiguous_witness and not summary.unambiguous
            )
            if _encoded_subset_exists(
                terms,
                target,
                require_marked=require_marked,
            ):
                return True
    return False


def encoded_tablet_closure_status(
    tablet: EncodedTablet,
) -> tuple[bool, bool]:
    """Return raw and unambiguous-witness closure in one search."""

    raw_closure = False
    supported_closure = False
    obverse_maps = tuple(dict(notation.readings) for notation in tablet.obverse)
    for summary in tablet.reverse:
        for system, target in summary.readings:
            terms = tuple(
                (readings[system], notation.unambiguous)
                for notation, readings in zip(
                    tablet.obverse, obverse_maps, strict=True
                )
                if system in readings
            )
            if summary.unambiguous:
                closes = _encoded_subset_exists(
                    terms,
                    target,
                    require_marked=False,
                )
                raw_closure |= closes
                supported_closure |= closes
            else:
                has_supported_witness = _encoded_subset_exists(
                    terms,
                    target,
                    require_marked=True,
                )
                if has_supported_witness:
                    raw_closure = True
                    supported_closure = True
                elif not raw_closure:
                    raw_closure = _encoded_subset_exists(
                        terms,
                        target,
                        require_marked=False,
                    )
            if raw_closure and supported_closure:
                return True, True
    return raw_closure, supported_closure


def encoded_closure_counts(
    tablets: Iterable[EncodedTablet],
) -> tuple[int, int]:
    """Return paired raw and unambiguous-witness closure counts."""

    raw_count = 0
    supported_count = 0
    for tablet in tablets:
        raw, supported = encoded_tablet_closure_status(tablet)
        raw_count += raw
        supported_count += supported
    return raw_count, supported_count


def encoded_tablet_full_sum_closure_status(
    tablet: EncodedTablet,
) -> tuple[bool, bool]:
    """Return strict full-obverse-sum raw and witness closure.

    Every encoded obverse numeral notation must have a reading in one shared
    system, and the sum of all those readings must equal one attested reverse
    reading.  No proper subset of the obverse is considered.
    """

    if not tablet.obverse:
        return False, False

    raw_closure = False
    obverse_maps = tuple(dict(notation.readings) for notation in tablet.obverse)
    for summary in tablet.reverse:
        for system, target in summary.readings:
            if not all(system in readings for readings in obverse_maps):
                continue
            if sum(readings[system] for readings in obverse_maps) != target:
                continue
            raw_closure = True
            if summary.unambiguous or any(
                notation.unambiguous for notation in tablet.obverse
            ):
                return True, True
    return raw_closure, False


def encoded_full_sum_closure_counts(
    tablets: Iterable[EncodedTablet],
) -> tuple[int, int]:
    """Return paired strict full-sum raw and witness closure counts."""

    raw_count = 0
    supported_count = 0
    for tablet in tablets:
        raw, supported = encoded_tablet_full_sum_closure_status(tablet)
        raw_count += raw
        supported_count += supported
    return raw_count, supported_count


def encoded_closure_count(
    tablets: Iterable[EncodedTablet],
    *,
    require_unambiguous_witness: bool,
) -> int:
    return sum(
        encoded_tablet_closes(
            tablet,
            require_unambiguous_witness=require_unambiguous_witness,
        )
        for tablet in tablets
    )

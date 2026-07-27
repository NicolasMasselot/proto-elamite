from fractions import Fraction

from pe.closure import (
    EncodedNotation,
    EncodedTablet,
    _subset_indices,
    baseline_closure_counts,
    baseline_witnesses,
    build_encoded_baseline_corpus,
    build_encoded_position_pools,
    encoded_closure_counts,
    encoded_closure_count,
    encoded_full_sum_closure_counts,
    encoded_tablet_full_sum_closure_status,
    encoded_tablet_closes,
    group_position_notations_by_magnitude,
    group_notations_by_length,
    index_notations,
    is_baseline_candidate,
    order_of_magnitude,
)
from pe.corpus import load_corpus
from pe.numerals import NumeralSystem, extract_numeral_notations


def test_subset_sum_uses_a_nonempty_subset():
    assert _subset_indices(
        (Fraction(2), Fraction(3), Fraction(7)),
        Fraction(5),
    ) == (0, 1)
    assert _subset_indices((Fraction(2), Fraction(3)), Fraction(4)) is None
    assert _subset_indices((Fraction(2),), Fraction(0)) is None


def test_exact_order_of_magnitude_buckets():
    assert order_of_magnitude(Fraction(1, 120)) == -3
    assert order_of_magnitude(Fraction(1, 10)) == -1
    assert order_of_magnitude(Fraction(1)) == 0
    assert order_of_magnitude(Fraction(999)) == 2
    assert order_of_magnitude(Fraction(1000)) == 3


def test_full_sum_uses_every_obverse_notation():
    def notation(value):
        return EncodedNotation(
            readings=((NumeralSystem.DECIMAL, value),),
            distinct_digit_sign_count=1,
        )

    full_sum = EncodedTablet(
        pnumber="PTEST1",
        obverse_entry_count=2,
        reverse_entry_count=1,
        obverse=(notation(2), notation(3)),
        reverse=(notation(5),),
    )
    subset_only = EncodedTablet(
        pnumber="PTEST2",
        obverse_entry_count=2,
        reverse_entry_count=1,
        obverse=(notation(2), notation(3)),
        reverse=(notation(2),),
    )

    assert encoded_tablet_full_sum_closure_status(full_sum) == (True, True)
    assert encoded_tablet_full_sum_closure_status(subset_only) == (
        False,
        False,
    )


def test_paper_examples_and_current_reverse_filter():
    tablets = {tablet.pnumber: tablet for tablet in load_corpus()}
    notation_index = index_notations(
        extract_numeral_notations(tablets.values())
    )

    assert baseline_witnesses(tablets["P008014"], notation_index)
    assert baseline_witnesses(tablets["P008173"], notation_index)
    assert baseline_witnesses(tablets["P008012"], notation_index)

    assert not is_baseline_candidate(tablets["P008179"])
    assert not baseline_witnesses(tablets["P008179"], notation_index)


def test_current_snapshot_baseline_candidate_counts():
    assert baseline_closure_counts(load_corpus()) == (151, 52)


def test_encoded_scorers_match_witness_counts():
    tablets, notation_pool = build_encoded_baseline_corpus(load_corpus())
    assert len(tablets) == 425
    assert len(notation_pool) == 7959
    assert sum(tablet.notation_count for tablet in tablets) == 2642
    assert encoded_closure_count(
        tablets, require_unambiguous_witness=False
    ) == 151
    assert encoded_closure_count(
        tablets, require_unambiguous_witness=True
    ) == 52
    assert encoded_closure_counts(tablets) == (151, 52)
    assert encoded_full_sum_closure_counts(tablets) == (63, 21)


def test_p008805_figure_2_entries_are_obverse_only():
    tablet = next(
        item for item in load_corpus() if item.pnumber == "P008805"
    )
    assert tuple(entry.surface for entry in tablet.entries) == (
        "obverse",
        "obverse",
    )
    assert tuple(
        notation.raw
        for notation in extract_numeral_notations((tablet,))
    ) == (
        "1(N34) 5(N14) 1(N01) 1(N8B)",
        "7(N14) 2(N01) 3(N39B)",
    )


def test_encoded_notation_composition_margins():
    tablets = load_corpus()
    candidates, notation_pool = build_encoded_baseline_corpus(tablets)
    position_pools = build_encoded_position_pools(tablets)
    length_pools = group_notations_by_length(notation_pool)

    candidate_obverse = tuple(
        notation
        for tablet in candidates
        for notation in tablet.obverse
    )
    candidate_reverse = tuple(
        notation
        for tablet in candidates
        for notation in tablet.reverse
    )
    assert (
        sum(item.unambiguous for item in candidate_obverse),
        len(candidate_obverse),
    ) == (495, 2218)
    assert (
        sum(item.unambiguous for item in candidate_reverse),
        len(candidate_reverse),
    ) == (200, 424)
    assert (
        sum(item.unambiguous for item in position_pools["obverse"]),
        len(position_pools["obverse"]),
    ) == (1561, 6718)
    assert (
        sum(item.unambiguous for item in position_pools["reverse"]),
        len(position_pools["reverse"]),
    ) == (380, 1131)
    assert sum(map(len, length_pools.values())) == len(notation_pool)
    assert set(length_pools) == {
        notation.distinct_digit_sign_count for notation in notation_pool
    }

    magnitude_pools = group_position_notations_by_magnitude(position_pools)
    assert sum(map(len, magnitude_pools.values())) == (
        len(position_pools["obverse"]) + len(position_pools["reverse"])
    )
    required_magnitude_strata = {
        stratum
        for tablet in candidates
        for stratum in tablet.position_magnitude_strata
    }
    assert required_magnitude_strata <= set(magnitude_pools)


def test_supported_pnumbers_and_appendix_a_overlap():
    expected_supported = (
        "P008014", "P008016", "P008018", "P008019", "P008020",
        "P008069", "P008106", "P008140", "P008150", "P008169",
        "P008173", "P008215", "P008243", "P008275", "P008292",
        "P008308", "P008313", "P008387", "P008419", "P008426",
        "P008438", "P008626", "P008641", "P008709", "P008753",
        "P008783", "P008821", "P008844", "P008946", "P008984",
        "P008998", "P009001", "P009011", "P009014", "P009028",
        "P009041", "P009092", "P009155", "P009166", "P009193",
        "P009196", "P009207", "P009219", "P009239", "P009366",
        "P009432", "P009441", "P009444", "P009524", "P009525",
        "P009526", "P009531",
    )
    appendix = {
        "P008014", "P008173", "P008798", "P008797", "P008791",
        "P008799", "P008800", "P008801", "P008802", "P008804",
        "P008810", "P008179", "P008012", "P008243", "P009048",
    }
    tablets = load_corpus()
    tablet_by_pnumber = {
        tablet.pnumber: tablet for tablet in tablets
    }
    candidates, _ = build_encoded_baseline_corpus(tablets)
    candidate_by_pnumber = {
        tablet.pnumber: tablet for tablet in candidates
    }
    supported = tuple(
        sorted(
            tablet.pnumber
            for tablet in candidates
            if encoded_tablet_closes(
                tablet,
                require_unambiguous_witness=True,
            )
        )
    )

    assert supported == expected_supported
    assert set(supported) & appendix == {
        "P008014",
        "P008173",
        "P008243",
    }
    assert appendix <= set(tablet_by_pnumber)
    assert encoded_tablet_closes(
        candidate_by_pnumber["P008012"],
        require_unambiguous_witness=False,
    )
    assert not encoded_tablet_closes(
        candidate_by_pnumber["P008012"],
        require_unambiguous_witness=True,
    )

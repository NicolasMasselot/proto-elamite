"""Deterministic conversion of Proto-Elamite numeral notations.

This implements Algorithm 1 and Figure 1 of the revised version of Born et
al., "Disambiguating Numeral Sequences to Decipher Ancient Accounting
Corpora" (arXiv:2502.00090v2, 25 April 2025).  Values are exact multiples of
N01; no contextual disambiguation is attempted.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import re
from typing import Iterable, Mapping

from pe.corpus import AtfToken, Tablet, TokenKind


PAPER_URL = "https://arxiv.org/abs/2502.00090"
DIGIT_RE = re.compile(r"(?P<count>\d+)\((?P<sign>N[^)]+)\)")


class NumeralSystem(str, Enum):
    DECIMAL = "D"
    SEXAGESIMAL = "S"
    BISEXAGESIMAL = "B"
    CAPACITY = "C"


@dataclass(frozen=True)
class Digit:
    count: int
    sign: str


@dataclass(frozen=True)
class DigitSpec:
    value: Fraction
    max_count: int | None


@dataclass(frozen=True)
class NumeralNotation:
    pnumber: str
    entry_label: str
    source_line: int
    digits: tuple[Digit, ...]
    tokens: tuple[AtfToken, ...]

    @property
    def raw(self) -> str:
        return " ".join(token.raw for token in self.tokens)


def _spec(
    chain: tuple[str, ...], radices: tuple[int, ...]
) -> dict[str, DigitSpec]:
    """Build Figure 1 values, normalized so N01 equals one."""

    if len(chain) != len(radices) + 1:
        raise ValueError("each adjacent pair in a digit chain needs one radix")

    relative_values = {chain[0]: Fraction(1)}
    for lower, higher, radix in zip(
        chain[:-1], chain[1:], radices, strict=True
    ):
        relative_values[higher] = relative_values[lower] * radix

    n01 = relative_values["N01"]
    result = {
        sign: DigitSpec(value=relative_values[sign] / n01, max_count=radix)
        for sign, radix in zip(chain[:-1], radices, strict=True)
    }
    result[chain[-1]] = DigitSpec(
        value=relative_values[chain[-1]] / n01,
        max_count=None,
    )
    return result


# Figure 1 is ordered from the smallest digit to the largest digit here.
# An arrow label is Algorithm 1's maximum count: a larger count is invalid.
SYSTEMS: Mapping[NumeralSystem, Mapping[str, DigitSpec]] = {
    NumeralSystem.DECIMAL: _spec(
        ("N01", "N14", "N23", "N51", "N54G"),
        (10, 10, 10, 10),
    ),
    NumeralSystem.SEXAGESIMAL: _spec(
        ("N08A", "N01", "N14", "N34", "N48", "N45"),
        (2, 10, 6, 10, 6),
    ),
    NumeralSystem.BISEXAGESIMAL: _spec(
        ("N01", "N14", "N34", "N51", "N54"),
        (10, 6, 2, 10),
    ),
    NumeralSystem.CAPACITY: _spec(
        (
            "N39C",
            "N30D",
            "N30C",
            "N24",
            "N39B",
            "N01",
            "N14",
            "N45",
            "N34",
            "N48",
            "N46",
        ),
        (2, 2, 3, 2, 5, 6, 10, 3, 10, 6),
    ),
}


def normalize_digit_sign(sign: str) -> str:
    """Map ATF spelling/allograph notation to the Figure 1 sign names."""

    # ATF modifiers after @ record graphetic orientation/allography.  Figure 1
    # names the underlying digit, so conversion operates on that base name.
    sign = sign.partition("@")[0]
    aliases = {
        "N1": "N01",
        "N8A": "N08A",
        "N8B": "N08A",
        "N08": "N08A",
        "N08b": "N08A",
    }
    return aliases.get(sign, sign)


def parse_digit_token(token: AtfToken) -> Digit | None:
    """Return an uppercase N-sign digit, or ``None`` for other ATF tokens."""

    if token.value is None:
        return None
    match = DIGIT_RE.fullmatch(token.value)
    if match is None:
        return None
    return Digit(
        count=int(match.group("count")),
        sign=normalize_digit_sign(match.group("sign")),
    )


def possible_readings(
    digits: Iterable[Digit | tuple[int, str]],
) -> dict[NumeralSystem, Fraction]:
    """Apply Algorithm 1 and return only systems with a valid reading."""

    normalized = tuple(
        digit
        if isinstance(digit, Digit)
        else Digit(count=digit[0], sign=normalize_digit_sign(digit[1]))
        for digit in digits
    )
    readings: dict[NumeralSystem, Fraction] = {}

    for system, digit_specs in SYSTEMS.items():
        value = Fraction(0)
        valid = True
        for digit in normalized:
            spec = digit_specs.get(digit.sign)
            if spec is None or (
                spec.max_count is not None and digit.count > spec.max_count
            ):
                valid = False
                break
            value += digit.count * spec.value
        if valid:
            readings[system] = value

    return readings


def extract_numeral_notations(
    tablets: Iterable[Tablet],
) -> tuple[NumeralNotation, ...]:
    """Extract intact contiguous uppercase N-sign runs from numeral fields.

    The transliteration orders digits from high to low.  Following the paper's
    regular-expression rule, a run is discarded when the next token in that
    field is broken or unreadable: that marker makes the adjacent lower-order
    portion unknown.  A preceding marker terminates the previous run rather
    than damaging the following notation.
    """

    notations: list[NumeralNotation] = []
    for tablet in tablets:
        for entry in tablet.entries:
            tokens = entry.numeral_notation
            index = 0
            while index < len(tokens):
                first = parse_digit_token(tokens[index])
                if first is None:
                    index += 1
                    continue

                end = index + 1
                digits = [first]
                while end < len(tokens):
                    digit = parse_digit_token(tokens[end])
                    if digit is None:
                        break
                    digits.append(digit)
                    end += 1

                damaged = (
                    end < len(tokens)
                    and tokens[end].kind is TokenKind.UNREADABLE
                )
                if not damaged:
                    notations.append(
                        NumeralNotation(
                            pnumber=tablet.pnumber,
                            entry_label=entry.label,
                            source_line=entry.source_line,
                            digits=tuple(digits),
                            tokens=tokens[index:end],
                        )
                    )
                index = end

    return tuple(notations)


def reading_distribution(
    notations: Iterable[NumeralNotation],
) -> Counter[frozenset[NumeralSystem]]:
    return Counter(
        frozenset(possible_readings(notation.digits))
        for notation in notations
    )

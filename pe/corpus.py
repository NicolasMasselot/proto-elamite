"""Parse the pinned ``pe-headers`` ATF corpus without interpreting values.

The parser preserves ATF surface-damage notation.  In particular, ``M001#``
is an identified but broken sign, while ``[...]`` is a missing span.  Square-
bracket restorations retain their supplied identity but remain marked missing.
Numeral notation is stored as notation; it is deliberately not converted.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Iterable, Iterator

from pe.constants import CORPUS_DIR


ENTRY_RE = re.compile(r"^(?P<label>\d\S*[.'])\s*(?P<body>.*)$")
PNUMBER_RE = re.compile(r"^&(?P<pnumber>P\d{6})\b")
IDENTIFIED_SIGN_RE = re.compile(r"M\d")
IDENTIFIED_NUMERAL_RE = re.compile(r"\d+\([Nn]")


class Damage(str, Enum):
    """Physical legibility recorded by the ATF editor."""

    INTACT = "intact"
    BROKEN = "broken"
    MISSING = "missing"


class TokenKind(str, Enum):
    """A structural token class, without assigning a numerical value."""

    SIGN = "sign"
    NUMERAL = "numeral"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class AtfToken:
    raw: str
    value: str | None
    kind: TokenKind
    damage: Damage
    uncertain: bool = False
    restored: bool = False
    supplied: bool = False

    @property
    def normalized(self) -> str | None:
        """Remove only external editorial/damage marks for type counts."""

        if self.value is None:
            return None
        return self.raw.strip("[]<>").rstrip("#?!")


@dataclass(frozen=True)
class Entry:
    label: str
    signs: tuple[AtfToken, ...]
    numeral_notation: tuple[AtfToken, ...]
    surface: str | None
    column: str | None
    raw: str
    source_line: int

    @property
    def tokens(self) -> tuple[AtfToken, ...]:
        return self.signs + self.numeral_notation


@dataclass(frozen=True)
class Tablet:
    pnumber: str
    entries: tuple[Entry, ...]
    path: Path

    @property
    def tokens(self) -> Iterator[AtfToken]:
        for entry in self.entries:
            yield from entry.tokens


@dataclass(frozen=True)
class CorpusStats:
    total_texts: int
    cleaned_texts: int
    total_entries: int
    total_tokens: int
    unreadable_or_missing: int
    numeral_tokens: int
    nonnumerical_tokens: int
    nonnumerical_types: int
    nonnumerical_hapax: int


def _split_entry(body: str) -> tuple[str, str | None]:
    """Split on the first comma outside square brackets.

    A handful of editorial restorations contain commas themselves.  Those
    commas are content, not the object/numeral delimiter.
    """

    square_depth = 0
    for index, character in enumerate(body):
        if character == "[":
            square_depth += 1
        elif character == "]":
            square_depth = max(0, square_depth - 1)
        elif character == "," and square_depth == 0:
            return body[:index], body[index + 1 :]
    return body, None


def _bare_value(raw: str) -> str:
    return raw.strip("[]<>").rstrip("#?!")


def _kind(raw: str) -> TokenKind:
    bare = _bare_value(raw)
    if IDENTIFIED_SIGN_RE.search(bare):
        return TokenKind.SIGN
    if IDENTIFIED_NUMERAL_RE.search(bare):
        return TokenKind.NUMERAL
    return TokenKind.UNREADABLE


def _tokenize(segment: str) -> tuple[AtfToken, ...]:
    tokens: list[AtfToken] = []
    square_depth = 0

    for raw in segment.split():
        if raw == ",":
            continue

        begins_restoration = "[" in raw
        restored = square_depth > 0 or begins_restoration
        square_depth += raw.count("[")

        kind = _kind(raw)
        bare = _bare_value(raw)
        unreadable = kind is TokenKind.UNREADABLE

        if restored:
            damage = Damage.MISSING
        elif "#" in raw or unreadable:
            damage = Damage.BROKEN
        else:
            damage = Damage.INTACT

        value = bare if not unreadable else None
        tokens.append(
            AtfToken(
                raw=raw,
                value=value,
                kind=kind,
                damage=damage,
                uncertain="?" in raw,
                restored=restored,
                supplied="<" in raw or ">" in raw,
            )
        )
        square_depth = max(0, square_depth - raw.count("]"))

    return tuple(tokens)


def parse_atf(path: Path) -> Tablet:
    """Parse one ATF file into a tablet and its entries in source order."""

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"empty ATF file: {path}")

    header = PNUMBER_RE.match(lines[0])
    if header is None:
        raise ValueError(f"missing P-number header in {path}")
    pnumber = header.group("pnumber")

    entries: list[Entry] = []
    surface: str | None = None
    column: str | None = None

    for source_line, raw_line in enumerate(lines, start=1):
        if raw_line.startswith("@"):
            directive, _, argument = raw_line.partition(" ")
            if directive in {"@obverse", "@reverse", "@top", "@bottom", "@edge"}:
                surface = directive[1:]
                column = None
            elif directive == "@column":
                column = argument.strip() or None
            continue

        match = ENTRY_RE.match(raw_line)
        if match is None:
            continue

        body = match.group("body").strip()
        sign_text, numeral_text = _split_entry(body)
        signs = _tokenize(sign_text)

        if numeral_text is not None:
            numerals = _tokenize(numeral_text)
        else:
            # Lines without a delimiter occur in the corpus.  Preserve purely
            # numerical tokens as notation; all other material stays on the
            # sign side.  No numerical value is inferred.
            numerals = tuple(token for token in signs if token.kind is TokenKind.NUMERAL)
            signs = tuple(token for token in signs if token.kind is not TokenKind.NUMERAL)

        entries.append(
            Entry(
                label=match.group("label"),
                signs=signs,
                numeral_notation=numerals,
                surface=surface,
                column=column,
                raw=raw_line,
                source_line=source_line,
            )
        )

    return Tablet(pnumber=pnumber, entries=tuple(entries), path=path)


def load_corpus(corpus_dir: Path = CORPUS_DIR) -> tuple[Tablet, ...]:
    paths = sorted(corpus_dir.glob("*.atf"))
    if not paths:
        raise FileNotFoundError(f"no ATF files found under {corpus_dir}")
    return tuple(parse_atf(path) for path in paths)


def iter_tokens(tablets: Iterable[Tablet]) -> Iterator[AtfToken]:
    for tablet in tablets:
        yield from tablet.tokens


def corpus_stats(tablets: Iterable[Tablet]) -> CorpusStats:
    """Compute directly observable corpus inventory counts."""

    tablets = tuple(tablets)
    tokens = tuple(iter_tokens(tablets))
    identified_signs = tuple(token for token in tokens if token.kind is TokenKind.SIGN)
    numerals = sum(token.kind is TokenKind.NUMERAL for token in tokens)
    unreadable = sum(token.kind is TokenKind.UNREADABLE for token in tokens)

    sign_counts = Counter(
        token.normalized for token in identified_signs if token.normalized is not None
    )
    cleaned_texts = sum(
        any(token.kind is TokenKind.SIGN for token in tablet.tokens)
        for tablet in tablets
    )

    return CorpusStats(
        total_texts=len(tablets),
        cleaned_texts=cleaned_texts,
        total_entries=sum(len(tablet.entries) for tablet in tablets),
        total_tokens=len(tokens),
        unreadable_or_missing=unreadable,
        numeral_tokens=numerals,
        nonnumerical_tokens=len(identified_signs),
        nonnumerical_types=len(sign_counts),
        nonnumerical_hapax=sum(count == 1 for count in sign_counts.values()),
    )


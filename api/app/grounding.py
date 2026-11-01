"""Number grounding (A22): model prose may only repeat figures tools returned.

A model explains; it never produces a figure the UI shows as fact. This
module finds every figure in a piece of model text (money, plain numbers,
percentages, dates) and checks each one against the figures the read-only
tools handed the model. A figure passes when it equals a tool figure, or
is that figure rounded to a precision of at least one decimal place
("8.8%" for 8.79 passes, "9%" does not). Digits inside identifiers such
as ORD-001, EVT-7b36d6f9 or PTB8850LS41 are names, not figures.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MONTHS = {
    name: index
    for index, names in enumerate(
        (
            ("jan", "january"),
            ("feb", "february"),
            ("mar", "march"),
            ("apr", "april"),
            ("may",),
            ("jun", "june"),
            ("jul", "july"),
            ("aug", "august"),
            ("sep", "sept", "september"),
            ("oct", "october"),
            ("nov", "november"),
            ("dec", "december"),
        ),
        start=1,
    )
    for name in names
}

_MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))
_ISO_DATE = re.compile(r"(?<![\w-])(\d{4})-(\d{2})-(\d{2})(?![\w-])")
_SLASH_DATE = re.compile(r"(?<![\w/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\w/])")
_NAMED_DATE = re.compile(
    rf"\b({_MONTH})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b",
    re.IGNORECASE,
)
# A number: optional $, digits with optional thousands commas, optional
# decimals, optional %. Not preceded by a letter, digit, dot or an
# identifier hyphen ("ORD-001"), not followed by a letter or digit
# ("8850LS41"). A trailing "-day" is allowed: "60-day" is a figure.
_NUMBER = re.compile(
    r"(?<![A-Za-z0-9.])(?<![A-Za-z]-)(\$)?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(%)?(?![A-Za-z0-9])"
)


@dataclass(frozen=True)
class Figure:
    """One figure found in text: a number or a date, with its raw spelling."""

    raw: str
    number: Decimal | None = None
    day: date | None = None
    # A named date without a year ("Jan 1") matches any year.
    month_day: tuple[int, int] | None = None


@dataclass
class GroundingResult:
    """Whether every figure in the text came from a tool."""

    grounded: bool
    ungrounded: list[str] = field(default_factory=list)


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_figures(text: str) -> list[Figure]:
    """Every money amount, number, percentage and date in ``text``."""
    figures: list[Figure] = []
    taken: list[tuple[int, int]] = []

    def claim(start: int, end: int) -> bool:
        if any(start < t_end and end > t_start for t_start, t_end in taken):
            return False
        taken.append((start, end))
        return True

    for match in _ISO_DATE.finditer(text):
        parsed = _safe_date(int(match[1]), int(match[2]), int(match[3]))
        if parsed and claim(*match.span()):
            figures.append(Figure(raw=match[0], day=parsed))
    for match in _SLASH_DATE.finditer(text):
        parsed = _safe_date(int(match[3]), int(match[1]), int(match[2]))
        if parsed and claim(*match.span()):
            figures.append(Figure(raw=match[0], day=parsed))
    for match in _NAMED_DATE.finditer(text):
        month = MONTHS[match[1].lower()]
        day_of_month = int(match[2])
        if match[3]:
            parsed = _safe_date(int(match[3]), month, day_of_month)
            if parsed and claim(*match.span()):
                figures.append(Figure(raw=match[0], day=parsed))
        elif 1 <= day_of_month <= 31 and claim(*match.span()):
            figures.append(Figure(raw=match[0], month_day=(month, day_of_month)))
    for match in _NUMBER.finditer(text):
        if not claim(*match.span()):
            continue
        digits = match[2].replace(",", "") + (match[3] or "")
        try:
            figures.append(Figure(raw=match[0], number=Decimal(digits)))
        except InvalidOperation:
            continue
    return figures


def tool_figures(values: Iterable[object]) -> list[Figure]:
    """Every figure inside tool output: nested dicts, lists, scalars, text."""
    found: list[Figure] = []

    def walk(value: object) -> None:
        if value is None or isinstance(value, bool):
            return
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)
        elif isinstance(value, date):
            found.append(Figure(raw=value.isoformat(), day=value))
        elif isinstance(value, (int, Decimal)):
            found.append(Figure(raw=str(value), number=Decimal(value)))
        else:
            found.extend(extract_figures(str(value)))

    for value in values:
        walk(value)
    return found


def _number_matches(claimed: Decimal, allowed: Decimal) -> bool:
    if claimed == allowed:
        return True
    exponent = claimed.as_tuple().exponent
    places = -exponent if isinstance(exponent, int) else 0
    if places < 1:
        return False
    quantum = Decimal(1).scaleb(-places)
    return allowed.quantize(quantum, ROUND_HALF_UP) == claimed


def _is_grounded(figure: Figure, allowed: list[Figure]) -> bool:
    allowed_days = [item.day for item in allowed if item.day is not None]
    if figure.day is not None:
        return figure.day in allowed_days
    if figure.month_day is not None:
        return any((day.month, day.day) == figure.month_day for day in allowed_days)
    assert figure.number is not None
    if any(
        item.number is not None and _number_matches(figure.number, item.number)
        for item in allowed
    ):
        return True
    # A bare year ("in 2027") is grounded by any tool date in that year.
    if figure.number == figure.number.to_integral_value() and 1900 <= figure.number <= 2100:
        return any(day.year == int(figure.number) for day in allowed_days)
    return False


def check(text: str, allowed: list[Figure]) -> GroundingResult:
    """Ground every figure in ``text`` against the tool figures ``allowed``."""
    ungrounded = [
        figure.raw for figure in extract_figures(text) if not _is_grounded(figure, allowed)
    ]
    return GroundingResult(grounded=not ungrounded, ungrounded=ungrounded)

"""Cost engine as pure, tested functions (A12).

Every figure on screen comes from here; a model never produces a number
the UI shows as fact. Money is always ``Decimal``, quantized to cents.
The lowest safe bid rounds the per-unit price UP: rounding down would
breach the margin floor it exists to protect.
"""

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from app.schemas import Quote

CENT = Decimal("0.01")


def landed_cost(quote: Quote) -> Decimal:
    """Supplier lines extended plus freight: the cash outlay if we win."""
    return sum((line.extended for line in quote.lines), Decimal("0")) + quote.freight


def total_units(quote: Quote) -> int:
    """Total units across all quote lines."""
    return sum(line.quantity for line in quote.lines)


def landed_per_unit(quote: Quote) -> Decimal:
    """Landed cost per unit, to the cent."""
    return (landed_cost(quote) / total_units(quote)).quantize(CENT, ROUND_HALF_UP)


def margin_at_price(landed: Decimal, price: Decimal) -> Decimal:
    """Margin percent at a bid price, e.g. 13.64 for 13.64%."""
    if price <= 0:
        raise ValueError(f"Bid price must be positive: {price}")
    return ((price - landed) / price * 100).quantize(CENT, ROUND_HALF_UP)


def lowest_safe_per_unit(landed_unit: Decimal, target_margin: Decimal) -> Decimal:
    """Lowest per-unit bid holding the margin floor; rounds UP to the cent."""
    if not Decimal("0") <= target_margin < 1:
        raise ValueError(f"Target margin must be in [0, 1): {target_margin}")
    return (landed_unit / (1 - target_margin)).quantize(CENT, ROUND_CEILING)


def lowest_safe_bid(quote: Quote, target_margin: Decimal) -> tuple[Decimal, Decimal]:
    """(per-unit, total) lowest safe bid for the quote's units."""
    per_unit = lowest_safe_per_unit(landed_per_unit(quote), target_margin)
    return per_unit, per_unit * total_units(quote)


def deposit_due(quote_total: Decimal, deposit_fraction: Decimal) -> Decimal:
    """Cash due with the PO; Net-30 quotes pass a zero fraction."""
    if not Decimal("0") <= deposit_fraction <= 1:
        raise ValueError(f"Deposit fraction must be in [0, 1]: {deposit_fraction}")
    return (quote_total * deposit_fraction).quantize(CENT, ROUND_HALF_UP)


def cash_exposure(quote: Quote) -> Decimal:
    """Max cash tied up before the customer pays: the full landed cost."""
    return landed_cost(quote)

"""Split arithmetic. Pure Decimal functions with no I/O."""

from decimal import Decimal

SATANG = Decimal("0.01")


def allocate_equal(amount: Decimal, members: list[str]) -> list[tuple[str, Decimal]]:
    """Split amount equally, giving remainder satang one at a time in list order."""
    total_satang = int(amount / SATANG)
    base, remainder = divmod(total_satang, len(members))
    return [
        (member, (base + (1 if index < remainder else 0)) * SATANG)
        for index, member in enumerate(members)
    ]


def check_exact(
    amount: Decimal, shares: list[tuple[str, Decimal]]
) -> list[tuple[str, Decimal]] | None:
    """Return the shares unchanged if they sum exactly to amount, otherwise None."""
    if sum(share for _, share in shares) != amount:
        return None
    return shares

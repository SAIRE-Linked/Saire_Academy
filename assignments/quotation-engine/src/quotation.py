"""SAIRE Academy quotation calculation starter — fill in the TODOs.

Monetary amounts must be Decimal values; do not use binary floats.
"""

from decimal import Decimal


def calculate_subtotal(package_price: Decimal, service_charge: Decimal) -> Decimal:
    """Return the package price plus service charges, rounded to cents.

    Raise ValueError for negative amounts or non-Decimal inputs.
    """
    # TODO: Validate package_price and service_charge.
    # TODO: Add them and round with ROUND_HALF_UP.
    raise NotImplementedError("Implement calculate_subtotal")


def calculate_discount(subtotal: Decimal, discount_percent: Decimal) -> Decimal:
    """Return the discount amount, rounded to cents.

    Percentage must be between zero and one hundred inclusive.
    Raise ValueError for negative subtotal or non-Decimal inputs.
    """
    # TODO: Validate all inputs.
    # TODO: Convert percent to a fraction and calculate the discount.
    raise NotImplementedError("Implement calculate_discount")


def calculate_final_total(package_price: Decimal, service_charge: Decimal,
                          discount_percent: Decimal) -> Decimal:
    """Return total after the discount, rounded to cents.

    Reuse the earlier functions instead of repeating their logic.
    """
    # TODO: Call calculate_subtotal and calculate_discount.
    # TODO: Subtract the discount and return the result.
    raise NotImplementedError("Implement calculate_final_total")

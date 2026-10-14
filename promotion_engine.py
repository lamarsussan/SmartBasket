from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models import Promotion


@dataclass
class PromotionResult:
    supported: bool
    kind: str

    required_qty: Optional[float] = None
    promotion_total: Optional[float] = None
    unit_price: Optional[float] = None

    description: str = ""


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def is_active(promotion, now=None):
    if now is None:
        now = datetime.now()

    start = parse_datetime(
        promotion.start_date
    )

    end = parse_datetime(
        promotion.end_date
    )

    if start and now < start:
        return False

    if end and now > end:
        return False

    return True


def is_conditional_shufersal_promotion(
    promotion,
):
    """
    Promotions that appear to require a coupon,
    membership program, special payment method,
    or Shufersal credit card.

    We do not apply these automatically.
    """

    if promotion.chain != "Shufersal":
        return False

    if promotion.reward_type in {
        "2",
        "12",
    }:
        return True

    description = (
        promotion.description
        or ""
    ).lower()

    conditional_words = [
        "קופון",
        "תו זהב",
        "sbox",
        "כ.אשראי",
        "כרטיס אשראי",
        "מועדון",
    ]

    return any(
        word in description
        for word in conditional_words
    )


def interpret_promotion(
    promotion: Promotion,
):
    if not is_active(promotion):
        return PromotionResult(
            supported=False,
            kind="inactive",
            description=promotion.description,
        )

    if is_conditional_shufersal_promotion(
        promotion
    ):
        return PromotionResult(
            supported=False,
            kind="conditional",
            description=promotion.description,
        )

    min_qty = promotion.min_qty
    discounted_price = (
        promotion.discounted_price
    )

    if (
        min_qty is None
        or discounted_price is None
    ):
        return PromotionResult(
            supported=False,
            kind="unknown",
            description=promotion.description,
        )

    # Regular discounted unit price.
    #
    # Example:
    # regular price 19.90
    # promotion price 14.90
    if min_qty <= 1:
        return PromotionResult(
            supported=True,
            kind="unit_price",
            required_qty=1,
            unit_price=discounted_price,
            description=promotion.description,
        )

    # Multi-buy promotion.
    #
    # Example:
    # 2 units for 9.00
    # 3 units for 110.00
    if (
        min_qty > 1
        and promotion.reward_type == "10"
    ):
        return PromotionResult(
            supported=True,
            kind="bundle_price",
            required_qty=min_qty,
            promotion_total=discounted_price,
            description=promotion.description,
        )

    return PromotionResult(
        supported=False,
        kind="unsupported",
        description=promotion.description,
    )


def calculate_price_with_promotion(
    regular_unit_price,
    requested_qty,
    promotion: Promotion,
):
    interpreted = interpret_promotion(
        promotion
    )

    regular_total = (
        regular_unit_price
        * requested_qty
    )

    if not interpreted.supported:
        return {
            "used_promotion": False,
            "total": regular_total,
            "promotion": interpreted,
        }

    if interpreted.kind == "unit_price":
        promo_total = (
            interpreted.unit_price
            * requested_qty
        )

        return {
            "used_promotion": (
                promo_total
                < regular_total
            ),
            "total": min(
                promo_total,
                regular_total,
            ),
            "promotion": interpreted,
        }

    if interpreted.kind == "bundle_price":
        bundle_qty = int(
            interpreted.required_qty
        )

        if requested_qty < bundle_qty:
            return {
                "used_promotion": False,
                "total": regular_total,
                "promotion": interpreted,
            }

        full_bundles = (
            requested_qty
            // bundle_qty
        )

        remaining_units = (
            requested_qty
            % bundle_qty
        )

        promo_total = (
            full_bundles
            * interpreted.promotion_total
        )

        promo_total += (
            remaining_units
            * regular_unit_price
        )

        return {
            "used_promotion": (
                promo_total
                < regular_total
            ),
            "total": min(
                promo_total,
                regular_total,
            ),
            "promotion": interpreted,
        }

    return {
        "used_promotion": False,
        "total": regular_total,
        "promotion": interpreted,
    }
import gzip
import requests
import xml.etree.ElementTree as ET

from models import Promotion

from providers.shufersal import (
    find_pricefull_file,
)


def safe_float(value):
    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def derive_promofull_from_pricefull(
    store_id,
):
    """
    Shufersal publishes PriceFull and PromoFull
    for the same store using the same naming
    structure.

    Instead of querying the slow promotion
    listing endpoint, first find PriceFull
    and derive the matching PromoFull URL.
    """

    price_file = find_pricefull_file(
        store_id
    )

    price_filename = (
        price_file["filename"]
    )

    price_url = price_file["url"]

    if "PriceFull" not in price_filename:
        raise RuntimeError(
            "Unexpected Shufersal "
            "PriceFull filename"
        )

    promo_filename = (
        price_filename.replace(
            "PriceFull",
            "PromoFull",
            1,
        )
    )

    promo_url = price_url.replace(
        price_filename,
        promo_filename,
    )

    print(
        "Derived Shufersal PromoFull:",
        promo_filename,
    )

    return {
        "filename": promo_filename,
        "url": promo_url,
        "store_id": str(
            store_id
        ).zfill(3),
    }


def download_xml(url):
    response = requests.get(
        url,
        timeout=60,
    )

    response.raise_for_status()

    content = response.content

    if content[:2] == b"\x1f\x8b":
        return gzip.decompress(
            content
        )

    return content


def load_promotions(
    store_id="001",
):
    store_id = str(
        store_id
    ).zfill(3)

    print(
        f"Loading Shufersal promotions "
        f"for store {store_id}..."
    )

    file_info = (
        derive_promofull_from_pricefull(
            store_id
        )
    )

    print(
        "Downloading Shufersal "
        "promotions:",
        file_info["filename"],
    )

    try:
        xml_bytes = download_xml(
            file_info["url"]
        )

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not download derived "
            f"Shufersal PromoFull for "
            f"store {store_id}: "
            f"{file_info['filename']}"
        ) from error

    try:
        root = ET.fromstring(
            xml_bytes
        )

    except ET.ParseError as error:
        raise RuntimeError(
            f"Invalid Shufersal "
            f"PromoFull XML for "
            f"store {store_id}"
        ) from error

    promotions = []

    for promotion_node in (
        root.findall(
            ".//Promotion"
        )
    ):
        promotion_id = (
            promotion_node.findtext(
                "PromotionID"
            )
            or ""
        )

        description = (
            promotion_node.findtext(
                "PromotionDescription"
            )
            or ""
        )

        start_date = (
            promotion_node.findtext(
                "PromotionStartDateTime"
            )
        )

        end_date = (
            promotion_node.findtext(
                "PromotionEndDateTime"
            )
        )

        for group in (
            promotion_node.findall(
                ".//Group"
            )
        ):
            min_purchase_amount = (
                safe_float(
                    group.findtext(
                        "MinPurchaseAmount"
                    )
                )
            )

            for item in (
                group.findall(
                    ".//PromotionItem"
                )
            ):
                item_code = (
                    item.findtext(
                        "ItemCode"
                    )
                )

                if not item_code:
                    continue

                promotions.append(
                    Promotion(
                        chain="Shufersal",
                        store_id=store_id,
                        promotion_id=(
                            promotion_id
                        ),
                        description=(
                            description
                        ),
                        item_code=(
                            item_code
                        ),
                        min_qty=safe_float(
                            item.findtext(
                                "MinQty"
                            )
                        ),
                        discounted_price=(
                            safe_float(
                                item.findtext(
                                    "DiscountedPrice"
                                )
                            )
                        ),
                        discount_rate=(
                            safe_float(
                                item.findtext(
                                    "DiscountRate"
                                )
                            )
                        ),
                        min_purchase_amount=(
                            min_purchase_amount
                        ),
                        reward_type=(
                            item.findtext(
                                "RewardType"
                            )
                        ),
                        start_date=(
                            start_date
                        ),
                        end_date=(
                            end_date
                        ),
                    )
                )

    print(
        f"Shufersal promotions "
        f"store {store_id}: "
        f"{len(promotions)}"
    )

    return promotions


if __name__ == "__main__":
    promotions = load_promotions(
        "344"
    )

    print(
        "Promotions loaded:",
        len(promotions),
    )

    for promotion in promotions[:5]:
        print(
            promotion
        )
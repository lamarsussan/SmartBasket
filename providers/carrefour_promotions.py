import gzip
import json
import re
import requests
import xml.etree.ElementTree as ET

from models import Promotion


BASE_URL = "https://prices.carrefour.co.il/"


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


def get_page_data():
    response = requests.get(
        BASE_URL,
        timeout=30,
    )
    response.raise_for_status()

    html = response.text

    path_match = re.search(
        r'const\s+path\s*=\s*["\']([^"\']+)["\']',
        html,
    )

    if not path_match:
        raise RuntimeError(
            "Could not find Carrefour data path"
        )

    files_match = re.search(
        r"const files = (\[.*?\]);",
        html,
        re.DOTALL,
    )

    if not files_match:
        raise RuntimeError(
            "Could not find Carrefour files list"
        )

    return (
        path_match.group(1),
        json.loads(
            files_match.group(1)
        ),
    )


def find_promofull_file(
    files,
    store_id,
):
    candidates = []

    for file_info in files:
        filename = file_info["name"]

        if not filename.startswith(
            "PromoFull"
        ):
            continue

        if not filename.endswith(".gz"):
            continue

        parts = filename.split("-")

        if len(parts) < 3:
            continue

        if parts[2] != store_id:
            continue

        candidates.append(
            filename
        )

    if not candidates:
        raise RuntimeError(
            f"No Carrefour PromoFull found "
            f"for store {store_id}"
        )

    candidates.sort()

    return candidates[-1]


def load_promotions(
    store_id="002",
):
    store_id = str(store_id).zfill(3)

    path, files = get_page_data()

    filename = find_promofull_file(
        files,
        store_id,
    )

    url = (
        f"{BASE_URL}"
        f"{path}/"
        f"{filename}"
    )

    print(
        f"Downloading Carrefour promotions "
        f"for store {store_id}: "
        f"{filename}"
    )

    response = requests.get(
        url,
        timeout=60,
    )
    response.raise_for_status()

    xml_bytes = gzip.decompress(
        response.content
    )

    root = ET.fromstring(
        xml_bytes
    )

    promotions = []

    for promotion_node in root.findall(
        ".//Promotion"
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

            for item in group.findall(
                ".//PromotionItem"
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
                        chain="Carrefour",
                        store_id=store_id,
                        promotion_id=promotion_id,
                        description=description,
                        item_code=item_code,
                        min_qty=safe_float(
                            item.findtext(
                                "MinQty"
                            )
                        ),
                        discounted_price=safe_float(
                            item.findtext(
                                "DiscountedPrice"
                            )
                        ),
                        discount_rate=safe_float(
                            item.findtext(
                                "DiscountRate"
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
                        start_date=start_date,
                        end_date=end_date,
                    )
                )

    print(
        f"Carrefour promotions "
        f"store {store_id}: "
        f"{len(promotions)}"
    )

    return promotions


if __name__ == "__main__":
    promotions = load_promotions(
        "002"
    )

    print(
        "Promotions loaded:",
        len(promotions),
    )
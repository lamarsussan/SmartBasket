import gzip
import re
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from models import Promotion


BASE_URL = (
    "https://shop.hazi-hinam.co.il/Prices"
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


def get_page_url(page):
    if page == 1:
        return BASE_URL

    return (
        f"{BASE_URL}"
        f"?d=&f=&p={page}&s=&t="
    )


def extract_promofull_filename(
    text,
):
    match = re.search(
        r"(PromoFull[^\s]+\.gz)",
        text,
    )

    if match:
        return match.group(1)

    return None


def find_promofull_file(
    store_id,
):
    store_id = str(
        store_id
    ).zfill(3)

    print(
        f"Searching Hazi Hinam "
        f"PromoFull for store "
        f"{store_id}..."
    )

    candidates = []

    for page in range(
        1,
        8,
    ):
        response = requests.get(
            get_page_url(page),
            timeout=30,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for row in soup.find_all(
            "tr"
        ):
            row_text = row.get_text(
                " ",
                strip=True,
            )

            filename = (
                extract_promofull_filename(
                    row_text
                )
            )

            if filename is None:
                continue

            parts = filename.split(
                "-"
            )

            if len(parts) < 3:
                continue

            if parts[2] != store_id:
                continue

            link = row.find(
                "a",
                href=True,
            )

            if link is None:
                continue

            candidates.append(
                {
                    "filename": filename,
                    "url": link["href"],
                }
            )

    if not candidates:
        raise RuntimeError(
            f"Could not find Hazi Hinam "
            f"PromoFull for store "
            f"{store_id}"
        )

    candidates.sort(
        key=lambda item: (
            item["filename"]
        )
    )

    return candidates[-1]


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
    store_id="204",
):
    store_id = str(
        store_id
    ).zfill(3)

    file_info = find_promofull_file(
        store_id
    )

    print(
        f"Downloading Hazi Hinam "
        f"promotions store "
        f"{store_id}: "
        f"{file_info['filename']}"
    )

    root = ET.fromstring(
        download_xml(
            file_info["url"]
        )
    )

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
                        chain="Hazi Hinam",
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
        f"Hazi Hinam promotions "
        f"store {store_id}: "
        f"{len(promotions)}"
    )

    return promotions


if __name__ == "__main__":
    promotions = load_promotions(
        "204"
    )

    print(
        "Promotions loaded:",
        len(promotions),
    )
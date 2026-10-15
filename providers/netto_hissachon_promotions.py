import gzip
import requests
import xml.etree.ElementTree as ET

from models import Promotion


BASE_URL = "https://supersapir.binaprojects.com/"
FILES_URL = BASE_URL + "MainIO_Hok.aspx"

CHAIN_ID = "7290058156016"


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


def find_promofull_file(
    store_id,
):
    store_id = str(
        store_id
    ).zfill(3)

    params = {
        "_": CHAIN_ID,
        "wReshet": "הכל",
        "WFileType": "5",
        "WDate": "",
        "WStore": store_id,
    }

    response = requests.get(
        FILES_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    files = response.json()

    candidates = []

    for file_info in files:

        filename = file_info.get(
            "FileNm",
            "",
        )

        if not filename.startswith(
            "PromoFull"
        ):
            continue

        if not filename.lower().endswith(
            ".gz"
        ):
            continue

        candidates.append(
            filename
        )

    if not candidates:
        raise RuntimeError(
            f"No Netto Hissachon PromoFull "
            f"found for store {store_id}"
        )

    candidates.sort()

    return candidates[-1]


def get_download_url(
    filename,
):
    url = (
        BASE_URL
        + "Download.aspx?FileNm="
        + filename
    )

    response = requests.get(
        url,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise RuntimeError(
            "Could not get Netto Hissachon "
            "promotion download URL"
        )

    real_url = data[0].get(
        "SPath"
    )

    if not real_url:
        raise RuntimeError(
            "Netto Hissachon promotion "
            "download URL is missing"
        )

    return real_url


def load_promotions(
    store_id="043",
):
    store_id = str(
        store_id
    ).zfill(3)

    filename = find_promofull_file(
        store_id
    )

    print(
        f"Downloading Netto Hissachon "
        f"promotions store {store_id}: "
        f"{filename}"
    )

    download_url = get_download_url(
        filename
    )

    response = requests.get(
        download_url,
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

        for group in promotion_node.findall(
            ".//Group"
        ):

            min_purchase_amount = safe_float(
                group.findtext(
                    "MinPurchaseAmount"
                )
            )

            for item in group.findall(
                ".//PromotionItem"
            ):

                item_code = item.findtext(
                    "ItemCode"
                )

                if not item_code:
                    continue

                promotions.append(
                    Promotion(
                        chain="Netto Hissachon",
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
        f"Netto Hissachon promotions "
        f"store {store_id}: "
        f"{len(promotions)}"
    )

    return promotions


if __name__ == "__main__":

    promotions = load_promotions(
        "043"
    )

    print(
        "Promotions loaded:",
        len(promotions),
    )
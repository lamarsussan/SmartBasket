import gzip
import re
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from models import Product


BASE_URL = (
    "https://shop.hazi-hinam.co.il/Prices"
)


def get_page_url(page):
    if page == 1:
        return BASE_URL

    return (
        f"{BASE_URL}"
        f"?d=&f=&p={page}&s=&t="
    )


def extract_pricefull_filename(
    text,
):
    match = re.search(
        r"(PriceFull[^\s]+\.gz)",
        text,
    )

    if match:
        return match.group(1)

    return None


def find_pricefull_file(
    store_id,
):
    store_id = str(
        store_id
    ).zfill(3)

    print(
        f"Searching Hazi Hinam "
        f"PriceFull for store "
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
                extract_pricefull_filename(
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
                    "url": urljoin(
                        BASE_URL,
                        link["href"],
                    ),
                }
            )

    if not candidates:
        raise RuntimeError(
            f"No Hazi Hinam "
            f"PriceFull found for "
            f"store {store_id}"
        )

    candidates.sort(
        key=lambda item: (
            item["filename"]
        )
    )

    return candidates[-1]


def load_products(
    store_id="204",
):
    store_id = str(
        store_id
    ).zfill(3)

    file_info = find_pricefull_file(
        store_id
    )

    print(
        f"Downloading Hazi Hinam "
        f"store {store_id}: "
        f"{file_info['filename']}"
    )

    response = requests.get(
        file_info["url"],
        timeout=60,
    )

    response.raise_for_status()

    content = response.content

    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(
            content
        )

    root = ET.fromstring(
        content
    )

    products = []

    for item in root.findall(
        ".//Item"
    ):
        barcode = item.findtext(
            "ItemCode"
        )

        name = item.findtext(
            "ItemName"
        )

        price_text = item.findtext(
            "ItemPrice"
        )

        if (
            not barcode
            or not name
            or not price_text
        ):
            continue

        try:
            price = float(
                price_text
            )
        except ValueError:
            continue

        quantity = None

        quantity_text = (
            item.findtext(
                "Quantity"
            )
        )

        if quantity_text:
            try:
                quantity = float(
                    quantity_text
                )
            except ValueError:
                pass

        products.append(
            Product(
                chain="Hazi Hinam",
                store_id=store_id,
                store_name=(
                    f"Hazi Hinam store "
                    f"{store_id}"
                ),
                barcode=barcode,
                name=name,
                price=price,
                manufacturer=(
                    item.findtext(
                        "ManufactureName"
                    )
                ),
                quantity=quantity,
                unit=item.findtext(
                    "UnitQty"
                ),
            )
        )

    print(
        f"Hazi Hinam store "
        f"{store_id}: "
        f"{len(products)} products"
    )

    return products


if __name__ == "__main__":
    products = load_products(
        "204"
    )

    print(
        "Products loaded:",
        len(products),
    )
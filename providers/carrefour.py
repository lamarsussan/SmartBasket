import gzip
import json
import re
import requests
import xml.etree.ElementTree as ET

from models import Product


BASE_URL = "https://prices.carrefour.co.il/"


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

    path = path_match.group(1)
    files = json.loads(
        files_match.group(1)
    )

    return path, files


def find_pricefull_file(
    files,
    store_id,
):
    candidates = []

    for file_info in files:
        filename = file_info["name"]

        if not filename.startswith(
            "PriceFull"
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
            f"No Carrefour PriceFull found "
            f"for store {store_id}"
        )

    candidates.sort()

    return candidates[-1]


def load_products(
    store_id="002",
):
    store_id = str(store_id).zfill(3)

    path, files = get_page_data()

    filename = find_pricefull_file(
        files,
        store_id,
    )

    url = (
        f"{BASE_URL}"
        f"{path}/"
        f"{filename}"
    )

    print(
        f"Downloading Carrefour store "
        f"{store_id}: {filename}"
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

        quantity_text = item.findtext(
            "Quantity"
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
                chain="Carrefour",
                store_id=store_id,
                store_name=(
                    f"Carrefour store "
                    f"{store_id}"
                ),
                barcode=barcode,
                name=name,
                price=price,
                manufacturer=item.findtext(
                    "ManufactureName"
                ),
                quantity=quantity,
                unit=item.findtext(
                    "UnitQty"
                ),
            )
        )

    print(
        f"Carrefour store {store_id}: "
        f"{len(products)} products"
    )

    return products


if __name__ == "__main__":
    products = load_products(
        "002"
    )

    print(
        "Products loaded:",
        len(products),
    )
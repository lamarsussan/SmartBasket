import gzip
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from models import Product


BASE_URL = "https://prices.shufersal.co.il/"

TABLE_URL = (
    "https://prices.shufersal.co.il/"
    "FileObject/UpdateCategory"
)


# Stores PriceFull metadata already found
# during this server run.
PRICE_FILE_CACHE = {}


def get_store_page(
    store_id,
    page=1,
):
    params = {
        "catID": 0,
        "page": page,
        "sort": "Category",
        "sortdir": "ASC",
        "storeId": int(store_id),
    }

    try:
        response = requests.get(
            TABLE_URL,
            params=params,
            timeout=4,
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as error:

        print(
            f"Shufersal request failed: "
            f"{error}"
        )

        raise RuntimeError(
            f"Could not load Shufersal "
            f"file list for store {store_id}"
        ) from error


def extract_filename(
    row_text,
    prefix,
):
    for part in row_text.split():
        if part.startswith(
            prefix
        ):
            return part

    return None


def find_pricefull_file(
    store_id,
):
    store_id = str(
        store_id
    ).zfill(3)

    # First check RAM.
    if store_id in PRICE_FILE_CACHE:

        print(
            f"Memory cache: Shufersal "
            f"PriceFull info store "
            f"{store_id}"
        )

        return PRICE_FILE_CACHE[
            store_id
        ]

    print(
        f"Searching Shufersal PriceFull "
        f"directly for store {store_id}..."
    )

    for page in range(
        1,
        5,
    ):

        print(
            f"Checking filtered page "
            f"{page}..."
        )

        html = get_store_page(
            store_id,
            page,
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        candidates = []

        for row in soup.find_all(
            "tr"
        ):
            row_text = row.get_text(
                " ",
                strip=True,
            )

            if (
                "pricefull"
                not in row_text.lower()
            ):
                continue

            filename = (
                extract_filename(
                    row_text,
                    "PriceFull",
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
                    "filename": (
                        filename
                    ),
                    "url": urljoin(
                        BASE_URL,
                        link["href"],
                    ),
                    "store_id": (
                        store_id
                    ),
                }
            )

        if candidates:
            candidates.sort(
                key=lambda item: (
                    item["filename"]
                )
            )

            selected = (
                candidates[-1]
            )

            PRICE_FILE_CACHE[
                store_id
            ] = selected

            print(
                "Found Shufersal "
                "PriceFull:",
                selected[
                    "filename"
                ],
            )

            return selected

    raise RuntimeError(
        f"Could not find Shufersal "
        f"PriceFull for store "
        f"{store_id}"
    )


def download_xml(url):
    response = requests.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    content = response.content

    if (
        content[:2]
        == b"\x1f\x8b"
    ):
        return gzip.decompress(
            content
        )

    return content


def load_products(
    store_id="001",
):
    store_id = str(
        store_id
    ).zfill(3)

    file_info = (
        find_pricefull_file(
            store_id
        )
    )

    print(
        f"Downloading Shufersal "
        f"store {store_id}: "
        f"{file_info['filename']}"
    )

    xml_bytes = download_xml(
        file_info["url"]
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
                chain="Shufersal",
                store_id=store_id,
                store_name=(
                    f"Shufersal store "
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
        f"Shufersal store "
        f"{store_id}: "
        f"{len(products)} products"
    )

    return products


if __name__ == "__main__":
    products = load_products(
        "344"
    )

    print(
        "Products loaded:",
        len(products),
    )
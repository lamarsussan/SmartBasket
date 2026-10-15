import gzip
import requests
import xml.etree.ElementTree as ET

from models import Product


BASE_URL = "https://supersapir.binaprojects.com/"
FILES_URL = BASE_URL + "MainIO_Hok.aspx"

CHAIN_ID = "7290058156016"


def find_pricefull_file(store_id):
    """
    Find the newest PriceFull file for a Super Sapir / Netto store.
    """

    store_id = str(store_id).zfill(3)

    params = {
        "_": CHAIN_ID,
        "wReshet": "הכל",
        "WFileType": "4",
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
            "PriceFull"
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
            f"No Netto Hissachon PriceFull "
            f"found for store {store_id}"
        )

    candidates.sort()

    return candidates[-1]


def get_download_url(filename):
    """
    Bina first returns the real file URL as JSON.
    """

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
            "download URL"
        )

    real_url = data[0].get(
        "SPath"
    )

    if not real_url:
        raise RuntimeError(
            "Netto Hissachon download URL "
            "is missing"
        )

    return real_url


def load_products(
    store_id="043",
):
    """
    Download and parse the PriceFull file
    for one Netto Hissachon store.
    """

    store_id = str(
        store_id
    ).zfill(3)

    filename = find_pricefull_file(
        store_id
    )

    print(
        f"Downloading Netto Hissachon "
        f"store {store_id}: {filename}"
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
                chain="Netto Hissachon",
                store_id=store_id,
                store_name=(
                    "Netto Hissachon Maalot"
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
        f"Netto Hissachon store "
        f"{store_id}: "
        f"{len(products)} products"
    )

    return products


if __name__ == "__main__":
    products = load_products(
        "043"
    )

    print(
        "Products loaded:",
        len(products),
    )

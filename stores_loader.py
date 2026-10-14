import gzip
import json
import re
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from models import Store
from data_cache import get_or_load
from localities import load_localities


SHUFERSAL_URL = "https://prices.shufersal.co.il/"

CARREFOUR_STORES_URL = (
    "https://shilut.carrefour.co.il/"
)

HAZI_URL = (
    "https://shop.hazi-hinam.co.il/Prices"
)


# ==================================================
# GENERAL HELPERS
# ==================================================

def clean_tag(tag):
    if "}" in tag:
        tag = tag.split(
            "}",
            1,
        )[1]

    return tag.lower()


def child_text(
    node,
    *possible_names,
):
    wanted = {
        name.lower()
        for name in possible_names
    }

    for child in list(node):
        if clean_tag(child.tag) in wanted:
            if child.text:
                return child.text.strip()

    return None


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


def parse_stores_xml(
    xml_bytes,
    chain_name,
    locality_names,
):
    root = ET.fromstring(
        xml_bytes
    )

    stores = []

    for node in root.iter():

        if clean_tag(
            node.tag
        ) != "store":
            continue


        store_id = child_text(
            node,
            "STOREID",
            "StoreID",
            "StoreId",
        )

        if not store_id:
            continue


        name = (
            child_text(
                node,
                "STORENAME",
                "StoreName",
            )
            or ""
        )


        city_code = child_text(
            node,
            "CITY",
            "City",
        )

        city = ""

        if city_code:

            city_code = str(
                city_code
            ).strip()

            city = locality_names.get(
                city_code,
                "",
            )


        address = (
            child_text(
                node,
                "ADDRESS",
                "Address",
            )
            or ""
        )


        subchain_id = child_text(
            node,
            "SUBCHAINID",
            "SubChainID",
            "SubChainId",
        )


        subchain_name = child_text(
            node,
            "SUBCHAINNAME",
            "SubChainName",
        )


        zipcode = child_text(
            node,
            "ZIPCODE",
            "ZipCode",
        )


        stores.append(
            Store(
                chain=chain_name,
                store_id=str(
                    store_id
                ).zfill(3),
                name=name,
                city=city,
                city_code=city_code,
                address=address,
                subchain_id=subchain_id,
                subchain_name=subchain_name,
                zipcode=zipcode,
            )
        )

    return stores


# ==================================================
# SHUFERSAL
# ==================================================

def load_shufersal_stores_raw():

    print(
        "Finding Shufersal Stores file..."
    )

    locality_names = (
        load_localities()
    )


    response = requests.get(
        SHUFERSAL_URL,
        params={
            "sort": "Branch",
            "sortdir": "DESC",
        },
        timeout=30,
    )

    response.raise_for_status()


    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )


    for row in soup.find_all("tr"):

        text = row.get_text(
            " ",
            strip=True,
        )

        if "stores" not in text.lower():
            continue


        link = row.find(
            "a",
            href=True,
        )

        if link is None:
            continue


        xml_bytes = download_xml(
            urljoin(
                SHUFERSAL_URL,
                link["href"],
            )
        )


        stores = parse_stores_xml(
            xml_bytes,
            "Shufersal",
            locality_names,
        )


        if stores:

            print(
                "Found Shufersal Stores file."
            )

            return stores


    raise RuntimeError(
        "Could not find Shufersal Stores file."
    )


# ==================================================
# CARREFOUR
# ==================================================

def load_carrefour_stores_raw():

    print(
        "Finding Carrefour Stores file..."
    )

    locality_names = (
        load_localities()
    )


    response = requests.get(
        CARREFOUR_STORES_URL,
        timeout=30,
    )

    response.raise_for_status()

    html = response.text


    path_match = re.search(
        r'const\s+path\s*=\s*["\']'
        r'([^"\']+)["\']',
        html,
    )


    files_match = re.search(
        r"const\s+files\s*=\s*"
        r"(\[.*?\]);",
        html,
        re.DOTALL,
    )


    if not files_match:
        raise RuntimeError(
            "Could not read Carrefour "
            "Stores file list."
        )


    files = json.loads(
        files_match.group(1)
    )


    candidates = []


    for file_info in files:

        filename = file_info.get(
            "name",
            "",
        )

        if not filename.lower().startswith(
            "stores"
        ):
            continue

        if not (
            filename.lower().endswith(
                ".xml"
            )
            or filename.lower().endswith(
                ".gz"
            )
        ):
            continue

        candidates.append(
            filename
        )


    if not candidates:
        raise RuntimeError(
            "Could not find Carrefour Stores file."
        )


    candidates.sort()

    filename = candidates[-1]


    print(
        "Found Carrefour Stores:",
        filename,
    )


    candidate_urls = []


    if path_match:

        path = path_match.group(1)

        candidate_urls.append(
            f"{CARREFOUR_STORES_URL}"
            f"{path}/{filename}"
        )


    candidate_urls.append(
        urljoin(
            CARREFOUR_STORES_URL,
            filename,
        )
    )


    last_error = None


    for url in candidate_urls:

        try:

            xml_bytes = download_xml(
                url
            )


            stores = parse_stores_xml(
                xml_bytes,
                "Carrefour",
                locality_names,
            )


            if stores:
                return stores


        except (
            requests.RequestException,
            ET.ParseError,
        ) as error:

            last_error = error


    raise RuntimeError(
        "Found Carrefour Stores file, "
        "but could not parse it."
    ) from last_error


# ==================================================
# HAZI HINAM
# ==================================================

def hazi_page_url(page):

    if page == 1:
        return HAZI_URL

    return (
        f"{HAZI_URL}"
        f"?d=&f=&p={page}&s=&t="
    )


def load_hazi_hinam_stores_raw():

    print(
        "Finding Hazi Hinam Stores file..."
    )

    locality_names = (
        load_localities()
    )

    candidates = []


    for page in range(1, 8):

        print(
            f"Checking Hazi Hinam page "
            f"{page}...",
            end="\r",
            flush=True,
        )


        response = requests.get(
            hazi_page_url(page),
            timeout=30,
        )

        response.raise_for_status()


        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )


        for row in soup.find_all("tr"):

            text = row.get_text(
                " ",
                strip=True,
            )


            match = re.search(
                r"(Stores[^\s]+"
                r"\.(?:gz|xml))",
                text,
                re.IGNORECASE,
            )


            if not match:
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
                        match.group(1)
                    ),
                    "url": link["href"],
                }
            )


    print()


    if not candidates:
        raise RuntimeError(
            "Could not find Hazi Hinam "
            "Stores file."
        )


    candidates.sort(
        key=lambda item: (
            item["filename"]
        )
    )


    selected = candidates[-1]


    print(
        "Found Hazi Hinam Stores:",
        selected["filename"],
    )


    xml_bytes = download_xml(
        selected["url"]
    )


    stores = parse_stores_xml(
        xml_bytes,
        "Hazi Hinam",
        locality_names,
    )


    if not stores:
        raise RuntimeError(
            "Hazi Hinam Stores file "
            "contained no stores."
        )


    return stores


# ==================================================
# SAFE LOADING
# ==================================================

def safe_load_stores(
    chain_name,
    cache_key,
    loader,
):
    """
    Load one supermarket's store list.

    If the external retailer is unavailable,
    return an empty list instead of crashing
    the whole SmartBasket application.
    """

    try:

        return get_or_load(
            cache_key,
            loader,
            ttl_minutes=1440,
        )


    except Exception as error:

        print()
        print("=" * 60)

        print(
            f"WARNING: {chain_name} "
            f"stores unavailable"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        print(
            "SmartBasket will continue "
            "without this retailer."
        )

        print("=" * 60)
        print()

        return []


# ==================================================
# CACHE
# ==================================================

def load_all_stores():

    # v2 keys deliberately force rebuilding
    # the old cached Store objects that had
    # numeric values in the city field.

    shufersal = safe_load_stores(
        "Shufersal",
        "shufersal_stores_v2",
        load_shufersal_stores_raw,
    )


    carrefour = safe_load_stores(
        "Carrefour",
        "carrefour_stores_v2",
        load_carrefour_stores_raw,
    )


    hazi_hinam = safe_load_stores(
        "Hazi Hinam",
        "hazi_hinam_stores_v2",
        load_hazi_hinam_stores_raw,
    )


    return {
        "Shufersal": shufersal,
        "Carrefour": carrefour,
        "Hazi Hinam": hazi_hinam,
    }


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    all_stores = load_all_stores()


    print(
        "\n"
        + "=" * 70
    )

    print(
        "STORES"
    )

    print(
        "=" * 70
    )


    for chain, stores in (
        all_stores.items()
    ):

        print(
            f"\n{chain}: "
            f"{len(stores)} stores"
        )


        cities = sorted(
            {
                store.city
                for store in stores
                if store.city
            }
        )


        print(
            "Cities:",
            ", ".join(
                cities[:30]
            ),
        )


        print(
            "\nExamples:"
        )


        for store in stores[:5]:

            print(
                f"  {store.store_id}"
                f" | {store.city}"
                f" | {store.name}"
                f" | {store.address}"
                f" | code={store.city_code}"
            )
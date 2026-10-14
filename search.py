import re

from data_cache import get_or_load

from providers.carrefour import (
    load_products as load_carrefour,
)

from providers.shufersal import (
    load_products as load_shufersal,
)

from providers.hazi_hinam import (
    load_products as load_hazi_hinam,
)


def load_all_products():
    print("\nLoading Carrefour...")

    carrefour_products = get_or_load(
        "carrefour_products",
        load_carrefour,
    )

    print("\nLoading Shufersal...")

    shufersal_products = get_or_load(
        "shufersal_products",
        load_shufersal,
    )

    print("\nLoading Hazi Hinam...")

    hazi_hinam_products = get_or_load(
        "hazi_hinam_products",
        load_hazi_hinam,
    )

    return {
        "Carrefour": carrefour_products,
        "Shufersal": shufersal_products,
        "Hazi Hinam": hazi_hinam_products,
    }


def normalize_text(text):
    text = text.lower().strip()

    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*אחוז",
        r"\1%",
        text,
    )

    text = re.sub(
        r"[^0-9a-zA-Zא-ת%]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def calculate_match_score(
    query,
    product_name,
):
    query = normalize_text(query)

    product_name = normalize_text(
        product_name
    )

    if not query or not product_name:
        return 0

    query_tokens = query.split()

    matched_tokens = sum(
        1
        for token in query_tokens
        if token in product_name
    )

    coverage = (
        matched_tokens
        / len(query_tokens)
    )

    if coverage == 1:
        return 100

    return coverage * 70


def build_barcode_index(
    all_products,
):
    index = {}

    for chain, products in (
        all_products.items()
    ):
        for product in products:
            if product.barcode not in index:
                index[
                    product.barcode
                ] = {}

            index[
                product.barcode
            ][chain] = product

    return index


def find_candidates(
    all_products,
    query,
    limit=10,
):
    barcode_index = (
        build_barcode_index(
            all_products
        )
    )

    candidates = {}

    for chain, products in (
        all_products.items()
    ):
        for product in products:

            # Direct barcode search
            if query.strip() == product.barcode:
                score = 1000

            else:
                score = (
                    calculate_match_score(
                        query,
                        product.name,
                    )
                )

            if score < 45:
                continue

            barcode = product.barcode

            chain_products = (
                barcode_index.get(
                    barcode,
                    {},
                )
            )

            chain_count = len(
                chain_products
            )

            current = candidates.get(
                barcode
            )

            candidate = {
                "product": product,
                "score": score,
                "chain": chain,
                "chain_count": chain_count,
                "chain_products": chain_products,
            }

            if current is None:
                candidates[
                    barcode
                ] = candidate

            elif (
                score
                > current["score"]
            ):
                candidates[
                    barcode
                ] = candidate

    results = list(
        candidates.values()
    )

    results.sort(
        key=lambda result: (
            result["score"],
            result["chain_count"],
        ),
        reverse=True,
    )

    return results[:limit]


def compare_barcode(
    all_products,
    barcode,
):
    comparison = {}

    for chain, products in (
        all_products.items()
    ):
        product = None

        for candidate in products:
            if (
                candidate.barcode
                == barcode
            ):
                product = candidate
                break

        comparison[chain] = product

    return comparison
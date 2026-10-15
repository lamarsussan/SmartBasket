from data_cache import get_or_load

from providers.carrefour import (
    load_products as load_carrefour_products,
)

from providers.shufersal import (
    load_products as load_shufersal_products,
)

from providers.hazi_hinam import (
    load_products as load_hazi_products,
)

from providers.carrefour_promotions import (
    load_promotions as load_carrefour_promotions,
)

from providers.shufersal_promotions import (
    load_promotions as load_shufersal_promotions,
)

from providers.hazi_hinam_promotions import (
    load_promotions as load_hazi_promotions,
)


# ==================================================
# IN-MEMORY CACHE
# ==================================================

PRODUCT_MEMORY_CACHE = {}
PROMOTION_MEMORY_CACHE = {}


# Remember failures during the current server run.
#
# This prevents SmartBasket from retrying the same
# unavailable retailer on every user action.
PRODUCT_FAILURE_CACHE = set()
PROMOTION_FAILURE_CACHE = set()


# ==================================================
# CACHE KEY
# ==================================================

def cache_key(
    chain,
    store_id,
):
    return (
        chain,
        str(store_id).zfill(3),
    )


# ==================================================
# SAFE LOADING
# ==================================================

def safe_load(
    description,
    loader,
    default,
):
    """
    Run an external retailer loader safely.

    If the retailer is unavailable, SmartBasket
    prints a warning and continues instead of
    crashing the entire application.
    """

    try:
        return loader()

    except Exception as error:

        print()
        print("=" * 60)

        print(
            f"WARNING: {description} unavailable"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        print(
            "SmartBasket will continue "
            "without this data."
        )

        print("=" * 60)
        print()

        return default


# ==================================================
# ONE STORE - PRODUCTS
# ==================================================

def load_products_for_store(
    chain,
    store_id,
):
    store_id = str(
        store_id
    ).zfill(3)

    key = cache_key(
        chain,
        store_id,
    )


    # ----------------------------------------------
    # Already loaded successfully
    # ----------------------------------------------

    if key in PRODUCT_MEMORY_CACHE:

        print(
            f"Memory cache: "
            f"{chain} products "
            f"store {store_id}"
        )

        return PRODUCT_MEMORY_CACHE[
            key
        ]


    # ----------------------------------------------
    # Failed earlier during this server run
    # ----------------------------------------------

    if key in PRODUCT_FAILURE_CACHE:

        print(
            f"Skipping unavailable "
            f"{chain} products "
            f"store {store_id}"
        )

        return []


    # ----------------------------------------------
    # Carrefour
    # ----------------------------------------------

    if chain == "Carrefour":

        products = safe_load(
            (
                f"Carrefour products "
                f"for store {store_id}"
            ),
            lambda: get_or_load(
                (
                    "carrefour_products_"
                    f"{store_id}"
                ),
                lambda: (
                    load_carrefour_products(
                        store_id
                    )
                ),
            ),
            None,
        )


    # ----------------------------------------------
    # Shufersal
    # ----------------------------------------------

    elif chain == "Shufersal":

        products = safe_load(
            (
                f"Shufersal products "
                f"for store {store_id}"
            ),
            lambda: get_or_load(
                (
                    "shufersal_products_"
                    f"{store_id}"
                ),
                lambda: (
                    load_shufersal_products(
                        store_id
                    )
                ),
            ),
            None,
        )


    # ----------------------------------------------
    # Hazi Hinam
    # ----------------------------------------------

    elif chain == "Hazi Hinam":

        products = safe_load(
            (
                f"Hazi Hinam products "
                f"for store {store_id}"
            ),
            lambda: get_or_load(
                (
                    "hazi_hinam_products_"
                    f"{store_id}"
                ),
                lambda: (
                    load_hazi_products(
                        store_id
                    )
                ),
            ),
            None,
        )


    else:
        return []


    # ----------------------------------------------
    # Loading failed
    # ----------------------------------------------

    if products is None:

        PRODUCT_FAILURE_CACHE.add(
            key
        )

        return []


    # ----------------------------------------------
    # Loading succeeded
    # ----------------------------------------------

    PRODUCT_MEMORY_CACHE[
        key
    ] = products

    return products


# ==================================================
# ONE STORE - PROMOTIONS
# ==================================================

def load_promotions_for_store(
    chain,
    store_id,
):
    store_id = str(
        store_id
    ).zfill(3)

    key = cache_key(
        chain,
        store_id,
    )


    # ----------------------------------------------
    # Already loaded successfully
    # ----------------------------------------------

    if key in PROMOTION_MEMORY_CACHE:

        print(
            f"Memory cache: "
            f"{chain} promotions "
            f"store {store_id}"
        )

        return PROMOTION_MEMORY_CACHE[
            key
        ]


    # ----------------------------------------------
    # Failed earlier during this server run
    # ----------------------------------------------

    if key in PROMOTION_FAILURE_CACHE:

        print(
            f"Skipping unavailable "
            f"{chain} promotions "
            f"store {store_id}"
        )

        return []


    # ----------------------------------------------
    # Carrefour
    # ----------------------------------------------

    if chain == "Carrefour":

        promotions = safe_load(
            (
                f"Carrefour promotions "
                f"for store {store_id}"
            ),
            lambda: get_or_load(
                (
                    "carrefour_promotions_"
                    f"{store_id}"
                ),
                lambda: (
                    load_carrefour_promotions(
                        store_id
                    )
                ),
            ),
            None,
        )


    # ----------------------------------------------
    # Shufersal
    # ----------------------------------------------

    elif chain == "Shufersal":

        promotions = safe_load(
            (
                f"Shufersal promotions "
                f"for store {store_id}"
            ),
            lambda: get_or_load(
                (
                    "shufersal_promotions_"
                    f"{store_id}"
                ),
                lambda: (
                    load_shufersal_promotions(
                        store_id
                    )
                ),
            ),
            None,
        )


    # ----------------------------------------------
    # Hazi Hinam
    # ----------------------------------------------

    elif chain == "Hazi Hinam":

        promotions = safe_load(
            (
                f"Hazi Hinam promotions "
                f"for store {store_id}"
            ),
            lambda: get_or_load(
                (
                    "hazi_hinam_promotions_"
                    f"{store_id}"
                ),
                lambda: (
                    load_hazi_promotions(
                        store_id
                    )
                ),
            ),
            None,
        )


    else:
        return []


    # ----------------------------------------------
    # Loading failed
    # ----------------------------------------------

    if promotions is None:

        PROMOTION_FAILURE_CACHE.add(
            key
        )

        return []


    # ----------------------------------------------
    # Loading succeeded
    # ----------------------------------------------

    PROMOTION_MEMORY_CACHE[
        key
    ] = promotions

    return promotions


# ==================================================
# SELECTED STORES
# ==================================================

def load_products_for_stores(
    selected_stores,
):
    result = {}

    for chain, store_id in (
        selected_stores.items()
    ):

        result[chain] = (
            load_products_for_store(
                chain,
                store_id,
            )
        )

    return result


def load_promotions_for_stores(
    selected_stores,
):
    result = {}

    for chain, store_id in (
        selected_stores.items()
    ):

        result[chain] = (
            load_promotions_for_store(
                chain,
                store_id,
            )
        )

    return result


# ==================================================
# AVAILABILITY STATUS
# ==================================================

def get_unavailable_product_chains(
    selected_stores,
):
    """
    Return selected supermarket chains whose
    product data failed to load during this
    server run.
    """

    unavailable = []

    for chain, store_id in (
        selected_stores.items()
    ):

        key = cache_key(
            chain,
            store_id,
        )

        if key in PRODUCT_FAILURE_CACHE:
            unavailable.append(
                chain
            )

    return unavailable


def get_unavailable_promotion_chains(
    selected_stores,
):
    """
    Return selected supermarket chains whose
    promotion data failed to load during this
    server run.
    """

    unavailable = []

    for chain, store_id in (
        selected_stores.items()
    ):

        key = cache_key(
            chain,
            store_id,
        )

        if key in PROMOTION_FAILURE_CACHE:
            unavailable.append(
                chain
            )

    return unavailable


# ==================================================
# OPTIONAL CACHE RESET
# ==================================================

def clear_memory_cache():

    PRODUCT_MEMORY_CACHE.clear()

    PROMOTION_MEMORY_CACHE.clear()

    PRODUCT_FAILURE_CACHE.clear()

    PROMOTION_FAILURE_CACHE.clear()

    print(
        "SmartBasket memory cache cleared."
    )
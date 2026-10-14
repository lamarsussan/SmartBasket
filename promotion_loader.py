from data_cache import get_or_load

from providers.carrefour_promotions import (
    load_promotions as load_carrefour_promotions,
)

from providers.shufersal_promotions import (
    load_promotions as load_shufersal_promotions,
)

from providers.hazi_hinam_promotions import (
    load_promotions as load_hazi_hinam_promotions,
)


def load_all_promotions():
    print(
        "\nLoading Carrefour promotions..."
    )

    carrefour_promotions = get_or_load(
        "carrefour_promotions",
        lambda: load_carrefour_promotions(
            store_id="002"
        ),
    )

    print(
        "Carrefour promotions loaded:",
        len(carrefour_promotions),
    )

    print(
        "\nLoading Shufersal promotions..."
    )

    shufersal_promotions = get_or_load(
        "shufersal_promotions",
        load_shufersal_promotions,
    )

    print(
        "Shufersal promotions loaded:",
        len(shufersal_promotions),
    )

    print(
        "\nLoading Hazi Hinam promotions..."
    )

    hazi_hinam_promotions = get_or_load(
        "hazi_hinam_promotions",
        load_hazi_hinam_promotions,
    )

    print(
        "Hazi Hinam promotions loaded:",
        len(hazi_hinam_promotions),
    )

    return {
        "Carrefour": carrefour_promotions,
        "Shufersal": shufersal_promotions,
        "Hazi Hinam": hazi_hinam_promotions,
    }
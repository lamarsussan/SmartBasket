from promotion_loader import load_all_promotions

from search import (
    load_all_products,
    find_candidates,
)

from providers.carrefour_promotions import (
    load_promotions as load_carrefour_promotions,
)

from providers.shufersal_promotions import (
    load_promotions as load_shufersal_promotions,
)

from providers.hazi_hinam_promotions import (
    load_promotions as load_hazi_hinam_promotions,
)

from promotion_engine import (
    calculate_price_with_promotion,
    interpret_promotion,
)


def choose_product(all_products, query):
    candidates = find_candidates(
        all_products,
        query,
        limit=7,
    )

    if not candidates:
        print("No matching products found.")
        return None

    print("\nPossible products:")

    for index, result in enumerate(candidates, start=1):
        product = result["product"]

        print("\n" + "-" * 60)
        print(f"{index}. {product.name}")
        print(f"   Barcode: {product.barcode}")
        print(
            f"   Available in "
            f"{result['chain_count']}/{len(all_products)} chains"
        )

        for chain, chain_product in result["chain_products"].items():
            print(
                f"   {chain}: "
                f"₪{chain_product.price:.2f}"
                f" | {chain_product.name}"
            )

    while True:
        choice = input("\nChoose product number: ").strip()

        try:
            index = int(choice) - 1

            if 0 <= index < len(candidates):
                return candidates[index]["product"]

        except ValueError:
            pass

        print("Invalid choice. Try again.")


def read_quantity():
    while True:
        value = input("Quantity: ").strip()

        try:
            quantity = int(value)

            if quantity > 0:
                return quantity

        except ValueError:
            pass

        print("Quantity must be a positive number.")


def build_promotion_index(promotions):
    index = {}

    for promotion in promotions:
        barcode = promotion.item_code

        if barcode not in index:
            index[barcode] = []

        index[barcode].append(promotion)

    return index


def find_quantity_upgrade_offer(
    all_products,
    promotion_indexes,
    barcode,
    requested_quantity,
):
    offers = []

    for chain, promotion_index in promotion_indexes.items():
        promotions = promotion_index.get(
            barcode,
            [],
        )

        chain_product = None

        for product in all_products.get(chain, []):
            if product.barcode == barcode:
                chain_product = product
                break

        if chain_product is None:
            continue

        for promotion in promotions:
            interpreted = interpret_promotion(
                promotion
            )

            if not interpreted.supported:
                continue

            if interpreted.kind != "bundle_price":
                continue

            required_qty = int(
                interpreted.required_qty
            )

            if requested_quantity >= required_qty:
                continue

            regular_required_total = (
                chain_product.price
                * required_qty
            )

            promotion_total = (
                interpreted.promotion_total
            )

            if promotion_total >= regular_required_total:
                continue

            offers.append(
                {
                    "chain": chain,
                    "required_qty": required_qty,
                    "promotion_total": promotion_total,
                    "description": promotion.description,
                }
            )

    if not offers:
        return None

    offers.sort(
        key=lambda offer: (
            offer["required_qty"] - requested_quantity,
            offer["promotion_total"],
        )
    )

    return offers[0]


def ask_about_quantity_upgrade(
    all_products,
    promotion_indexes,
    selected_product,
    requested_quantity,
):
    offer = find_quantity_upgrade_offer(
        all_products,
        promotion_indexes,
        selected_product.barcode,
        requested_quantity,
    )

    if offer is None:
        return requested_quantity

    print("\n" + "=" * 60)
    print("PROMOTION AVAILABLE")

    print(
        f"{offer['chain']} has a promotion:"
    )

    print(
        f"{offer['required_qty']} for "
        f"₪{offer['promotion_total']:.2f}"
    )

    print(
        f"You requested {requested_quantity}."
    )

    while True:
        answer = input(
            f"Buy {offer['required_qty']} instead? "
            "(y/n): "
        ).strip().lower()

        if answer in {"y", "yes"}:
            print(
                f"Quantity updated: "
                f"{requested_quantity} -> "
                f"{offer['required_qty']}"
            )

            return offer["required_qty"]

        if answer in {"n", "no"}:
            return requested_quantity

        print("Please enter y or n.")


def build_basket(
    all_products,
    promotion_indexes,
):
    basket = []

    print("\nAdd products to your basket.")
    print(
        "Press Enter without typing anything "
        "when finished."
    )

    while True:
        query = input("\nProduct: ").strip()

        if not query:
            break

        selected_product = choose_product(
            all_products,
            query,
        )

        if selected_product is None:
            continue

        quantity = read_quantity()

        quantity = ask_about_quantity_upgrade(
            all_products,
            promotion_indexes,
            selected_product,
            quantity,
        )

        basket.append(
            {
                "barcode": selected_product.barcode,
                "name": selected_product.name,
                "quantity": quantity,
            }
        )

        print(
            f"Added: "
            f"{selected_product.name} "
            f"x{quantity}"
        )

    return basket


def find_best_promotion(
    regular_unit_price,
    quantity,
    promotions,
):
    best = None

    for promotion in promotions:
        result = calculate_price_with_promotion(
            regular_unit_price,
            quantity,
            promotion,
        )

        if not result["used_promotion"]:
            continue

        if (
            best is None
            or result["total"] < best["total"]
        ):
            best = {
                "promotion": promotion,
                "total": result["total"],
                "interpreted": result["promotion"],
            }

    return best


def calculate_basket_for_chain(
    chain,
    products,
    basket,
    promotion_index=None,
):
    products_by_barcode = {
        product.barcode: product
        for product in products
    }

    total = 0.0
    found_items = []
    missing_items = []

    for item in basket:
        product = products_by_barcode.get(
            item["barcode"]
        )

        if product is None:
            missing_items.append(item)
            continue

        quantity = item["quantity"]

        regular_total = (
            product.price
            * quantity
        )

        final_total = regular_total
        used_promotion = None

        if promotion_index is not None:
            product_promotions = promotion_index.get(
                product.barcode,
                [],
            )

            best_promotion = find_best_promotion(
                product.price,
                quantity,
                product_promotions,
            )

            if best_promotion is not None:
                final_total = best_promotion["total"]
                used_promotion = best_promotion["promotion"]

        total += final_total

        found_items.append(
            {
                "name": product.name,
                "barcode": product.barcode,
                "quantity": quantity,
                "unit_price": product.price,
                "regular_total": regular_total,
                "total": final_total,
                "promotion": used_promotion,
            }
        )

    return {
        "chain": chain,
        "total": total,
        "found_items": found_items,
        "missing_items": missing_items,
    }


def compare_basket(
    all_products,
    basket,
    promotion_indexes,
):
    results = []

    for chain, products in all_products.items():
        promotion_index = (
            promotion_indexes.get(chain)
        )

        results.append(
            calculate_basket_for_chain(
                chain,
                products,
                basket,
                promotion_index,
            )
        )

    return results


def print_basket_results(
    results,
    basket_size,
):
    print("\n" + "=" * 70)
    print("BASKET COMPARISON")
    print("=" * 70)

    for result in results:
        found_count = len(
            result["found_items"]
        )

        print(f"\n{result['chain']}")
        print("-" * 40)

        print(
            f"Basket coverage: "
            f"{found_count}/{basket_size}"
        )

        for item in result["found_items"]:
            print()

            print(
                f"  {item['name']}"
                f" x{item['quantity']}"
            )

            print(
                f"  Regular total: "
                f"₪{item['regular_total']:.2f}"
            )

            if item["promotion"] is not None:
                promotion = item["promotion"]

                print(
                    f"  PROMOTION: "
                    f"{promotion.description}"
                )

                print(
                    f"  Final price: "
                    f"₪{item['total']:.2f}"
                )

                saving = (
                    item["regular_total"]
                    - item["total"]
                )

                print(
                    f"  Saving: "
                    f"₪{saving:.2f}"
                )

            else:
                print(
                    f"  Final price: "
                    f"₪{item['total']:.2f}"
                )

        if result["missing_items"]:
            print("\nMissing:")

            for item in result["missing_items"]:
                print(
                    f"  {item['name']}"
                    f" x{item['quantity']}"
                )

        print(
            f"\nBasket total: "
            f"₪{result['total']:.2f}"
        )

    complete_results = [
        result
        for result in results
        if not result["missing_items"]
    ]

    print("\n" + "=" * 70)

    if not complete_results:
        print(
            "No chain currently contains "
            "the complete basket."
        )
        return

    cheapest_price = min(
        result["total"]
        for result in complete_results
    )

    winners = [
        result
        for result in complete_results
        if abs(
            result["total"]
            - cheapest_price
        ) < 0.01
    ]

    if len(winners) == 1:
        print(
            f"Cheapest complete basket: "
            f"{winners[0]['chain']}"
            f" - ₪{cheapest_price:.2f}"
        )

    else:
        names = ", ".join(
            result["chain"]
            for result in winners
        )

        print(
            f"Cheapest complete basket: "
            f"{names}"
            f" - ₪{cheapest_price:.2f}"
        )


if __name__ == "__main__":
    all_products = load_all_products()

    all_promotions = load_all_promotions()

    promotion_indexes = {
        chain: build_promotion_index(
            promotions
        )
        for chain, promotions
        in all_promotions.items()
    }

    print(
        "\nAll supermarket data loaded."
    )

    basket = build_basket(
        all_products,
        promotion_indexes,
    )

    if not basket:
        print("Basket is empty.")
        raise SystemExit

    results = compare_basket(
        all_products,
        basket,
        promotion_indexes,
    )

    print_basket_results(
        results,
        len(basket),
    )
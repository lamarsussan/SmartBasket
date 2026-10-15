import os

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from search import find_candidates

from stores_loader import load_all_stores

from store_data import (
    load_products_for_stores,
    load_promotions_for_stores,
    get_unavailable_product_chains,
    get_unavailable_promotion_chains,
)

from basket import (
    build_promotion_index,
    compare_basket,
    find_quantity_upgrade_offer,
)


app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SMARTBASKET_SECRET_KEY",
        "smartbasket-dev-secret-key",
    ),
)

templates = Jinja2Templates(
    directory="templates"
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


# ==================================================
# LOAD STORE LIST
# ==================================================

print("Loading SmartBasket store data...")

ALL_STORES = load_all_stores()

print("SmartBasket ready.")


# ==================================================
# LOCATION
# ==================================================

def get_selected_city(request):
    return request.session.get(
        "selected_city"
    )


def get_selected_stores(request):
    return request.session.get(
        "selected_stores",
        {},
    )


def get_available_cities():
    cities = set()

    for stores in ALL_STORES.values():
        for store in stores:
            if store.city:
                cities.add(
                    store.city.strip()
                )

    return sorted(cities)


def get_stores_for_city(city):
    result = {}

    for chain, stores in ALL_STORES.items():

        matching = [
            store
            for store in stores
            if (
                store.city
                and store.city.strip() == city
            )
        ]

        matching.sort(
            key=lambda store: store.name
        )

        result[chain] = matching

    return result


def find_store(
    chain,
    store_id,
):
    for store in ALL_STORES.get(
        chain,
        [],
    ):
        if store.store_id == store_id:
            return store

    return None


def get_selected_store_details(
    request,
):
    details = {}

    for chain, store_id in (
        get_selected_stores(
            request
        ).items()
    ):
        store = find_store(
            chain,
            store_id,
        )

        if store:
            details[chain] = store

    return details


# ==================================================
# DYNAMIC STORE DATA
# ==================================================

def get_current_products(
    request,
):
    return load_products_for_stores(
        get_selected_stores(
            request
        )
    )


def get_current_promotions(
    request,
):
    return load_promotions_for_stores(
        get_selected_stores(
            request
        )
    )


def get_current_promotion_indexes(
    request,
):
    promotions = (
        get_current_promotions(
            request
        )
    )

    return {
        chain: build_promotion_index(
            chain_promotions
        )
        for chain, chain_promotions
        in promotions.items()
    }


# ==================================================
# BASKET HELPERS
# ==================================================

def get_basket(request):
    return request.session.get(
        "basket",
        [],
    )


def save_basket(
    request,
    basket,
):
    request.session[
        "basket"
    ] = basket


def find_product_by_barcode(
    all_products,
    barcode,
):
    for products in all_products.values():

        for product in products:

            if product.barcode == barcode:
                return product

    return None


# ==================================================
# RESULTS
# ==================================================

def prepare_results_for_web(
    results,
):
    complete_results = [
        result
        for result in results
        if not result["missing_items"]
    ]

    winner = None

    if complete_results:
        winner = min(
            complete_results,
            key=lambda result: result["total"],
        )

    prepared_results = []

    for result in results:

        prepared = dict(
            result
        )

        prepared["is_complete"] = (
            len(
                result["missing_items"]
            )
            == 0
        )

        prepared["is_winner"] = False

        prepared[
            "difference_from_winner"
        ] = None

        regular_total = sum(
            item["regular_total"]
            for item in result[
                "found_items"
            ]
        )

        prepared[
            "regular_basket_total"
        ] = regular_total

        prepared[
            "promotion_savings"
        ] = (
            regular_total
            - result["total"]
        )

        if (
            winner is not None
            and prepared["is_complete"]
        ):
            prepared["is_winner"] = (
                result["chain"]
                == winner["chain"]
            )

            prepared[
                "difference_from_winner"
            ] = (
                result["total"]
                - winner["total"]
            )

        prepared_results.append(
            prepared
        )

    winner_info = None

    if winner is not None:

        others = [
            result
            for result in complete_results
            if (
                result["chain"]
                != winner["chain"]
            )
        ]

        savings = 0.0

        if others:

            next_cheapest = min(
                others,
                key=lambda result: (
                    result["total"]
                ),
            )

            savings = (
                next_cheapest["total"]
                - winner["total"]
            )

        winner_info = {
            "chain": winner["chain"],
            "total": winner["total"],
            "savings_vs_next": savings,
        }

    return (
        prepared_results,
        winner_info,
    )


def page_context(
    request,
    candidates=None,
    query="",
    results=None,
    winner=None,
    pending_offer=None,
):
    selected_stores = (
        get_selected_stores(
            request
        )
    )

    return {
        "basket": get_basket(
            request
        ),
        "candidates": candidates,
        "query": query,
        "results": results,
        "winner": winner,
        "pending_offer": (
            pending_offer
        ),
        "selected_city": (
            get_selected_city(
                request
            )
        ),
        "selected_stores": (
            get_selected_store_details(
                request
            )
        ),
        "unavailable_product_chains": (
            get_unavailable_product_chains(
                selected_stores
            )
        ),
        "unavailable_promotion_chains": (
            get_unavailable_promotion_chains(
                selected_stores
            )
        ),
    }


# ==================================================
# LOCATION
# ==================================================

@app.get(
    "/location",
    response_class=HTMLResponse,
)
def location_page(
    request: Request,
):
    city = get_selected_city(
        request
    )

    stores_by_chain = None

    if city:
        stores_by_chain = (
            get_stores_for_city(
                city
            )
        )

    return templates.TemplateResponse(
        request=request,
        name="location.html",
        context={
            "cities": (
                get_available_cities()
            ),
            "selected_city": city,
            "stores_by_chain": (
                stores_by_chain
            ),
            "selected_stores": (
                get_selected_stores(
                    request
                )
            ),
        },
    )


@app.post(
    "/location/city"
)
def choose_city(
    request: Request,
    city: str = Form(...),
):
    if city not in (
        get_available_cities()
    ):
        return RedirectResponse(
            "/location",
            status_code=303,
        )

    old_city = get_selected_city(
        request
    )

    request.session[
        "selected_city"
    ] = city

    if old_city != city:

        request.session[
            "selected_stores"
        ] = {}

        save_basket(
            request,
            [],
        )

    return RedirectResponse(
        "/location",
        status_code=303,
    )


@app.post(
    "/location/stores"
)
def choose_stores(
    request: Request,
    shufersal_store: str = Form(""),
    carrefour_store: str = Form(""),
    hazi_hinam_store: str = Form(""),
    netto_hissachon_store: str = Form(""),
):
    city = get_selected_city(
        request
    )

    if not city:
        return RedirectResponse(
            "/location",
            status_code=303,
        )

    submitted = {
        "Shufersal": (
            shufersal_store
        ),
        "Carrefour": (
            carrefour_store
        ),
        "Hazi Hinam": (
            hazi_hinam_store
        ),
        "Netto Hissachon": (
            netto_hissachon_store
        ),
    }

    selected = {}

    for chain, store_id in (
        submitted.items()
    ):
        if not store_id:
            continue

        store = find_store(
            chain,
            store_id,
        )

        if (
            store is not None
            and store.city == city
        ):
            selected[
                chain
            ] = store_id

    if not selected:
        return RedirectResponse(
            "/location",
            status_code=303,
        )

    old_selected = (
        get_selected_stores(
            request
        )
    )

    request.session[
        "selected_stores"
    ] = selected

    if old_selected != selected:
        save_basket(
            request,
            [],
        )

    return RedirectResponse(
        "/",
        status_code=303,
    )


@app.get(
    "/change-location"
)
def change_location(
    request: Request,
):
    return RedirectResponse(
        "/location",
        status_code=303,
    )


# ==================================================
# HOME
# ==================================================

@app.get(
    "/",
    response_class=HTMLResponse,
)
def home(
    request: Request,
):
    if (
        not get_selected_city(
            request
        )
        or not get_selected_stores(
            request
        )
    ):
        return RedirectResponse(
            "/location",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=page_context(
            request
        ),
    )


# ==================================================
# SEARCH
# ==================================================

@app.post(
    "/search",
    response_class=HTMLResponse,
)
def search_product(
    request: Request,
    query: str = Form(...),
):
    all_products = (
        get_current_products(
            request
        )
    )

    candidates = find_candidates(
        all_products,
        query,
        limit=8,
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=page_context(
            request,
            candidates=candidates,
            query=query,
        ),
    )


# ==================================================
# ADD PRODUCT
# ==================================================

@app.post(
    "/add",
    response_class=HTMLResponse,
)
def add_product(
    request: Request,
    barcode: str = Form(...),
    quantity: int = Form(...),
):
    all_products = (
        get_current_products(
            request
        )
    )

    promotion_indexes = (
        get_current_promotion_indexes(
            request
        )
    )

    product = (
        find_product_by_barcode(
            all_products,
            barcode,
        )
    )

    if product is None:
        return RedirectResponse(
            "/",
            status_code=303,
        )

    offer = (
        find_quantity_upgrade_offer(
            all_products,
            promotion_indexes,
            barcode,
            quantity,
        )
    )

    if offer is not None:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=page_context(
                request,
                pending_offer={
                    "barcode": barcode,
                    "product_name": (
                        product.name
                    ),
                    "requested_quantity": (
                        quantity
                    ),
                    "required_quantity": (
                        offer[
                            "required_qty"
                        ]
                    ),
                    "chain": (
                        offer["chain"]
                    ),
                    "promotion_total": (
                        offer[
                            "promotion_total"
                        ]
                    ),
                    "description": (
                        offer[
                            "description"
                        ]
                    ),
                },
            ),
        )

    basket = get_basket(
        request
    )

    basket.append(
        {
            "barcode": (
                product.barcode
            ),
            "name": (
                product.name
            ),
            "quantity": quantity,
        }
    )

    save_basket(
        request,
        basket,
    )

    return RedirectResponse(
        "/",
        status_code=303,
    )


# ==================================================
# EDIT BASKET ITEM
# ==================================================

@app.post(
    "/basket/update"
)
def update_basket_item(
    request: Request,
    item_index: int = Form(...),
    quantity: int = Form(...),
):
    basket = get_basket(
        request
    )

    if (
        item_index < 0
        or item_index >= len(
            basket
        )
    ):
        return RedirectResponse(
            "/",
            status_code=303,
        )

    if quantity < 1:
        quantity = 1

    basket[
        item_index
    ]["quantity"] = quantity

    save_basket(
        request,
        basket,
    )

    return RedirectResponse(
        "/",
        status_code=303,
    )


# ==================================================
# REMOVE BASKET ITEM
# ==================================================

@app.post(
    "/basket/remove"
)
def remove_basket_item(
    request: Request,
    item_index: int = Form(...),
):
    basket = get_basket(
        request
    )

    if (
        item_index >= 0
        and item_index < len(
            basket
        )
    ):
        basket.pop(
            item_index
        )

        save_basket(
            request,
            basket,
        )

    return RedirectResponse(
        "/",
        status_code=303,
    )


# ==================================================
# PROMOTION CHOICE
# ==================================================

@app.post(
    "/promotion-choice"
)
def promotion_choice(
    request: Request,
    barcode: str = Form(...),
    requested_quantity: int = Form(...),
    required_quantity: int = Form(...),
    action: str = Form(...),
):
    all_products = (
        get_current_products(
            request
        )
    )

    product = (
        find_product_by_barcode(
            all_products,
            barcode,
        )
    )

    if product is None:
        return RedirectResponse(
            "/",
            status_code=303,
        )

    final_quantity = (
        required_quantity
        if action == "accept"
        else requested_quantity
    )

    basket = get_basket(
        request
    )

    basket.append(
        {
            "barcode": (
                product.barcode
            ),
            "name": (
                product.name
            ),
            "quantity": (
                final_quantity
            ),
        }
    )

    save_basket(
        request,
        basket,
    )

    return RedirectResponse(
        "/",
        status_code=303,
    )


# ==================================================
# COMPARE
# ==================================================

@app.post(
    "/compare",
    response_class=HTMLResponse,
)
def compare(
    request: Request,
):
    all_products = (
        get_current_products(
            request
        )
    )

    promotion_indexes = (
        get_current_promotion_indexes(
            request
        )
    )

    results = compare_basket(
        all_products,
        get_basket(
            request
        ),
        promotion_indexes,
    )

    results, winner = (
        prepare_results_for_web(
            results
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=page_context(
            request,
            results=results,
            winner=winner,
        ),
    )


# ==================================================
# CLEAR
# ==================================================

@app.post(
    "/clear"
)
def clear_basket(
    request: Request,
):
    save_basket(
        request,
        [],
    )

    return RedirectResponse(
        "/",
        status_code=303,
    )
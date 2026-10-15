# SmartBasket

SmartBasket is a web application for comparing the cost of a grocery basket across supermarket branches in Israel.

The application uses public supermarket price-transparency data and allows users to select a city and specific branches, search for products, build a basket, apply supported promotions, and compare the final basket price between supermarkets.

## Live Demo

https://smartbasket-5gkh.onrender.com

## Main Features

- Select a city and supermarket branches
- Load branch-specific product prices
- Load branch-specific promotions
- Search real supermarket products
- Search products by barcode
- Compare matching products across chains
- Build a shopping basket
- Update product quantities
- Remove products from the basket
- Detect supported promotions
- Offer quantity increases when a promotion requires more units
- Show regular price and promotion price
- Calculate promotion savings
- Compare complete basket prices
- Show the cheapest complete basket
- Continue working when one retailer's external data is temporarily unavailable
- Use disk and memory caching to reduce repeated network requests

## Supported Supermarkets

SmartBasket currently integrates with:

- Carrefour
- Shufersal
- Hazi Hinam
- Netto Hissachon

The application uses branch-specific store IDs. Product and promotion data are requested for the selected branch rather than using one fixed supermarket location.

Branch availability depends on the store information published by each retailer.

## Branch-Specific Data

The general flow is:

City → Selected branch → Store ID → PriceFull + PromoFull

The same retailer provider can therefore work with different branches.

Branch-specific product and promotion loading has been tested successfully with multiple locations, including:

- Carrefour store 002 in Ashkelon
- Netto Hissachon store 084 in Bat Yam
- Hazi Hinam store 202 in Holon

Shufersal is also implemented using branch-specific store IDs, although its public server can sometimes be unavailable or time out.

## Data Sources

SmartBasket uses public supermarket price-transparency data.

Depending on the retailer, the application retrieves files such as:

- Stores
- PriceFull
- PromoFull

Each retailer publishes its files differently, so SmartBasket contains separate provider modules for retailer-specific downloading and parsing.

After parsing, retailer data is converted into common internal models used by the rest of the application.

## Architecture

### `app.py`

FastAPI routes, session handling, form processing, page rendering, and application flow.

### `models.py`

Common models representing products, stores, and promotions.

### `providers/`

Retailer-specific integrations for downloading and parsing product and promotion data.

Supported provider integrations include:

- Carrefour
- Shufersal
- Hazi Hinam
- Netto Hissachon

### `store_data.py`

Loads product and promotion data for selected branches.

It also manages in-memory caching and retailer failure handling.

### `stores_loader.py`

Loads branch information and maps stores to Israeli localities.

Some public retailer data contains incomplete city information. When possible, SmartBasket uses a small fallback based on the branch name to recover the locality.

### `localities.py`

Maps Israeli locality codes to readable city names.

### `search.py`

Implements product search using:

- exact barcode matching
- word-based product-name matching
- simple text normalization

The search intentionally uses a transparent and understandable scoring approach.

### `basket.py`

Compares the user's basket across selected supermarkets.

It checks product availability, calculates totals, applies supported promotions, and determines the cheapest complete basket.

### `promotion_engine.py`

Interprets and calculates supported promotion formats.

### `data_cache.py`

Provides disk caching for retailer data.

### `templates/`

Jinja2 HTML templates.

### `static/`

CSS styling.

## Caching

Retailer files can contain thousands of products and promotions and external servers can sometimes be slow.

SmartBasket uses two cache levels:

### Disk Cache

Avoids downloading and parsing the same retailer data repeatedly between application runs.

### Memory Cache

Reuses branch data that has already been loaded during the current server process.

The application also remembers failed retailer requests during the current server run so that the same unavailable source is not contacted on every user action.

## Failure Handling

SmartBasket depends on external retailer systems that are outside the application's control.

If one retailer is temporarily unavailable, SmartBasket does not crash the entire comparison.

Instead, it:

- catches the loading error
- marks the retailer data as unavailable
- displays a warning
- continues working with the remaining supermarkets

This behavior is especially important for retailer servers that occasionally respond slowly or time out.

## Promotions

SmartBasket supports basic promotion formats that can be safely calculated from the public promotion files.

Examples include:

- one item at a promotional price
- two items for a fixed price
- three items for a fixed price
- similar quantity-based bundle promotions

If a promotion requires more items than the user requested, SmartBasket can offer the user the option to increase the basket quantity.

The comparison can display:

- regular price
- promotion price
- promotion description
- amount saved

Promotions that depend on conditions the application cannot reliably verify are not guaranteed to be applied.

Examples include:

- credit-card promotions
- membership-only promotions
- coupons
- complex conditional promotions
- promotions requiring unrelated additional purchases

## Retailer Notes

### Carrefour

Carrefour supports branch-specific product and promotion loading and has been tested successfully with multiple store IDs.

### Netto Hissachon

Netto Hissachon uses the Super Sapir / Bina price-transparency system.

SmartBasket dynamically loads Netto branches from the published Stores file.

Both product and promotion data are loaded according to the selected store ID.

### Hazi Hinam

Hazi Hinam supports branch-specific product and promotion loading.

The integration has been tested successfully with a branch other than the original default branch.

### Shufersal

Shufersal is implemented using branch-specific product and promotion loading.

However, Shufersal's public price-transparency endpoint can sometimes be slow or unavailable and may time out.

SmartBasket handles this situation without crashing.

## Limitations

This is a portfolio project and intentionally keeps the implementation understandable and maintainable.

Current limitations include:

- Not every Israeli supermarket chain is supported
- External retailer systems may occasionally be unavailable
- Not every possible promotion format is supported
- Conditional card, membership, and coupon promotions are not fully handled
- Product matching is based mainly on barcode and simple text matching
- Location selection is city-based rather than GPS-distance based
- The project depends on the format and availability of external retailer data
- Some public store records contain incomplete or inconsistent locality information

## Technologies

- Python
- FastAPI
- Uvicorn
- Jinja2
- HTML
- CSS
- Requests
- BeautifulSoup
- XML parsing
- Session middleware

## Installation

Clone the repository:

```bash
git clone https://github.com/lamarsussan/SmartBasket.git
cd SmartBasket
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the development server:

```bash
uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Deployment

The project is deployed on Render.

Production start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Live application:

https://smartbasket-5gkh.onrender.com

## Project Goal

The goal of SmartBasket is to demonstrate a practical software project that combines:

- backend web development
- external data integration
- parsing structured retailer files
- data normalization
- caching
- failure handling
- product search
- basket logic
- promotion handling
- branch-specific supermarket comparison

The implementation is intentionally kept simple enough to understand and explain while still working with real external data and real failure cases.
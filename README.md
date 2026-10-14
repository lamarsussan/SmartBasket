# SmartBasket

SmartBasket is a web application that compares the cost of a grocery basket across selected supermarket branches in Israel.

The application uses official supermarket price-transparency data and allows the user to choose a city and specific branches, search for products, build a basket, apply supported promotions, and compare the final basket price between supermarkets.

## Main Features

- Select a city and supermarket branches
- Search real supermarket products
- Compare the same product across chains
- Build a shopping basket
- Update product quantities
- Remove products from the basket
- Detect supported quantity-based promotions
- Compare total basket prices
- Show the cheapest complete basket
- Continue working even if one retailer's data is temporarily unavailable
- In-memory and disk caching to reduce repeated network requests

## Supported Supermarkets

Currently supported:

- Shufersal
- Carrefour
- Hazi Hinam

The exact available branches depend on the selected city.

## Data Source

SmartBasket uses official supermarket price-transparency files published by the retailers.

The project downloads and parses product, store, and promotion files directly from the retailers' public price-transparency systems.

## How It Works

1. The user selects a city.
2. SmartBasket shows the available supermarket branches in that city.
3. The selected branch IDs are stored in the user session.
4. Product data is loaded for those branches.
5. The user searches for products and adds them to a basket.
6. SmartBasket checks whether each product exists in each selected supermarket.
7. Supported promotions are applied when relevant.
8. The application calculates the basket total for each supermarket.
9. The cheapest complete basket is displayed.

## Architecture

The project is separated into several simple components:

- `app.py`  
  FastAPI routes, session handling, page rendering, and application flow.

- `models.py`  
  Data classes used to represent products, stores, and promotions.

- `providers/`  
  Retailer-specific code for downloading and parsing official price files.

- `store_data.py`  
  Loads product and promotion data for the branches selected by the user.

- `stores_loader.py`  
  Loads supermarket branch information.

- `localities.py`  
  Converts Israeli locality codes into readable city names.

- `search.py`  
  Product search and barcode-based matching.

- `basket.py`  
  Basket comparison logic and promotion integration.

- `promotion_engine.py`  
  Calculates supported promotions.

- `data_cache.py`  
  Disk caching for downloaded data.

- `templates/`  
  HTML templates.

- `static/`  
  CSS styling.

## Caching

Retailer files can be large and external servers can sometimes be slow.

SmartBasket uses two cache levels:

1. Disk cache  
   Avoids downloading the same data repeatedly between application runs.

2. Memory cache  
   Avoids loading the same branch data repeatedly while the server is running.

If promotion data for a retailer is temporarily unavailable, SmartBasket can continue using the available product data instead of crashing.

## Promotions

The current version supports basic quantity-based promotions such as:

- 2 items for a fixed price
- 3 items for a fixed price

SmartBasket does not automatically increase the user's requested quantity.

If the user requests fewer items than required for a promotion, the application can offer the user the option to increase the quantity.

## Limitations

This is a portfolio MVP and intentionally keeps the implementation simple.

Current limitations include:

- Not every Israeli supermarket chain is supported.
- Some retailer servers are occasionally slow or unavailable.
- Some promotion formats are not supported.
- Conditional promotions such as credit-card, membership, or coupon promotions are not fully handled.
- Product matching is primarily based on barcodes and simple text search.
- Location selection is city-based rather than GPS-distance based.

## Technologies

- Python
- FastAPI
- Jinja2
- HTML
- CSS
- Requests
- BeautifulSoup
- lxml

## Installation

Create a virtual environment:

```bash
python -m venv .venv
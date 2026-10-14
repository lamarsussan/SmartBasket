from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    chain: str
    store_id: str
    store_name: str
    barcode: str
    name: str
    price: float

    manufacturer: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None


@dataclass
class Promotion:
    chain: str
    store_id: str

    promotion_id: str
    description: str
    item_code: str

    min_qty: Optional[float] = None
    discounted_price: Optional[float] = None
    discount_rate: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    reward_type: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class Store:
    chain: str
    store_id: str
    name: str
    city: str
    address: str

    city_code: Optional[str] = None
    subchain_id: Optional[str] = None
    subchain_name: Optional[str] = None
    zipcode: Optional[str] = None
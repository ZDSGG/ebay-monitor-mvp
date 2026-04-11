from decimal import Decimal

from pydantic import BaseModel


class EbayItemData(BaseModel):
    title: str
    price: Decimal
    currency: str
    shipping_cost: Decimal
    seller_name: str | None
    condition: str | None
    availability: str | None
    image: str | None
    item_url: str

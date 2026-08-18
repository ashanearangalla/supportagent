from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ProductOption(BaseModel):
    """A resolved customization choice, e.g. a specific fragrance or color."""
    id: int
    name: str


class OrderItemDetail(BaseModel):
    id: int
    productId: int
    productName: str
    quantity: int
    price: Decimal
    fragrance: Optional[ProductOption] = None
    color: Optional[ProductOption] = None
    pot: Optional[ProductOption] = None
    waxType: Optional[ProductOption] = None


class OrderDetail(BaseModel):
    id: int
    orderRef: str
    firstName: str
    lastName: str
    email: str
    totalPrice: Decimal
    orderStatus: str
    paymentMethod: str
    createdAt: str
    notes: Optional[str] = None
    items: list[OrderItemDetail] = []
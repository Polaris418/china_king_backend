from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResolveMenuItemRequest(BaseModel):
    text: str = Field(..., min_length=1)
    category_hint: str | None = None
    limit: int = 5


class OrderItemInput(BaseModel):
    item_name: str = Field(..., min_length=1)
    qty: int = Field(default=1, ge=1)
    size: str | None = None


class ValidateOrderRequest(BaseModel):
    items: list[OrderItemInput]
    order_type: Literal["takeout", "dine-in"] | None = None
    pickup_time: str | None = None


class QuoteOrderRequest(ValidateOrderRequest):
    pass

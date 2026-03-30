from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DEFAULT_STORE_ID = "372f821f-9ee9-4686-8142-19efd3dbc5a8"


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


class ResolveOrderContextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    category_hint: str | None = None
    order_type: Literal["takeout", "dine-in"] | None = "takeout"
    current_time: str | None = None


class PlaceOrderRequest(BaseModel):
    storeId: str = Field(default=DEFAULT_STORE_ID, min_length=1)
    customerName: str = Field(default="Phone Order", min_length=1)
    customerPhone: str = Field(default="unknown", min_length=1)
    paymentMethod: str = Field(default="cash", min_length=1)
    items: str = Field(..., min_length=1)
    total: str = Field(default="pending", min_length=1)
    notes: str | None = None
    currency: str | None = None


class NotifyOrderRequest(BaseModel):
    order_summary: str = Field(default="Phone order from Retell", min_length=1)
    items: str = Field(..., min_length=1)
    total: str = Field(default="pending", min_length=1)
    customer_phone: str | None = "unknown"


class TransferCallRequest(BaseModel):
    customer_phone: str = Field(default="unknown", min_length=1)
    customer_name: str | None = None


class InitSmsOrderRequest(BaseModel):
    customer_phone: str = Field(default="unknown", min_length=1)
    store_id: str = Field(default=DEFAULT_STORE_ID, min_length=1)


class PostCallRequest(BaseModel):
    call_id: str | None = None
    agent_id: str | None = None
    transcript: str | None = None
    summary: str | None = None
    successful: bool | None = None
    metadata: dict | None = None

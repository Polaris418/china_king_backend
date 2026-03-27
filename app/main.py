from __future__ import annotations

from fastapi import FastAPI

from .matcher import resolve_menu_item
from .pricing import quote_order, validate_order
from .schemas import QuoteOrderRequest, ResolveMenuItemRequest, ValidateOrderRequest


app = FastAPI(title="China King Backend", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/resolve_menu_item")
def resolve_menu_item_endpoint(payload: ResolveMenuItemRequest) -> dict:
    return resolve_menu_item(payload.text, category_hint=payload.category_hint, limit=payload.limit)


@app.post("/validate_order")
def validate_order_endpoint(payload: ValidateOrderRequest) -> dict:
    items = [item.model_dump() for item in payload.items]
    return validate_order(items, order_type=payload.order_type, pickup_time=payload.pickup_time)


@app.post("/quote_order")
def quote_order_endpoint(payload: QuoteOrderRequest) -> dict:
    items = [item.model_dump() for item in payload.items]
    return quote_order(items, order_type=payload.order_type, pickup_time=payload.pickup_time)

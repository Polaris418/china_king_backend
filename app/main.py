from __future__ import annotations

from fastapi import FastAPI, Request

from .call_integration import (
    init_sms_order,
    notify_order,
    post_call,
    retell_webhook,
    save_order,
    transfer_call,
)
from .matcher import resolve_menu_item
from .pricing import quote_order, validate_order
from .schemas import (
    InitSmsOrderRequest,
    NotifyOrderRequest,
    PlaceOrderRequest,
    PostCallRequest,
    QuoteOrderRequest,
    ResolveMenuItemRequest,
    TransferCallRequest,
    ValidateOrderRequest,
)


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


@app.post("/orders/save")
def save_order_endpoint(payload: PlaceOrderRequest) -> dict:
    return save_order(payload.model_dump())


@app.post("/orders/noop")
def notify_order_endpoint(payload: NotifyOrderRequest) -> dict:
    return notify_order(payload.model_dump())


@app.post("/tools/transfer_call")
def transfer_call_endpoint(payload: TransferCallRequest) -> dict:
    return transfer_call(payload.model_dump())


@app.post("/sms/init")
def init_sms_order_endpoint(payload: InitSmsOrderRequest) -> dict:
    return init_sms_order(payload.model_dump())


@app.post("/retell/post-call")
def post_call_endpoint(payload: PostCallRequest) -> dict:
    return post_call(payload.model_dump())


@app.get("/retell/webhook")
def retell_webhook_health() -> dict:
    return {"ok": True, "status": "retell_webhook_ready"}


@app.post("/retell/webhook")
async def retell_webhook_endpoint(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    headers = {k.lower(): v for k, v in request.headers.items()}
    return retell_webhook(payload, headers=headers)

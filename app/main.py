from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

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


APP_VERSION = "0.1.5"


app = FastAPI(title="China King Backend", version=APP_VERSION)


async def _unwrap_tool_payload(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        return {}
    if isinstance(payload, dict) and isinstance(payload.get("args"), dict):
        return payload["args"]
    return payload


@app.get("/health")
def health() -> dict:
    return {"ok": True, "version": APP_VERSION}


@app.get("/current_time")
def current_time_get(timezone: str = "America/New_York") -> dict:
    now = datetime.now(ZoneInfo(timezone))
    return {
        "timezone": timezone,
        "current_time": now.strftime("%Y-%m-%d %I:%M %p"),
        "hour_24": now.hour,
        "minute": now.minute,
        "is_lunch_special_time": 11 <= now.hour < 15,
    }


@app.post("/current_time")
async def current_time_post(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    timezone = "America/New_York"
    if isinstance(raw, dict) and isinstance(raw.get("timezone"), str) and raw["timezone"].strip():
        timezone = raw["timezone"].strip()
    return current_time_get(timezone=timezone)


@app.post("/resolve_menu_item")
async def resolve_menu_item_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = ResolveMenuItemRequest.model_validate(raw)
    return resolve_menu_item(payload.text, category_hint=payload.category_hint, limit=payload.limit)


@app.post("/validate_order")
async def validate_order_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = ValidateOrderRequest.model_validate(raw)
    items = [item.model_dump() for item in payload.items]
    return validate_order(items, order_type=payload.order_type, pickup_time=payload.pickup_time)


@app.post("/quote_order")
async def quote_order_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = QuoteOrderRequest.model_validate(raw)
    items = [item.model_dump() for item in payload.items]
    return quote_order(items, order_type=payload.order_type, pickup_time=payload.pickup_time)


@app.post("/orders/save")
async def save_order_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = PlaceOrderRequest.model_validate(raw)
    return save_order(payload.model_dump())


@app.post("/orders/noop")
async def notify_order_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = NotifyOrderRequest.model_validate(raw)
    return notify_order(payload.model_dump())


@app.post("/tools/transfer_call")
async def transfer_call_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = TransferCallRequest.model_validate(raw)
    return transfer_call(payload.model_dump())


@app.post("/sms/init")
async def init_sms_order_endpoint(request: Request) -> dict:
    raw = await _unwrap_tool_payload(request)
    payload = InitSmsOrderRequest.model_validate(raw)
    return init_sms_order(payload.model_dump())


@app.post("/retell/post-call")
def post_call_endpoint(payload: PostCallRequest) -> dict:
    return post_call(payload.model_dump())


@app.get("/retell/webhook")
def retell_webhook_health() -> dict:
    return {"ok": True, "status": "retell_webhook_ready", "version": APP_VERSION}


@app.post("/retell/webhook")
async def retell_webhook_endpoint(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    headers = {k.lower(): v for k, v in request.headers.items()}
    return retell_webhook(payload, headers=headers)

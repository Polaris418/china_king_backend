from __future__ import annotations

import json
import os
import uuid
import urllib.error
import urllib.request
from typing import Any


DEFAULT_STORE_ID = "372f821f-9ee9-4686-8142-19efd3dbc5a8"


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return {"ok": False, "error": f"HTTP {exc.code}", "detail": detail}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": "request_failed", "detail": str(exc)}


def _relay_or_mock(env_key: str, payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    url = os.getenv(env_key, "").strip()
    if url:
        return _post_json(url, payload)
    return fallback


def save_order(payload: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "storeId": payload.get("storeId") or DEFAULT_STORE_ID,
        "customerName": payload.get("customerName") or "Phone Order",
        "customerPhone": payload.get("customerPhone") or "unknown",
        "paymentMethod": payload.get("paymentMethod") or "cash",
        "items": payload.get("items") or "",
        "total": payload.get("total") or "pending",
        "notes": payload.get("notes"),
        "currency": payload.get("currency"),
    }
    order_id = f"ck_{uuid.uuid4().hex[:12]}"
    fallback = {
        "ok": True,
        "mode": "mock",
        "order": {
            "id": order_id,
            "items": payload.get("items"),
            "total": payload.get("total"),
        },
        "payment_url": payload.get("payment_url") or "",
    }
    return _relay_or_mock("CHINA_KING_PLACE_ORDER_URL", payload, fallback)


def notify_order(payload: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "order_summary": payload.get("order_summary") or "Phone order from Retell",
        "items": payload.get("items") or "",
        "total": payload.get("total") or "pending",
        "customer_phone": payload.get("customer_phone") or "unknown",
    }
    fallback = {
        "ok": True,
        "mode": "mock",
        "status": "notified",
    }
    return _relay_or_mock("CHINA_KING_NOTIFY_ORDER_URL", payload, fallback)


def transfer_call(payload: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "customer_phone": payload.get("customer_phone") or "unknown",
        "customer_name": payload.get("customer_name"),
    }
    fallback = {
        "ok": True,
        "mode": "mock",
        "status": "transfer_requested",
    }
    return _relay_or_mock("CHINA_KING_TRANSFER_CALL_URL", payload, fallback)


def init_sms_order(payload: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "customer_phone": payload.get("customer_phone") or "unknown",
        "store_id": payload.get("store_id") or DEFAULT_STORE_ID,
    }
    fallback = {
        "ok": True,
        "mode": "mock",
        "status": "sms_initialized",
    }
    return _relay_or_mock("CHINA_KING_SMS_INIT_URL", payload, fallback)


def post_call(payload: dict[str, Any]) -> dict[str, Any]:
    fallback = {
        "ok": True,
        "mode": "mock",
        "status": "post_call_received",
    }
    return _relay_or_mock("CHINA_KING_POST_CALL_URL", payload, fallback)


def retell_webhook(payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    event_type = (
        payload.get("event")
        or payload.get("event_type")
        or payload.get("type")
        or "unknown"
    )
    call_id = payload.get("call_id") or payload.get("call", {}).get("call_id")
    print(
        json.dumps(
            {
                "source": "retell_webhook",
                "event_type": event_type,
                "call_id": call_id,
                "has_headers": bool(headers),
            },
            ensure_ascii=False,
        )
    )
    fallback = {
        "ok": True,
        "mode": "mock",
        "status": "webhook_received",
        "event_type": event_type,
        "call_id": call_id,
    }
    forward_payload = {
        "headers": headers or {},
        "payload": payload,
    }
    return _relay_or_mock("CHINA_KING_RETELL_WEBHOOK_URL", forward_payload, fallback)

from __future__ import annotations

from .catalog import build_indexes, normalize_text
from .matcher import resolve_menu_item


def choose_variant(item: dict, requested_size: str | None) -> tuple[str | None, float | None, str | None]:
    variants = item["variants"]
    if not variants:
        return None, None, "No price variants available."
    if requested_size:
        key = normalize_text(requested_size)
        for label, price in variants.items():
            if normalize_text(label) == key:
                return label, float(price), None
        return None, None, f"Size '{requested_size}' is not available for {item['name']}."
    if len(variants) == 1:
        label, price = next(iter(variants.items()))
        return label, float(price), None
    return None, None, f"Size is required for {item['name']}."


def validate_order(items: list[dict], order_type: str | None = None, pickup_time: str | None = None) -> dict:
    catalog_by_name, _, _, _ = build_indexes()
    resolved_items: list[dict] = []
    missing_required: list[str] = []
    invalid_fields: list[str] = []
    unresolved_items: list[dict] = []

    if not items:
        missing_required.append("At least one order item is required.")

    for raw_item in items:
        resolved = resolve_menu_item(raw_item["item_name"])
        if not resolved.get("canonical_item"):
            unresolved_items.append(
                {
                    "input": raw_item["item_name"],
                    "candidates": resolved.get("candidates", []),
                }
            )
            continue

        item = catalog_by_name[resolved["canonical_item"]]
        label, unit_price, error = choose_variant(item, raw_item.get("size"))
        if error:
            missing_required.append(error)
            unit_price = None
            label = None
        resolved_items.append(
            {
                "input": raw_item["item_name"],
                "canonical_item": item["name"],
                "category": item["category"],
                "qty": raw_item["qty"],
                "size": label,
                "unit_price": unit_price,
                "spicy": item["spicy"],
            }
        )

    if order_type == "takeout" and not pickup_time:
        missing_required.append("Pickup time is required for takeout orders.")

    valid = not unresolved_items and not missing_required and not invalid_fields
    return {
        "valid": valid,
        "resolved_items": resolved_items,
        "unresolved_items": unresolved_items,
        "missing_required": missing_required,
        "invalid_fields": invalid_fields,
        "order_type": order_type,
        "pickup_time": pickup_time,
    }


def quote_order(items: list[dict], order_type: str | None = None, pickup_time: str | None = None) -> dict:
    validation = validate_order(items, order_type=order_type, pickup_time=pickup_time)
    if not validation["valid"]:
        return {
            **validation,
            "total_price": None,
            "line_items": [],
        }

    line_items = []
    total = 0.0
    for item in validation["resolved_items"]:
        subtotal = round(item["unit_price"] * item["qty"], 2)
        total += subtotal
        line_items.append(
            {
                "canonical_item": item["canonical_item"],
                "qty": item["qty"],
                "size": item["size"],
                "unit_price": item["unit_price"],
                "subtotal": subtotal,
            }
        )

    return {
        **validation,
        "line_items": line_items,
        "total_price": round(total, 2),
    }

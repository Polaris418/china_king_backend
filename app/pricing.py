from __future__ import annotations

from .catalog import build_indexes, normalize_text
from .matcher import resolve_menu_item


TAX_RATE = 0.07


VARIANT_ALIASES = {
    "pt": {
        "pt",
        "pint",
        "paint",
        "point",
        "points",
        "hint",
        "hind",
        "hunt",
        "first",
        "first one",
        "the first",
        "the first one",
    },
    "qt": {
        "qt",
        "quart",
        "court",
        "quard",
        "quote",
        "accord",
        "second",
        "second one",
        "the second",
        "the second one",
    },
    "regular": {
        "regular",
        "plain",
        "normal",
    },
    "small": {
        "small",
        "sm",
    },
    "large": {
        "large",
        "lg",
        "big",
    },
    "extra large": {
        "extra large",
        "x large",
        "xl",
    },
}


def _find_exactish_catalog_matches(concept_name: str, catalog_by_name: dict[str, dict]) -> list[str]:
    concept_key = normalize_text(concept_name)
    exact_matches = []
    prefix_matches = []
    contains_matches = []
    for catalog_name in catalog_by_name:
        catalog_key = normalize_text(catalog_name)
        if catalog_key == concept_key:
            exact_matches.append(catalog_name)
        elif catalog_key.startswith(f"{concept_key} "):
            prefix_matches.append(catalog_name)
        elif f" {concept_key} " in f" {catalog_key} ":
            contains_matches.append(catalog_name)
    if exact_matches:
        return exact_matches
    if prefix_matches:
        return prefix_matches
    return contains_matches


def _resolve_concept_alias_to_catalog_item(
    concept_name: str,
    catalog_by_name: dict[str, dict],
) -> tuple[str | None, str | None]:
    exactish_matches = _find_exactish_catalog_matches(concept_name, catalog_by_name)
    if len(exactish_matches) == 1:
        return exactish_matches[0], None

    lowered = concept_name.lower()
    if " with " in lowered:
        base_name, variant_tail = concept_name.rsplit(" with ", 1)
        base_matches = _find_exactish_catalog_matches(base_name, catalog_by_name)
        if len(base_matches) == 1:
            base_item_name = base_matches[0]
            base_item = catalog_by_name[base_item_name]
            variant_candidates = [
                f"with {variant_tail}".strip(),
                variant_tail.strip(),
            ]
            normalized_variants = {
                normalize_text(label): label for label in base_item.get("variants", {})
            }
            for variant_candidate in variant_candidates:
                label = normalized_variants.get(normalize_text(variant_candidate))
                if label:
                    return base_item_name, label

    return None, None


def _infer_preferred_category_from_text(item_name: str) -> str | None:
    normalized = normalize_text(item_name)
    if "lunch special" in normalized:
        return "LUNCH SPECIAL"
    if "combo" in normalized or "combination dinner" in normalized or "dinner special" in normalized:
        return "COMBINATION DINNER"
    return None


def _prefer_category_variant_for_item(
    item_name: str,
    preferred_category: str | None,
    catalog_by_name: dict[str, dict],
) -> str | None:
    if not preferred_category:
        return None

    preferred = normalize_text(preferred_category)
    item_key = normalize_text(item_name)
    for catalog_name, catalog_item in catalog_by_name.items():
        if normalize_text(catalog_item["category"]) != preferred:
            continue
        catalog_key = normalize_text(catalog_name)
        if (
            catalog_key == item_key
            or catalog_key.startswith(f"{item_key} ")
            or item_key.startswith(f"{catalog_key} ")
            or f" {item_key} " in f" {catalog_key} "
        ):
            return catalog_name
    return None


def canonicalize_item_request(item_name: str, requested_size: str | None = None) -> tuple[str, str | None]:
    catalog_by_name, _, _, _ = build_indexes()
    resolved = resolve_menu_item(item_name)
    canonical_item = resolved.get("canonical_item")
    preferred_category = _infer_preferred_category_from_text(item_name)
    if canonical_item:
        preferred_variant = _prefer_category_variant_for_item(canonical_item, preferred_category, catalog_by_name)
        if preferred_variant:
            canonical_item = preferred_variant
        return canonical_item, requested_size

    candidates = resolved.get("candidates", [])
    if resolved.get("match_type") == "concept_only" and len(candidates) == 1:
        concept_name = candidates[0]["name"]
        exact_catalog_item, implied_variant = _resolve_concept_alias_to_catalog_item(concept_name, catalog_by_name)
        if exact_catalog_item:
            return exact_catalog_item, requested_size or implied_variant

    return item_name, requested_size


def canonicalize_item_name(item_name: str) -> str:
    canonical_name, _ = canonicalize_item_request(item_name)
    return canonical_name


def canonicalize_variant_label(item: dict, requested_size: str | None) -> str | None:
    if not requested_size:
        return requested_size

    normalized_requested = normalize_text(requested_size)
    variants = item["variants"]
    normalized_variants = {normalize_text(label): label for label in variants}

    if normalized_requested in normalized_variants:
        return normalized_variants[normalized_requested]

    for canonical_label, aliases in VARIANT_ALIASES.items():
        if normalized_requested not in aliases:
            continue
        for label in variants:
            if normalize_text(label) == canonical_label:
                return label

    return requested_size


def canonicalize_order_items(items: list[dict]) -> list[dict]:
    catalog_by_name, _, _, _ = build_indexes()
    normalized_items: list[dict] = []
    for raw_item in items:
        normalized_item = dict(raw_item)
        canonical_name, canonical_requested_size = canonicalize_item_request(
            raw_item["item_name"],
            raw_item.get("size"),
        )
        normalized_item["item_name"] = canonical_name
        item = catalog_by_name.get(canonical_name)
        if item:
            normalized_item["size"] = canonicalize_variant_label(item, canonical_requested_size)
        normalized_items.append(normalized_item)
    return normalized_items


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
    items = canonicalize_order_items(items)
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

    # Phone takeout orders may use the default ready window instead of a caller-specified pickup time.
    # Keep pickup_time optional so the flow can quote and place standard 10-30 minute pickup orders
    # without forcing an exact time.

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
    relaxed_order_type = order_type
    if order_type == "takeout" and not pickup_time:
        relaxed_order_type = None
    validation = validate_order(items, order_type=relaxed_order_type, pickup_time=pickup_time)
    validation["order_type"] = order_type
    validation["pickup_time"] = pickup_time
    if not validation["valid"]:
        return {
            **validation,
            "subtotal_price": None,
            "tax_rate": TAX_RATE,
            "tax_amount": None,
            "total_price": None,
            "line_items": [],
        }

    line_items = []
    subtotal = 0.0
    for item in validation["resolved_items"]:
        item_subtotal = round(item["unit_price"] * item["qty"], 2)
        subtotal += item_subtotal
        line_items.append(
            {
                "canonical_item": item["canonical_item"],
                "qty": item["qty"],
                "size": item["size"],
                "unit_price": item["unit_price"],
                "subtotal": item_subtotal,
            }
        )

    subtotal = round(subtotal, 2)
    tax_amount = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax_amount, 2)

    return {
        **validation,
        "line_items": line_items,
        "subtotal_price": subtotal,
        "tax_rate": TAX_RATE,
        "tax_amount": tax_amount,
        "total_price": total,
    }

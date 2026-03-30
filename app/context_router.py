from __future__ import annotations

from .catalog import build_indexes, normalize_text
from .matcher import resolve_menu_item
from .pricing import canonicalize_item_request


def _is_lunch_time(current_time: str | None) -> bool | None:
    if not current_time:
        return None
    text = current_time.strip().lower()
    try:
        date_part, time_part, meridiem = text.split()
        hour_s, minute_s = time_part.split(":")
        hour = int(hour_s)
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return 11 <= hour < 15
    except Exception:
        return None


def _followups_for_category(category: str, item_name: str) -> dict:
    cat = normalize_text(category)
    name = normalize_text(item_name)

    asks_noodle_choice = cat in {"lunch special"}
    asks_pickup_time = cat not in {"daily special", "chicken wings", "teriyaki chicken"}
    short_confirm_only = cat in {"daily special", "chicken wings", "teriyaki chicken"}

    if cat == "combination dinner":
        asks_noodle_choice = False
        asks_pickup_time = False
        short_confirm_only = False

    if cat == "daily special":
        asks_noodle_choice = False
        asks_pickup_time = False
        short_confirm_only = True

    if cat == "chicken wings":
        asks_noodle_choice = False
        asks_pickup_time = False
        short_confirm_only = True

    if cat == "teriyaki chicken":
        asks_noodle_choice = False
        asks_pickup_time = False
        short_confirm_only = True

    if "lunch" in name:
        asks_noodle_choice = False
        asks_pickup_time = False
        short_confirm_only = False

    return {
        "asks_noodle_choice": asks_noodle_choice,
        "asks_pickup_time": asks_pickup_time,
        "short_confirm_only": short_confirm_only,
    }


def _pick_canonical_from_candidates(candidates: list[dict], preferred_category: str | None = None) -> tuple[str | None, str | None]:
    if not candidates:
        return None, None
    if preferred_category:
        pref = normalize_text(preferred_category)
        filtered = [c for c in candidates if normalize_text(c.get("category", "")) == pref]
        if filtered:
            return filtered[0]["name"], filtered[0]["category"]
    if len(candidates) == 1:
        return candidates[0]["name"], candidates[0]["category"]
    return None, None


def _prefer_category_variant_for_item(
    item_name: str,
    preferred_category: str | None,
    catalog_by_name: dict[str, dict],
) -> tuple[str, str] | None:
    if not preferred_category:
        return None

    preferred = normalize_text(preferred_category)
    item_key = normalize_text(item_name)
    matches: list[tuple[str, str]] = []
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
            matches.append((catalog_name, catalog_item["category"]))

    if matches:
        return matches[0]
    return None


def resolve_order_context(
    text: str,
    category_hint: str | None = None,
    order_type: str | None = "takeout",
    current_time: str | None = None,
) -> dict:
    catalog_by_name, _, _, _ = build_indexes()
    resolved = resolve_menu_item(text, category_hint=category_hint)

    normalized_text = normalize_text(text)
    mentions_lunch = "lunch special" in normalized_text or normalized_text.startswith("l ")
    mentions_combo = "combo" in normalized_text or "combination dinner" in normalized_text
    mentions_dinner_special = "dinner special" in normalized_text

    preferred_category = None
    if mentions_lunch:
        preferred_category = "LUNCH SPECIAL"
    elif mentions_combo:
        preferred_category = "COMBINATION DINNER"

    lunch_time = _is_lunch_time(current_time)

    canonical_from_request, implied_variant = canonicalize_item_request(text)
    if canonical_from_request in catalog_by_name:
        item = catalog_by_name[canonical_from_request]
        category = item["category"]
        preferred_variant = _prefer_category_variant_for_item(canonical_from_request, preferred_category, catalog_by_name)
        if preferred_variant:
            canonical_from_request, category = preferred_variant
            item = catalog_by_name[canonical_from_request]
        followups = _followups_for_category(category, canonical_from_request)

        if normalize_text(category) == "lunch special":
            followups["asks_noodle_choice"] = False
            followups["asks_pickup_time"] = False

        return {
            "resolved": True,
            "raw_text": text,
            "resolved_item": canonical_from_request,
            "resolved_category": category,
            "resolved_variant": implied_variant,
            "match_type": resolved.get("match_type"),
            "needs_clarification": False,
            "asks_noodle_choice": followups["asks_noodle_choice"],
            "asks_pickup_time": followups["asks_pickup_time"],
            "short_confirm_only": followups["short_confirm_only"],
            "should_offer_lunch": bool(lunch_time) if lunch_time is not None else None,
            "should_block_lunch": bool(lunch_time is False) if lunch_time is not None else None,
            "order_type": order_type,
            "candidates": resolved.get("candidates", []),
        }

    if not resolved.get("canonical_item") and resolved.get("match_type") in {"ambiguous_exact", "high_fuzzy", "medium_fuzzy", "concept_only"}:
        chosen_name, chosen_category = _pick_canonical_from_candidates(resolved.get("candidates", []), preferred_category=preferred_category)
        if chosen_name:
            resolved = {
                **resolved,
                "canonical_item": chosen_name,
                "category": chosen_category,
                "needs_clarification": False,
            }

    if not resolved.get("canonical_item"):
        return {
            "resolved": False,
            "raw_text": text,
            "resolved_item": None,
            "resolved_category": None,
            "resolved_variant": None,
            "match_type": resolved.get("match_type"),
            "needs_clarification": True,
            "asks_noodle_choice": False,
            "asks_pickup_time": False,
            "short_confirm_only": False,
            "should_offer_lunch": bool(lunch_time) if lunch_time is not None else None,
            "should_block_lunch": bool(lunch_time is False) if lunch_time is not None else None,
            "candidates": resolved.get("candidates", []),
        }

    item_name = resolved["canonical_item"]
    if mentions_lunch:
        lunch_candidates = [
            candidate for candidate in resolved.get("candidates", [])
            if normalize_text(candidate.get("category", "")) == "lunch special"
        ]
        if lunch_candidates:
            item_name = lunch_candidates[0]["name"]
    elif mentions_combo:
        combo_candidates = [
            candidate for candidate in resolved.get("candidates", [])
            if normalize_text(candidate.get("category", "")) == "combination dinner"
        ]
        if combo_candidates:
            item_name = combo_candidates[0]["name"]
    elif preferred_category:
        preferred_variant = _prefer_category_variant_for_item(item_name, preferred_category, catalog_by_name)
        if preferred_variant:
            item_name, _ = preferred_variant

    if item_name not in catalog_by_name:
        return {
            "resolved": False,
            "raw_text": text,
            "resolved_item": None,
            "resolved_category": None,
            "resolved_variant": None,
            "match_type": resolved.get("match_type"),
            "needs_clarification": True,
            "asks_noodle_choice": False,
            "asks_pickup_time": False,
            "short_confirm_only": False,
            "should_offer_lunch": bool(lunch_time) if lunch_time is not None else None,
            "should_block_lunch": bool(lunch_time is False) if lunch_time is not None else None,
            "candidates": resolved.get("candidates", []),
        }
    item = catalog_by_name[item_name]
    category = item["category"]

    # Explicit concrete resolved item wins over vague prior special wording.
    if mentions_dinner_special and normalize_text(category) in {"daily special", "chicken wings", "teriyaki chicken"}:
        pass
    elif mentions_lunch and normalize_text(category) != "lunch special":
        # Keep the resolved item category, but signal that lunch wording conflicted.
        pass
    elif mentions_combo and normalize_text(category) != "combination dinner":
        pass

    followups = _followups_for_category(category, item_name)

    if normalize_text(category) == "lunch special":
        if lunch_time is False:
            followups["asks_noodle_choice"] = False
        else:
            # Lunch items from this menu already encode the actual lunch dish; no extra lo mein/chow mein prompt.
            followups["asks_noodle_choice"] = False
        followups["asks_pickup_time"] = False

    return {
        "resolved": True,
        "raw_text": text,
        "resolved_item": item_name,
        "resolved_category": category,
        "resolved_variant": None,
        "match_type": resolved.get("match_type"),
        "needs_clarification": bool(resolved.get("needs_clarification")),
        "asks_noodle_choice": followups["asks_noodle_choice"],
        "asks_pickup_time": followups["asks_pickup_time"],
        "short_confirm_only": followups["short_confirm_only"],
        "should_offer_lunch": bool(lunch_time) if lunch_time is not None else None,
        "should_block_lunch": bool(lunch_time is False) if lunch_time is not None else None,
        "order_type": order_type,
        "candidates": resolved.get("candidates", []),
    }

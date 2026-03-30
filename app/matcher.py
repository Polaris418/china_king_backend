from __future__ import annotations

from rapidfuzz import fuzz

from .catalog import build_indexes, normalize_text


def resolve_menu_item(text: str, category_hint: str | None = None, limit: int = 5) -> dict:
    query = normalize_text(text)
    if not query:
        return {
            "canonical_item": None,
            "confidence": 0.0,
            "match_type": "empty",
            "candidates": [],
            "needs_clarification": True,
        }

    catalog_by_name, alias_index, concept_aliases, catalog = build_indexes()
    exact_matches = alias_index.get(query, [])
    exact_concepts = concept_aliases.get(query, [])

    if exact_matches:
        if category_hint:
            filtered = [item for item in exact_matches if normalize_text(item["category"]) == normalize_text(category_hint)]
            if filtered:
                exact_matches = filtered
        if len(exact_matches) == 1:
            item = exact_matches[0]
            return {
                "canonical_item": item["name"],
                "confidence": 1.0,
                "match_type": "exact_alias",
                "category": item["category"],
                "candidates": [
                    {"name": item["name"], "category": item["category"], "score": 100.0}
                ],
                "needs_clarification": False,
            }
        return {
            "canonical_item": None,
            "confidence": 0.0,
            "match_type": "ambiguous_exact",
            "candidates": [
                {"name": item["name"], "category": item["category"], "score": 100.0}
                for item in exact_matches[:limit]
            ],
            "needs_clarification": True,
        }

    if exact_concepts:
        return {
            "canonical_item": None,
            "confidence": 0.0,
            "match_type": "concept_only",
            "candidates": [{"name": name, "category": "concept", "score": 100.0} for name in exact_concepts[:limit]],
            "needs_clarification": True,
        }

    scored: list[tuple[float, dict]] = []
    for item in catalog:
        if category_hint and normalize_text(item["category"]) != normalize_text(category_hint):
            continue
        name_key = normalize_text(item["name"])
        score = max(
            fuzz.token_set_ratio(query, name_key),
            fuzz.partial_ratio(query, name_key),
        )
        if name_key == query:
            score += 5
        elif name_key.startswith(f"{query} "):
            score += 2
        scored.append((float(score), item))

    if not scored and category_hint:
        for item in catalog:
            name_key = normalize_text(item["name"])
            score = max(
                fuzz.token_set_ratio(query, name_key),
                fuzz.partial_ratio(query, name_key),
            )
            if name_key == query:
                score += 5
            elif name_key.startswith(f"{query} "):
                score += 2
            scored.append((float(score), item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]
    candidates = [
        {"name": item["name"], "category": item["category"], "score": round(score, 2)}
        for score, item in top
    ]

    if not top:
        return {
            "canonical_item": None,
            "confidence": 0.0,
            "match_type": "no_match",
            "candidates": [],
            "needs_clarification": True,
        }

    best_score, best_item = top[0]
    confidence = round(best_score / 100.0, 4)
    second_score = top[1][0] if len(top) > 1 else 0.0

    if best_score >= 92:
        return {
            "canonical_item": best_item["name"],
            "confidence": confidence,
            "match_type": "high_fuzzy",
            "category": best_item["category"],
            "candidates": candidates,
            "needs_clarification": False,
        }

    if best_score >= 80 and best_score - second_score >= 5:
        return {
            "canonical_item": best_item["name"],
            "confidence": confidence,
            "match_type": "medium_fuzzy",
            "category": best_item["category"],
            "candidates": candidates,
            "needs_clarification": True,
        }

    return {
        "canonical_item": None,
        "confidence": confidence,
        "match_type": "ambiguous_fuzzy",
        "candidates": candidates,
        "needs_clarification": True,
    }

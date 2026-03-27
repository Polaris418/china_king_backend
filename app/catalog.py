from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def normalize_text(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = []
    for ch in lowered:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    text = "".join(cleaned)
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


@lru_cache(maxsize=1)
def load_catalog() -> list[dict]:
    return json.loads((DATA_DIR / "menu_catalog.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_alias_groups() -> dict[str, list[str]]:
    return json.loads((DATA_DIR / "menu_aliases.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def build_indexes() -> tuple[dict[str, dict], dict[str, list[dict]], dict[str, list[str]], list[dict]]:
    catalog = load_catalog()
    catalog_by_name = {item["name"]: item for item in catalog}
    alias_groups = load_alias_groups()

    alias_index: dict[str, list[dict]] = {}
    concept_aliases: dict[str, list[str]] = {}
    for canonical, aliases in alias_groups.items():
        if canonical not in catalog_by_name:
            for alias in aliases + [canonical]:
                key = normalize_text(alias)
                concept_aliases.setdefault(key, []).append(canonical)
            continue
        item = catalog_by_name[canonical]
        for alias in aliases + [canonical]:
            key = normalize_text(alias)
            alias_index.setdefault(key, []).append(item)

    return catalog_by_name, alias_index, concept_aliases, catalog

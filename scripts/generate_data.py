from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
MENU_MD = ROOT / "china_king_menu_structured.md"
ALIASES_MD = ROOT / "china_king_menu_aliases.md"
OUT_CATALOG = BACKEND_ROOT / "data" / "menu_catalog.json"
OUT_ALIASES = BACKEND_ROOT / "data" / "menu_aliases.json"


PRICE_PART_RE = re.compile(r"(?P<label>[A-Za-z&.'() /]+?)\s+(?P<price>\d+\.\d{2})$")
CODE_RE = re.compile(r"^(?P<code>[A-Z]?\d+)\s+(?P<name>.+)$")


def clean_name(raw: str) -> tuple[str | None, str]:
    raw = raw.strip()
    match = CODE_RE.match(raw)
    if match:
        return match.group("code"), match.group("name").strip()
    return None, raw


def parse_price_blob(blob: str) -> dict[str, float]:
    blob = blob.replace("[Spicy]", "").strip()
    parts = [p.strip() for p in blob.split(";") if p.strip()]
    variants: dict[str, float] = {}
    for part in parts:
        m = PRICE_PART_RE.match(part)
        if not m:
            continue
        label = m.group("label").strip().lower()
        price = float(m.group("price"))
        variants[label] = price
    return variants


def parse_menu() -> list[dict]:
    current_section = None
    items: list[dict] = []
    for line in MENU_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current_section = None
            continue
        if line.startswith("### "):
            current_section = line[4:].strip()
            continue
        if current_section is None:
            continue
        if not line.startswith("- "):
            continue
        content = line[2:].strip()
        if " - " not in content:
            continue
        if current_section in {
            "Source",
            "Store Information",
            "Online Ordering Facts",
            "Handwritten Menu Reference",
            "Modifier Summary",
        }:
            continue
        left, right = content.split(" - ", 1)
        code, canonical_name = clean_name(left)
        prices = parse_price_blob(right)
        if not prices:
            continue
        items.append(
            {
                "code": code,
                "name": canonical_name,
                "category": current_section,
                "spicy": "[Spicy]" in content,
                "variants": prices,
            }
        )
    return items


def parse_aliases() -> dict[str, list[str]]:
    alias_map: dict[str, list[str]] = {}
    current_key: str | None = None
    for raw in ALIASES_MD.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("- ") and not line.startswith("- aliases:"):
            current_key = line[2:].strip()
            alias_map.setdefault(current_key, [])
            continue
        if current_key and line.strip().startswith("- aliases:"):
            _, raw_aliases = line.strip().split(":", 1)
            aliases = [a.strip() for a in raw_aliases.split(",") if a.strip()]
            alias_map[current_key].extend(aliases)
    return alias_map


def main() -> None:
    catalog = parse_menu()
    aliases = parse_aliases()
    OUT_CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_ALIASES.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(catalog)} catalog items to {OUT_CATALOG}")
    print(f"Wrote {len(aliases)} alias groups to {OUT_ALIASES}")


if __name__ == "__main__":
    main()

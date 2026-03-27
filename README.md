# China King Backend

FastAPI backend for China King phone agents. This service is designed for Railway deployment and Retell custom function integration.

## Folder Layout

- `app/` FastAPI app code
- `data/menu_catalog.json` generated menu catalog from the structured menu
- `data/menu_aliases.json` generated alias map from the alias knowledge file
- `scripts/generate_data.py` regenerates JSON data from the markdown source files
- `scripts/smoke_test.py` local sanity checks

## Implemented Endpoints

- `GET /health`
- `POST /resolve_menu_item`
- `POST /validate_order`
- `POST /quote_order`

## What This Version Handles

- Fuzzy menu item resolution from phone-transcribed text
- Alias normalization based on `china_king_menu_aliases.md`
- Menu matching against qMenu-derived catalog data
- Required size detection when an item has multiple price variants
- Takeout pickup time requirement
- Deterministic order quoting when the item and size are clear

## What This Version Does Not Yet Handle

- Full modifier trees from qMenu
- Extra protein pricing
- No-onion / less-salt / substitution logic
- Complex multi-item sentence parsing
- Webhook signature verification

## Local Run

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Regenerate data:

```bash
python scripts/generate_data.py
```

Run smoke test:

```bash
set PYTHONPATH=%CD%
python scripts/smoke_test.py
```

Run server:

```bash
set PYTHONPATH=%CD%
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Railway Deployment

Recommended setup:

1. Create a new Railway project from this folder.
2. Ensure the start command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

3. Keep these files in the deployed project:
   - `app/`
   - `data/`
   - `requirements.txt`
   - `Procfile`

4. After deploy, verify:

```text
GET https://YOUR-RAILWAY-DOMAIN/health
```

Expected response:

```json
{"ok": true}
```

## Retell Integration Suggestion

Use these as Custom Functions or backend endpoints for your Retell flow.

### 1. Resolve Menu Item

Request:

```json
{
  "text": "general zo chicken",
  "category_hint": "LUNCH SPECIAL",
  "limit": 5
}
```

Response example:

```json
{
  "canonical_item": null,
  "confidence": 0.9091,
  "match_type": "ambiguous_fuzzy",
  "candidates": [
    {
      "name": "General Tso's Chicken (Lunch)",
      "category": "LUNCH SPECIAL",
      "score": 90.91
    }
  ],
  "needs_clarification": true
}
```

### 2. Validate Order

Request:

```json
{
  "items": [
    {
      "item_name": "General Tso Chicken",
      "qty": 1,
      "size": "large"
    }
  ],
  "order_type": "takeout",
  "pickup_time": "6:30 PM"
}
```

### 3. Quote Order

Request:

```json
{
  "items": [
    {
      "item_name": "General Tso Chicken",
      "qty": 2,
      "size": "large"
    }
  ],
  "order_type": "takeout",
  "pickup_time": "6:30 PM"
}
```

Response example:

```json
{
  "valid": true,
  "line_items": [
    {
      "canonical_item": "General Tso's Chicken",
      "qty": 2,
      "size": "large",
      "unit_price": 13.95,
      "subtotal": 27.9
    }
  ],
  "total_price": 27.9
}
```

## Recommended Next Step

After Railway deploy, connect Retell to:

- `/resolve_menu_item` after order intake
- `/validate_order` before final recap
- `/quote_order` only after item and size are confirmed

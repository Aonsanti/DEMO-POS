"""Shared shelf data: Stock 2D writes it, Shelf Management reads it.

File shape: {"active": <warehouse id>, "warehouses": [{id, name, w, h, shelves: [...]}]}
"""
import json
import re
from pathlib import Path

FILE = Path(__file__).with_name("shelves.json")


def load():
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"active": None, "warehouses": []}
    if isinstance(data, list):  # first version: one flat shelf list
        data = {"active": 1, "warehouses": [{"id": 1, "name": "คลัง 1", "w": 1000, "h": 520, "shelves": data}]}
    return data


def save(data):
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def status(item):
    """Same rule as stockClass() in the Stock 2D page."""
    if item.get("empty") or item.get("stock", 0) == 0:
        return "ว่าง"
    ratio = item["stock"] / max(item.get("maxStock", 1), 1)
    if ratio > 0.5:
        return "เพียงพอ"
    if ratio > 0.2:
        return "ปานกลาง"
    return "ต่ำ"


def _norm(text):
    return re.sub(r"\s+", "", text.lower())


def search(query, data=None):
    """Rows for every non-empty slot (in every warehouse) whose barcode or name matches."""
    data = load() if data is None else data
    q = query.strip()
    rows = []
    for wh in data.get("warehouses", []):
        for shelf in wh.get("shelves", []):
            cols = max(shelf.get("cols", 1), 1)
            for idx, item in enumerate(shelf.get("items", [])):
                if item.get("empty"):
                    continue
                if q in item.get("barcode", "") or _norm(q) in _norm(item.get("name", "")):
                    rows.append({
                        "คลัง": wh["name"],
                        "ชั้น": shelf["name"],
                        "แถว": idx // cols + 1,
                        "คอลัมน์": idx % cols + 1,
                        "บาร์โค้ด": item["barcode"],
                        "ชื่อสินค้า": item["name"],
                        "สต็อก": f'{item["stock"]} / {item["maxStock"]}',
                        "สถานะ": status(item),
                        "wh_id": wh["id"],
                    })
    return rows

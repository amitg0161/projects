"""Local JSON persistence for NutriWise meal records."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

try:
    from .nutrition import NutritionEstimate
except ImportError:
    from nutrition import NutritionEstimate

ROOT = Path(__file__).parent
MEALS_PATH = ROOT / "data" / "meals.json"


def _read() -> list[dict]:
    if not MEALS_PATH.exists():
        return []
    try:
        return json.loads(MEALS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write(records: list[dict]) -> None:
    MEALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEALS_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def save_meal(estimate: NutritionEstimate, meal_date: date | None = None) -> dict:
    record = {"id": str(uuid4()), "date": (meal_date or date.today()).isoformat(), "created_at": datetime.now(timezone.utc).isoformat(), **estimate.model_dump()}
    _write([record, *_read()])
    return record


def delete_meal(record_id: str) -> bool:
    records = _read()
    remaining = [record for record in records if record.get("id") != record_id.strip()]
    if len(remaining) == len(records):
        return False
    _write(remaining)
    return True


def today_records() -> list[dict]:
    today = date.today().isoformat()
    return [record for record in _read() if record.get("date") == today]


def daily_total() -> float:
    return round(sum(float(record.get("calories", 0)) for record in today_records()), 1)
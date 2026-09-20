"""Nutrition estimation pipeline for NutriWise AI."""

from __future__ import annotations

import csv
import json
import os
import re
import time
from difflib import get_close_matches
from pathlib import Path

import requests
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DATASET_PATH = ROOT / "data" / "healthy_meal_plans.csv"
USER_DATASET_PATH = ROOT / "data" / "user_foods.csv"
DATASET_FIELDS = ["meal_name", "num_ingredients", "calories", "prep_time", "protein", "fat", "carbs", "vegan", "vegetarian", "non_vegetarian", "keto", "paleo", "gluten_free", "mediterranean", "is_healthy"]
CACHE_TTL_SECONDS = 24 * 60 * 60
CACHE: dict[str, tuple[float, NutritionEstimate]] = {}


def clear_estimate_cache() -> None:
    CACHE.clear()


class NutritionEstimate(BaseModel):
    name: str
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)
    note: str
    source: str


class FoodItem(BaseModel):
    name: str
    portion: str = "1 serving"


LOCAL_FOODS = {
    "dal rice": {"calories": 430, "protein": 16, "carbs": 68, "fat": 10},
    "chicken curry": {"calories": 480, "protein": 34, "carbs": 18, "fat": 28},
    "chicken biryani": {"calories": 560, "protein": 28, "carbs": 68, "fat": 19},
    "vegetable pulao": {"calories": 390, "protein": 9, "carbs": 65, "fat": 11},
    "paneer tikka": {"calories": 360, "protein": 22, "carbs": 12, "fat": 25},
    "chana masala": {"calories": 330, "protein": 14, "carbs": 45, "fat": 11},
    "lentil soup": {"calories": 280, "protein": 16, "carbs": 42, "fat": 6},
    "chickpea stew": {"calories": 350, "protein": 15, "carbs": 48, "fat": 11},
    "vegan curry": {"calories": 380, "protein": 12, "carbs": 42, "fat": 19},
    "tofu stir fry": {"calories": 320, "protein": 20, "carbs": 25, "fat": 16},
    "grilled salmon": {"calories": 420, "protein": 36, "carbs": 8, "fat": 27},
    "grilled chicken salad": {"calories": 390, "protein": 36, "carbs": 18, "fat": 18},
    "cauliflower rice bowl": {"calories": 340, "protein": 18, "carbs": 27, "fat": 18},
    "turkey lettuce wraps": {"calories": 300, "protein": 29, "carbs": 14, "fat": 15},
    "almond flour pancakes": {"calories": 410, "protein": 14, "carbs": 20, "fat": 30},
    "gluten-free pasta": {"calories": 430, "protein": 12, "carbs": 72, "fat": 10},
}


def _dataset_names() -> list[str]:
    if not DATASET_PATH.exists():
        return []
    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        return sorted({row["meal_name"].strip().lower() for row in csv.DictReader(handle) if row.get("meal_name")})


DATASET_NAMES = _dataset_names()


def load_user_foods() -> dict[str, dict[str, float]]:
    """Load user-maintained nutrition rows without changing the supplied CSV."""
    if not USER_DATASET_PATH.exists():
        return {}
    foods = {}
    try:
        with USER_DATASET_PATH.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = row.get("meal_name", "").strip().lower()
                if name:
                    foods[name] = {metric: float(row.get(metric, 0) or 0) for metric in ("calories", "protein", "fat", "carbs")}
    except (OSError, ValueError):
        return {}
    return foods


def save_user_food(row: dict[str, object]) -> None:
    """Insert or update one row in the separate user food CSV."""
    USER_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if USER_DATASET_PATH.exists():
        with USER_DATASET_PATH.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
    normalized_name = str(row["meal_name"]).strip().lower()
    clean_row = {field: row.get(field, 0 if field not in ("meal_name",) else "") for field in DATASET_FIELDS}
    clean_row["meal_name"] = str(row["meal_name"]).strip()
    for field in DATASET_FIELDS[1:]:
        clean_row[field] = str(row.get(field, 0))
    replaced = False
    for index, saved in enumerate(existing):
        if saved.get("meal_name", "").strip().lower() == normalized_name:
            existing[index] = clean_row
            replaced = True
            break
    if not replaced:
        existing.append(clean_row)
    with USER_DATASET_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DATASET_FIELDS)
        writer.writeheader()
        writer.writerows(existing)
    clear_estimate_cache()


def user_food_rows() -> list[list[str]]:
    if not USER_DATASET_PATH.exists():
        return []
    with USER_DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        return [[row.get(field, "") for field in DATASET_FIELDS] for row in csv.DictReader(handle)]


def delete_user_food(meal_name: str) -> bool:
    """Delete one custom food row by meal name and return whether it was removed."""
    name = (meal_name or "").strip()
    if not name or not USER_DATASET_PATH.exists():
        return False
    with USER_DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    remaining = [row for row in rows if row.get("meal_name", "").strip().lower() != name.lower()]
    if len(remaining) == len(rows):
        return False
    with USER_DATASET_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DATASET_FIELDS)
        writer.writeheader()
        writer.writerows(remaining)
    clear_estimate_cache()
    return True


def parse_food_items(description: str) -> list[FoodItem]:
    text = re.sub(r"\s+", " ", description.strip())
    if not text:
        return []
    chunks = re.split(r"\s*(?:,|;|\band\b|\bwith\b|\bplus\b)\s*", text, flags=re.I)
    items = []
    for chunk in chunks:
        chunk = chunk.strip(" .")
        if not chunk:
            continue
        match = re.match(r"(?P<portion>\d+(?:\.\d+)?\s*(?:cups?|tbsp|tsp|grams?|g|pieces?|slices?|servings?)?)\s+(?P<name>.+)", chunk, re.I)
        items.append(FoodItem(name=(match.group("name") if match else chunk).strip(), portion=(match.group("portion") if match else "1 serving")))
    return items


def _scale(item: dict[str, float], portion: str) -> dict[str, float]:
    match = re.search(r"\d+(?:\.\d+)?", portion)
    factor = float(match.group()) if match else 1.0
    if "tbsp" in portion.lower() or "tsp" in portion.lower():
        factor /= 4
    return {key: round(value * factor, 1) for key, value in item.items()}


def _local_match(name: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
    user_foods = load_user_foods()
    if normalized in user_foods or normalized in LOCAL_FOODS:
        return normalized
    close = get_close_matches(normalized, list(user_foods) + list(LOCAL_FOODS) + DATASET_NAMES, n=1, cutoff=0.72)
    return close[0] if close else None


def _estimate_local(description: str, items: list[FoodItem]) -> NutritionEstimate | None:
    totals = {key: 0.0 for key in ("calories", "protein", "carbs", "fat")}
    matched = []
    user_foods = load_user_foods()
    for item in items:
        key = _local_match(item.name)
        values = user_foods.get(key or "") or LOCAL_FOODS.get(key or "")
        if values:
            values = _scale(values, item.portion)
            for metric in totals:
                totals[metric] += values[metric]
            matched.append(key.title())
    if not matched:
        return None
    source = "user-food-dataset" if any(name.lower() in user_foods for name in matched) else "local-food-table"
    return NutritionEstimate(name=description, **{k: round(v, 1) for k, v in totals.items()}, note=f"Estimated for {', '.join(matched)}. Portion size and recipe can change these values.", source=source)


def _estimate_usda(description: str, items: list[FoodItem]) -> NutritionEstimate | None:
    api_key = os.getenv("USDA_API_KEY")
    if not api_key:
        return None
    totals = {key: 0.0 for key in ("calories", "protein", "carbs", "fat")}
    found = 0
    try:
        for item in items:
            response = requests.get("https://api.nal.usda.gov/fdc/v1/foods/search", params={"api_key": api_key, "query": item.name, "pageSize": 1}, timeout=8)
            response.raise_for_status()
            foods = response.json().get("foods", [])
            if not foods:
                continue
            nutrients = {n.get("nutrientName", "").lower(): n.get("value", 0) for n in foods[0].get("foodNutrients", [])}
            totals["calories"] += nutrients.get("energy", 0)
            totals["protein"] += nutrients.get("protein", 0)
            totals["carbs"] += nutrients.get("carbohydrate, by difference", 0)
            totals["fat"] += nutrients.get("total lipid (fat)", 0)
            found += 1
    except requests.RequestException:
        return None
    if not found:
        return None
    return NutritionEstimate(name=description, **{k: round(v, 1) for k, v in totals.items()}, note="USDA result; recipe and portion interpretation may vary.", source="usda-fooddata-central")


LLM_SCHEMA = {"name": "string", "calories": "number", "protein": "number", "carbs": "number", "fat": "number", "note": "string"}
PROMPT = "Estimate nutrition for this meal: {meal}\nReturn only valid JSON matching this schema: {schema}. Values are for the described serving; protein, carbs, and fat are grams; calories are kcal. Mention uncertainty in note."


def _parse_llm(text: str, description: str, source: str) -> NutritionEstimate | None:
    try:
        clean = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.I).strip()
        data = json.loads(clean)
        return NutritionEstimate(name=str(data.get("name") or description), calories=max(0, float(data["calories"])), protein=max(0, float(data["protein"])), carbs=max(0, float(data["carbs"])), fat=max(0, float(data["fat"])), note=str(data.get("note") or "LLM estimate; recipe and portion size create uncertainty."), source=source)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _estimate_llm(description: str) -> NutritionEstimate | None:
    prompt = PROMPT.format(meal=description, schema=json.dumps(LLM_SCHEMA))
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        try:
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
            response = client.models.generate_content(model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), contents=prompt)
            result = _parse_llm(response.text, description, "gemini")
            if result:
                return result
        except Exception:
            pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            response = OpenAI().chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), messages=[{"role": "user", "content": prompt}], temperature=0.1)
            result = _parse_llm(response.choices[0].message.content or "", description, "openai")
            if result:
                return result
        except Exception:
            pass
    try:
        response = requests.post(f"{os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')}/api/generate", json={"model": os.getenv("OLLAMA_MODEL", "llama3.2"), "prompt": prompt, "format": "json", "stream": False}, timeout=20)
        response.raise_for_status()
        result = _parse_llm(response.json().get("response", ""), description, "ollama")
        if result:
            return result
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def estimate_meal(description: str) -> NutritionEstimate:
    normalized = (description or "").strip()
    if not normalized:
        return NutritionEstimate(name="Unspecified meal", calories=0, protein=0, carbs=0, fat=0, note="Enter a meal description to receive an estimate.", source="validation")

    now = time.time()
    cached = CACHE.get(normalized.lower())
    if cached is not None:
        cached_at, cached_result = cached
        if now - cached_at <= CACHE_TTL_SECONDS:
            return cached_result

    items = parse_food_items(description)
    if not items:
        result = NutritionEstimate(name="Unspecified meal", calories=0, protein=0, carbs=0, fat=0, note="Enter a meal description to receive an estimate.", source="validation")
        CACHE[normalized.lower()] = (now, result)
        return result
    for stage in (_estimate_local, _estimate_usda):
        result = stage(description, items)
        if result:
            CACHE[normalized.lower()] = (now, result)
            return result
    result = _estimate_llm(description)
    if result:
        CACHE[normalized.lower()] = (now, result)
        return result
    result = NutritionEstimate(name=description, calories=400, protein=20, carbs=45, fat=16, note="Rough placeholder because no local match, API, or LLM provider was available. Treat this as a low-confidence estimate.", source="placeholder")
    CACHE[normalized.lower()] = (now, result)
    return result
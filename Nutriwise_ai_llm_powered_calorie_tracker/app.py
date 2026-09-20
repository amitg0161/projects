"""Gradio interface for NutriWise AI."""

from __future__ import annotations

import gradio as gr
from dotenv import load_dotenv

try:
    from .nutrition import DATASET_FIELDS, NutritionEstimate, USER_DATASET_PATH, clear_estimate_cache, delete_user_food, estimate_meal, save_user_food, user_food_rows
    from .storage import daily_total, delete_meal, save_meal, today_records
except ImportError:
    try:
        from projects.Nutriwise_ai_llm_powered_calorie_tracker.nutrition import DATASET_FIELDS, NutritionEstimate, USER_DATASET_PATH, clear_estimate_cache, delete_user_food, estimate_meal, save_user_food, user_food_rows
        from projects.Nutriwise_ai_llm_powered_calorie_tracker.storage import daily_total, delete_meal, save_meal, today_records
    except ImportError:
        from nutrition import DATASET_FIELDS, NutritionEstimate, USER_DATASET_PATH, clear_estimate_cache, delete_user_food, estimate_meal, save_user_food, user_food_rows
        from storage import daily_total, delete_meal, save_meal, today_records

load_dotenv()

COLUMNS = ["id", "name", "calories", "protein", "carbs", "fat", "source", "created_at"]
EXAMPLE_ESTIMATE = {
    "name": "Example: 1 bowl chicken curry with rice",
    "calories": 540,
    "protein": 32,
    "carbs": 58,
    "fat": 20,
    "note": "Example output for a meal estimate. Replace with your actual estimate after entering a description.",
    "source": "placeholder"
}


def meal_rows() -> list[list]:
    return [[record.get(column, "") for column in COLUMNS] for record in today_records()]


def summary() -> str:
    return f"Today: {daily_total():,.0f} kcal across {len(today_records())} saved meal(s)"


def handle_estimate(description: str) -> dict:
    return estimate_meal(description or "").model_dump()


def handle_save(description: str, current: dict | None) -> tuple[dict, list[list], str]:
    try:
        estimate = NutritionEstimate.model_validate(current) if current else estimate_meal(description or "")
    except Exception:
        estimate = estimate_meal(description or "")
    save_meal(estimate)
    return estimate.model_dump(), meal_rows(), summary()


def handle_delete(record_id: str) -> tuple[list[list], str]:
    if record_id:
        delete_meal(record_id)
    return meal_rows(), summary()


def _safe_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan"}:
        return default
    cleaned = text.replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return default


def _safe_bool(value: object) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return 1
    if text in {"0", "false", "no", "n", "off"}:
        return 0
    return 0


def _is_valid_custom_food_row(row: list[str] | tuple[str, ...]) -> bool:
    if not row:
        return False
    meal_name = str(row[0]).strip()
    return bool(meal_name) and len(meal_name) >= 2


def handle_user_food_save(meal_name: str, num_ingredients: float, calories: float, prep_time: float, protein: float, fat: float, carbs: float, vegan: bool, vegetarian: bool, non_vegetarian: bool, keto: bool, paleo: bool, gluten_free: bool, mediterranean: bool, is_healthy: bool) -> tuple[list[list], str]:
    numeric_values = [calories or 0, protein or 0, fat or 0, carbs or 0]
    if not meal_name or min(numeric_values) < 0:
        return user_food_rows(), "Enter a meal name and non-negative nutrition values."
    save_user_food({
        "meal_name": meal_name,
        "num_ingredients": num_ingredients,
        "calories": calories,
        "prep_time": prep_time,
        "protein": protein,
        "fat": fat,
        "carbs": carbs,
        "vegan": int(vegan),
        "vegetarian": int(vegetarian),
        "non_vegetarian": int(non_vegetarian),
        "keto": int(keto),
        "paleo": int(paleo),
        "gluten_free": int(gluten_free),
        "mediterranean": int(mediterranean),
        "is_healthy": int(is_healthy),
    })
    return user_food_rows(), f"Saved '{meal_name.strip()}' to data/user_foods.csv. Existing names are updated."


def handle_user_food_table_update(rows: list[list[str]]) -> tuple[list[list[str]], str]:
    if rows is None:
        return user_food_rows(), "No custom food rows to update."

    existing_rows = user_food_rows()
    valid_rows = []
    for row in rows:
        if not _is_valid_custom_food_row(row):
            continue
        if len(row) != len(DATASET_FIELDS):
            continue
        record = dict(zip(DATASET_FIELDS, row))
        valid_rows.append({
            "meal_name": str(record.get("meal_name", "")).strip(),
            "num_ingredients": _safe_float(record.get("num_ingredients", 0), 0.0),
            "calories": _safe_float(record.get("calories", 0), 0.0),
            "prep_time": _safe_float(record.get("prep_time", 0), 0.0),
            "protein": _safe_float(record.get("protein", 0), 0.0),
            "fat": _safe_float(record.get("fat", 0), 0.0),
            "carbs": _safe_float(record.get("carbs", 0), 0.0),
            "vegan": _safe_bool(record.get("vegan", 0)),
            "vegetarian": _safe_bool(record.get("vegetarian", 0)),
            "non_vegetarian": _safe_bool(record.get("non_vegetarian", 0)),
            "keto": _safe_bool(record.get("keto", 0)),
            "paleo": _safe_bool(record.get("paleo", 0)),
            "gluten_free": _safe_bool(record.get("gluten_free", 0)),
            "mediterranean": _safe_bool(record.get("mediterranean", 0)),
            "is_healthy": _safe_bool(record.get("is_healthy", 0)),
        })

    if not valid_rows:
        if not existing_rows:
            USER_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
            with USER_DATASET_PATH.open("w", newline="", encoding="utf-8") as handle:
                handle.write(",".join(DATASET_FIELDS) + "\n")
            return [], "Custom food dataset is empty and no valid rows were submitted."
        return existing_rows, "No valid custom food rows were submitted; existing items were kept."

    for record in valid_rows:
        save_user_food(record)
    return user_food_rows(), "Updated custom food dataset. Existing valid entries were kept and new edits were saved."


def handle_user_food_delete(meal_name: str) -> tuple[list[list[str]], str]:
    if not meal_name:
        return user_food_rows(), "Enter a meal name to delete from the custom food dataset."
    deleted = delete_user_food(meal_name)
    if not deleted:
        return user_food_rows(), f"No custom food named '{meal_name.strip()}' was found."
    return user_food_rows(), f"Deleted '{meal_name.strip()}' from the custom food dataset."


def handle_clear_estimate_cache() -> tuple[dict, str]:
    clear_estimate_cache()
    return EXAMPLE_ESTIMATE, "Estimate cache cleared. The next lookup will recalculate fresh values."


def build_app() -> gr.Blocks:
    with gr.Blocks(title="NutriWise AI", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# NutriWise AI\nDescribe a meal in everyday language and get a transparent nutrition estimate.")
        summary_box = gr.Markdown(summary())
        meal_input = gr.Textbox(label="Meal description", placeholder="1 bowl chicken curry with rice and a salad", lines=3)
        with gr.Row():
            estimate_button = gr.Button("Estimate", variant="primary")
            save_button = gr.Button("Save meal")
            clear_cache_button = gr.Button("Clear cache", variant="secondary")
        cache_status = gr.Markdown("Cache is active for 24 hours.")
        latest = gr.JSON(label="Latest estimate", value=EXAMPLE_ESTIMATE)
        gr.Markdown("### Today's saved meals")
        meals = gr.Dataframe(headers=COLUMNS, value=meal_rows(), datatype=["str", "str", "number", "number", "number", "number", "str", "str"], interactive=False)
        delete_id = gr.Textbox(label="Meal ID to delete", placeholder="Paste the ID from the table")
        delete_button = gr.Button("Delete meal")
        estimate_button.click(handle_estimate, inputs=meal_input, outputs=latest)
        save_button.click(handle_save, inputs=[meal_input, latest], outputs=[latest, meals, summary_box])
        clear_cache_button.click(handle_clear_estimate_cache, inputs=None, outputs=[latest, cache_status])
        delete_button.click(handle_delete, inputs=delete_id, outputs=[meals, summary_box])
        gr.Markdown("### Add or update a custom food")
        gr.Markdown("Custom foods are saved separately in `data/user_foods.csv` and override built-in values for future estimates.")
        with gr.Row():
            custom_name = gr.Textbox(label="Meal name", placeholder="Homemade vegetable khichdi")
            custom_calories = gr.Number(label="Calories (kcal)", minimum=0, value=0)
            custom_protein = gr.Number(label="Protein (g)", minimum=0, value=0)
            custom_carbs = gr.Number(label="Carbs (g)", minimum=0, value=0)
            custom_fat = gr.Number(label="Fat (g)", minimum=0, value=0)
        with gr.Row():
            custom_ingredients = gr.Number(label="Number of ingredients", minimum=0, value=0)
            custom_prep = gr.Number(label="Prep time (minutes)", minimum=0, value=0)
            custom_vegan = gr.Checkbox(label="Vegan")
            custom_vegetarian = gr.Checkbox(label="Vegetarian")
            custom_non_vegetarian = gr.Checkbox(label="Non-Vegetarian")
            custom_healthy = gr.Checkbox(label="Healthy")
        with gr.Row():
            custom_keto = gr.Checkbox(label="Keto")
            custom_paleo = gr.Checkbox(label="Paleo")
            custom_gluten_free = gr.Checkbox(label="Gluten-free")
            custom_mediterranean = gr.Checkbox(label="Mediterranean")
            custom_save = gr.Button("Save custom food", variant="secondary")
        custom_status = gr.Markdown()
        custom_foods = gr.Dataframe(headers=DATASET_FIELDS, value=user_food_rows(), interactive=True, label="User food dataset")
        with gr.Row():
            custom_delete_name = gr.Textbox(label="Delete custom food by name", placeholder="Homemade vegetable khichdi")
            custom_delete_button = gr.Button("Delete custom food", variant="secondary")
            custom_update_button = gr.Button("Save table edits", variant="secondary")
        custom_save.click(handle_user_food_save, inputs=[custom_name, custom_ingredients, custom_calories, custom_prep, custom_protein, custom_fat, custom_carbs, custom_vegan, custom_vegetarian, custom_non_vegetarian, custom_keto, custom_paleo, custom_gluten_free, custom_mediterranean, custom_healthy], outputs=[custom_foods, custom_status])
        custom_update_button.click(handle_user_food_table_update, inputs=custom_foods, outputs=[custom_foods, custom_status])
        custom_delete_button.click(handle_user_food_delete, inputs=custom_delete_name, outputs=[custom_foods, custom_status])
    return demo


def launch() -> None:
    build_app().launch()


if __name__ == "__main__":
    launch()
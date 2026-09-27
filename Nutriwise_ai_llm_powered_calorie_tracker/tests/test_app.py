from datetime import date

import projects.Nutriwise_ai_llm_powered_calorie_tracker.nutrition as nutrition
import projects.Nutriwise_ai_llm_powered_calorie_tracker.storage as storage


def test_local_estimate_has_normalized_fields():
    result = nutrition.estimate_meal("2 cups lentil soup")
    assert result.source == "local-food-table"
    assert result.calories == 560
    assert result.protein == 32
    assert set(result.model_dump()) == {"name", "calories", "protein", "carbs", "fat", "note", "source"}


def test_placeholder_never_crashes(monkeypatch):
    monkeypatch.setattr(nutrition, "_estimate_usda", lambda *_: None)
    monkeypatch.setattr(nutrition, "_estimate_llm", lambda *_: None)
    result = nutrition.estimate_meal("a mysterious snack")
    assert result.source == "placeholder"
    assert result.calories > 0


def test_storage_inserts_and_filters_today(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEALS_PATH", tmp_path / "meals.json")
    estimate = nutrition.NutritionEstimate(name="Test meal", calories=100, protein=5, carbs=10, fat=2, note="test", source="test")
    storage.save_meal(estimate, date.today())
    assert len(storage.today_records()) == 1
    assert storage.daily_total() == 100
    assert storage.delete_meal(storage.today_records()[0]["id"])
    assert storage.today_records() == []


def test_custom_food_dataset_is_separate_and_used(tmp_path, monkeypatch):
    custom_path = tmp_path / "user_foods.csv"
    monkeypatch.setattr(nutrition, "USER_DATASET_PATH", custom_path)
    nutrition.save_user_food({"meal_name": "Family Khichdi", "calories": 510, "protein": 19, "carbs": 75, "fat": 14})
    result = nutrition.estimate_meal("family khichdi")
    assert result.source == "user-food-dataset"
    assert result.calories == 510
    nutrition.save_user_food({"meal_name": "Family Khichdi", "calories": 600, "protein": 22, "carbs": 80, "fat": 18})
    assert len(nutrition.user_food_rows()) == 1
    assert nutrition.estimate_meal("family khichdi").calories == 600


def test_custom_food_dataset_can_be_deleted(tmp_path, monkeypatch):
    custom_path = tmp_path / "user_foods.csv"
    monkeypatch.setattr(nutrition, "USER_DATASET_PATH", custom_path)
    nutrition.save_user_food({"meal_name": "Dal Bowl", "calories": 420, "protein": 18, "carbs": 52, "fat": 10})
    assert len(nutrition.user_food_rows()) == 1
    assert nutrition.delete_user_food("Dal Bowl") is True
    assert nutrition.user_food_rows() == []
    assert nutrition.estimate_meal("lentil soup").source == "local-food-table"


def test_table_update_keeps_existing_rows_when_validation_fails(tmp_path, monkeypatch):
    app = __import__("app")
    custom_path = tmp_path / "user_foods.csv"
    monkeypatch.setattr(nutrition, "USER_DATASET_PATH", custom_path)
    monkeypatch.setattr(app, "USER_DATASET_PATH", custom_path)
    nutrition.save_user_food({"meal_name": "Boiled Eggs", "calories": 34, "protein": 4, "fat": 4, "carbs": 12})
    nutrition.save_user_food({"meal_name": "Dal Bowl", "calories": 420, "protein": 18, "fat": 10, "carbs": 52})

    rows = [["", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]]
    result_rows, message = app.handle_user_food_table_update(rows)

    assert len(result_rows) == 2
    assert "kept" in message.lower()
    assert {row[0] for row in result_rows} == {"Boiled Eggs", "Dal Bowl"}


def test_estimate_cache_reuses_recent_results_for_24_hours(monkeypatch):
    monkeypatch.setattr(nutrition, "CACHE", {})
    monkeypatch.setattr(nutrition, "CACHE_TTL_SECONDS", 24 * 60 * 60)
    calls = {"count": 0}

    def fake_local(description, items):
        calls["count"] += 1
        return nutrition.NutritionEstimate(
            name=description,
            calories=250,
            protein=10,
            carbs=20,
            fat=8,
            note="cached",
            source="local-food-table",
        )

    monkeypatch.setattr(nutrition, "_estimate_local", fake_local)
    monkeypatch.setattr(nutrition, "_estimate_usda", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(nutrition, "_estimate_llm", lambda *_args, **_kwargs: None)

    first = nutrition.estimate_meal("2 cups lentil soup")
    second = nutrition.estimate_meal("2 cups lentil soup")

    assert calls["count"] == 1
    assert first.model_dump() == second.model_dump()
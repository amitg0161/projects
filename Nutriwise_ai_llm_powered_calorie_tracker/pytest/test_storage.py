from datetime import date, timedelta

import projects.Nutriwise_ai_llm_powered_calorie_tracker.nutrition as nutrition
import projects.Nutriwise_ai_llm_powered_calorie_tracker.storage as storage


def test_daily_total_ignores_records_from_other_dates(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEALS_PATH", tmp_path / "meals.json")
    estimate = nutrition.NutritionEstimate(name="Old meal", calories=900, protein=30, carbs=90, fat=20, note="test", source="test")

    storage.save_meal(estimate, date.today() - timedelta(days=1))
    storage.save_meal(estimate, date.today())

    assert len(storage.today_records()) == 1
    assert storage.daily_total() == 900


def test_delete_unknown_id_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEALS_PATH", tmp_path / "meals.json")

    assert storage.delete_meal("missing-id") is False
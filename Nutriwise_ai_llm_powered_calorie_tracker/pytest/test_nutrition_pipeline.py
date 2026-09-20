import projects.Nutriwise_ai_llm_powered_calorie_tracker.nutrition as nutrition


def test_parser_extracts_multiple_food_items_and_portions():
    items = nutrition.parse_food_items("2 cups lentil soup with 1 slice toast")

    assert [(item.name, item.portion) for item in items] == [
        ("lentil soup", "2 cups"),
        ("toast", "1 slice"),
    ]


def test_supplied_dataset_is_read_from_data_folder():
    assert nutrition.DATASET_PATH.name == "healthy_meal_plans.csv"
    assert nutrition.DATASET_PATH.parent.name == "data"
    assert nutrition.DATASET_PATH.exists()
    assert nutrition.DATASET_NAMES


def test_empty_description_returns_validation_result():
    result = nutrition.estimate_meal("")

    assert result.source == "validation"
    assert result.calories == 0
    assert "Enter a meal description" in result.note


def test_user_dataset_values_override_builtin_foods(tmp_path, monkeypatch):
    monkeypatch.setattr(nutrition, "USER_DATASET_PATH", tmp_path / "user_foods.csv")
    nutrition.save_user_food({"meal_name": "Lentil Soup", "calories": 500, "protein": 25, "carbs": 60, "fat": 12})

    result = nutrition.estimate_meal("lentil soup")

    assert result.source == "user-food-dataset"
    assert result.calories == 500
    assert result.protein == 25
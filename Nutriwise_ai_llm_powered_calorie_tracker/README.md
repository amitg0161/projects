# NutriWise AI

NutriWise is a local-first calorie tracker that turns natural-language meal descriptions into normalized nutrition estimates and a daily meal log.

## Setup

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The application works without credentials. For the best fallback coverage, install [Ollama](https://ollama.com), then run:

```powershell
ollama pull llama3.2
ollama serve
```

Optionally add `GEMINI_API_KEY` or `OPENAI_API_KEY` to `.env`. Load environment variables before starting from a shell or notebook:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Run

```powershell
python app.py
```

Open the local Gradio URL. The app stores records in `data/meals.json`, creates the file automatically, inserts new records first, and filters the summary to today's date.

The **Add or update a custom food** section lets users enter a meal in the same column format as `data/healthy_meal_plans.csv`. Custom rows are stored separately in `data/user_foods.csv`; the supplied dataset is never overwritten. Saving an existing meal name updates its row. Custom nutrition values take priority over built-in local values for future estimates.

## Estimation pipeline

1. The local food table handles common Indian and home-cooked meals.
2. USDA FoodData Central is used when `USDA_API_KEY` is configured.
3. Providers are tried in order: Gemini, OpenAI, then Ollama.
4. A low-confidence placeholder keeps the interface usable when all providers are unavailable.

Every result contains `name`, `calories`, `protein`, `carbs`, `fat`, `note`, and `source`. The supplied `data/healthy_meal_plans.csv` is used as matching vocabulary; its numeric fields are normalized dataset features, so they are not presented as nutrition units.

## Test

```powershell
pytest -q
```

The original regression tests are in `tests/`. An additional organized suite is in `pytest/`; run both explicitly with:

```powershell
pytest -q tests pytest
```

## Clear cache

```powershell
pytest\clear_cache.py
```
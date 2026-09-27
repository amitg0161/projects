# Projects Portfolio

This repository contains a collection of data-driven mini projects focused on business analysis, forecasting, and data visualization.

## 1. Customer Data Analysis
This project analyzes customer order data to understand spending behavior, category trends, and customer segmentation.

- Dataset: customer orders data with product, category, customer, and revenue information
- Goal: identify high-value customers, top-selling products, and key revenue insights
- Files:
  - Customer Data Analysis/Customer_Orders_Analysis.ipynb
  - Customer Data Analysis/report.md
  - Customer Data Analysis/Datasets/customer_orders/customer_orders.csv

## 2. Forecasting
This project focuses on predicting temperature for upcoming weeks using historical weather data.

- Dataset: Delhi weather data
- Goal: build a forecast based on past patterns and trends
- Files:
  - Forecasting/weather_forcasting.ipynb
  - Forecasting/weather_data_delhi.csv

## 3. Visualization
This project visualizes COVID-19 case trends worldwide for selected countries using Python-based plotting libraries.

- Goal: explore and present global pandemic data in an interactive and readable form
- Files:
  - Visualization/Covid_Visualization.ipynb

## 4. Text-Based Adventure Game
This project is an interactive command-line adventure game in which the player explores an ancient land in search of legendary treasure.

- Objective: find the treasure by making strategic decisions and overcoming obstacles
- Gameplay: enter a player name, choose between a dark forest and a mysterious cave, and respond to location-specific challenges
- Functions:
  - `start_game()`: displays the introduction, collects the player's name, and starts the chosen path
  - `forest_path()`: handles the river and tree decisions
  - `cave_path()`: handles the torch and darkness decisions
  - `main()`: runs the game loop and offers the option to restart
- Outcomes:
  - Winning: follow the river or light the torch to find the treasure
  - Losing: climb the tree or proceed in the dark and end the quest
  - Restarting: replay the adventure after either outcome
- Files:
  - adventure_game.py
- Run command:
  - `python adventure_game.py`
 
## 5. Boston Housing Analysis

This project demonstrates a small, reproducible regression workflow for the Boston housing dataset: data loading, tabular analysis, optional EDA plots, and comparison of linear, Ridge, and Lasso regression.

The dataset is loaded from OpenML because sklearn.datasets.load_boston was removed from scikit-learn. The first run requires network access to download the cached dataset.

## 5. NutriWise AI Calorie Tracker
NutriWise is a local-first calorie tracker that converts natural-language meal descriptions into nutrition estimates and maintains a daily meal log through a Gradio interface.

- Features: local food matching, daily calorie summaries, saved meal records, and custom food management
- Estimation providers: local dataset, optional USDA FoodData Central, Gemini, OpenAI, and Ollama
- Goal: make nutrition tracking usable without requiring external credentials while supporting richer estimates when providers are configured
- Files:
  - Nutriwise_ai_llm_powered_calorie_tracker/app.py
  - Nutriwise_ai_llm_powered_calorie_tracker/nutrition.py
  - Nutriwise_ai_llm_powered_calorie_tracker/storage.py
  - Nutriwise_ai_llm_powered_calorie_tracker/data/healthy_meal_plans.csv
  - Nutriwise_ai_llm_powered_calorie_tracker/README.md
- Run command:
  - `python app.py`

## Summary
These projects demonstrate practical applications of Python, data analysis, forecasting, visualization, AI-assisted applications, functions, conditionals, and interactive programming.

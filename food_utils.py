import pandas as pd
import numpy as np


# -------------------- SEARCH FUNCTION --------------------
def search_food(food_df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Search food by name (case-insensitive) in the dataset.
    Returns a dataframe of matching foods.
    """
    if not query:
        return pd.DataFrame()
    return food_df[food_df['food_name'].str.contains(query, case=False, na=False)].reset_index(drop=True)


# -------------------- FOOD SUGGESTION FUNCTION --------------------
def suggest_foods(food_df: pd.DataFrame, age: int, income: str, macros: dict, meals_per_day: int = 3) -> pd.DataFrame:
    """
    Suggest foods based on user age, income, and daily macros.

    Parameters:
        food_df : pd.DataFrame - dataset with columns:
            'food_name', 'calories_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g'
        age : int - user's age
        income : str - 'Low', 'Medium', 'High'
        macros : dict - target daily macros, e.g. {'protein_g': 150, 'carbs_g': 300, 'fats_g': 70}
        meals_per_day : int - assumed number of meals per day

    Returns:
        pd.DataFrame - top 20 suggested foods sorted by best fit to macros
    """
    df = food_df.copy()

    # Ensure all required columns exist
    for col in ['calories_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g']:
        if col not in df.columns:
            df[col] = 0.0

    # Replace NaNs with 0
    df[['calories_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g']] = df[
        ['calories_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g']].fillna(0.0)

    # Filter out foods with zero calories
    df = df[df['calories_kcal'] > 0]

    # ------------------- INCOME FILTER -------------------
    if income.lower() == "low":
        df = df[df['calories_kcal'] <= 300]  # affordable, lower calorie foods
    elif income.lower() == "high":
        df = df[df['protein_g'] >= 5]  # protein-rich foods

    # ------------------- AGE PREFERENCE -------------------
    if age > 50:
        df = df.sort_values('protein_g', ascending=False)  # prioritize protein for older adults
    else:
        df = df.sort_values('calories_kcal', ascending=False)  # prioritize energy-dense foods for younger adults

    # ------------------- MACRO MATCHING -------------------
    protein_target = macros.get('protein_g', 0) / meals_per_day
    carbs_target = macros.get('carbs_g', 0) / meals_per_day
    fats_target = macros.get('fats_g', 0) / meals_per_day

    df['protein_diff'] = abs(df['protein_g'] - protein_target)
    df['carbs_diff'] = abs(df['carbs_g'] - carbs_target)
    df['fats_diff'] = abs(df['fat_g'] - fats_target)

    # Total macro difference (lower = better match)
    df['total_diff'] = df['protein_diff'] + df['carbs_diff'] + df['fats_diff']

    # Optional: prioritize foods with higher protein or lower sugar
    df['score'] = df['protein_g'] * 1.2 - df['sugar_g'] * 0.5 - df['total_diff']

    # Sort by score descending
    df = df.sort_values(['score', 'total_diff'], ascending=[False, True])

    # Return top 20 suggestions
    return df[['food_name', 'calories_kcal', 'protein_g', 'carbs_g', 'fat_g', 'sugar_g']].head(20).reset_index(
        drop=True)


# -------------------- EXAMPLE USAGE --------------------
if __name__ == "__main__":
    food_df = pd.read_csv("data/merged_foods.csv")
    macros = {'protein_g': 150, 'carbs_g': 300, 'fats_g': 70}

    # Test search
    print(search_food(food_df, "milk").head())

    # Test suggestion
    suggestions = suggest_foods(food_df, age=30, income="Medium", macros=macros)
    print(suggestions)

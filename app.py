import streamlit as st
import pandas as pd
from datetime import datetime
from health_utils import calculate_bmr, calculate_tdee, macro_split
from food_utils import search_food, suggest_foods
from exercise_utils import estimate_burn

# ================= PAGE CONFIG =================
st.set_page_config(page_title="AI Diet & Exercise Planner", page_icon="🏋️", layout="wide")
st.title("🏋️ AI Diet & Exercise Planner")

# ================= LOAD DATA =================
food_df = pd.read_csv("merged_foods.csv")

# ================= SIDEBAR - USER PROFILE =================
st.sidebar.header("User Profile")
weight = st.sidebar.number_input("Weight (kg)", 40, 150, 70)
height = st.sidebar.number_input("Height (cm)", 140, 210, 170)
age = st.sidebar.number_input("Age", 15, 80, 25)
sex = st.sidebar.radio("Sex", ["male", "female"])
activity_level = st.sidebar.selectbox("Activity Level", ["sedentary","light","moderate","active"], index=2)
income = st.sidebar.selectbox("Income Level", ["Low","Medium","High"], index=1)

activity_map = {"sedentary":1.2,"light":1.375,"moderate":1.55,"active":1.725}
bmr = calculate_bmr(weight, height, age, sex)
tdee = calculate_tdee(bmr, activity_map[activity_level])
macros = macro_split(tdee)

st.sidebar.markdown(f"**BMR:** {bmr:.1f} kcal/day")
st.sidebar.markdown(f"**TDEE:** {tdee:.1f} kcal/day")
st.sidebar.write("Recommended macros (grams/day):", macros)

# ================= TABS =================
tab1, tab2, tab3, tab4 = st.tabs(["🍎 Food Log","🏋️ Exercise Log","📊 Daily Totals","🥗 Meal Planner"])

# ================= FOOD LOG =================
with tab1:
    st.subheader("Search Food & Add to Log")
    food_query = st.text_input("Search food...")
    if food_query:
        results = search_food(food_df, food_query)
        st.dataframe(results.head(10) if not results.empty else pd.DataFrame())

    st.markdown("**Log Food Intake**")
    food_name = st.selectbox("Select Food", food_df["food_name"].head(50))
    qty = st.number_input("Quantity (grams)", 10, 1000, 100)

    if st.button("Add Food"):
        food_data = food_df[food_df["food_name"]==food_name].iloc[0]
        calories = food_data["calories_kcal"] * qty / 100
        protein = food_data["protein_g"] * qty / 100
        carbs = food_data["carbs_g"] * qty / 100
        fats = food_data["fat_g"] * qty / 100
        sugar = food_data["sugar_g"] * qty / 100
        if "food_log" not in st.session_state:
            st.session_state.food_log = []
        st.session_state.food_log.append({
            "food":food_name,
            "qty_g":qty,
            "calories":calories,
            "protein":protein,
            "carbs":carbs,
            "fats":fats,
            "sugar":sugar,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.success(f"Added {qty}g of {food_name}!")

    # ---------------- AI Food Suggestions ----------------
    st.markdown("**AI Food Suggestions**")
    if st.button("Suggest Foods"):
        suggestions = suggest_foods(food_df, age, income, macros)
        st.dataframe(suggestions)

    # Display Food Log
    if "food_log" in st.session_state and st.session_state.food_log:
        df_log = pd.DataFrame(st.session_state.food_log)
        
        # Display with delete options
        for i, item in enumerate(st.session_state.food_log):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"{item['food']} - {item['qty_g']}g")
            col2.write(f"{item['calories']:.1f} kcal")
            if col3.button("Delete", key=f"delete_food_{i}"):
                st.session_state.food_log.pop(i)
                st.rerun()
        
        totals = df_log[["calories","protein","carbs","fats","sugar"]].sum()
        st.markdown(f"**Total Calories:** {totals['calories']:.1f} kcal")
        st.markdown(f"Protein {totals['protein']:.1f} g | Carbs {totals['carbs']:.1f} g | Fats {totals['fats']:.1f} g | Sugar {totals['sugar']:.1f} g")

# ================= EXERCISE LOG =================
with tab2:
    st.subheader("Exercise Log")
    exercise = st.selectbox("Activity", ["strength_training","jogging","yoga","cycling","walking"])
    duration = st.number_input("Duration (minutes)", 10, 180, 30)

    if st.button("Add Exercise"):
        kcal_burned = estimate_burn(exercise, duration, weight)
        if "exercise_log" not in st.session_state:
            st.session_state.exercise_log = []
        st.session_state.exercise_log.append({
            "activity":exercise,
            "duration_min":duration,
            "calories_burned":kcal_burned,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.success(f"Logged {duration}min of {exercise}!")

    if "exercise_log" in st.session_state and st.session_state.exercise_log:
        df_ex = pd.DataFrame(st.session_state.exercise_log)
        
        # Display with delete options
        for i, item in enumerate(st.session_state.exercise_log):
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"{item['activity']} - {item['duration_min']}min")
            col2.write(f"{item['calories_burned']:.1f} kcal")
            if col3.button("Delete", key=f"delete_exercise_{i}"):
                st.session_state.exercise_log.pop(i)
                st.rerun()
                
        st.markdown(f"**Total Calories Burned:** {df_ex['calories_burned'].sum():.1f} kcal")

# ================= DAILY TOTALS =================
with tab3:
    st.subheader("Daily Summary")
    total_calories = total_protein = total_carbs = total_fats = total_sugar = 0

    if "food_log" in st.session_state:
        df_log = pd.DataFrame(st.session_state.food_log)
        total_calories += df_log["calories"].sum()
        total_protein += df_log["protein"].sum()
        total_carbs += df_log["carbs"].sum()
        total_fats += df_log["fats"].sum()
        total_sugar += df_log["sugar"].sum()

    calories_burned = 0
    if "exercise_log" in st.session_state:
        df_ex = pd.DataFrame(st.session_state.exercise_log)
        calories_burned += df_ex["calories_burned"].sum()

    net_calories = total_calories - calories_burned

    col1, col2, col3 = st.columns(3)
    col1.metric("Calories In", f"{total_calories:.1f} kcal")
    col2.metric("Calories Out", f"{calories_burned:.1f} kcal")
    col3.metric("Net Calories", f"{net_calories:.1f} kcal", f"{net_calories - tdee:+.0f}")

    st.markdown(f"**Macros:** Protein {total_protein:.1f}g | Carbs {total_carbs:.1f}g | Fats {total_fats:.1f}g")
    
    # Progress bars for macros
    if macros['protein'] > 0:
        st.progress(min(total_protein / macros['protein'], 1.0), text=f"Protein: {total_protein:.1f}g / {macros['protein']}g")
    if macros['carbs'] > 0:
        st.progress(min(total_carbs / macros['carbs'], 1.0), text=f"Carbs: {total_carbs:.1f}g / {macros['carbs']}g")
    if macros['fats'] > 0:
        st.progress(min(total_fats / macros['fats'], 1.0), text=f"Fats: {total_fats:.1f}g / {macros['fats']}g")

# ================= MEAL PLANNER =================
with tab4:
    st.subheader("AI Meal Planner")
    meal_suggestions = suggest_foods(food_df, age, income, macros)
    for i, row in meal_suggestions.iterrows():
        st.markdown(f"**{i+1}. {row['food_name']}** - {row['calories_kcal']:.1f} kcal | P:{row['protein_g']}g C:{row['carbs_g']}g F:{row['fat_g']}g")

    # Export Grocery List
    if st.button("Export Grocery List (CSV)"):
        meal_suggestions.to_csv("grocery_list.csv", index=False)
        st.success("Saved grocery_list.csv!")

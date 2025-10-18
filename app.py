import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io

# ================= UTILITY FUNCTIONS =================
def calculate_bmr(weight, height, age, sex):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if sex == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return bmr

def calculate_tdee(bmr, activity_multiplier):
    """Calculate Total Daily Energy Expenditure"""
    return bmr * activity_multiplier

def macro_split(tdee, protein_ratio=0.3, carb_ratio=0.4, fat_ratio=0.3):
    """Calculate macronutrient split in grams"""
    protein_cals = tdee * protein_ratio
    carb_cals = tdee * carb_ratio
    fat_cals = tdee * fat_ratio
    
    protein_grams = protein_cals / 4
    carb_grams = carb_cals / 4
    fat_grams = fat_cals / 9
    
    return {
        "protein": round(protein_grams, 1),
        "carbs": round(carb_grams, 1),
        "fats": round(fat_grams, 1)
    }

def search_food(food_df, query):
    """Search for foods by name"""
    if not query:
        return pd.DataFrame()
    mask = food_df["food_name"].str.contains(query, case=False, na=False)
    return food_df[mask].copy()

def suggest_foods(food_df, age, income, macros, n_suggestions=5):
    """Suggest foods based on user profile and macros"""
    try:
        # Filter based on income level
        if income == "Low":
            affordable_foods = food_df[food_df["food_name"].str.contains("rice|beans|potato|pasta|bread|egg|chicken", case=False, na=False)]
            suggestions = affordable_foods if not affordable_foods.empty else food_df
        elif income == "High":
            premium_foods = food_df[food_df["food_name"].str.contains("salmon|avocado|quinoa|almond|organic|steak|tuna", case=False, na=False)]
            suggestions = premium_foods if not premium_foods.empty else food_df
        else:
            suggestions = food_df
        
        # Sort by protein content to meet macro goals
        suggestions = suggestions.sort_values("protein_g", ascending=False)
        return suggestions.head(n_suggestions).reset_index(drop=True)
    except:
        return food_df.head(n_suggestions)

def estimate_burn(exercise_type, duration_minutes, weight_kg):
    """Estimate calories burned for various exercises"""
    met_values = {
        "strength_training": 3.5,
        "jogging": 7.0,
        "yoga": 2.5,
        "cycling": 7.5,
        "walking": 3.5,
        "swimming": 8.0,
        "hiit": 9.0,
        "dancing": 5.0
    }
    
    met = met_values.get(exercise_type, 3.0)
    calories_burned = met * weight_kg * (duration_minutes / 60)
    return round(calories_burned, 1)

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI Diet & Exercise Planner", 
    page_icon="🏋️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ================= APP TITLE =================
st.markdown('<h1 class="main-header">🏋️ AI Diet & Exercise Planner</h1>', unsafe_allow_html=True)

# ================= LOAD DATA =================
try:
    food_df = pd.read_csv("data/merged_foods.csv")
except:
    # Fallback data if CSV is not available
    st.error("⚠️ Food database not found. Using sample data.")
    food_df = pd.DataFrame({
        "food_name": ["Apple", "Banana", "Chicken Breast", "Rice", "Salmon", "Eggs", "Broccoli", "Oatmeal"],
        "calories_kcal": [52, 89, 165, 130, 208, 155, 34, 68],
        "protein_g": [0.3, 1.1, 31, 2.7, 20, 13, 2.8, 2.4],
        "carbs_g": [14, 23, 0, 28, 0, 1.1, 7, 12],
        "fat_g": [0.2, 0.3, 3.6, 0.3, 13, 11, 0.4, 1.4],
        "sugar_g": [10, 12, 0, 0, 0, 1.1, 1.7, 0.5]
    })

# ================= SIDEBAR - USER PROFILE =================
st.sidebar.header("👤 User Profile")

with st.sidebar.expander("Personal Information", expanded=True):
    weight = st.number_input("Weight (kg)", 40, 150, 70, help="Your current weight in kilograms")
    height = st.number_input("Height (cm)", 140, 210, 170, help="Your height in centimeters")
    age = st.number_input("Age", 15, 80, 25, help="Your age in years")
    sex = st.radio("Sex", ["male", "female"], horizontal=True)
    activity_level = st.selectbox("Activity Level", 
        ["sedentary (little or no exercise)", 
         "light (light exercise 1-3 days/week)", 
         "moderate (moderate exercise 3-5 days/week)", 
         "active (hard exercise 6-7 days/week)"], 
        index=2)
    income = st.selectbox("Income Level", ["Low", "Medium", "High"], index=1)

# Calculate metrics
activity_map = {
    "sedentary (little or no exercise)": 1.2, 
    "light (light exercise 1-3 days/week)": 1.375, 
    "moderate (moderate exercise 3-5 days/week)": 1.55, 
    "active (hard exercise 6-7 days/week)": 1.725
}

bmr = calculate_bmr(weight, height, age, sex)
tdee = calculate_tdee(bmr, activity_map[activity_level])
macros = macro_split(tdee)

# Display metrics in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Your Metrics")
st.sidebar.markdown(f"""
<div class="metric-card">
    <b>BMR:</b> {bmr:.0f} kcal/day<br>
    <b>TDEE:</b> {tdee:.0f} kcal/day
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("**Recommended Daily Macros:**")
st.sidebar.write(f"🍗 Protein: {macros['protein']}g")
st.sidebar.write(f"🍞 Carbs: {macros['carbs']}g")
st.sidebar.write(f"🥑 Fats: {macros['fats']}g")

# ================= SESSION STATE INITIALIZATION =================
if "food_log" not in st.session_state:
    st.session_state.food_log = []
if "exercise_log" not in st.session_state:
    st.session_state.exercise_log = []

# ================= TABS =================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🍎 Food Log", "🏋️ Exercise Log", "📊 Daily Totals", "📈 Progress", "🥗 Meal Planner"])

# ================= FOOD LOG =================
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Search Food & Add to Log")
        food_query = st.text_input("Search for foods...", placeholder="e.g., apple, chicken, rice")
        
        if food_query:
            results = search_food(food_df, food_query)
            if not results.empty:
                st.dataframe(results[["food_name", "calories_kcal", "protein_g", "carbs_g", "fat_g"]].head(8), 
                           use_container_width=True)
            else:
                st.info("No foods found. Try different keywords.")
        
        st.markdown("---")
        st.subheader("📝 Log Food Intake")
        
        food_col1, food_col2 = st.columns([2, 1])
        with food_col1:
            food_name = st.selectbox("Select Food", food_df["food_name"].unique())
        with food_col2:
            qty = st.number_input("Quantity (grams)", 10, 1000, 100, step=10)
        
        if st.button("➕ Add Food", type="primary"):
            food_data = food_df[food_df["food_name"] == food_name].iloc[0]
            calories = food_data["calories_kcal"] * qty / 100
            protein = food_data["protein_g"] * qty / 100
            carbs = food_data["carbs_g"] * qty / 100
            fats = food_data["fat_g"] * qty / 100
            sugar = food_data["sugar_g"] * qty / 100
            
            st.session_state.food_log.append({
                "food": food_name,
                "qty_g": qty,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fats": fats,
                "sugar": sugar,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            st.success(f"Added {qty}g of {food_name}!")
            st.rerun()
    
    with col2:
        st.subheader("🤖 AI Food Suggestions")
        if st.button("🎯 Get Smart Suggestions", use_container_width=True):
            with st.spinner("Finding optimal foods for you..."):
                suggestions = suggest_foods(food_df, age, income, macros, n_suggestions=8)
                st.dataframe(suggestions[["food_name", "calories_kcal", "protein_g", "carbs_g", "fat_g"]], 
                           use_container_width=True)

    # Display Food Log
    st.markdown("---")
    st.subheader("📋 Today's Food Log")
    if st.session_state.food_log:
        df_log = pd.DataFrame(st.session_state.food_log)
        
        # Add delete buttons for each entry
        cols = st.columns([3, 2, 2, 2, 2, 2, 1])
        headers = ["Food", "Quantity", "Calories", "Protein", "Carbs", "Fats", "Delete"]
        for col, header in zip(cols, headers):
            col.write(f"**{header}**")
        
        for i, item in enumerate(st.session_state.food_log):
            cols = st.columns([3, 2, 2, 2, 2, 2, 1])
            cols[0].write(f"{item['food']} ({item['timestamp']})")
            cols[1].write(f"{item['qty_g']}g")
            cols[2].write(f"{item['calories']:.1f} kcal")
            cols[3].write(f"{item['protein']:.1f}g")
            cols[4].write(f"{item['carbs']:.1f}g")
            cols[5].write(f"{item['fats']:.1f}g")
            
            if cols[6].button("🗑️", key=f"delete_food_{i}"):
                st.session_state.food_log.pop(i)
                st.rerun()
        
        # Totals
        totals = df_log[["calories", "protein", "carbs", "fats", "sugar"]].sum()
        
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Calories", f"{totals['calories']:.1f} kcal")
        col2.metric("Protein", f"{totals['protein']:.1f}g")
        col3.metric("Carbs", f"{totals['carbs']:.1f}g")
        col4.metric("Fats", f"{totals['fats']:.1f}g")
        col5.metric("Sugar", f"{totals['sugar']:.1f}g")
        
    else:
        st.info("No food entries yet. Add some foods to get started!")

# ================= EXERCISE LOG =================
with tab2:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("💪 Log Exercise")
        exercise = st.selectbox("Activity Type", 
                               ["walking", "jogging", "cycling", "strength_training", "yoga", "swimming", "hiit", "dancing"])
        duration = st.number_input("Duration (minutes)", 5, 300, 30, step=5)
        
        if st.button("➕ Add Exercise", type="primary"):
            kcal_burned = estimate_burn(exercise, duration, weight)
            st.session_state.exercise_log.append({
                "activity": exercise,
                "duration_min": duration,
                "calories_burned": kcal_burned,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            st.success(f"Logged {duration} minutes of {exercise}! ({kcal_burned} kcal burned)")
            st.rerun()
    
    with col2:
        st.subheader("📊 Exercise History")
        if st.session_state.exercise_log:
            df_ex = pd.DataFrame(st.session_state.exercise_log)
            
            # Display with delete options
            cols = st.columns([3, 2, 2, 1])
            headers = ["Activity", "Duration", "Calories Burned", "Delete"]
            for col, header in zip(cols, headers):
                col.write(f"**{header}**")
            
            for i, item in enumerate(st.session_state.exercise_log):
                cols = st.columns([3, 2, 2, 1])
                cols[0].write(f"{item['activity'].replace('_', ' ').title()} ({item['timestamp']})")
                cols[1].write(f"{item['duration_min']} min")
                cols[2].write(f"{item['calories_burned']:.1f} kcal")
                
                if cols[3].button("🗑️", key=f"delete_exercise_{i}"):
                    st.session_state.exercise_log.pop(i)
                    st.rerun()
            
            total_burned = df_ex['calories_burned'].sum()
            st.metric("Total Calories Burned Today", f"{total_burned:.1f} kcal")
        else:
            st.info("No exercises logged today.")

# ================= DAILY TOTALS =================
with tab3:
    st.subheader("📈 Daily Summary")
    
    # Calculate totals
    total_calories = total_protein = total_carbs = total_fats = total_sugar = 0
    calories_burned = 0
    
    if st.session_state.food_log:
        df_log = pd.DataFrame(st.session_state.food_log)
        total_calories = df_log["calories"].sum()
        total_protein = df_log["protein"].sum()
        total_carbs = df_log["carbs"].sum()
        total_fats = df_log["fats"].sum()
        total_sugar = df_log["sugar"].sum()
    
    if st.session_state.exercise_log:
        df_ex = pd.DataFrame(st.session_state.exercise_log)
        calories_burned = df_ex["calories_burned"].sum()
    
    net_calories = total_calories - calories_burned
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Calories Consumed", f"{total_calories:.0f} kcal", 
                 f"{total_calories - tdee:+.0f} kcal vs target")
    
    with col2:
        st.metric("Calories Burned", f"{calories_burned:.0f} kcal")
    
    with col3:
        status_color = "normal" if abs(net_calories - tdee) < 100 else "inverse"
        st.metric("Net Calories", f"{net_calories:.0f} kcal", 
                 f"{net_calories - tdee:+.0f} kcal", delta_color=status_color)
    
    # Macronutrient progress
    st.markdown("---")
    st.subheader("🍽️ Macronutrient Progress")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        protein_pct = min((total_protein / macros['protein']) * 100, 100)
        st.metric("Protein", f"{total_protein:.1f}g / {macros['protein']}g", f"{protein_pct:.1f}%")
        st.progress(protein_pct / 100)
    
    with col2:
        carbs_pct = min((total_carbs / macros['carbs']) * 100, 100)
        st.metric("Carbs", f"{total_carbs:.1f}g / {macros['carbs']}g", f"{carbs_pct:.1f}%")
        st.progress(carbs_pct / 100)
    
    with col3:
        fats_pct = min((total_fats / macros['fats']) * 100, 100)
        st.metric("Fats", f"{total_fats:.1f}g / {macros['fats']}g", f"{fats_pct:.1f}%")
        st.progress(fats_pct / 100)
    
    # Calorie comparison chart
    if total_calories > 0:
        st.markdown("---")
        st.subheader("🔥 Calorie Balance")
        
        fig = go.Figure(data=[
            go.Bar(name='Calories In', x=['Today'], y=[total_calories], marker_color='#1f77b4'),
            go.Bar(name='Calories Out', x=['Today'], y=[calories_burned], marker_color='#ff7f0e'),
            go.Bar(name='TDEE Target', x=['Today'], y=[tdee], marker_color='#2ca02c', opacity=0.6)
        ])
        fig.update_layout(barmode='group', showlegend=True, height=300)
        st.plotly_chart(fig, use_container_width=True)

# ================= PROGRESS TAB =================
with tab4:
    st.subheader("📊 Progress Analytics")
    
    # Macronutrient pie chart
    if total_calories > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            macro_cals = {
                'Protein': total_protein * 4,
                'Carbs': total_carbs * 4,
                'Fats': total_fats * 9
            }
            fig = px.pie(values=list(macro_cals.values()), names=list(macro_cals.keys()),
                        title="Macronutrient Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Exercise distribution
            if st.session_state.exercise_log:
                exercise_df = pd.DataFrame(st.session_state.exercise_log)
                fig = px.pie(exercise_df, values='calories_burned', names='activity',
                            title="Exercise Calorie Burn Distribution")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Log some exercises to see distribution charts.")
    else:
        st.info("Log some food and exercise data to see progress analytics.")

# ================= MEAL PLANNER =================
with tab5:
    st.subheader("🍽️ AI Meal Planner")
    
    st.info("💡 Based on your profile, here are personalized food recommendations:")
    
    meal_suggestions = suggest_foods(food_df, age, income, macros, n_suggestions=10)
    
    for i, row in meal_suggestions.iterrows():
        with st.expander(f"🍴 {row['food_name']} - {row['calories_kcal']:.1f} kcal per 100g"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Protein", f"{row['protein_g']}g")
            col2.metric("Carbs", f"{row['carbs_g']}g")
            col3.metric("Fats", f"{row['fat_g']}g")
            col4.metric("Calories", f"{row['calories_kcal']:.1f}")
    
    # Export functionality
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📥 Export Grocery List (CSV)", use_container_width=True):
            meal_suggestions.to_csv("grocery_list.csv", index=False)
            st.success("✅ Grocery list saved as 'grocery_list.csv'!")
    
    with col2:
        if st.button("🔄 Generate New Suggestions", use_container_width=True):
            st.rerun()

# ================= FOOTER =================
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>"
           "💪 Stay consistent and track your progress daily!"
           "</div>", unsafe_allow_html=True)

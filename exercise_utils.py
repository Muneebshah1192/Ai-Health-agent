exercise_met = {
    "strength_training": 6,
    "jogging": 7,
    "yoga": 3,
    "cycling": 8,
    "walking": 3.5
}

def estimate_burn(activity, duration_min, weight_kg):
    met = exercise_met.get(activity, 4)
    kcal_burned = (met * 3.5 * weight_kg / 200) * duration_min
    return kcal_burned
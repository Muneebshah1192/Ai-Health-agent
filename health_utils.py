def calculate_bmr(weight, height, age, sex):
    if sex.lower() == 'male':
        return 10*weight + 6.25*height - 5*age + 5
    else:
        return 10*weight + 6.25*height - 5*age - 161

def calculate_tdee(bmr, activity_factor):
    return bmr * activity_factor

def macro_split(tdee, protein_ratio=0.25, carbs_ratio=0.5, fats_ratio=0.25):
    protein_g = (tdee * protein_ratio) / 4
    carbs_g = (tdee * carbs_ratio) / 4
    fats_g = (tdee * fats_ratio) / 9
    return {"protein_g": protein_g, "carbs_g": carbs_g, "fats_g": fats_g}
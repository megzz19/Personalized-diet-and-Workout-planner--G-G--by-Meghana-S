import pandas as pd
from recommendation_engine import initialize_system, recommend_workouts, recommend_meals, calculate_bmr, calculate_target_macros
import sys

def colored_print(text, color_code):
    print(f"\033[{color_code}m{text}\033[0m")

def test_workouts():
    print("\n" + "="*50)
    print("TEST SUITE 1: WORKOUT RECOMMENDER")
    print("="*50)

    scenarios = [
        {"desc": "Beginner, Home Workout", "level": 0, "home": True},
        {"desc": "Advanced, Gym Workout", "level": 2, "home": False},
    ]

    for sc in scenarios:
        print(f"\nScenario: {sc['desc']}")
        recs = recommend_workouts(sc['level'], sc['home'])
        print(recs[['Exercise_Name', 'Difficulty Level', 'is_home_friendly']].to_string(index=False))

def test_diet():
    print("\n" + "="*50)
    print("TEST SUITE 2: DIET RECOMMENDER")
    print("="*50)

    # Scenarios using approx user stats
    # User A: 25M, 70kg, 175cm, Moderately Active (Maintenance) - Previously tested
    # Let's test diverse goals
    
    # BMR Calculation Check
    # Male, 30, 80kg, 180cm
    bmr = calculate_bmr(age=30, weight_kg=80, height_cm=180, gender='male') 
    # (10*80) + (6.25*180) - (5*30) + 5 = 800 + 1125 - 150 + 5 = 1780
    print(f"BMR Check (Expected ~1780): {bmr}")

    # Scenario 1: Muscle Gain (High Calorie/Protein), Indian Food
    print("\nScenario: Muscle Gain, Indian Food")
    target_macros = calculate_target_macros(bmr, 'very_active', goal='muscle_gain')
    # Use a meal portion (e.g., 30% of day)
    meal_macros = [x * 0.3 for x in target_macros]
    print(f"Target Meal Macros (Cals, P, C, F): {[round(x) for x in meal_macros]}")
    
    try:
        recs = recommend_meals(meal_macros, food_category='Indian')
        if not recs.empty:
             print(recs[['Food_Name', 'Food Category', 'Calories', 'Protein']].head(3).to_string(index=False))
        else:
            print("No recommendations found for this filter.")
    except Exception as e:
        print(f"Error testing Indian filter: {e}")

    # Scenario 2: Low Calorie / Weight Loss
    print("\nScenario: Weight Loss (Low Cal/Carb)")
    target_macros_wl = calculate_target_macros(bmr, 'sedentary', goal='weight_loss')
    meal_macros_wl = [x * 0.3 for x in target_macros_wl]
    print(f"Target Meal Macros (Cals, P, C, F): {[round(x) for x in meal_macros_wl]}")
    
    recs_wl = recommend_meals(meal_macros_wl)
    print(recs_wl[['Food_Name', 'Calories', 'Protein']].head(3).to_string(index=False))

def test_preferences():
    print("\n" + "="*50)
    print("TEST SUITE 3: PREFERENCE FILTERING")
    print("="*50)
    
    # Dummy Macros (Maintenance)
    macros = [500, 20, 60, 20] # Broad target
    
    # 1. Test Vegan
    print("\n[TEST] Vegan Filter (Should exlude Dairy/Meat)")
    try:
        recs = recommend_meals(macros, food_preference='Vegan')
        if not recs.empty:
            print(recs[['Food_Name', 'Food Category', 'Calories', 'Protein']].head(5).to_string(index=False))
        else:
            print("No Vegan options found.")
    except Exception as e:
        print(e)
        
    # 2. Test Non-Veg
    print("\n[TEST] Non-Veg Filter (Should include Meat)")
    try:
        recs = recommend_meals(macros, food_preference='Non-Veg')
        if not recs.empty:
            print(recs[['Food_Name', 'Calories', 'Protein']].head(5).to_string(index=False))
        else:
             print("No Non-Veg options found.")
    except Exception as e:
        print(e)

    # 3. Test Veg (Should include Paneer/Milk but no Meat)
    print("\n[TEST] Veg Filter (Should include Paneer, exclude Chicken)")
    try:
        # Targeting high protein to tempt it to pick Chicken, but forcing Veg
        high_protein_macros = [400, 40, 20, 15] 
        recs = recommend_meals(high_protein_macros, food_preference='Veg')
        if not recs.empty:
            print(recs[['Food_Name', 'Calories', 'Protein']].head(5).to_string(index=False))
    except Exception as e:
        print(e)

def verify():
    print("Initializing System...")
    initialize_system()
    
    test_workouts()
    test_diet()
    test_preferences()

if __name__ == "__main__":
    verify()

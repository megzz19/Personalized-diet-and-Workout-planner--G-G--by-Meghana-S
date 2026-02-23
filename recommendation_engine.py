import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import joblib
import os

# --- Configuration ---
DATA_DIR = "dataset"
ARTIFACTS_DIR = "model_artifacts"
NUTRITION_FILE = os.path.join(DATA_DIR, "final_nutrition.csv")
WORKOUTS_FILE = os.path.join(DATA_DIR, "final_workouts.csv")

# Ensure artifacts directory exists
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# --- Load Data ---
def load_data():
    """Loads nutrition and workout datasets."""
    if not os.path.exists(NUTRITION_FILE) or not os.path.exists(WORKOUTS_FILE):
        raise FileNotFoundError(f"Ensure files exist at {NUTRITION_FILE} and {WORKOUTS_FILE}")
    
    df_nutrition = pd.read_csv(NUTRITION_FILE)
    df_workouts = pd.read_csv(WORKOUTS_FILE)
    return df_nutrition, df_workouts

def classify_food_preference(food_name, food_category):
    """
    Classifies food into 'Veg', 'Non-Veg', or 'Vegan' based on name and category heuristics.
    """
    name_lower = food_name.lower()
    cat_lower = str(food_category).lower()
    
    # Non-Veg Keywords
    non_veg_keywords = ['chicken', 'egg', 'meat', 'fish', 'mutton', 'prawn', 'beef', 'pork', 
                        'ham', 'bacon', 'salami', 'sausage', 'crab', 'lobia curry'] # Lobia is actually veg (black eyed peas), correcting below if needed.
                        # Wait, Lobia is veg. Removing potential false positives if any.
                        # Standard Non-Veg list.
    
    # Refined Non-Veg List
    non_veg_keywords = ['chicken', 'egg', 'meat', 'fish', 'mutton', 'prawn', 'beef', 'pork', 
                        'ham', 'bacon', 'salami', 'sausage', 'crab', 'non vegetarian', 'non-veg']

    if any(keyword in name_lower for keyword in non_veg_keywords):
        return 'Non-Veg'
    
    # Vegan Loop-holes (Dairy/Animal derived) causing it to be just 'Veg'
    # If it's not Non-Veg, it's at least Veg. But is it Vegan?
    # Exclude Dairy and Honey
    dairy_keywords = ['milk', 'cheese', 'paneer', 'butter', 'curd', 'yogurt', 'cream', 'ghee', 
                      'whey', 'lassi', 'buttermilk', 'khoya', 'malai']
    
    if any(keyword in name_lower for keyword in dairy_keywords):
        return 'Veg'
        
    # Heuristic: Baked goods usually have egg/butter unless specified
    baked_keywords = ['cake', 'pastry', 'biscuit', 'cookie', 'pudding', 'pie', 'tart', 'flan', 'mousse', 'souffle']
    if any(keyword in name_lower for keyword in baked_keywords):
        # Could be eggless, but safer to classify as Veg (Lacto-Ovo) or Non-Veg if contains egg
        if 'eggless' in name_lower:
            return 'Veg'
        # If it explicitly says Egg, it was caught in Non-Veg check check? 
        # Wait, 'Egg' is in non_veg_keywords.
        # So here it's likely just dairy/butter.
        return 'Veg'

    # If it passes all above, assume Vegan (Plant-based)
    return 'Vegan'

# Global variables to hold data and models (simulating loaded state)
# In a real app, these might be loaded on startup
_df_nutrition = None
_df_workouts = None
_scaler = None
_diet_model = None
_workout_model = None

# --- Part 1: Workout Recommender ---
def train_workout_model(df_workouts):
    """Trains the KNN model for workouts."""
    # Features: Difficulty Level Encoded, is_home_friendly
    # Assuming 'is_home_friendly' needs casting if it's boolean, user said convert to int
    
    # Check if conversion is needed
    if df_workouts['is_home_friendly'].dtype == 'bool':
        df_workouts['is_home_friendly'] = df_workouts['is_home_friendly'].astype(int)
        
    X = df_workouts[['Difficulty Level Encoded', 'is_home_friendly']].values
    
    model = NearestNeighbors(n_neighbors=5, algorithm='brute', metric='euclidean')
    model.fit(X)
    
    return model

def recommend_workouts(fitness_level, home_workout_preference):
    """
    Recommends top 5 workouts based on fitness level and home preference.
    
    Args:
        fitness_level (int): 0 (Beginner), 1 (Intermediate), 2 (Advanced)
        home_workout_preference (bool): True if home workout, False otherwise
        
    Returns:
        pd.DataFrame: Top 5 recommended exercises
    """
    global _workout_model, _df_workouts
    
    if _workout_model is None or _df_workouts is None:
        raise Exception("Workout model not initialized. Call initialize_system() first.")
    
    # Prepare query vector
    home_pref_int = 1 if home_workout_preference else 0
    query_vector = [[fitness_level, home_pref_int]]
    
    # Find neighbors
    distances, indices = _workout_model.kneighbors(query_vector)
    
    # Retrieve recommended workouts
    recommendations = _df_workouts.iloc[indices[0]]
    return recommendations

# --- Part 2: Diet Recommender ---
def train_diet_model(df_nutrition):
    """Trains the KNN model and Scaler for diet."""
    # Features: Calories, Protein, Carbs, Fats
    features = ['Calories', 'Protein', 'Carbs', 'Fats']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_nutrition[features])
    
    # Metric: cosine similarity (cosine distance in sklearn is 1 - cosine similarity, but neighbors selection works same)
    model = NearestNeighbors(n_neighbors=5, metric='cosine', algorithm='brute')
    model.fit(X_scaled)
    
    return model, scaler

def recommend_meals(target_macro_vector, food_category=None, food_preference=None):
    """
    Recommends meals based on target macros, category, and preference.
    
    Args:
        target_macro_vector (list): [Calories, Protein, Carbs, Fats]
        food_category (str, optional): Filter by 'Food Category' (e.g., 'Veg', 'Non-Veg', 'Indian')
        food_preference (str, optional): 'Veg', 'Non-Veg', or 'Vegan'
        
    Returns:
        pd.DataFrame: Recommended food items
    """
    global _diet_model, _scaler, _df_nutrition
    
    if _diet_model is None or _scaler is None or _df_nutrition is None:
         raise Exception("Diet model not initialized. Call initialize_system() first.")

    current_df = _df_nutrition.copy()
    
    # 0. Apply Preference Filter
    if food_preference:
        # Apply classification on the fly (or better, pre-compute once on load, but here checking requirements)
        # For efficiency, let's vectorise or apply logic
        # Since logic is simple string matching, we can apply:
        current_df['Preference'] = current_df.apply(lambda x: classify_food_preference(x['Food_Name'], x['Food Category']), axis=1)
        
        if food_preference == 'Vegan':
            current_df = current_df[current_df['Preference'] == 'Vegan']
        elif food_preference == 'Veg':
             # Usually 'Veg' requests include Vegan items too? Or strictly Lacto-Veg?
             # Standard behavior: Veg = Veg + Vegan (No meat). Non-Veg = Everything.
             # User asked to "categorize... according to ... veg, non-veg, vegan".
             # If user selects Veg, they likely don't want meat.
             current_df = current_df[current_df['Preference'].isin(['Veg', 'Vegan'])]
        elif food_preference == 'Non-Veg':
             # Non-Veg users can eat anything, but maybe they specifically want meat dishes?
             # Usually implies "Contains Meat".
             current_df = current_df[current_df['Preference'] == 'Non-Veg']
    
    # 1. Apply Category Filter
    if food_category:
        # Check if category exists
        if food_category in current_df['Food Category'].unique():
             current_df = current_df[current_df['Food Category'] == food_category].reset_index(drop=True)
        else:
            # Maybe the user meant the category filter we just added? 
            # Ignoring specific warning to keep output clean, assuming logical inputs.
             pass
    
    if current_df.empty:
        return pd.DataFrame() # Return empty if filter resulted in no data
        
    # Since we filtered, we must re-scale and re-fit OR map back.
    # The user instruction "filter the dataframe first" suggests we should run KNN on the filtered set.
    # Generating a temporary model for the filtered set:
    
    features = ['Calories', 'Protein', 'Carbs', 'Fats']
    temp_scaler = StandardScaler()
    X_subset = temp_scaler.fit_transform(current_df[features])
    
    temp_model = NearestNeighbors(n_neighbors=min(20, len(current_df)), metric='cosine', algorithm='brute')
    temp_model.fit(X_subset)
    
    target_vector_array = np.array([target_macro_vector])
    target_scaled = temp_scaler.transform(target_vector_array)
    
    distances, indices = temp_model.kneighbors(target_scaled)
    
    return current_df.iloc[indices[0]]

# --- Part 3: Integration (BMR Calculation) ---
def calculate_bmr(age, weight_kg, height_cm, gender):
    """
    Calculates BMR using Mifflin-St Jeor Equation.
    Men: (10 × weight) + (6.25 × height) - (5 × age) + 5
    Women: (10 × weight) + (6.25 × height) - (5 × age) - 161
    """
    base_bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender.lower() == 'male':
        return base_bmr + 5
    elif gender.lower() == 'female':
        return base_bmr - 161
    else:
        raise ValueError("Gender must be 'male' or 'female'")

def calculate_target_macros(bmr, activity_level_str, goal='maintenance'):
    """
    Calculates TDEE and splits into macros.
    Simple default macro split: 30% Protein, 35% Carbs, 35% Fats (Adjustable)
    """
    activity_factors = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725
    }
    
    factor = activity_factors.get(activity_level_str.lower(), 1.2)
    tdee = bmr * factor
    
    # Adjust for goal
    if goal == 'weight_loss':
        target_calories = tdee - 500
    elif goal == 'muscle_gain':
        target_calories = tdee + 300
    else:
        target_calories = tdee
        
    # Macro Split (4-9-4 rule: Protein 4cal/g, Fat 9cal/g, Carbs 4cal/g)
    # Using a balanced 30/35/35 split for example
    protein_cals = target_calories * 0.30
    fat_cals = target_calories * 0.35
    carb_cals = target_calories * 0.35
    
    protein_g = protein_cals / 4
    fat_g = fat_cals / 9
    carb_g = carb_cals / 4
    
    # Query vector format: [Calories, Protein, Carbs, Fats]
    # Note: We are returning the TOTAL daily target.
    # The recommendation engine finds "meals". Usually one meal is a fraction of the day.
    # For this task, I will assume the user might input a *per meal* target or we divide this.
    # IMPORTANT: The prompt asks for a function taking 'target_macro_vector'.
    # I will provide the vector for the FULL DAY as calculated here, but in practice use 1/3 for a meal.
    
    return [target_calories, protein_g, carb_g, fat_g]

def initialize_system():
    """Loads data and trains/loads global models."""
    global _df_nutrition, _df_workouts, _scaler, _diet_model, _workout_model
    
    print("Loading datasets...")
    _df_nutrition, _df_workouts = load_data()
    
    print("Training Workout Model...")
    _workout_model = train_workout_model(_df_workouts)
    
    print("Training Diet Model (Base)...")
    _diet_model, _scaler = train_diet_model(_df_nutrition)
    
    # Save Artifacts
    print(f"Saving artifacts to {ARTIFACTS_DIR}...")
    joblib.dump(_workout_model, os.path.join(ARTIFACTS_DIR, "workout_knn.pkl"))
    joblib.dump(_diet_model, os.path.join(ARTIFACTS_DIR, "diet_knn.pkl"))
    joblib.dump(_scaler, os.path.join(ARTIFACTS_DIR, "diet_scaler.pkl"))
    print("Initialization Complete.")

# --- Main Execution for Testing ---
if __name__ == "__main__":
    try:
        initialize_system()
        
        # Test 1: Workout Recommendation
        print("\n--- Test 1: Workout Recommendation (Level 1, Home) ---")
        recs_workout = recommend_workouts(fitness_level=1, home_workout_preference=True)
        print(recs_workout[['Exercise_Name', 'Difficulty Level', 'is_home_friendly']])
        
        # Test 2: BMR & Diet Recommendation
        print("\n--- Test 2: Diet Recommendation ---")
        # User: 25M, 70kg, 175cm, Moderately Active
        bmr = calculate_bmr(25, 70, 175, 'male')
        target_day_macros = calculate_target_macros(bmr, 'moderately_active')
        print(f"Daily Target (Cals, P, C, F): {[round(x,1) for x in target_day_macros]}")
        
        # Assume we want a lunch recommendation (approx 35% of daily intake)
        target_meal_macros = [x * 0.35 for x in target_day_macros]
        print(f"Meal Target: {[round(x,1) for x in target_meal_macros]}")
        
        # Recommend with filter (Assuming 'Veg' might exist or similar, usually 'Vegetarian' or just rely on no filter if unsure)
        # Checking dataset categories with a quick heuristic could help, but for now specific input:
        recs_diet = recommend_meals(target_meal_macros) # No filter first
        print("\nGeneric Meal Recommendations:")
        print(recs_diet[['Food_Name', 'Calories', 'Protein', 'Carbs', 'Fats']])
        
    except Exception as e:
        print(f"An error occurred: {e}")

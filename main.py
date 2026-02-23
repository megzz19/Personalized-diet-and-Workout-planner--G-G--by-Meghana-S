from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import recommendation_engine as re
import uvicorn
import os

# Import Refactored Models & Gemini Service
from models import UserProfile, PlanResponse
from gemini_service import GeminiService

# --- 2. Logic Wrappers for Fallback ---
class WorkoutRecommender:
    @staticmethod
    def get_recommendations(fitness_level_str: str, home_preference: bool):
        # Map activity/fitness level to int (Simple heuristic for demo)
        # sed/light -> 0 (Beginner), mod -> 1 (Int), very -> 2 (Adv)
        mapping = {
            'sedentary': 0, 'lightly_active': 0,
            'moderately_active': 1, 'very_active': 2
        }
        level = mapping.get(fitness_level_str, 0)
        
        recs = re.recommend_workouts(fitness_level=level, home_workout_preference=home_preference)
        return recs.to_dict(orient='records')

class DietOptimizer:
    @staticmethod
    def generate_plan(age, weight, height, gender, activity, goal, food_type):
        # 1. BMR & TDEE
        bmr = re.calculate_bmr(age, weight, height, gender)
        target_macros = re.calculate_target_macros(bmr, activity, goal) # [Cals, P, C, F]
        
        # 2. Get Recommendations (Assuming 3 meals structure for simplicity, dividing daily target by 3)
        meal_target = [x / 3 for x in target_macros]
        
        recommendations = re.recommend_meals(
            target_macro_vector=meal_target, 
            food_preference=food_type
        )
        
        plan = recommendations.to_dict(orient='records')
        stats = {
            "bmr": round(bmr, 2),
            "tdee": round(bmr * 1.2, 2), # Approx, re-calc if needed
            "target_calories": round(target_macros[0], 2),
            "target_protein": round(target_macros[1], 1),
            "target_carbs": round(target_macros[2], 1),
            "target_fats": round(target_macros[3], 1)
        }
        return plan, stats

# --- 3. FastAPI App ---
app = FastAPI(title="G&G Fitness Planner API", version="1.0")

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
gemini_service = GeminiService()

# Startup Event
@app.on_event("startup")
def startup_event():
    print("Initializing Recommendation Engine...")
    try:
        re.initialize_system()
        print("Heuristic Engine Ready.")
    except Exception as e:
        print(f"Failed to initialize engine: {e}")

# Endpoints
@app.post("/generate-plan", response_model=PlanResponse)
async def generate_plan(user: UserProfile = Body(...)):
    try:
        # Try Gemini First
        if gemini_service.model:
            print("Attempting to generate plan with Gemini...")
            gemini_plan = gemini_service.generate_fitness_plan(user)
            if gemini_plan:
                print("Gemini Plan Generated Successfully.")
                return gemini_plan
            else:
                print("Gemini generation failed. Falling back to heuristic engine.")
        
        # Fallback to Heuristic Engine
        print("Using Heuristic Engine.")
        
        # Use user provided activity level
        current_activity_level = user.activityLevel

        # Generate Workout Plan
        workout_plan = WorkoutRecommender.get_recommendations(current_activity_level, home_preference=False)
        
        # Generate Diet Plan (Base 1-day plan)
        base_diet_plan, stats = DietOptimizer.generate_plan(
            user.age, user.weight, user.height, user.gender, 
            current_activity_level, user.goal, user.foodType
        )
        
        # Convert to 7-Day Structure for Consistency
        diet_plan_7_days = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in days:
            # Randomly sample 4-5 meals from the bigger list for variety
            import random
            daily_meals = []
            if len(base_diet_plan) > 5:
                # Pick 4 to 5 meals
                num_meals = random.randint(4, 5)
                daily_meals = random.sample(base_diet_plan, min(num_meals, len(base_diet_plan)))
            else:
                daily_meals = base_diet_plan

            diet_plan_7_days.append({
                "day": day,
                "meals": daily_meals
            })
        
        # Budget/Cultural Tips (Static placeholders based on logic)
        tips = [
            f"Since you are {user.foodType}, prioritize local seasonal produce for better budget.",
            f"To achieve '{user.goal}', consistency is key. Stick to the calorie target of {stats['target_calories']} kcal."
        ]
        
        if user.foodType == 'Veg' or user.foodType == 'Vegan':
            tips.append("Lentils and Chickpeas are great budget-friendly protein sources.")
        if user.foodType == 'Non-Veg':
            tips.append("Eggs are the most cost-effective protein source.")

        return {
            "diet_plan": diet_plan_7_days,
            "workout_plan": workout_plan,
            "additional_tips": tips,
            "daily_stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-food")
async def analyze_food(file: UploadFile = File(...)):
    """Analyze a food image using Gemini's multimodal capabilities."""
    try:
        if not gemini_service.model:
            raise HTTPException(status_code=503, detail="Gemini API is not configured. Please set GEMINI_API_KEY.")
        
        # Read image bytes
        image_bytes = await file.read()
        
        # Analyze with Gemini
        result = gemini_service.analyze_food_image(image_bytes, file.content_type)
        
        if result:
            return result
        else:
            raise HTTPException(status_code=500, detail="Failed to analyze food image. Please try again with a clearer image.")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

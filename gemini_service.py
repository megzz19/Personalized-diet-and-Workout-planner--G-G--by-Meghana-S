import google.generativeai as genai
import os
import json
from models import UserProfile, PlanResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not found. Gemini Service disabled.")

    def generate_fitness_plan(self, user: UserProfile) -> dict:
        """
        Generates a personalized fitness and diet plan using Gemini API.
        Returns a dictionary compatible with PlanResponse model or None if failed.
        """
        if not self.model:
            return None

        prompt = f"""
        Act as an expert fitness coach and nutritionist. Create a personalized 7-DAY diet and workout plan for the following user.
        
        CRITICAL INSTRUCTIONS:
        1. You MUST provide a diet plan for exactly 7 separate days (Monday to Sunday).
        2. **VARIETY IS KEY**: Do NOT repeat the same meals every day. Provide different breakfast, lunch, and dinner options for each day to keep the user engaged.
        3. Consider the user's Health Condition and adjust the recommendations accordingly.

        User Profile:
        - Age: {user.age}
        - Gender: {user.gender}
        - Height: {user.height} cm
        - Weight: {user.weight} kg
        - Activity Level: {user.activityLevel}
        - Health Condition: {user.health_condition}
        - Dietary Preference: {user.foodType}
        - Goal: {user.goal}

        You must return the response in strict JSON format matching the following structure exactly. Do not include markdown formatting (like ```json), just the raw JSON.

        Structure:
        {{
            "diet_plan": [
                {{
                   "day": "Day 1 (Monday)",
                   "meals": [
                        {{
                            "Food_Name": "Dish Name",
                            "Food Category": "Veg/Non-Veg/Vegan",
                            "Calories": 0,
                            "Protein": 0,
                            "Carbs": 0,
                            "Fats": 0
                        }},
                        ... (3-4 varied meals)
                   ]
                }},
                {{
                   "day": "Day 2 (Tuesday)",
                   "meals": [ ... different meals ... ]
                }},
                ... (Continue for all 7 days with unique meals)
            ],
            "workout_plan": [
                {{
                    "Exercise_Name": "Exercise Name",
                    "Difficulty Level": "Beginner/Intermediate/Advanced",
                    "Equipment": "None/Dumbbells/Gym Machine",
                    "Sets": "3",
                    "Reps": "10-12"
                }},
                ... (Provide 4-5 exercises)
            ],
            "additional_tips": [
                "Tip 1",
                "Tip 2",
                "Tip 3"
            ],
            "daily_stats": {{
                "target_calories": 0,
                "target_protein": 0,
                "target_carbs": 0,
                "target_fats": 0
            }}
        }}

        Ensure the stats are calculated correctly based on the user's BMR/TDEE and goal.
        """

        try:
            response = self.model.generate_content(prompt)
            
            # Clean response text (remove markdown if present)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text)
            
            # Validate structure lightly (Pydantic in main.py will handle strict validation)
            if "diet_plan" in data and "workout_plan" in data:
                return data
            else:
                print("Gemini response missing required keys.")
                return None

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None

    def analyze_food_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        """
        Analyzes a food image using Gemini's multimodal capabilities.
        Returns a dictionary with nutritional analysis.
        """
        if not self.model:
            return None

        prompt = """
        You are an expert nutritionist. Analyze the food in this image thoroughly.

        Provide the following details in strict JSON format (no markdown, just raw JSON):
        {
            "food_name": "Name of the dish/food",
            "food_category": "Veg / Non-Veg / Vegan",
            "description": "Brief description of the dish",
            "estimated_serving_size": "e.g., 1 plate, 250g, 1 bowl",
            "nutrition_per_serving": {
                "calories": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fats_g": 0,
                "fiber_g": 0,
                "sugar_g": 0
            },
            "ingredients": ["ingredient 1", "ingredient 2", "..."],
            "health_benefits": ["benefit 1", "benefit 2"],
            "health_warnings": ["warning 1 (if any)"],
            "healthier_alternatives": ["alternative 1", "alternative 2"],
            "overall_health_rating": "Healthy / Moderate / Unhealthy",
            "detailed_analysis": "A paragraph explaining why this food is good or bad, who should eat it, and any dietary considerations."
        }

        Be accurate with the calorie and macro estimates. If you cannot identify the food, say so in the food_name field.
        """

        try:
            import PIL.Image
            import io

            image = PIL.Image.open(io.BytesIO(image_bytes))
            response = self.model.generate_content([prompt, image])

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())
            return data

        except Exception as e:
            print(f"Error analyzing food image: {e}")
            return None

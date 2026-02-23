from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re as regex_lib
import html

# --- Pydantic Models & Validation ---
class UserProfile(BaseModel):
    age: int = Field(..., ge=10, le=100, description="Age in years (10-100)")
    height: float = Field(..., ge=50, le=250, description="Height in cm")
    weight: float = Field(..., ge=20, le=300, description="Weight in kg")
    gender: str = Field(..., pattern="^(male|female)$", description="Gender (male/female)")
    foodType: str = Field(..., pattern="^(Veg|Non-Veg|Vegan)$", description="Dietary Preference")
    activityLevel: str = Field(..., description="Activity Level")
    health_condition: str = Field(..., description="Any pre-existing health conditions or dietary restrictions")
    goal: str = Field(..., min_length=3, max_length=50, description="Fitness Goal")

    @validator('goal')
    def sanitize_goal(cls, v):
        # Basic sanitization: Strip HTML tags and dangerous characters
        clean_text = html.escape(v)
        # Remove potential script tags via regex just in case
        clean_text = regex_lib.sub(r'<script.*?>.*?</script>', '', clean_text, flags=regex_lib.DOTALL)
        return clean_text

class DailyDiet(BaseModel):
    day: str
    meals: List[dict]

class PlanResponse(BaseModel):
    diet_plan: List[DailyDiet]
    workout_plan: List[dict]
    additional_tips: List[str]
    daily_stats: dict

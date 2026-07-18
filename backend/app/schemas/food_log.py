from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

class FoodLogBase(BaseModel):
    food_name: str
    quantity: float
    serving_size: str
    calories: Optional[float] = 0.0
    protein: Optional[float] = 0.0
    carbohydrates: Optional[float] = 0.0
    fat: Optional[float] = 0.0
    iron: Optional[float] = 0.0
    calcium: Optional[float] = 0.0
    vitamin_d: Optional[float] = 0.0
    vitamin_b12: Optional[float] = 0.0
    zinc: Optional[float] = 0.0

class FoodLogCreate(FoodLogBase):
    meal_type: str  # Breakfast, Lunch, Dinner, Snack

    @field_validator('meal_type')
    @classmethod
    def validate_meal_type(cls, v: str) -> str:
        allowed = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
        if v not in allowed:
            raise ValueError(f"meal_type must be one of {allowed}")
        return v

class FoodLogOut(FoodLogBase):
    id: int
    user_id: int
    meal_type: str
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DailySummary(BaseModel):
    calories: float = 0.0
    protein: float = 0.0
    carbohydrates: float = 0.0
    fat: float = 0.0
    iron: float = 0.0
    calcium: float = 0.0
    vitamin_d: float = 0.0
    vitamin_b12: float = 0.0
    zinc: float = 0.0


class FoodCatalogOut(BaseModel):
    id: int
    fdc_id: Optional[int] = None
    food_name: str
    source: Optional[str] = None
    calories_kcal: Optional[float] = 0.0
    protein_g: Optional[float] = 0.0
    carbs_g: Optional[float] = 0.0
    fat_g: Optional[float] = 0.0
    iron_mg: Optional[float] = 0.0
    calcium_mg: Optional[float] = 0.0
    vitamin_d_mcg: Optional[float] = 0.0
    vitamin_b12_mcg: Optional[float] = 0.0
    zinc_mg: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)

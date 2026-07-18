from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Input ──────────────────────────────────────────────────────────────────────

class PredictInput(BaseModel):
    """
    Patient demographic and physiological attributes sent by the frontend.
    All values come from the user's registered profile or can be overridden.
    """
    age: Optional[float]          = Field(None, ge=18, le=100, description="Age in years")
    gender: Optional[int]         = Field(None, ge=0, le=1,   description="0 = Male, 1 = Female")
    race_ethnicity: Optional[int] = Field(3,    ge=1, le=7,    description="NHANES race/ethnicity code (1-7)")
    weight_kg: Optional[float]    = Field(None, gt=0,          description="Body weight in kilograms")
    height_cm: Optional[float]    = Field(None, gt=0,          description="Height in centimetres")
    bmi: Optional[float]          = Field(None, gt=0,          description="Body Mass Index (kg/m^2)")
    activity_level: Optional[str] = Field(None,                description="User physical activity level")
    include_shap: bool            = Field(True,                description="Include SHAP feature explanations")


# ── SHAP explanation item ──────────────────────────────────────────────────────

class ShapFeature(BaseModel):
    feature: str
    value: float
    contribution: float


# ── Per-nutrient result ────────────────────────────────────────────────────────

class NutrientRisk(BaseModel):
    risk_score: float                     # probability 0.0 – 1.0
    risk_label: str                       # "Low", "Moderate", "High"
    explanation: Optional[List[ShapFeature]] = None


class RecommendationFoodItem(BaseModel):
    food_name: str
    nutrient_amount: float
    unit: str

class NutrientTarget(BaseModel):
    nutrient: str
    target_value: float
    unit: str

class RecommendationsOut(BaseModel):
    foods_to_eat: List[RecommendationFoodItem]
    foods_to_avoid: List[str]
    daily_nutrient_targets: List[NutrientTarget]
    short_health_advice: str

# ── Full prediction response ───────────────────────────────────────────────────

class PredictResponse(BaseModel):
    user_id: int
    prediction_date: datetime
    results: Dict[str, NutrientRisk]      # keyed by nutrient name
    # Flat risk scores for backward compatibility and DB storage
    iron_risk: float
    vitamin_d_risk: float
    vitamin_b12_risk: float
    calcium_risk: float
    zinc_risk: float
    recommendations: Optional[RecommendationsOut] = None


# ── History schema ─────────────────────────────────────────────────────────────

class PredictionHistoryOut(BaseModel):
    id: int
    user_id: int
    iron_risk: float
    vitamin_d_risk: float
    vitamin_b12_risk: float
    calcium_risk: float
    zinc_risk: float
    prediction_date: datetime

    model_config = ConfigDict(from_attributes=True)

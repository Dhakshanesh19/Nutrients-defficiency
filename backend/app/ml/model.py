"""
app/ml/model.py
---------------
Bridge module: wraps backend/ml/predict.py for use inside FastAPI.
Adds lazy loading and risk-label classification.
"""
import sys
import os

# Add backend root to path so `ml.predict` can be imported
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from ml.predict import predict_deficiencies          # real XGBoost inference
from typing import Dict, Optional


def _risk_label(score: Optional[float]) -> str:
    """Convert a probability score to a human-readable risk label."""
    if score is None:
        return "Unknown"
    if score >= 0.70:
        return "High"
    if score >= 0.45:
        return "Moderate"
    return "Low"


def run_prediction(
    age: float,
    gender: int,
    race_ethnicity: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Dict[str, Dict]:
    """
    Calls the real models and returns risk scores + labels.
    """
    raw_scores = predict_deficiencies(
        age=age,
        gender=gender,
        race_ethnicity=race_ethnicity,
        weight_kg=weight_kg,
        height_cm=height_cm,
        bmi=bmi,
        activity_level=activity_level,
        nutrient_totals=nutrient_totals,
    )

    return {
        nutrient: {
            "risk_score": score if score is not None else 0.0,
            "risk_label": _risk_label(score),
        }
        for nutrient, score in raw_scores.items()
    }

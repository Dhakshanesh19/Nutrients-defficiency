"""
app/ml/explainer.py
-------------------
Bridge module: wraps backend/ml/shap_explain.py for use inside FastAPI.
"""
import sys
import os

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from ml.shap_explain import explain_prediction       # real SHAP explainer
from typing import Dict, List, Optional


def run_explanation(
    nutrient: str,
    age: float,
    gender: int,
    race_ethnicity: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Optional[List[Dict]]:
    """
    Returns SHAP feature contribution list for a single nutrient.
    Returns None if the model file is not yet available.
    """
    try:
        return explain_prediction(
            nutrient=nutrient,
            age=age,
            gender=gender,
            race_ethnicity=race_ethnicity,
            weight_kg=weight_kg,
            height_cm=height_cm,
            bmi=bmi,
            activity_level=activity_level,
            nutrient_totals=nutrient_totals,
        )
    except FileNotFoundError:
        return None

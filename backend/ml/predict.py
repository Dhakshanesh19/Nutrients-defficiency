"""
predict.py
----------
Loads the best-performing model for each deficiency target and runs
inference. Automatically detects whether the saved model is XGBoost
or Random Forest by reading {nutrient}_model_type.txt.

Usage:
    from ml.predict import predict_deficiencies

    result = predict_deficiencies(
        age=35, gender=1, race_ethnicity=3,
        weight_kg=68.0, height_cm=165.0, bmi=24.9
    )
    # -> {"iron": 0.72, "calcium": 0.35, "vitamin_d": 0.91,
    #     "vitamin_b12": 0.21, "zinc": 0.58}
"""
import os
import json
import pickle
from typing import Dict, Optional

import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")

DEFICIENCY_TARGETS = ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]

# ── Lazy caches ────────────────────────────────────────────────────────────────
_model_cache:        Dict[str, object]  = {}
_model_type_cache:   Dict[str, str]     = {}
_feature_names:      Optional[list]     = None


# ── Loaders ────────────────────────────────────────────────────────────────────

def get_feature_names() -> list:
    """Load and cache the ordered feature name list."""
    global _feature_names
    if _feature_names is None:
        path = os.path.join(MODELS_DIR, "feature_names.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"feature_names.json not found at {path}. "
                "Run `python ml/train.py` first."
            )
        with open(path) as f:
            _feature_names = json.load(f)
    return _feature_names


def get_model_type(nutrient: str) -> str:
    """Return 'xgboost' or 'random_forest' for the given nutrient."""
    if nutrient not in _model_type_cache:
        type_path = os.path.join(MODELS_DIR, f"{nutrient}_model_type.txt")
        if not os.path.exists(type_path):
            # Legacy fallback: assume xgboost if only .json exists
            if os.path.exists(os.path.join(MODELS_DIR, f"{nutrient}_model.json")):
                _model_type_cache[nutrient] = "xgboost"
            else:
                raise FileNotFoundError(
                    f"Model type file not found for '{nutrient}'. "
                    "Run `python ml/train.py` first."
                )
        else:
            with open(type_path) as f:
                _model_type_cache[nutrient] = f.read().strip()
    return _model_type_cache[nutrient]


def load_model(nutrient: str) -> object:
    """Load and cache the best model for the given nutrient."""
    if nutrient not in _model_cache:
        model_type = get_model_type(nutrient)

        if model_type == "xgboost":
            path = os.path.join(MODELS_DIR, f"{nutrient}_model.json")
            if not os.path.exists(path):
                raise FileNotFoundError(f"XGBoost model not found: {path}")
            model = xgb.XGBClassifier()
            model.load_model(path)

        elif model_type == "random_forest":
            path = os.path.join(MODELS_DIR, f"{nutrient}_model.pkl")
            if not os.path.exists(path):
                raise FileNotFoundError(f"RandomForest model not found: {path}")
            with open(path, "rb") as f:
                model = pickle.load(f)

        else:
            raise ValueError(f"Unknown model type '{model_type}' for nutrient '{nutrient}'.")

        _model_cache[nutrient] = model

    return _model_cache[nutrient]


# ── Inference ──────────────────────────────────────────────────────────────────

def predict_deficiencies(
    age: float,
    gender: int,
    race_ethnicity: int,
    weight_kg: float,
    height_cm: float,
    bmi: float,
    activity_level: Optional[str] = None,
    nutrient_totals: Optional[Dict[str, float]] = None,
) -> Dict[str, Optional[float]]:
    """
    Run deficiency risk predictions for all 5 nutrients.

    Parameters:
        age            : Age in years (18–80)
        gender         : 0 = Male, 1 = Female
        race_ethnicity : NHANES race/ethnicity code (1–7)
        weight_kg      : Body weight in kilograms
        height_cm      : Height in centimetres
        bmi            : Body Mass Index (kg/m²)
        activity_level : Optional physical activity description
        nutrient_totals: Optional dictionary of daily nutrient intakes

    Returns:
        dict mapping nutrient name -> risk probability (0.0–1.0)
        Value is None if the model is not yet trained.
    """
    feature_names = get_feature_names()
    feature_map   = {
        "age":            age,
        "gender":         gender,
        "race_ethnicity": race_ethnicity,
        "weight_kg":      weight_kg,
        "height_cm":      height_cm,
        "bmi":            bmi,
    }
    if nutrient_totals:
        feature_map.update(nutrient_totals)

    X = np.array([[feature_map.get(f, 0.0) for f in feature_names]], dtype=float)

    results: Dict[str, Optional[float]] = {}
    for nutrient in DEFICIENCY_TARGETS:
        try:
            model  = load_model(nutrient)
            prob   = float(model.predict_proba(X)[0][1])
            results[nutrient] = round(prob, 4)
        except FileNotFoundError:
            results[nutrient] = None

    return results


def get_loaded_model_types() -> Dict[str, str]:
    """Return a dict of {nutrient: model_type} for all trained targets."""
    info = {}
    for nutrient in DEFICIENCY_TARGETS:
        try:
            info[nutrient] = get_model_type(nutrient)
        except FileNotFoundError:
            info[nutrient] = "not_trained"
    return info


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Model type selection:")
    for n, t in get_loaded_model_types().items():
        print(f"  {n:<14} -> {t}")

    print("\nSample prediction (Female, 32, BMI 22.9):")
    sample = predict_deficiencies(
        age=32, gender=1, race_ethnicity=3,
        weight_kg=60.0, height_cm=162.0, bmi=22.9
    )
    for k, v in sample.items():
        status = "!! HIGH RISK" if v and v > 0.70 else ("~ Moderate" if v and v > 0.45 else "OK")
        val_str = f"{v:.4f}" if v is not None else "N/A (not trained)"
        print(f"  {k:<14} : {val_str}  {status}")

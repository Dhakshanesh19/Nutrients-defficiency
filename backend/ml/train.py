"""
train.py
--------
Trains Random Forest AND XGBoost binary classifiers for all 5 deficiency
targets (Iron, Calcium, Vitamin D, Vitamin B12, Zinc).

For each nutrient:
  1. Same train/test split used for both models.
  2. Both evaluated on: Accuracy, Precision, Recall, F1, ROC-AUC.
  3. Best model auto-saved based on ROC-AUC score.
  4. Comparison table printed to console.

Outputs (ml/models/):
  {nutrient}_model.json        <- XGBoost (native) or RF pickle, best model
  {nutrient}_model_type.txt    <- "xgboost" or "random_forest"
  feature_names.json           <- ordered feature column list
  metrics.json                 <- full comparison metrics for all nutrients
  comparison_table.csv         <- printable summary table

Run:
    python ml/train.py
"""
import os
import json
import pickle
import textwrap
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR   = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
FEATURE_COLS = ["age", "gender", "race_ethnicity", "weight_kg", "height_cm", "bmi"]

TARGETS = {
    "iron":        "label_iron",
    "calcium":     "label_calcium",
    "vitamin_d":   "label_vitamin_d",
    "vitamin_b12": "label_vitamin_b12",
    "zinc":        "label_zinc",
}

RANDOM_STATE = 42
TEST_SIZE    = 0.20


# ── Helpers ────────────────────────────────────────────────────────────────────

def evaluate(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    """Compute all five evaluation metrics."""
    return {
        "accuracy":  round(accuracy_score(y_true, y_pred),                           4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0),         4),
        "recall":    round(recall_score(y_true, y_pred, zero_division=0),             4),
        "f1":        round(f1_score(y_true, y_pred, zero_division=0),                4),
        "roc_auc":   round(roc_auc_score(y_true, y_prob),                            4),
    }


def train_xgboost(X_train, y_train, X_test, scale_pos_weight: float) -> tuple:
    """Train XGBoost and return (model, y_pred, y_prob)."""
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, verbose=False)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    return model, y_pred, y_prob


def train_random_forest(X_train, y_train, X_test, scale_pos_weight: float) -> tuple:
    """Train Random Forest and return (model, y_pred, y_prob)."""
    # Convert scale_pos_weight to class_weight dict
    class_weight = {0: 1.0, 1: scale_pos_weight}
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=5,
        class_weight=class_weight,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    return model, y_pred, y_prob


def save_model(nutrient: str, model, model_type: str) -> str:
    """Save model to disk. Returns the saved path."""
    if model_type == "xgboost":
        path = os.path.join(MODELS_DIR, f"{nutrient}_model.json")
        model.save_model(path)
    else:
        path = os.path.join(MODELS_DIR, f"{nutrient}_model.pkl")
        with open(path, "wb") as f:
            pickle.dump(model, f)

    # Record which type was saved
    type_path = os.path.join(MODELS_DIR, f"{nutrient}_model_type.txt")
    with open(type_path, "w") as f:
        f.write(model_type)

    return path


def print_comparison_table(nutrient: str, xgb_m: dict, rf_m: dict, winner: str):
    """Print a formatted side-by-side comparison table."""
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    header  = f"\n{'='*60}\n  {nutrient.upper().replace('_', ' ')} — Model Comparison\n{'='*60}"
    row_fmt = "  {:<12} {:>10} {:>10} {:>10}"
    print(header)
    print(row_fmt.format("Metric", "XGBoost", "Rand.Forest", "Winner"))
    print("  " + "-" * 46)
    for m in metrics:
        xv  = xgb_m[m]
        rfv = rf_m[m]
        w   = "XGBoost" if xv >= rfv else "RF"
        print(row_fmt.format(m.upper(), f"{xv:.4f}", f"{rfv:.4f}", w))
    print(f"\n  >> Best overall model saved: {winner.upper()}")


# ── Main Training Loop ─────────────────────────────────────────────────────────

print("=" * 60)
print("  Nutrition Deficiency Prediction — Model Training")
print("=" * 60)

print(f"\nLoading nhanes_master.csv ...")
master = pd.read_csv(os.path.join(PROC_DIR, "nhanes_master.csv"))
feature_cols = [c for c in FEATURE_COLS if c in master.columns]
label_cols   = [c for c in master.columns if c.startswith("label_")]

print(f"  Shape    : {master.shape}")
print(f"  Features : {feature_cols}")
print(f"  Targets  : {label_cols}")

# Save feature names
with open(os.path.join(MODELS_DIR, "feature_names.json"), "w") as f:
    json.dump(feature_cols, f)

all_metrics      = {}   # {nutrient: {xgboost: {...}, random_forest: {...}, winner: "..."}}
comparison_rows  = []   # for CSV export

for nutrient, label_col in TARGETS.items():
    if label_col not in master.columns:
        print(f"\nWARNING: {label_col} not found — skipping {nutrient}.")
        continue

    df = master[feature_cols + [label_col]].dropna()
    X  = df[feature_cols].astype(float).values
    y  = df[label_col].astype(int).values

    n_pos = y.sum()
    n_neg = len(y) - n_pos
    scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

    print(f"\nPreparing: {nutrient.upper()} | samples={len(y)} | pos={n_pos} | neg={n_neg}")

    # Shared split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # ── Train XGBoost ──────────────────────────────────────────────────────────
    print(f"  Training XGBoost ...")
    xgb_model, xgb_pred, xgb_prob = train_xgboost(
        X_train, y_train, X_test, scale_pos_weight
    )
    xgb_metrics = evaluate(y_test, xgb_pred, xgb_prob)
    print(f"  XGBoost  -> AUC={xgb_metrics['roc_auc']:.4f}  F1={xgb_metrics['f1']:.4f}")

    # ── Train Random Forest ────────────────────────────────────────────────────
    print(f"  Training Random Forest ...")
    rf_model, rf_pred, rf_prob = train_random_forest(
        X_train, y_train, X_test, scale_pos_weight
    )
    rf_metrics = evaluate(y_test, rf_pred, rf_prob)
    print(f"  RandomForest -> AUC={rf_metrics['roc_auc']:.4f}  F1={rf_metrics['f1']:.4f}")

    # ── Select winner by ROC-AUC ───────────────────────────────────────────────
    if xgb_metrics["roc_auc"] >= rf_metrics["roc_auc"]:
        winner       = "xgboost"
        best_model   = xgb_model
    else:
        winner       = "random_forest"
        best_model   = rf_model

    # ── Save best model ────────────────────────────────────────────────────────
    saved_path = save_model(nutrient, best_model, winner)
    print(f"  [OK] Saved {winner} -> {os.path.basename(saved_path)}")

    # ── Print comparison table ─────────────────────────────────────────────────
    print_comparison_table(nutrient, xgb_metrics, rf_metrics, winner)

    # ── Detailed classification report for winner ──────────────────────────────
    best_pred = xgb_pred if winner == "xgboost" else rf_pred
    print(classification_report(y_test, best_pred, zero_division=0))

    # ── Store results ──────────────────────────────────────────────────────────
    all_metrics[nutrient] = {
        "xgboost":       xgb_metrics,
        "random_forest": rf_metrics,
        "winner":        winner,
    }

    for model_name, m in [("xgboost", xgb_metrics), ("random_forest", rf_metrics)]:
        comparison_rows.append({
            "nutrient":   nutrient,
            "model":      model_name,
            "accuracy":   m["accuracy"],
            "precision":  m["precision"],
            "recall":     m["recall"],
            "f1":         m["f1"],
            "roc_auc":    m["roc_auc"],
            "winner":     "YES" if model_name == winner else "",
        })

# ── Save metrics JSON ──────────────────────────────────────────────────────────
metrics_path = os.path.join(MODELS_DIR, "metrics.json")
with open(metrics_path, "w") as f:
    json.dump(all_metrics, f, indent=2)
print(f"\nMetrics saved -> {metrics_path}")

# ── Save comparison CSV ────────────────────────────────────────────────────────
csv_path = os.path.join(MODELS_DIR, "comparison_table.csv")
pd.DataFrame(comparison_rows).to_csv(csv_path, index=False)
print(f"Comparison table saved -> {csv_path}")

# ── Final Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  FINAL SUMMARY — Best Models Selected")
print("=" * 60)
fmt = "  {:<14} {:<16} {:>8} {:>8}"
print(fmt.format("Nutrient", "Best Model", "AUC", "F1"))
print("  " + "-" * 50)
for nutrient, data in all_metrics.items():
    w = data["winner"]
    m = data[w]
    print(fmt.format(nutrient, w, f"{m['roc_auc']:.4f}", f"{m['f1']:.4f}"))
print("=" * 60)
print("Done.")

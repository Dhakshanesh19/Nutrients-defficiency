"""
preprocess.py
-------------
Reads raw NHANES XPT files and outputs cleaned CSVs:
  - data/processed/clean_demo.csv  (demographics)
  - data/processed/clean_bmx.csv   (body measurements)
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw", "NHANES")
OUT_DIR  = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)


def load_xpt(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    print(f"  Loading {filename} ...")
    return pd.read_sas(path, format="xport", iterator=False)


# ──────────────────────────────────────────────
# 1. DEMOGRAPHICS (DEMO_L.xpt)
# ──────────────────────────────────────────────
print("=== Processing DEMO_L.xpt ===")
demo = load_xpt("DEMO_L.xpt")

demo = demo[["SEQN", "RIAGENDR", "RIDAGEYR", "RIDRETH3"]].copy()
demo.columns = ["seqn", "gender", "age", "race_ethnicity"]

# Drop records with missing core demographic values
demo.dropna(subset=["gender", "age"], inplace=True)

# Encode gender: 1 = Male, 2 = Female → 0/1
demo["gender"] = demo["gender"].map({1.0: 0, 2.0: 1}).astype("Int8")

# Keep only adults aged 18–80 for dietary deficiency modelling
demo = demo[(demo["age"] >= 18) & (demo["age"] <= 80)].copy()
demo["age"] = demo["age"].astype(int)

out_path = os.path.join(OUT_DIR, "clean_demo.csv")
demo.to_csv(out_path, index=False)
print(f"  clean_demo.csv saved -> {len(demo)} rows, {demo.shape[1]} cols")


# ──────────────────────────────────────────────
# 2. BODY MEASUREMENTS (BMX_L.xpt)
# ──────────────────────────────────────────────
print("\n=== Processing BMX_L.xpt ===")
bmx = load_xpt("BMX_L.xpt")

bmx = bmx[["SEQN", "BMXWT", "BMXHT", "BMXBMI"]].copy()
bmx.columns = ["seqn", "weight_kg", "height_cm", "bmi"]

# Drop records with missing primary body measurement values
bmx.dropna(subset=["weight_kg", "height_cm", "bmi"], inplace=True)

# Physiological sanity filters
bmx = bmx[(bmx["bmi"] >= 10) & (bmx["bmi"] <= 70)].copy()
bmx = bmx[(bmx["height_cm"] >= 100) & (bmx["height_cm"] <= 250)].copy()
bmx = bmx[(bmx["weight_kg"] >= 20) & (bmx["weight_kg"] <= 300)].copy()

out_path = os.path.join(OUT_DIR, "clean_bmx.csv")
bmx.to_csv(out_path, index=False)
print(f"  clean_bmx.csv saved -> {len(bmx)} rows, {bmx.shape[1]} cols")

print("\nDone. Preprocessing complete.")

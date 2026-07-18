"""
merge.py
--------
Merges clean_demo.csv + clean_bmx.csv + DR1TOT_L.xpt nutrient totals.
Generates binary deficiency target labels based on RDA thresholds.
Saves: data/processed/nhanes_master.csv
"""
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw", "NHANES")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

# ──────────────────────────────────────────────
# Recommended Dietary Allowances (RDA) by gender
# Gender: 0 = Male, 1 = Female
# ----------------------------------------------
RDA = {
    # nutrient_column: {gender: threshold}
    "iron_mg":         {0: 8.0,    1: 18.0},   # mg/day
    "calcium_mg":      {0: 1000.0, 1: 1000.0}, # mg/day
    "vitamin_d_mcg":   {0: 15.0,   1: 15.0},   # mcg/day (600 IU)
    "vitamin_b12_mcg": {0: 2.4,    1: 2.4},    # mcg/day
    "zinc_mg":         {0: 11.0,   1: 8.0},    # mg/day
}


def load_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(PROC_DIR, filename)
    print(f"  Loading {filename} ...")
    return pd.read_csv(path)


# ----------------------------------------------
# 1. Load cleaned demo and BMX
# ----------------------------------------------
print("=== Loading cleaned files ===")
demo = load_csv("clean_demo.csv")
bmx  = load_csv("clean_bmx.csv")

# ----------------------------------------------
# 2. Load Day-1 Nutrient Totals from raw XPT
# ----------------------------------------------
print("\n=== Loading DR1TOT_L.xpt ===")
dr1 = pd.read_sas(os.path.join(RAW_DIR, "DR1TOT_L.xpt"), format="xport")

# Select only the nutritional columns we care about
dr1_cols = {
    "SEQN":    "seqn",
    "DR1TKCAL": "calories_kcal",
    "DR1TPROT": "protein_g",
    "DR1TCARB": "carbs_g",
    "DR1TTFAT": "fat_g",
    "DR1TIRON": "iron_mg",
    "DR1TCALC": "calcium_mg",
    "DR1TVD":    "vitamin_d_mcg",
    "DR1TVB12":  "vitamin_b12_mcg",
    "DR1TZINC": "zinc_mg",
}
dr1 = dr1[[c for c in dr1_cols if c in dr1.columns]].copy()
dr1.rename(columns={k: v for k, v in dr1_cols.items() if k in dr1.columns}, inplace=True)
dr1["seqn"] = dr1["seqn"].astype(float)

# ----------------------------------------------
# 3. Merge demo + BMX + DR1TOT on SEQN
# ----------------------------------------------
print("\n=== Merging datasets ===")
demo["seqn"] = demo["seqn"].astype(float)
bmx["seqn"]  = bmx["seqn"].astype(float)

master = demo.merge(bmx, on="seqn", how="inner")
master = master.merge(dr1, on="seqn", how="inner")
print(f"  Merged shape: {master.shape}")

# ----------------------------------------------
# 4. Compute Deficiency Labels (binary 0/1)
# ----------------------------------------------
print("\n=== Computing deficiency labels ===")
for nutrient_col, gender_thresholds in RDA.items():
    if nutrient_col not in master.columns:
        print(f"  WARNING: {nutrient_col} not found in merged data, skipping.")
        continue
    # Label name: strip unit suffix like _mg or _mcg
    label_col = "label_" + nutrient_col.replace("_mg", "").replace("_mcg", "")
    # Apply gender-specific RDA threshold
    thresholds = master["gender"].map(gender_thresholds)
    master[label_col] = np.where(
        master[nutrient_col].isna(), np.nan,
        (master[nutrient_col] < thresholds).astype(float)
    )
    deficient_count = master[label_col].sum()
    total = master[label_col].notna().sum()
    print(f"  {label_col}: {int(deficient_count)}/{int(total)} deficient ({100*deficient_count/total:.1f}%)")

# Drop rows where all label columns are NaN
label_cols = [c for c in master.columns if c.startswith("label_")]
master.dropna(subset=label_cols, how="all", inplace=True)

# ----------------------------------------------
# 5. Save master training file
# ----------------------------------------------
out_path = os.path.join(PROC_DIR, "nhanes_master.csv")
master.to_csv(out_path, index=False)
print(f"\nDone. nhanes_master.csv saved -> {len(master)} rows, {master.shape[1]} cols")
print(f"  Feature columns  : {[c for c in master.columns if not c.startswith('label_')]}")
print(f"  Target columns   : {label_cols}")

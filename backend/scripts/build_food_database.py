import os
import gc
import pandas as pd

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USDA_DIR = os.path.join(BASE_DIR, "data", "raw", "USDA")
OFF_DIR  = os.path.join(BASE_DIR, "data", "raw", "OpenFoodFacts")
OUT_DIR  = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

def build_database():
    print("=== Step 1: Loading USDA Nutrient Metadata ===")
    needed = [
        "Energy",
        "Protein",
        "Total lipid (fat)",
        "Carbohydrate, by difference",
        "Iron, Fe",
        "Calcium, Ca",
        "Vitamin D (D2 + D3)",
        "Vitamin B-12",
        "Zinc, Zn"
    ]

    nutrient = pd.read_csv(os.path.join(USDA_DIR, "nutrient.csv"))
    nut_filtered = nutrient[nutrient["name"].isin(needed)].copy()
    nut_map = dict(zip(nut_filtered["id"], nut_filtered["name"]))
    print(f"  Mapped {len(nut_map)} target nutrient IDs.")
    del nutrient; gc.collect()

    print("\n=== Step 2: Loading USDA Food Master ===")
    food = pd.read_csv(os.path.join(USDA_DIR, "food.csv"), usecols=["fdc_id", "description"])
    print(f"  Loaded {len(food):,} food description mappings.")

    print("\n=== Step 3: Chunk-Processing USDA Food Nutrient Ledger (1.79 GB) ===")
    target_nutrient_ids = set(nut_map.keys())
    chunks = []
    
    # Process in memory-efficient chunks to prevent Out-Of-Memory exceptions
    for chunk in pd.read_csv(
        os.path.join(USDA_DIR, "food_nutrient.csv"),
        usecols=["fdc_id", "nutrient_id", "amount"],
        chunksize=250000,
        dtype={"fdc_id": "int32", "nutrient_id": "int32", "amount": "float32"}
    ):
        filtered_chunk = chunk[chunk["nutrient_id"].isin(target_nutrient_ids)].copy()
        chunks.append(filtered_chunk)
        
    merged_nutrients = pd.concat(chunks, ignore_index=True)
    print(f"  Extracted {len(merged_nutrients):,} raw nutrient records matching targets.")
    del chunks; gc.collect()

    print("\n=== Step 4: Merging USDA Tables ===")
    merged_nutrients["name"] = merged_nutrients["nutrient_id"].map(nut_map)
    merged = merged_nutrients.merge(food, on="fdc_id", how="inner")
    del merged_nutrients, food; gc.collect()

    print("\n=== Step 5: Pivoting USDA Nutrients Matrix ===")
    food_database = merged.pivot_table(
        index="description",
        columns="name",
        values="amount",
        aggfunc="first"
    ).reset_index()
    del merged; gc.collect()

    print("\n=== Step 6: Renaming USDA Columns ===")
    name_mapping = {
        "description": "food_name",
        "Energy": "calories",
        "Protein": "protein",
        "Total lipid (fat)": "fat",
        "Carbohydrate, by difference": "carbs",
        "Iron, Fe": "iron",
        "Calcium, Ca": "calcium",
        "Vitamin D (D2 + D3)": "vitamin_d",
        "Vitamin B-12": "vitamin_b12",
        "Zinc, Zn": "zinc"
    }
    food_database = food_database.rename(columns=name_mapping)
    
    # Align and order target columns
    cols = ["food_name", "calories", "protein", "fat", "carbs", "iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]
    for col in cols:
        if col not in food_database.columns:
            food_database[col] = 0.0
    food_database = food_database[cols]
    print(f"  USDA sub-database ready: {len(food_database):,} unique items.")

    print("\n=== Step 7: Loading Open Food Facts Branded Products (1.27 GB gzip) ===")
    off_cols = [
        "product_name",
        "energy-kcal_100g",
        "proteins_100g",
        "fat_100g",
        "carbohydrates_100g",
        "iron_100g",
        "calcium_100g",
        "vitamin-d_100g",
        "vitamin-b12_100g",
        "zinc_100g"
    ]
    off_rename = {
        "product_name": "food_name",
        "energy-kcal_100g": "calories",
        "proteins_100g": "protein",
        "fat_100g": "fat",
        "carbohydrates_100g": "carbs",
        "iron_100g": "iron",
        "calcium_100g": "calcium",
        "vitamin-d_100g": "vitamin_d",
        "vitamin-b12_100g": "vitamin_b12",
        "zinc_100g": "zinc"
    }

    off_chunks = []
    # Read only target columns in chunks to keep memory usage minimal
    for chunk in pd.read_csv(
        os.path.join(OFF_DIR, "en.openfoodfacts.org.products.csv.gz"),
        compression="gzip",
        sep="\t",
        usecols=off_cols,
        chunksize=200000,
        low_memory=False
    ):
        chunk = chunk.dropna(subset=["product_name"]).copy()
        off_chunks.append(chunk)

    off = pd.concat(off_chunks, ignore_index=True)
    off = off.rename(columns=off_rename)
    del off_chunks; gc.collect()

    # Align columns
    for col in cols:
        if col not in off.columns:
            off[col] = 0.0
    off = off[cols]
    print(f"  Open Food Facts sub-database ready: {len(off):,} branded items.")

    print("\n=== Step 8: Combining & Cleaning Databases ===")
    food_database = pd.concat([food_database, off], ignore_index=True)
    del off; gc.collect()

    print("  Removing duplicates...")
    food_database.drop_duplicates(subset="food_name", inplace=True)

    print("  Dropping missing rows & filling NaN...")
    food_database = food_database.dropna(subset=["food_name"])
    food_database.fillna(0.0, inplace=True)

    print("\n=== Step 9: Saving Unified Food Database ===")
    out_path = os.path.join(OUT_DIR, "food_database.csv")
    food_database.to_csv(out_path, index=False)
    print(f"SUCCESS: Unified database saved to {out_path} - {len(food_database):,} records.")

if __name__ == "__main__":
    build_database()

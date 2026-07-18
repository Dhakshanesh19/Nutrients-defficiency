import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./nutrition.db")
csv_path = os.path.join(BASE_DIR, "data", "processed", "food_database.csv")

def import_csv():
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} does not exist. Run build_food_database.py first.")
        return

    print(f"Loading unified food database from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Loaded {len(df):,} records.")

    # Map the pivoted csv columns to backend model schema columns
    rename_map = {
        "calories": "calories_kcal",
        "protein": "protein_g",
        "fat": "fat_g",
        "carbs": "carbs_g",
        "iron": "iron_mg",
        "calcium": "calcium_mg",
        "vitamin_d": "vitamin_d_mcg",
        "vitamin_b12": "vitamin_b12_mcg",
        "zinc": "zinc_mg"
    }
    df = df.rename(columns=rename_map)

    # Ensure source and fdc_id are present
    if "source" not in df.columns:
        df["source"] = "USDA/OFF"
    if "fdc_id" not in df.columns:
        df["fdc_id"] = None

    db_cols = [
        "fdc_id", "food_name", "source", "calories_kcal", "protein_g", 
        "carbs_g", "fat_g", "iron_mg", "calcium_mg", "vitamin_d_mcg", 
        "vitamin_b12_mcg", "zinc_mg"
    ]
    df = df[db_cols]

    print(f"Connecting to database: {DB_URL}")
    from sqlalchemy import text
    engine = create_engine(DB_URL)

    print("Clearing existing food catalog records...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM food_catalog;"))

    print("Seeding SQLite food_catalog table (inserting in chunks)...")
    df.to_sql("food_catalog", engine, if_exists="append", index=False, chunksize=30000)
    print(f"SUCCESS: Database seeded successfully with {len(df):,} food rows!")

if __name__ == "__main__":
    import_csv()

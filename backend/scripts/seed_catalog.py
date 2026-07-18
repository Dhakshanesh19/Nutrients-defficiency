import os
import sys
from dotenv import load_dotenv

# Load settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import Base, engine, SessionLocal
from app.models.deficiency import FoodCatalog

def seed():
    db = SessionLocal()
    # Check if catalog has data
    if db.query(FoodCatalog).count() > 0:
        print("Catalog already seeded.")
        db.close()
        return

    # Predefined catalog items
    foods = [
        {"food_name": "Spinach, raw", "calories_kcal": 23.0, "protein_g": 2.86, "carbs_g": 3.63, "fat_g": 0.39, "iron_mg": 2.71, "calcium_mg": 99.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.53, "source": "USDA"},
        {"food_name": "Salmon, wild, cooked", "calories_kcal": 182.0, "protein_g": 25.0, "carbs_g": 0.0, "fat_g": 8.0, "iron_mg": 0.8, "calcium_mg": 12.0, "vitamin_d_mcg": 10.9, "vitamin_b12_mcg": 4.8, "zinc_mg": 0.6, "source": "USDA"},
        {"food_name": "Beef, ribeye, cooked", "calories_kcal": 291.0, "protein_g": 24.0, "carbs_g": 0.0, "fat_g": 21.0, "iron_mg": 2.6, "calcium_mg": 10.0, "vitamin_d_mcg": 0.1, "vitamin_b12_mcg": 2.6, "zinc_mg": 6.3, "source": "USDA"},
        {"food_name": "Yogurt, plain, lowfat", "calories_kcal": 63.0, "protein_g": 5.25, "carbs_g": 7.04, "fat_g": 1.55, "iron_mg": 0.05, "calcium_mg": 183.0, "vitamin_d_mcg": 0.1, "vitamin_b12_mcg": 0.56, "zinc_mg": 0.89, "source": "USDA"},
        {"food_name": "Lentils, cooked", "calories_kcal": 116.0, "protein_g": 9.02, "carbs_g": 20.13, "fat_g": 0.38, "iron_mg": 3.33, "calcium_mg": 19.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 1.27, "source": "USDA"},
        {"food_name": "Nutritional Yeast", "calories_kcal": 325.0, "protein_g": 50.0, "carbs_g": 37.0, "fat_g": 5.0, "iron_mg": 5.0, "calcium_mg": 100.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 49.0, "zinc_mg": 12.0, "source": "USDA"},
        {"food_name": "Oysters, cooked", "calories_kcal": 163.0, "protein_g": 19.0, "carbs_g": 10.0, "fat_g": 5.0, "iron_mg": 9.2, "calcium_mg": 62.0, "vitamin_d_mcg": 8.0, "vitamin_b12_mcg": 16.0, "zinc_mg": 16.6, "source": "USDA"},
        {"food_name": "Chicken Breast, cooked", "calories_kcal": 165.0, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "iron_mg": 1.0, "calcium_mg": 15.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.3, "zinc_mg": 1.0, "source": "USDA"},
        {"food_name": "Pumpkin Seeds, roasted", "calories_kcal": 574.0, "protein_g": 29.8, "carbs_g": 14.7, "fat_g": 49.0, "iron_mg": 8.8, "calcium_mg": 52.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 7.8, "source": "USDA"},
        {"food_name": "Eggs, whole, boiled", "calories_kcal": 155.0, "protein_g": 13.0, "carbs_g": 1.1, "fat_g": 11.0, "iron_mg": 1.2, "calcium_mg": 50.0, "vitamin_d_mcg": 2.2, "vitamin_b12_mcg": 1.1, "zinc_mg": 1.1, "source": "USDA"},
    ]

    for f in foods:
        db.add(FoodCatalog(**f))
    db.commit()
    print("Catalog seeded successfully!")
    db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed()

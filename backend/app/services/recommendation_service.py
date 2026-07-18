from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.deficiency import FoodCatalog, User
from app.schemas.predict import RecommendationFoodItem, NutrientTarget, RecommendationsOut

# Static high-quality food recommendations (per 100g) as fallbacks/benchmarks
STATIC_FOODS = {
    "iron": [
        {"food_name": "Cooked Lentils", "amount": 3.3, "unit": "mg"},
        {"food_name": "Pumpkin Seeds", "amount": 8.8, "unit": "mg"},
        {"food_name": "Spinach", "amount": 2.7, "unit": "mg"},
        {"food_name": "Grass-Fed Beef", "amount": 2.6, "unit": "mg"}
    ],
    "calcium": [
        {"food_name": "Plain Yogurt", "amount": 110.0, "unit": "mg"},
        {"food_name": "Sardines (canned with bones)", "amount": 380.0, "unit": "mg"},
        {"food_name": "Almonds", "amount": 260.0, "unit": "mg"},
        {"food_name": "Tofu (calcium-set)", "amount": 350.0, "unit": "mg"}
    ],
    "vitamin_d": [
        {"food_name": "Wild-Caught Salmon", "amount": 10.9, "unit": "mcg"},
        {"food_name": "Canned Light Tuna", "amount": 5.4, "unit": "mcg"},
        {"food_name": "Egg Yolks", "amount": 5.4, "unit": "mcg"},
        {"food_name": "Fortified Milk", "amount": 1.3, "unit": "mcg"}
    ],
    "vitamin_b12": [
        {"food_name": "Clams (cooked)", "amount": 98.9, "unit": "mcg"},
        {"food_name": "Beef Liver", "amount": 59.3, "unit": "mcg"},
        {"food_name": "Tuna", "amount": 2.2, "unit": "mcg"},
        {"food_name": "Fortified Nutritional Yeast", "amount": 49.0, "unit": "mcg"}
    ],
    "zinc": [
        {"food_name": "Oysters", "amount": 16.6, "unit": "mg"},
        {"food_name": "Pumpkin Seeds", "amount": 7.8, "unit": "mg"},
        {"food_name": "Beef Steak", "amount": 6.3, "unit": "mg"},
        {"food_name": "Cashews", "amount": 5.8, "unit": "mg"}
    ]
}

FOODS_TO_AVOID = {
    "iron": "Avoid drinking black tea or coffee with meals (tannins and polyphenols inhibit non-heme iron absorption). Avoid high-calcium supplements during iron-rich meals.",
    "calcium": "Avoid excessive sodium intake and phosphoric acid (commonly found in dark colas), as they increase urinary calcium excretion.",
    "vitamin_d": "Avoid excessive alcohol consumption, which impairs liver enzymes that convert Vitamin D to its active form.",
    "vitamin_b12": "Avoid heavy alcohol intake. Avoid taking mega-doses of Vitamin C supplements at the same time as B12-rich meals (can destroy the vitamin).",
    "zinc": "Avoid consuming raw whole grains or unsoaked legumes with zinc-rich foods, as high phytate levels strongly bind to zinc and inhibit its absorption."
}

HEALTH_ADVICE = {
    "iron": "Your profile indicates a risk of iron deficiency. Focus on combining iron-rich foods with Vitamin C (e.g., citrus, bell peppers) to boost absorption.",
    "calcium": "Ensure adequate daily calcium intake to support bone mineral density. Pair with Vitamin D to enhance absorption.",
    "vitamin_d": "Boost Vitamin D levels through dietary sources (salmon, egg yolks) and safe sunlight exposure (10-15 minutes daily).",
    "vitamin_b12": "B12 is primary to nerve function and red blood cell production. If you follow a plant-based diet, ensure you consume fortified foods or supplements.",
    "zinc": "Zinc supports immune function and DNA synthesis. Focus on protein-rich foods, which enhance zinc bioavailability."
}


class RecommendationService:
    @staticmethod
    def get_nutrient_targets(user: User) -> List[NutrientTarget]:
        """
        Calculate daily Recommended Dietary Allowance (RDA) targets adjusted for age and gender.
        """
        is_female = (user.gender is not None and str(user.gender).strip().lower() in ("female", "f", "1"))
        age = user.age or 30

        # 1. Iron Target
        if is_female and age < 50:
            iron_val = 18.0
        else:
            iron_val = 8.0

        # 2. Calcium Target
        if is_female and age > 50:
            calcium_val = 1200.0
        elif not is_female and age > 70:
            calcium_val = 1200.0
        else:
            calcium_val = 1000.0

        # 3. Vitamin D Target
        if age > 70:
            vit_d_val = 20.0
        else:
            vit_d_val = 15.0

        # 4. Vitamin B12 Target
        vit_b12_val = 2.4

        # 5. Zinc Target
        if is_female:
            zinc_val = 8.0
        else:
            zinc_val = 11.0

        return [
            NutrientTarget(nutrient="Iron", target_value=iron_val, unit="mg"),
            NutrientTarget(nutrient="Calcium", target_value=calcium_val, unit="mg"),
            NutrientTarget(nutrient="Vitamin D", target_value=vit_d_val, unit="mcg"),
            NutrientTarget(nutrient="Vitamin B12", target_value=vit_b12_val, unit="mcg"),
            NutrientTarget(nutrient="Zinc", target_value=zinc_val, unit="mg"),
        ]

    @staticmethod
    def query_db_foods(db: Session, nutrient: str, limit: int = 3) -> List[RecommendationFoodItem]:
        """
        Query the food catalog database table for foods containing highest values of the target nutrient.
        """
        col_map = {
            "iron": (FoodCatalog.iron_mg, "mg"),
            "calcium": (FoodCatalog.calcium_mg, "mg"),
            "vitamin_d": (FoodCatalog.vitamin_d_mcg, "mcg"),
            "vitamin_b12": (FoodCatalog.vitamin_b12_mcg, "mcg"),
            "zinc": (FoodCatalog.zinc_mg, "mg")
        }

        if nutrient not in col_map:
            return []

        db_col, unit = col_map[nutrient]

        try:
            # Query highest nutrient values, filtering out long non-food items or supplements
            query = (
                db.query(FoodCatalog)
                .filter(db_col.isnot(None))
                .filter(FoodCatalog.food_name.not_like("%powder%"))
                .filter(FoodCatalog.food_name.not_like("%supplement%"))
                .filter(FoodCatalog.food_name.not_like("%infant%"))
                .order_by(desc(db_col))
                .limit(limit)
                .all()
            )

            return [
                RecommendationFoodItem(
                    food_name=item.food_name,
                    nutrient_amount=round(float(getattr(item, db_col.key)), 2),
                    unit=unit
                )
                for item in query
            ]
        except Exception:
            # Fall back to empty list if table does not exist or database is unseeded
            return []

    @classmethod
    def generate_recommendations(
        cls,
        db: Session,
        user: User,
        risks: Dict[str, float]
    ) -> RecommendationsOut:
        """
        Identify deficient nutrients, query database / fallback catalog, and construct recommendations.
        """
        # Determine deficient nutrients (ordered by risk descending)
        sorted_risks = sorted(risks.items(), key=lambda x: x[1], reverse=True)
        
        # Select deficient nutrients (risk >= 0.50). If none are above 0.50, recommend for the single highest risk.
        deficient_keys = [k for k, r in sorted_risks if r >= 0.50]
        if not deficient_keys and sorted_risks:
            deficient_keys = [sorted_risks[0][0]]

        foods_to_eat: List[RecommendationFoodItem] = []
        foods_to_avoid: List[str] = []
        advice_parts: List[str] = []

        # For each target deficient nutrient, extract recommendations
        for nut in deficient_keys:
            # 1. Foods to eat: Combine database query and static fallbacks
            db_results = cls.query_db_foods(db, nut, limit=2)
            if db_results:
                foods_to_eat.extend(db_results)
            
            # Supplement with static high-quality recommendations for variety
            static_list = STATIC_FOODS.get(nut, [])
            for item in static_list:
                # Add if not already included
                if not any(f.food_name.lower() == item["food_name"].lower() for f in foods_to_eat):
                    foods_to_eat.append(
                        RecommendationFoodItem(
                            food_name=item["food_name"],
                            nutrient_amount=item["amount"],
                            unit=item["unit"]
                        )
                    )

            # 2. Foods to avoid
            if nut in FOODS_TO_AVOID:
                foods_to_avoid.append(FOODS_TO_AVOID[nut])

            # 3. Advice parts
            if nut in HEALTH_ADVICE:
                advice_parts.append(HEALTH_ADVICE[nut])

        # Limit foods to eat list to top 6 items
        foods_to_eat = foods_to_eat[:6]

        # Structure short health advice
        if advice_parts:
            short_advice = " · ".join(advice_parts)
        else:
            short_advice = "Maintain a balanced diet rich in whole grains, proteins, and fresh leafy greens."

        # Daily nutrient targets
        targets = cls.get_nutrient_targets(user)

        return RecommendationsOut(
            foods_to_eat=foods_to_eat,
            foods_to_avoid=foods_to_avoid,
            daily_nutrient_targets=targets,
            short_health_advice=short_advice
        )

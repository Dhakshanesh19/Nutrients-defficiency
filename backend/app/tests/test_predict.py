# pyrefly: ignore [missing-import]
import pytest

PREDICT_PAYLOAD = {
    "age": 32,
    "gender": 1,
    "race_ethnicity": 3,
    "weight_kg": 60.0,
    "height_cm": 162.0,
    "bmi": 22.9,
    "include_shap": True
}


def get_auth_header(client, email="predict_user@example.com"):
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepassword",
        "name": "Predict User"
    })
    resp = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "securepassword"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_predict_unauthorized(client):
    """Prediction endpoint requires authentication."""
    resp = client.post("/api/v1/predict/", json=PREDICT_PAYLOAD)
    assert resp.status_code == 401


def test_predict_success(client):
    """Successful prediction returns all 5 nutrient risk scores."""
    headers = get_auth_header(client, "pred_success@example.com")
    resp = client.post("/api/v1/predict/", json=PREDICT_PAYLOAD, headers=headers)
    assert resp.status_code == 200

    data = resp.json()

    # Check top-level structure
    assert "results" in data
    assert "user_id" in data
    assert "prediction_date" in data

    # All 5 nutrients must be present
    for nutrient in ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]:
        assert nutrient in data["results"], f"Missing nutrient: {nutrient}"
        result = data["results"][nutrient]
        assert "risk_score" in result
        assert "risk_label" in result
        assert 0.0 <= result["risk_score"] <= 1.0
        assert result["risk_label"] in ["Low", "Moderate", "High"]

    # Flat risk scores also returned
    assert "iron_risk" in data
    assert "vitamin_d_risk" in data
    assert "vitamin_b12_risk" in data
    assert "calcium_risk" in data
    assert "zinc_risk" in data


def test_predict_with_shap(client):
    """SHAP explanations are returned when include_shap=True."""
    headers = get_auth_header(client, "pred_shap@example.com")
    payload = {**PREDICT_PAYLOAD, "include_shap": True}
    resp = client.post("/api/v1/predict/", json=payload, headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    # At least one nutrient should have SHAP explanations
    has_shap = any(
        data["results"][n].get("explanation") is not None
        for n in ["iron", "calcium", "vitamin_d", "vitamin_b12", "zinc"]
    )
    assert has_shap, "Expected SHAP explanations for at least one nutrient"

    # Validate SHAP item structure
    for nutrient, result in data["results"].items():
        if result.get("explanation"):
            for item in result["explanation"]:
                assert "feature" in item
                assert "value" in item
                assert "contribution" in item


def test_predict_without_shap(client):
    """SHAP explanations are omitted when include_shap=False."""
    headers = get_auth_header(client, "pred_noshap@example.com")
    payload = {**PREDICT_PAYLOAD, "include_shap": False}
    resp = client.post("/api/v1/predict/", json=payload, headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    for nutrient, result in data["results"].items():
        assert result.get("explanation") is None, \
            f"Expected no SHAP for {nutrient} when include_shap=False"


def test_predict_invalid_input(client):
    """Invalid age range returns 422 validation error."""
    headers = get_auth_header(client, "pred_invalid@example.com")
    bad_payload = {**PREDICT_PAYLOAD, "age": 10}  # age < 18
    resp = client.post("/api/v1/predict/", json=bad_payload, headers=headers)
    assert resp.status_code == 422


def test_predict_history(client):
    """Prediction history endpoint returns past records."""
    headers = get_auth_header(client, "pred_history@example.com")

    # Make 2 predictions
    client.post("/api/v1/predict/", json=PREDICT_PAYLOAD, headers=headers)
    client.post("/api/v1/predict/", json={**PREDICT_PAYLOAD, "age": 40}, headers=headers)

    resp = client.get("/api/v1/predict/history", headers=headers)
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 2

    # Each record has all risk fields
    for record in records:
        assert "iron_risk" in record
        assert "calcium_risk" in record
        assert "vitamin_d_risk" in record
        assert "vitamin_b12_risk" in record
        assert "zinc_risk" in record
        assert "prediction_date" in record


def test_predict_profile_fallback_success(client, db):
    """Uses database profile fields if missing from request payload."""
    email = "fallback_success@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepassword",
        "name": "Fallback User"
    })
    resp = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "securepassword"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update user profile fields directly in DB
    from app.models.deficiency import User as DBUser
    db_user = db.query(DBUser).filter(DBUser.email == email).first()
    db_user.age = 45
    db_user.gender = "Female"
    db_user.height = 172.0
    db_user.weight = 68.0
    db_user.bmi = 23.0
    db.commit()

    payload = {
        "include_shap": False
    }
    resp = client.post("/api/v1/predict/", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert data["results"]["iron"]["risk_score"] is not None


def test_predict_profile_missing_error(client):
    """Returns 400 if user profile is missing and not sent in body."""
    headers = get_auth_header(client, "missing_profile@example.com")
    payload = {
        "include_shap": False
    }
    resp = client.post("/api/v1/predict/", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "missing" in resp.json()["detail"].lower()


def test_predict_with_food_log_totals(client, db):
    """Verify that predictions run successfully when today's food log entries exist."""
    email = "food_log_pred@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepassword",
        "name": "Food Log Pred User"
    })
    resp = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "securepassword"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add a food log entry for today
    client.post("/api/v1/food-log/", json={
        "food_name": "Spinach Salad",
        "quantity": 100,
        "serving_size": "g",
        "meal_type": "Lunch",
        "calories": 25,
        "protein": 2.9,
        "carbohydrates": 3.6,
        "fat": 0.4,
        "iron": 2.7,
        "calcium": 99.0,
        "vitamin_d": 0.0,
        "vitamin_b12": 0.0,
        "zinc": 0.53
    }, headers=headers)

    resp = client.post("/api/v1/predict/", json=PREDICT_PAYLOAD, headers=headers)
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_recommendations_returned(client, db):
    """Verify that predictions return recommendations with correct properties."""
    email = "recs_user@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepassword",
        "name": "Recs User"
    })
    resp = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "securepassword"
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update database user gender and age
    from app.models.deficiency import User as DBUser
    db_user = db.query(DBUser).filter(DBUser.email == email).first()
    db_user.age = 28
    db_user.gender = "Female"
    db_user.height = 165.0
    db_user.weight = 58.0
    db_user.bmi = 21.3
    db.commit()

    resp = client.post("/api/v1/predict/", json={"include_shap": False}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    recs = data["recommendations"]

    # Verify structured JSON properties
    assert "foods_to_eat" in recs
    assert "foods_to_avoid" in recs
    assert "daily_nutrient_targets" in recs
    assert "short_health_advice" in recs

    # Verify foods to eat properties
    assert len(recs["foods_to_eat"]) > 0
    for food in recs["foods_to_eat"]:
        assert "food_name" in food
        assert "nutrient_amount" in food
        assert "unit" in food

    # Check targets (RDA) - Young female target for iron should be 18mg
    targets = recs["daily_nutrient_targets"]
    iron_target = next((t for t in targets if t["nutrient"] == "Iron"), None)
    assert iron_target is not None
    assert iron_target["target_value"] == 18.0
    assert iron_target["unit"] == "mg"


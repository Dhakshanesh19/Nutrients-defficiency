import pytest

def get_auth_header(client, email="food_user@example.com", name="Food User"):
    # Helper function to register, login, and return authorization headers
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "secretpassword",
        "name": name
    })
    login_response = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "secretpassword"
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_food_log_unauthorized(client):
    """
    Test that endpoints reject requests without authorization.
    """
    resp_post = client.post("/api/v1/food-log/", json={"food_name": "Apple", "quantity": 1, "serving_size": "Medium"})
    assert resp_post.status_code == 401

    resp_get = client.get("/api/v1/food-log/")
    assert resp_get.status_code == 401


def test_create_food_log(client):
    """
    Test logging a meal with nutrition details.
    """
    headers = get_auth_header(client, "create_log@example.com")
    
    payload = {
        "food_name": "Oatmeal",
        "quantity": 150.0,
        "serving_size": "grams",
        "meal_type": "Breakfast",
        "calories": 250.0,
        "protein": 8.0,
        "carbohydrates": 40.0,
        "fat": 5.0,
        "iron": 4.5,
        "calcium": 80.0,
        "vitamin_d": 0.0,
        "vitamin_b12": 0.0,
        "zinc": 2.1
    }
    response = client.post("/api/v1/food-log/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["food_name"] == "Oatmeal"
    assert data["meal_type"] == "Breakfast"
    assert data["calories"] == 250.0
    assert "id" in data


def test_create_food_log_invalid_type(client):
    """
    Test validation errors on invalid meal types.
    """
    headers = get_auth_header(client, "invalid_log@example.com")
    payload = {
        "food_name": "Apple",
        "quantity": 1.0,
        "serving_size": "piece",
        "meal_type": "Brunch"  # Invalid meal type
    }
    response = client.post("/api/v1/food-log/", json=payload, headers=headers)
    assert response.status_code == 422


def test_list_food_logs(client):
    """
    Test listing logged foods with date filtering options.
    """
    headers = get_auth_header(client, "list_logs@example.com")
    
    # 1. Log breakfast item
    client.post("/api/v1/food-log/", json={
        "food_name": "Egg",
        "quantity": 2.0,
        "serving_size": "large",
        "meal_type": "Breakfast",
        "calories": 140.0,
        "protein": 12.0
    }, headers=headers)

    # 2. Retrieve logs list
    response = client.get("/api/v1/food-log/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["food_name"] == "Egg"

    # 3. Retrieve logs filtering by date
    today_str = datetime_to_date_str()
    response_filtered = client.get(f"/api/v1/food-log/?date_str={today_str}", headers=headers)
    assert response_filtered.status_code == 200
    assert len(response_filtered.json()) == 1


def test_delete_food_log(client):
    """
    Test deleting a food log entry.
    """
    headers = get_auth_header(client, "delete_log@example.com")
    
    # 1. Log food
    post_response = client.post("/api/v1/food-log/", json={
        "food_name": "Banana",
        "quantity": 1.0,
        "serving_size": "Medium",
        "meal_type": "Snack"
    }, headers=headers)
    log_id = post_response.json()["id"]

    # 2. Delete it
    delete_response = client.delete(f"/api/v1/food-log/{log_id}", headers=headers)
    assert delete_response.status_code == 200

    # 3. Confirm deletion
    list_response = client.get("/api/v1/food-log/", headers=headers)
    assert len(list_response.json()) == 0


def test_delete_unauthorized(client):
    """
    Test that users cannot delete other users' logs.
    """
    headers1 = get_auth_header(client, "user1@example.com", "User One")
    headers2 = get_auth_header(client, "user2@example.com", "User Two")

    # 1. User 1 logs a food item
    post_response = client.post("/api/v1/food-log/", json={
        "food_name": "Protein Shake",
        "quantity": 1.0,
        "serving_size": "bottle",
        "meal_type": "Snack"
    }, headers=headers1)
    log_id = post_response.json()["id"]

    # 2. User 2 attempts to delete User 1's log
    delete_response = client.delete(f"/api/v1/food-log/{log_id}", headers=headers2)
    assert delete_response.status_code == 403


def test_daily_summary(client):
    """
    Test daily nutrient aggregates sum.
    """
    headers = get_auth_header(client, "summary@example.com")
    
    # 1. Log Item 1
    client.post("/api/v1/food-log/", json={
        "food_name": "Chicken",
        "quantity": 200.0,
        "serving_size": "grams",
        "meal_type": "Lunch",
        "calories": 300.0,
        "protein": 50.0,
        "iron": 2.0
    }, headers=headers)

    # 2. Log Item 2
    client.post("/api/v1/food-log/", json={
        "food_name": "Rice",
        "quantity": 150.0,
        "serving_size": "grams",
        "meal_type": "Lunch",
        "calories": 200.0,
        "protein": 4.0,
        "iron": 1.0
    }, headers=headers)

    # 3. Query daily summary
    summary_response = client.get("/api/v1/food-log/summary", headers=headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["calories"] == 500.0
    assert summary["protein"] == 54.0
    assert summary["iron"] == 3.0


def datetime_to_date_str():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d")

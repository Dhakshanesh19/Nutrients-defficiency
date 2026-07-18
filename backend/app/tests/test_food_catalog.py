import pytest

def get_auth_header(client, email="catalog_user@example.com", name="Catalog User"):
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


def test_search_unauthorized(client):
    """Reject food search query if user is unauthorized."""
    resp = client.get("/api/v1/food-catalog/search?q=spinach")
    assert resp.status_code == 401


def test_search_invalid_query(client):
    """Empty or short queries return empty list."""
    headers = get_auth_header(client, "search_val@example.com")
    resp = client.get("/api/v1/food-catalog/search?q=", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    resp_short = client.get("/api/v1/food-catalog/search?q=a", headers=headers)
    assert resp_short.status_code == 200
    assert resp_short.json() == []


def test_search_success_fallback(client):
    """Returns matches from fallback foods catalog when DB is empty."""
    headers = get_auth_header(client, "search_success@example.com")
    resp = client.get("/api/v1/food-catalog/search?q=spinach", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert "spinach" in results[0]["food_name"].lower()
    
    # Assert nutrient properties exist
    assert "calories_kcal" in results[0]
    assert "protein_g" in results[0]
    assert "iron_mg" in results[0]

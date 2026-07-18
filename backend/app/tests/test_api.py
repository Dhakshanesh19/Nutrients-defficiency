def test_health_check(client):
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register(client):
    """
    Test successful user registration.
    """
    payload = {
        "email": "register_test@example.com",
        "password": "secretpassword",
        "name": "Register User",
        "age": 30,
        "gender": "Male",
        "height": 175.5,
        "weight": 70.0,
        "bmi": 22.7,
        "activity_level": "Moderate"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "register_test@example.com"
    assert data["name"] == "Register User"
    assert data["age"] == 30
    assert "id" in data


def test_register_duplicate(client):
    """
    Test registering duplicate email.
    """
    payload = {
        "email": "duplicate@example.com",
        "password": "secretpassword",
        "name": "First User"
    }
    response1 = client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    response2 = client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 400
    assert response2.json()["detail"] == "The user with this email already exists in the system."


def test_login_success(client):
    """
    Test login with correct credentials.
    """
    # 1. Register
    register_payload = {
        "email": "login_test@example.com",
        "password": "secretpassword",
        "name": "Login User"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    # 2. Login
    login_payload = {
        "username": "login_test@example.com",
        "password": "secretpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client):
    """
    Test login with incorrect password.
    """
    register_payload = {
        "email": "login_fail@example.com",
        "password": "secretpassword",
        "name": "Fail User"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "username": "login_fail@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


def test_me_authenticated(client):
    """
    Test accessing protected route with access token.
    """
    # 1. Register & Login
    register_payload = {
        "email": "me_test@example.com",
        "password": "secretpassword",
        "name": "Me User"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "username": "me_test@example.com",
        "password": "secretpassword"
    }
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    access_token = login_response.json()["access_token"]

    # 2. Get /me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_test@example.com"
    assert data["name"] == "Me User"


def test_me_unauthorized(client):
    """
    Test protected route without auth token.
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_token(client):
    """
    Test renewing access token using a refresh token.
    """
    # 1. Register & Login
    register_payload = {
        "email": "refresh_test@example.com",
        "password": "secretpassword",
        "name": "Refresh User"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "username": "refresh_test@example.com",
        "password": "secretpassword"
    }
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    refresh_token = login_response.json()["refresh_token"]

    # 2. Call refresh endpoint
    refresh_payload = {
        "refresh_token": refresh_token
    }
    response = client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout(client):
    """
    Test logout endpoint.
    """
    # 1. Register & Login
    register_payload = {
        "email": "logout_test@example.com",
        "password": "secretpassword",
        "name": "Logout User"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {
        "username": "logout_test@example.com",
        "password": "secretpassword"
    }
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    access_token = login_response.json()["access_token"]

    # 2. Logout
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully logged out"

import pytest
from smse_backend.models import User
from flask_jwt_extended import create_access_token


@pytest.fixture
def new_user_data():
    """Fixture for new user registration data."""
    return {
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "password123",
    }


@pytest.fixture
def auth_header(existing_user):
    """Fixture for JWT authorization header."""
    access_token = create_access_token(identity=str(existing_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def existing_user(db_session):
    """Create an existing user for testing."""
    user = User(username="existinguser", email="existinguser@test.com")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


def test_register(client, new_user_data):
    """Test the user registration route."""
    response = client.post("/api/v1/auth/register", json=new_user_data)
    assert response.status_code == 201
    assert response.json["msg"] == "User created successfully"


def test_register_missing_fields(client):
    """Test the user registration route with missing fields."""
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 400
    assert response.json["msg"] == "Missing required fields"


def test_register_existing_username(client, existing_user, new_user_data):
    """Test the user registration route with an existing username."""
    new_user_data["username"] = existing_user.username
    response = client.post("/api/v1/auth/register", json=new_user_data)
    assert response.status_code == 400
    assert response.json["msg"] == "Username already exists"


def test_register_existing_email(client, existing_user, new_user_data):
    """Test the user registration route with an existing email."""
    new_user_data["email"] = existing_user.email
    response = client.post("/api/v1/auth/register", json=new_user_data)
    assert response.status_code == 400
    assert response.json["msg"] == "Email already exists"


def test_login(client, existing_user):
    """Test the user login route."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": existing_user.username, "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json


def test_login_invalid_credentials(client):
    """Test the user login route with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistentuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json["msg"] == "Invalid credentials"


def test_protected_route(client, auth_header, existing_user):
    """Test the protected route."""
    response = client.get("/api/v1/auth/protected", headers=auth_header)
    assert response.status_code == 200
    assert response.json["username"] == existing_user.username

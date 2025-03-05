import pytest
from smse_backend.models import User
from flask_jwt_extended import create_access_token


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(username="testuser", email="test@email.com")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_header(client, sample_user):
    """Create an authorization header with a valid JWT token."""
    access_token = create_access_token(identity=str(sample_user.id))
    return {"Authorization": f"Bearer {access_token}"}


def test_get_user(client, auth_header, sample_user):
    """Test the GET /users/me route."""
    response = client.get("/api/users/me", headers=auth_header)
    assert response.status_code == 200
    assert response.json["id"] == sample_user.id
    assert response.json["username"] == sample_user.username
    assert response.json["email"] == sample_user.email


def test_update_user(client, auth_header, sample_user):
    """Test the PUT /users/me route."""
    new_username = "updateduser"
    new_email = "updateduser@test.com"
    response = client.put(
        "/api/users/me",
        headers=auth_header,
        json={"username": new_username, "email": new_email},
    )
    assert response.status_code == 200
    assert response.json["user"]["username"] == new_username
    assert response.json["user"]["email"] == new_email


def test_update_user_existing_username(client, auth_header, sample_user, db_session):
    """Test the PUT /users/me route with an existing username."""
    existing_user = User(username="existinguser", email="existinguser@test.com")
    existing_user.set_password("password123")
    db_session.add(existing_user)
    db_session.commit()

    response = client.put(
        "/api/users/me",
        headers=auth_header,
        json={"username": "existinguser"},
    )
    assert response.status_code == 400
    assert response.json["message"] == "Username already exists"


def test_update_user_existing_email(client, auth_header, sample_user, db_session):
    """Test the PUT /users/me route with an existing email."""
    existing_user = User(username="existinguser2", email="existinguser2@test.com")
    existing_user.set_password("password123")
    db_session.add(existing_user)
    db_session.commit()

    response = client.put(
        "/api/users/me",
        headers=auth_header,
        json={"email": "existinguser2@test.com"},
    )
    assert response.status_code == 400
    assert response.json["message"] == "Email already exists"


def test_delete_user(client, auth_header, sample_user, db_session):
    """Test the DELETE /users/me route."""
    response = client.delete("/api/users/me", headers=auth_header)

    assert response.status_code == 200
    assert response.json["message"] == "User deleted successfully"
    assert db_session.get(User, sample_user.id) is None

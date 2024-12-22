import pytest
from smse_backend.models import User
from sqlalchemy.exc import IntegrityError


def test_create_user(db_session):
    """Test user creation with valid data"""
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")

    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.check_password("password123") is True


def test_invalid_email(db_session):
    """Test user creation with invalid email"""
    with pytest.raises(ValueError, match="Invalid email address"):
        User(username="testuser", email="invalid-email")


def test_duplicate_username(db_session):
    """Test unique username constraint"""
    user1 = User(username="testuser", email="test1@example.com")
    user1.set_password("password123")
    db_session.add(user1)
    db_session.commit()

    user2 = User(username="testuser", email="test2@example.com")
    user2.set_password("password123")
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_password_hashing(db_session):
    """Test password hashing functionality"""
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")

    assert user.password_hash != "password123"
    assert user.check_password("password123") is True
    assert user.check_password("wrongpass") is False


def test_user_relationships(db_session):
    """Test user relationships initialization"""
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()

    assert hasattr(user, "contents")
    assert hasattr(user, "queries")
    assert len(user.contents) == 0
    assert len(user.queries) == 0

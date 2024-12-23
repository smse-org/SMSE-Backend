import pytest
from smse_backend import create_app, db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app("TestConfig")
    return app


@pytest.fixture()
def setup_database(app):
    with app.app_context():
        db.create_all()  # Create schema once for the test session
        yield db
        db.session.remove()
        db.drop_all()  # Drop schema after the session is over


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def db_session(setup_database):
    """Provide a clean database session for each test."""
    db.session.begin_nested()  # Use a nested transaction
    yield db.session
    db.session.rollback()  # Rollback after each test

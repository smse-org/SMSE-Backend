import pytest
from unittest.mock import patch
from smse_backend import create_app, db
import numpy as np


@pytest.fixture(autouse=True)
def mock_celery_tasks():
    """Mock Celery tasks to prevent actual task execution during tests."""
    # Mock the embedding service functions directly
    with patch(
        "smse_backend.services.embedding.schedule_embedding_task"
    ) as mock_schedule_task, patch(
        "smse_backend.services.embedding.generate_query_embedding"
    ) as mock_generate_embedding:

        # Return a string task ID (not a MagicMock object)
        mock_schedule_task.return_value = "mocked-task-id-12345"

        # Configure the generate_query_embedding mock
        mock_generate_embedding.return_value = (np.random.rand(1024), "text")

        yield


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
def db_session(setup_database):
    """Provide a clean database session for each test."""
    db.session.begin_nested()  # Use a nested transaction
    yield db.session
    db.session.rollback()  # Rollback after each test


@pytest.fixture
def client(app, db_session):
    """A test client for the app."""
    return app.test_client()

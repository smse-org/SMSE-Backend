"""
Test multimodal search functionality.

This test ensures that the search API can handle both text and file-based queries
with the SMSE AI framework integration.
"""

import io
import os
import pytest
from werkzeug.datastructures import FileStorage

from smse_backend.models.user import User
from smse_backend.models.content import Content
from smse_backend.models.embedding import Embedding
from smse_backend.models.model import Model
from smse_backend.models.query import Query
from flask_jwt_extended import create_access_token
import datetime
import numpy as np


@pytest.fixture
def auth_header(client, sample_user):
    """Create an authorization header with a valid JWT token."""
    access_token = create_access_token(identity=str(sample_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(username="testuser", email="testuser@test.com")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_content_with_embedding(db_session, sample_user, sample_embedding):
    """Create a sample content with embedding for testing."""
    content = Content(
        content_path=os.path.normpath(f"/{sample_user.id}/test/path/file.txt"),
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
        content_size=1024,
        upload_date=datetime.datetime(2023, 10, 1, 12, 0),
    )
    db_session.add(content)
    db_session.commit()
    return content


@pytest.fixture
def sample_embedding(db_session, sample_model):
    """Create a sample embedding for testing."""
    embedding = Embedding(vector=np.random.rand(1024), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_model(db_session):
    """Create a sample model for testing."""
    model = Model(model_name="testmodel", modality=1)
    db_session.add(model)
    db_session.commit()
    return model


@pytest.fixture
def sample_query(db_session, sample_user, sample_embedding):
    """Create a sample query for testing."""
    query = Query(
        text="sample query text",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query)
    db_session.commit()
    return query


def test_text_search(client, auth_header, sample_content_with_embedding):
    """Test searching with text query."""
    # Search for content
    data = {"query": "test query"}
    response = client.post("/api/search", headers=auth_header, json=data)

    # Verify response
    assert response.status_code == 200
    json_data = response.json
    assert json_data["message"] == "Search completed successfully"
    assert "query_id" in json_data
    assert "query_type" in json_data
    assert json_data["query_type"] == "text"
    assert "results" in json_data
    assert "pagination" in json_data

    # Verify pagination
    assert "limit" in json_data["pagination"]


def test_text_search_with_pagination(
    client, auth_header, sample_content_with_embedding
):
    """Test searching with text query and pagination."""
    # Search for content with pagination
    data = {"query": "test query"}
    response = client.post("/api/search?limit=5", headers=auth_header, json=data)

    # Verify response
    assert response.status_code == 200
    json_data = response.json
    assert json_data["pagination"]["limit"] == 5


def test_file_search(client, auth_header, sample_content_with_embedding, tmp_path):
    """Test searching with file upload."""
    # Create a temporary text file
    test_file_path = os.path.join(tmp_path, "test_query.txt")
    with open(test_file_path, "w") as f:
        f.write("This is a test query file")

    # Create file storage object for upload
    with open(test_file_path, "rb") as f:
        file_storage = FileStorage(
            stream=io.BytesIO(f.read()),
            filename="test_query.txt",
            content_type="text/plain",
        )

    # Upload file for search
    data = {"file": file_storage}
    response = client.post("/api/search", headers=auth_header, data=data)

    # Verify response
    assert response.status_code == 200
    json_data = response.json
    assert json_data["message"] == "Search completed successfully"
    assert json_data["query_type"] == "file"


def test_invalid_file_type(client, auth_header, tmp_path):
    """Test searching with an unsupported file type."""
    # Create a temporary invalid file
    test_file_path = os.path.join(tmp_path, "test.xyz")
    with open(test_file_path, "w") as f:
        f.write("This is an unsupported file type")

    # Create file storage object for upload
    with open(test_file_path, "rb") as f:
        file_storage = FileStorage(
            stream=io.BytesIO(f.read()),
            filename="test.xyz",
            content_type="application/octet-stream",
        )

    # Upload file for search
    data = {"file": file_storage}
    response = client.post("/api/search", headers=auth_header, data=data)

    # Verify response shows invalid file type error
    assert response.status_code == 400
    assert "Unsupported file type" in response.json["message"]


def test_query_history_pagination(client, auth_header, sample_query):
    """Test getting paginated query history."""
    # Get query history with pagination
    response = client.get("/api/search?limit=5&offset=0", headers=auth_header)

    # Verify response
    assert response.status_code == 200
    json_data = response.json
    assert "queries" in json_data
    assert "pagination" in json_data
    assert json_data["pagination"]["limit"] == 5
    assert json_data["pagination"]["offset"] == 0

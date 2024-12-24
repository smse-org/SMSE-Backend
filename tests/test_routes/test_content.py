from unittest.mock import MagicMock
import numpy as np
import pytest
import smse_backend
from smse_backend.models import Content, Embedding, Model, User
from flask_jwt_extended import create_access_token
from io import BytesIO


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
def sample_model(db_session):
    """Create a sample model for testing."""
    model = Model(model_name="testmodel", modality=1)
    db_session.add(model)
    db_session.commit()
    return model


@pytest.fixture
def sample_embedding(db_session, sample_model, sample_user):
    """Create a sample embedding for testing."""
    embedding = Embedding(vector=np.random.rand(328), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_content(db_session, sample_user, sample_embedding):
    """Create a sample content for testing."""
    content = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()
    return content


def test_create_content(client, auth_header, sample_user, sample_model, monkeypatch):
    """Test the POST /contents route."""

    def mock_create_embedding_from_path(file_path):
        return np.random.rand(328)

    monkeypatch.setattr(
        "smse_backend.services.create_embedding_from_path",
        mock_create_embedding_from_path,
    )

    data = {"file": (BytesIO(b"file content"), "test.txt")}
    response = client.post(
        "/api/v1/contents",
        headers=auth_header,
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.json["message"] == "Content created successfully"


def test_get_all_contents(client, auth_header, sample_content):
    """Test the GET /contents route."""
    response = client.get("/api/v1/contents", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json["contents"]) == 1
    assert response.json["contents"][0]["id"] == sample_content.id


def test_get_content(client, auth_header, sample_content):
    """Test the GET /contents/<int:content_id> route."""
    response = client.get(f"/api/v1/contents/{sample_content.id}", headers=auth_header)
    assert response.status_code == 200
    assert response.json["content"]["id"] == sample_content.id


def test_update_content(client, auth_header, sample_content):
    """Test the PUT /contents/<int:content_id> route."""
    data = {"content_tag": False}
    response = client.put(
        f"/api/v1/contents/{sample_content.id}", headers=auth_header, json=data
    )
    assert response.status_code == 200
    assert response.json["content"]["content_tag"] is False


def test_delete_content(client, auth_header, sample_content):
    """Test the DELETE /contents/<int:content_id> route."""
    response = client.delete(
        f"/api/v1/contents/{sample_content.id}", headers=auth_header
    )
    assert response.status_code == 200
    assert response.json["message"] == "Content deleted successfully"


def test_get_allowed_extensions(client):
    """Test the GET /contents/allowed_extensions route."""
    response = client.get("/api/v1/contents/allowed_extensions")
    assert response.status_code == 200
    assert "txt" in response.json["allowed_extensions"]


def test_download_content(client, auth_header, sample_content, monkeypatch):
    """Test the GET /contents/<int:content_id>/download route."""

    mock_send_file = MagicMock(
        return_value=sample_content.content_path,
    )

    def mock_os_path_exists(path):
        return path == sample_content.content_path

    monkeypatch.setattr("os.path.exists", mock_os_path_exists)
    monkeypatch.setattr("smse_backend.routes.v1.content.send_file", mock_send_file)

    response = client.get(
        f"/api/v1/contents/{sample_content.id}/download", headers=auth_header
    )

    mock_send_file.assert_called_once_with(
        sample_content.content_path, as_attachment=True
    )
    assert response.status_code == 200
    assert response.data.decode() == sample_content.content_path

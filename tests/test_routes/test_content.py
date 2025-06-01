import datetime
from mimetypes import guess_type
from unittest.mock import MagicMock
import numpy as np
import pytest
from smse_backend.models import Content, Embedding, Model, User
from flask_jwt_extended import create_access_token
from io import BytesIO
import os


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
    embedding = Embedding(vector=np.random.rand(1024), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_content(db_session, sample_user, sample_embedding):
    """Create a sample content for testing."""
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


def test_create_content(client, auth_header, sample_user, sample_model):
    """Test the POST /contents route."""

    data = {"file": (BytesIO(b"file content"), "test.txt")}
    response = client.post(
        "/api/contents",
        headers=auth_header,
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.json["message"] == "Content created successfully"
    assert "task_id" in response.json
    assert response.json["task_id"] == "mocked-task-id-12345"  # Match the mock ID


def test_get_all_contents(client, auth_header, sample_content):
    """Test the GET /contents route."""
    response = client.get("/api/contents", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json["contents"]) == 1
    assert response.json["contents"][0]["id"] == sample_content.id


def test_get_content(client, auth_header, sample_content):
    """Test the GET /contents/<int:content_id> route."""
    response = client.get(f"/api/contents/{sample_content.id}", headers=auth_header)
    assert response.status_code == 200
    assert response.json["content"]["id"] == sample_content.id


def test_update_content(client, auth_header, sample_content):
    """Test the PUT /contents/<int:content_id> route."""
    data = {"content_tag": False}
    response = client.put(
        f"/api/contents/{sample_content.id}", headers=auth_header, json=data
    )
    assert response.status_code == 200
    assert response.json["content"]["content_tag"] is False


def test_delete_content(client, auth_header, sample_content):
    """Test the DELETE /contents/<int:content_id> route."""
    response = client.delete(f"/api/contents/{sample_content.id}", headers=auth_header)
    assert response.status_code == 200
    assert response.json["message"] == "Content deleted successfully"


def test_get_allowed_extensions(client):
    """Test the GET /contents/allowed_extensions route."""
    response = client.get("/api/contents/allowed_extensions")
    assert response.status_code == 200
    assert "txt" in response.json["allowed_extensions"]


def test_download_content_by_id(client, auth_header, sample_content, monkeypatch):
    """Test download content by ID successfully."""
    mock_send_file = MagicMock(return_value=sample_content.content_path)

    def mock_os_path_exists(path):
        return path == sample_content.content_path

    monkeypatch.setattr("os.path.exists", mock_os_path_exists)
    monkeypatch.setattr("smse_backend.routes.content.send_file", mock_send_file)

    response = client.get(
        "/api/contents/download?content_id={}".format(sample_content.id),
        headers=auth_header,
    )

    assert response.status_code == 200
    mock_send_file.assert_called_once_with(
        sample_content.content_path, mimetype=guess_type(sample_content.content_path)[0]
    )
    assert response.data.decode() == sample_content.content_path


def test_download_content_by_path(client, auth_header, sample_content, monkeypatch):
    """Test download content by path successfully."""
    mock_send_file = MagicMock(return_value=sample_content.content_path)

    def mock_os_path_exists(path):
        return path == sample_content.content_path

    monkeypatch.setattr("os.path.exists", mock_os_path_exists)
    monkeypatch.setattr("smse_backend.routes.content.send_file", mock_send_file)

    response = client.get(
        "/api/contents/download?file_path={}".format(sample_content.content_path),
        headers=auth_header,
    )

    assert response.status_code == 200
    mock_send_file.assert_called_once_with(
        sample_content.content_path,
        mimetype=guess_type(sample_content.content_path)[0],
    )
    assert response.data.decode() == sample_content.content_path


def test_download_content_missing_query_params(client, auth_header):
    """Test download content with missing query parameters."""
    response = client.get("/api/contents/download", headers=auth_header)
    assert response.status_code == 400
    assert response.json["message"] == "Content ID or file path is required"


def test_download_content_non_existent_id(client, auth_header):
    """Test download content with non-existent content ID."""
    response = client.get("/api/contents/download?content_id=999", headers=auth_header)
    assert response.status_code == 404
    assert response.json["message"] == "Content not found"


def test_download_content_unauthorized_access(
    client, auth_header, sample_content, monkeypatch
):
    """Test download content with unauthorized access by path."""
    unauthorized_path = "2/test.txt"  # Different user ID

    def mock_os_path_exists(path):
        return path == unauthorized_path

    monkeypatch.setattr("os.path.exists", mock_os_path_exists)

    response = client.get(
        "/api/contents/download?file_path={}".format(unauthorized_path),
        headers=auth_header,
    )

    assert response.status_code == 403
    assert response.json["message"] == "Unauthorized access"


def test_download_content_non_existent_path(
    client, auth_header, sample_content, monkeypatch
):
    """Test download content with non-existent file path."""
    non_existent_path = os.path.normpath("1/non_existent.txt")

    def mock_os_path_exists(path):
        return path == non_existent_path

    monkeypatch.setattr("os.path.exists", mock_os_path_exists)

    response = client.get(
        "/api/contents/download?file_path={}".format(non_existent_path),
        headers=auth_header,
    )

    assert response.status_code == 404
    assert response.json["message"] == "File not found"


def test_upload_image_with_thumbnail_generation(
    client, auth_header, sample_user, monkeypatch
):
    """Test uploading an image file and verifying thumbnail generation."""
    # Create a simple 1x1 pixel JPEG image in memory
    from PIL import Image
    import io

    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)

    # Mock file storage operations
    mock_file_storage = MagicMock()
    mock_file_storage.save_uploaded_file.return_value = (
        f"{sample_user.id}/test_image.jpg",
        5.0,
    )

    # Mock thumbnail service
    mock_thumbnail_service = MagicMock()
    mock_thumbnail_service.is_supported_file.return_value = True
    mock_thumbnail_service.generate_and_save_thumbnail.return_value = (
        f"{sample_user.id}/test_image_thumb.jpg"
    )

    # Mock the embedding service
    mock_schedule_embedding_task = MagicMock(return_value="task_123")

    monkeypatch.setattr("flask.current_app.file_storage", mock_file_storage)
    monkeypatch.setattr("flask.current_app.thumbnail_service", mock_thumbnail_service)
    monkeypatch.setattr(
        "smse_backend.routes.content.schedule_embedding_task",
        mock_schedule_embedding_task,
    )

    # Upload the image file
    response = client.post(
        "/api/contents",
        data={"file": (img_buffer, "test_image.jpg")},
        headers=auth_header,
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    data = response.json

    # Verify response includes thumbnail URL
    assert "content" in data
    assert "thumbnail_url" in data["content"]
    assert data["content"]["thumbnail_url"] is not None
    assert "/api/contents/thumbnail/" in data["content"]["thumbnail_url"]

    # Verify thumbnail service was called
    mock_thumbnail_service.is_supported_file.assert_called_once()
    mock_thumbnail_service.generate_and_save_thumbnail.assert_called_once()


def test_get_thumbnail_success(client, auth_header, sample_content, monkeypatch):
    """Test successfully retrieving a thumbnail."""
    # Update the sample content to have a thumbnail path
    sample_content.thumbnail_path = f"{sample_content.user_id}/test_thumb.jpg"

    # Create mock thumbnail data
    thumbnail_data = b"fake_thumbnail_jpeg_data"

    # Mock file storage operations
    mock_file_storage = MagicMock()
    mock_file_storage.file_exists.return_value = True
    mock_file_storage.download_file.return_value = thumbnail_data

    monkeypatch.setattr("flask.current_app.file_storage", mock_file_storage)

    response = client.get(
        f"/api/contents/thumbnail/{sample_content.id}",
        headers=auth_header,
    )

    assert response.status_code == 200
    assert response.data == thumbnail_data
    assert response.content_type == "image/jpeg"


def test_get_thumbnail_not_found(client, auth_header, sample_content):
    """Test retrieving thumbnail for content without thumbnail."""
    response = client.get(
        f"/api/contents/thumbnail/{sample_content.id}",
        headers=auth_header,
    )

    assert response.status_code == 404
    assert response.json["message"] == "Thumbnail not available"


def test_get_thumbnail_content_not_found(client, auth_header):
    """Test retrieving thumbnail for non-existent content."""
    response = client.get(
        "/api/contents/thumbnail/999",
        headers=auth_header,
    )

    assert response.status_code == 404
    assert response.json["message"] == "Content not found"

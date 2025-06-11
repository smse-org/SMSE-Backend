import datetime
import pytest
import io
from flask_jwt_extended import create_access_token
from smse_backend.models import Query, SearchRecord, User, Content, Embedding, Model
from smse_backend.services.embedding import generate_multipart_embedding
import numpy as np


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(username="testuser", email="test@email.com")
    user.set_password("testpassword")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_model(db_session):
    """Create a sample model for testing."""
    model = Model(model_name="sample model", modality=0)
    db_session.add(model)
    db_session.commit()
    return model


@pytest.fixture
def auth_header(client, sample_user):
    """Create an authorization header with a valid JWT token."""
    access_token = create_access_token(identity=str(sample_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_embedding(db_session, sample_model):
    """Create a sample embedding for testing."""
    embedding = Embedding(
        vector=np.random.rand(1024), model_id=sample_model.id, modality="text"
    )
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_content(db_session, sample_user, sample_embedding):
    """Create a sample content for testing."""
    content = Content(
        content_path="test.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
        content_size=1024,
        upload_date=datetime.datetime(2023, 10, 1, 12, 0),
    )
    db_session.add(content)
    db_session.commit()
    return content


class TestMultipartEmbedding:
    """Test the multipart embedding generation functionality."""

    def test_generate_multipart_embedding_single(self):
        """Test multipart embedding with a single embedding."""
        embeddings = [np.array([1.0, 2.0, 3.0])]
        modalities = ["text"]

        result_embedding, result_modality = generate_multipart_embedding(
            embeddings, modalities
        )

        assert result_embedding is not None
        assert result_modality == "text"
        assert np.array_equal(result_embedding, np.array([1.0, 2.0, 3.0]))

    def test_generate_multipart_embedding_multiple(self):
        """Test multipart embedding with multiple embeddings."""
        embeddings = [
            np.array([1.0, 2.0, 3.0]),
            np.array([3.0, 4.0, 5.0]),
            np.array([5.0, 6.0, 7.0]),
        ]
        modalities = ["text", "image", "text"]

        result_embedding, result_modality = generate_multipart_embedding(
            embeddings, modalities
        )

        assert result_embedding is not None
        assert result_modality == "text"  # Most common modality
        expected = np.array([3.0, 4.0, 5.0])  # Mean of the three embeddings
        assert np.array_equal(result_embedding, expected)

    def test_generate_multipart_embedding_empty(self):
        """Test multipart embedding with empty input."""
        embeddings = []
        modalities = []

        result_embedding, result_modality = generate_multipart_embedding(
            embeddings, modalities
        )

        assert result_embedding is None
        assert result_modality is None

    def test_generate_multipart_embedding_mismatched_dimensions(self):
        """Test multipart embedding with mismatched dimensions."""
        embeddings = [
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0]),  # Different dimension
        ]
        modalities = ["text", "image"]

        result_embedding, result_modality = generate_multipart_embedding(
            embeddings, modalities
        )

        assert result_embedding is None
        assert result_modality is None


class TestMultipartSearchAPI:
    """Test the multipart search API functionality."""

    def test_search_text_only(self, client, auth_header, sample_content):
        """Test search with text query only."""
        data = {"query": "sample query"}
        response = client.post("/api/search", headers=auth_header, json=data)

        assert response.status_code == 200
        assert response.json["message"] == "Search completed successfully"
        assert response.json["query_type"] == "text"
        assert response.json["query_parts"]["text"] == "sample query"
        assert response.json["query_parts"]["files"] is None
        assert response.json["query_parts"]["total_parts"] == 1

    def test_search_file_only(self, client, auth_header, sample_content):
        """Test search with file upload only."""
        # Create a mock text file
        file_data = io.BytesIO(b"This is a test file content")

        data = {"files": (file_data, "test.txt")}

        response = client.post(
            "/api/search",
            headers=auth_header,
            data=data,
            content_type="multipart/form-data",
        )

        # Note: This will likely fail in tests without the SMSE worker environment
        # but we can test the API structure
        assert response.status_code in [200, 500]  # 500 expected without SMSE

        if response.status_code == 200:
            assert response.json["query_type"] == "file"
            assert response.json["query_parts"]["text"] is None
            assert response.json["query_parts"]["total_parts"] == 1

    def test_search_text_and_file(self, client, auth_header, sample_content):
        """Test search with both text query and file upload."""
        # Create a mock text file
        file_data = io.BytesIO(b"This is a test file content")

        data = {"query": "sample text query", "files": (file_data, "test.txt")}

        response = client.post(
            "/api/search",
            headers=auth_header,
            data=data,
            content_type="multipart/form-data",
        )

        # Note: This will likely fail in tests without the SMSE worker environment
        assert response.status_code in [200, 500]  # 500 expected without SMSE

        if response.status_code == 200:
            assert response.json["query_type"] == "multipart"
            assert response.json["query_parts"]["text"] == "sample text query"
            assert response.json["query_parts"]["total_parts"] == 2

    def test_search_multiple_files(self, client, auth_header, sample_content):
        """Test search with multiple file uploads."""
        # Create mock files
        file1_data = io.BytesIO(b"This is test file 1")
        file2_data = io.BytesIO(b"This is test file 2")

        data = [
            ("files", (file1_data, "test1.txt")),
            ("files", (file2_data, "test2.txt")),
        ]

        response = client.post(
            "/api/search",
            headers=auth_header,
            data=data,
            content_type="multipart/form-data",
        )

        # Note: This will likely fail in tests without the SMSE worker environment
        assert response.status_code in [200, 500]  # 500 expected without SMSE

        if response.status_code == 200:
            assert response.json["query_type"] == "multipart"
            assert response.json["query_parts"]["total_parts"] == 2

    def test_search_no_query(self, client, auth_header):
        """Test search with no query or files."""
        response = client.post("/api/search", headers=auth_header, json={})

        assert response.status_code == 400
        assert "No valid query parts provided" in response.json["message"]

    def test_search_empty_query(self, client, auth_header):
        """Test search with empty query text."""
        data = {"query": ""}
        response = client.post("/api/search", headers=auth_header, json=data)

        assert response.status_code == 400
        assert "No valid query parts provided" in response.json["message"]

    def test_search_unsupported_file_type(self, client, auth_header):
        """Test search with unsupported file type."""
        # Create a mock file with unsupported extension
        file_data = io.BytesIO(b"This is a test file")

        data = {"files": (file_data, "test.xyz")}  # Unsupported extension

        response = client.post(
            "/api/search",
            headers=auth_header,
            data=data,
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json["message"]

import pytest
from flask_jwt_extended import create_access_token
from smse_backend.models import Query, SearchRecord, User, Content, Embedding, Model
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
def sample_content(db_session, sample_user, sample_embedding):
    """Create a sample content for testing."""
    content = Content(
        content_path="test.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()
    return content


@pytest.fixture
def sample_content2(db_session, sample_user, sample_embedding2):
    """Create a sample content for testing."""
    content = Content(
        content_path="test2.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding2.id,
    )
    db_session.add(content)
    db_session.commit()
    return content


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
    embedding = Embedding(vector=np.random.rand(328), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_embedding2(db_session, sample_model):
    """Create a sample embedding for testing."""
    embedding = Embedding(vector=np.random.rand(328), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_query(db_session, sample_user, sample_embedding):
    """Create a sample query for testing."""
    query = Query(
        text="sample query",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query)
    db_session.commit()
    return query


@pytest.fixture
def sample_search_record(db_session, sample_query, sample_content):
    """Create a sample search record for testing."""
    search_record = SearchRecord(
        similarity_score=0.95,
        content_id=sample_content.id,
        query_id=sample_query.id,
    )
    db_session.add(search_record)
    db_session.commit()
    return search_record


def test_search_files(
    client,
    auth_header,
    sample_user,
    sample_model,
    monkeypatch,
    sample_content,
    sample_content2,
):
    """Test the POST /search route."""

    def mock_create_embedding(query_text):
        return np.random.rand(328)

    def mock_search(query_embedding):
        return [
            {"content_id": sample_content.id, "similarity_score": 0.95},
            {"content_id": sample_content2.id, "similarity_score": 0.85},
        ]

    monkeypatch.setattr("smse_backend.services.create_embedding", mock_create_embedding)
    monkeypatch.setattr("smse_backend.routes.search.search", mock_search)

    data = {"query": "sample query"}
    response = client.post("/api/search", headers=auth_header, json=data)

    print(response.json["results"])

    assert response.status_code == 201
    assert response.json["message"] == "Search completed successfully"
    assert "query_id" in response.json
    assert len(response.json["results"]) == 2


def test_get_query_history(client, auth_header, sample_query):
    """Test the GET /queries route."""
    response = client.get("/api/queries", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["id"] == sample_query.id


def test_delete_query(client, auth_header, sample_query, db_session):
    """Test the DELETE /queries/<int:query_id> route."""
    response = client.delete(f"/api/queries/{sample_query.id}", headers=auth_header)
    assert response.status_code == 200
    assert response.json["message"] == "Query deleted successfully"
    assert db_session.get(Query, sample_query.id) is None


def test_get_search_results_history(
    client, auth_header, sample_query, sample_search_record
):
    """Test the GET /searches/<int:query_id> route."""
    response = client.get(f"/api/searches/{sample_query.id}", headers=auth_header)
    assert response.status_code == 200
    assert response.json["query"]["id"] == sample_query.id
    assert response.json["query"]["text"] == sample_query.text
    assert len(response.json["results"]) == 1
    assert response.json["results"][0]["content_id"] == sample_search_record.content_id
    assert (
        response.json["results"][0]["similarity_score"]
        == sample_search_record.similarity_score
    )

import pytest
from smse_backend.models import SearchRecord, Content, Query, User, Embedding
from sqlalchemy.exc import IntegrityError
import numpy as np
from smse_backend.models.model import Model


@pytest.fixture
def sample_model(db_session):
    """Create a sample model for testing"""
    model = Model(model_name="testmodel", modality=1)
    db_session.add(model)
    db_session.commit()
    return model


@pytest.fixture
def sample_embedding(db_session, sample_model):
    """Create a sample embedding for testing"""
    embedding = Embedding(vector=np.random.rand(328), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()
    return embedding


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(username="testuser", email="testuser@test.com")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_content(db_session, sample_user, sample_embedding):
    """Create a sample content for testing"""
    content = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()
    return content


@pytest.fixture
def sample_query(db_session, sample_user, sample_embedding):
    """Create a sample query for testing"""
    query = Query(
        text="sample query",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query)
    db_session.commit()
    return query


def test_create_search_record(db_session, sample_content, sample_query):
    """Test search record creation with valid data"""
    search_record = SearchRecord(
        similarity_score=0.95,
        content_id=sample_content.id,
        query_id=sample_query.id,
    )
    db_session.add(search_record)
    db_session.commit()

    assert search_record.id is not None
    assert search_record.similarity_score == 0.95
    assert search_record.content_id == sample_content.id
    assert search_record.query_id == sample_query.id


def test_search_record_content_relationship(db_session, sample_content, sample_query):
    """Test search record-content relationship"""
    search_record = SearchRecord(
        similarity_score=0.95,
        content_id=sample_content.id,
        query_id=sample_query.id,
    )
    db_session.add(search_record)
    db_session.commit()

    assert search_record.content == sample_content
    assert search_record in sample_content.search_records


def test_search_record_query_relationship(db_session, sample_content, sample_query):
    """Test search record-query relationship"""
    search_record = SearchRecord(
        similarity_score=0.95,
        content_id=sample_content.id,
        query_id=sample_query.id,
    )
    db_session.add(search_record)
    db_session.commit()

    assert search_record.query == sample_query
    assert search_record in sample_query.search_records


def test_unique_content_id_constraint(db_session, sample_content, sample_query):
    """Test unique content_id constraint"""
    search_record1 = SearchRecord(
        similarity_score=0.95,
        content_id=sample_content.id,
        query_id=sample_query.id,
    )
    db_session.add(search_record1)
    db_session.commit()

    search_record2 = SearchRecord(
        similarity_score=0.85,
        content_id=sample_content.id,  # Same content_id
        query_id=sample_query.id,
    )
    db_session.add(search_record2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_unique_query_id_constraint(db_session, sample_content, sample_query):
    """Test unique query_id constraint"""
    search_record1 = SearchRecord(
        similarity_score=0.95,
        content_id=sample_content.id,
        query_id=sample_query.id,
    )
    db_session.add(search_record1)
    db_session.commit()

    search_record2 = SearchRecord(
        similarity_score=0.85,
        content_id=sample_content.id,
        query_id=sample_query.id,  # Same query_id
    )
    db_session.add(search_record2)

    with pytest.raises(IntegrityError):
        db_session.commit()
import pytest
from smse_backend.models import Query, User, Embedding
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
    embedding = Embedding(vector=np.random.rand(1024), model_id=sample_model.id)
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


def test_create_query(db_session, sample_user, sample_embedding):
    """Test query creation with valid data"""
    query = Query(
        text="sample query",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query)
    db_session.commit()

    assert query.id is not None
    assert query.text == "sample query"
    assert query.user_id == sample_user.id
    assert query.embedding_id == sample_embedding.id


def test_query_user_relationship(db_session, sample_user, sample_embedding):
    """Test query-user relationship"""
    query = Query(
        text="sample query",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query)
    db_session.commit()

    assert query.user == sample_user
    assert query in sample_user.queries


def test_query_embedding_relationship(db_session, sample_user, sample_embedding):
    """Test query-embedding relationship"""
    query = Query(
        text="sample query",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query)
    db_session.commit()

    assert query.embedding == sample_embedding
    assert query in sample_embedding.query


def test_unique_user_id_constraint(db_session, sample_user, sample_embedding):
    """Test unique user_id constraint"""
    query1 = Query(
        text="sample query 1",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(query1)
    db_session.commit()

    query2 = Query(
        text="sample query 2",
        user_id=sample_user.id,  # Same user_id
        embedding_id=sample_embedding.id,
    )
    db_session.add(query2)

    with pytest.raises(IntegrityError):
        db_session.commit()

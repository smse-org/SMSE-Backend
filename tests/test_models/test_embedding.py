import datetime
import pytest
from smse_backend.models import Embedding, Model, User
from sqlalchemy.exc import IntegrityError
import numpy as np

from smse_backend.models.content import Content
from smse_backend.models.query import Query


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


def test_create_embedding(db_session, sample_model):
    """Test embedding creation with valid data"""
    embedding = Embedding(vector=np.random.rand(1024), model_id=sample_model.id)
    db_session.add(embedding)
    db_session.commit()

    assert embedding.id is not None
    assert embedding.model_id == sample_model.id


def test_embedding_relationships(db_session, sample_embedding, sample_user):
    """Test embedding relationships initialization"""
    content = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        embedding_id=sample_embedding.id,
        user_id=sample_user.id,
        content_size=1024,
        upload_date=datetime.datetime(2023, 10, 1, 12, 0),
    )

    query = Query(
        text="sample query",
        embedding_id=sample_embedding.id,
        user_id=sample_user.id,
    )

    db_session.add(content)
    db_session.add(query)
    db_session.commit()

    assert content.embedding == sample_embedding
    assert query.embedding == sample_embedding


def test_non_unique_vector_constraint(db_session, sample_model):
    """Test non unique vector constraint"""
    vector = np.random.rand(1024)
    embedding1 = Embedding(vector=vector, model_id=sample_model.id)
    db_session.add(embedding1)
    db_session.commit()

    embedding2 = Embedding(vector=vector, model_id=sample_model.id)
    db_session.add(embedding2)

    assert db_session.commit() is None


def test_embedding_model_relationship(db_session, sample_embedding, sample_model):
    """Test embedding-model relationship"""
    assert sample_embedding.model == sample_model
    assert sample_embedding in sample_model.embeddings

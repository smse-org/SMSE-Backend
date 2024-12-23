import pytest
from smse_backend.models import Content, User
from sqlalchemy.exc import IntegrityError

import pytest
import numpy as np
from smse_backend.models import Embedding
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


def test_create_content(db_session, sample_user, sample_embedding):
    """Test content creation with valid data"""
    content = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()

    assert content.id is not None
    assert content.content_path == "/test/path/file.txt"
    assert content.content_tag is True
    assert content.user_id == sample_user.id
    assert content.embedding_id == sample_embedding.id


def test_unique_content_path(db_session, sample_user, sample_embedding):
    """Test unique content_path constraint"""
    content1 = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content1)
    db_session.commit()

    content2 = Content(
        content_path="/test/path/file.txt",  # Same path
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_relationship(db_session, sample_user, sample_embedding):
    """Test content-user relationship"""
    content = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()

    assert content.user == sample_user
    assert content in sample_user.contents


def test_cascade_delete(db_session, sample_user, sample_embedding):
    """Test if content is deleted when user is deleted"""
    content = Content(
        content_path="/test/path/file.txt",
        content_tag=True,
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()

    content_id = content.id
    db_session.delete(sample_user)
    db_session.commit()

    assert db_session.get(Content, content_id) is None


def test_content_tag_default(db_session, sample_user, sample_embedding):
    """Test content_tag default value"""
    content = Content(
        content_path="/test/path/file.txt",
        user_id=sample_user.id,
        embedding_id=sample_embedding.id,
    )
    db_session.add(content)
    db_session.commit()

    assert content.content_tag is True

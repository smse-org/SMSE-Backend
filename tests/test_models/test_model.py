import pytest
from smse_backend.models import Model


def test_create_model(db_session):
    """Test model creation with valid data"""
    model = Model(model_name="test_model", modality=1)
    db_session.add(model)
    db_session.commit()

    assert model.id is not None
    assert model.model_name == "test_model"
    assert model.modality == 1


def test_model_relationships(db_session):
    """Test model relationships initialization"""
    model = Model(model_name="test_model", modality=1)
    db_session.add(model)
    db_session.commit()

    assert hasattr(model, "embeddings")
    assert len(model.embeddings) == 0


def test_model_representation(db_session):
    """Test model string representation"""
    model = Model(model_name="test_model", modality=1)
    db_session.add(model)
    db_session.commit()

    assert str(model) == f"<Model {model.id}>"


def test_create_multiple_models(db_session):
    """Test creating multiple models"""
    model1 = Model(model_name="model1", modality=1)
    model2 = Model(model_name="model2", modality=2)

    db_session.add(model1)
    db_session.add(model2)
    db_session.commit()

    assert model1.id != model2.id
    assert model1.model_name == "model1"
    assert model2.model_name == "model2"


def test_model_null_constraints_model_name(db_session):
    """Test model null constraints"""
    with pytest.raises(Exception):
        model = Model(modality=1)  # Missing model_name
        db_session.add(model)
        db_session.commit()


def test_model_null_constraints_model_modality(db_session):
    with pytest.raises(Exception):
        model = Model(model_name="test_model")  # Missing modality
        db_session.add(model)
        db_session.commit()

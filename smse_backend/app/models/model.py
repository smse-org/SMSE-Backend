from smse_backend.app import db
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Relationship


class Model(db.Model):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(50), nullable=False)
    modality = Column(Integer, nullable=False)

    embeddings = Relationship("Embedding", back_populates="model", passive_deletes=True)
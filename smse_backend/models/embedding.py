from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import Relationship, mapped_column
from smse_backend.models.base import BaseModel


class Embedding(BaseModel):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vector = mapped_column(Vector(1024), nullable=True)

    content = Relationship("Content", back_populates="embedding")
    query = Relationship("Query", back_populates="embedding")

    model_id = Column(
        Integer,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=False,
    )
    model = Relationship("Model", back_populates="embeddings")

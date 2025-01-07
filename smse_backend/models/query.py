from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import Relationship
from smse_backend.models.base import BaseModel


class Query(BaseModel):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(250), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    user = Relationship("User", back_populates="queries")

    embedding_id = Column(
        Integer,
        ForeignKey("embeddings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    embedding = Relationship(
        "Embedding", back_populates="query", uselist=False, passive_deletes=True
    )

    search_records = Relationship(
        "SearchRecord", back_populates="query_relation", passive_deletes=True
    )

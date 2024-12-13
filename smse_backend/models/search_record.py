from sqlalchemy import Column, Float, Integer, DateTime, func, ForeignKey
from sqlalchemy.orm import Relationship
from smse_backend.models.base import BaseModel


class SearchRecord(BaseModel):
    __tablename__ = "search_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    similarity_score = Column(Float, nullable=False)
    retrieved_at = Column(DateTime, server_default=func.now())

    content_id = Column(
        Integer,
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    content = Relationship("Content", back_populates="search_records")

    query_id = Column(
        Integer,
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    query = Relationship("Query", back_populates="search_records")

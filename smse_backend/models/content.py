from smse_backend.models import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Relationship


class Content(BaseModel):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_path = Column(String(250), unique=True, nullable=False)
    content_tag = Column(Boolean, default=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=False,
    )
    user = Relationship("User", back_populates="contents")

    embedding_id = Column(
        Integer,
        ForeignKey("embeddings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    embedding = Relationship(
        "Embedding", back_populates="content", uselist=False, passive_deletes=True
    )

    search_records = Relationship(
        "SearchRecord", back_populates="content", passive_deletes=True
    )

from smse_backend.models import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Relationship
from smse_backend.utils.file_extensions import get_modality_from_extension


class Content(BaseModel):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_path = Column(String(250), unique=True, nullable=False)
    content_tag = Column(Boolean, default=True)
    upload_date = Column(DateTime, server_default=func.now(), nullable=False)
    content_size = Column(Integer, nullable=False)
    thumbnail_path = Column(String(250), nullable=True)  # Path to thumbnail image
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
        nullable=True,
        index=True,
        unique=True,
    )
    embedding = Relationship(
        "Embedding", back_populates="content", uselist=False, passive_deletes=True
    )

    search_records = Relationship(
        "SearchRecord", back_populates="content", passive_deletes=True
    )

    tasks = Relationship("Task", back_populates="content", passive_deletes=True)

    @property
    def filename(self):
        """Get the original filename from the content path.
        Extracts the original filename from the format: UUID_originalname"""
        import os

        basename = os.path.basename(self.content_path)
        # Extract original filename from the UUID_originalname format
        # Find the first underscore which separates UUID from original name
        if "_" in basename:
            # Everything after the first underscore is the original filename
            return basename.split("_", 1)[1]
        # Fallback to the full basename if the expected format is not found
        return basename

    @property
    def file_extension(self):
        """Get the file extension from the content path."""
        import os

        _, ext = os.path.splitext(self.content_path)
        return ext.lower()

    @property
    def modality(self):
        """Determine the modality based on the file extension."""
        return get_modality_from_extension(self.content_path)

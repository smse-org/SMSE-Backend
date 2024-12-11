from smse_backend.app import db, bcrypt

from sqlalchemy.orm import validates
import re

class Embedding(db.Model):
    __tablename__ = "embeddings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # TODO create a vector column
    #embedding_vector = db.Column(db.Vector, unique=True, nullable=False)
    
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    content = db.Relationship("Content", back_populates="embedding")

    query_id = db.Column(db.Integer, db.ForeignKey('queries.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    query = db.Relationship("Query", back_populates="embedding")

    model_id = db.Column(db.Integer, db.ForeignKey('models.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    model = db.Relationship("Model", back_populates="embeddings")
    

from smse_backend.app import db, bcrypt

from sqlalchemy.orm import validates
import re

class SearchRecord(db.Model):
    __tablename__ = "search_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    similarity_score = db.Column(db.Integer, nullable=False)
    retrieved_at = db.Column(db.DateTime, server_default=db.func.now())
    
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    content = db.Relationship("Content", back_populates="search_records")

    query_id = db.Column(db.Integer, db.ForeignKey('queries.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    query = db.Relationship("Query", back_populates="search_records")


    

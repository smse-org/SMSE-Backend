from smse_backend.app import db, bcrypt

from sqlalchemy.orm import validates
import re

class Query(db.Model):
    __tablename__ = "queries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    query_text = db.Column(db.String(250), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    user = db.Relationship("User", back_populates="queries")

    search_records = db.relationship("SearchRecord", back_populates="query", passive_deletes=True)

    embedding = db.relationship("Embedding", back_populates="query", useList=False, passive_deletes=True)

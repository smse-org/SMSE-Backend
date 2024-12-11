from smse_backend.app import db, bcrypt

from sqlalchemy.orm import validates
import re

class Content(db.Model):
    __tablename__ = "contents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content_path = db.Column(db.String(250), unique=True, nullable=False)
    content_tag = db.Column(db.Boolean, default=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True, unique=True)
    user = db.Relationship("User", back_populates="contents")

    search_records = db.relationship("SearchRecord", back_populates="content", passive_deletes=True)
 
    embedding = db.relationship("Embedding", back_populates="content", useList=False, passive_deletes=True)
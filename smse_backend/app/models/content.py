from smse_backend.app import db, bcrypt

from sqlalchemy.orm import validates
import re

class Content(db.Model):
    __tablename__ = "content"

    id = db.Column(db.Integer, primary_key=True)
    content_path = db.Column(db.String(250), unique=True, nullable=False)
    content_tag = db.Column(db.Boolean, default=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", back_populates="contents")

    

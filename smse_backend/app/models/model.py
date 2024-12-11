from smse_backend.app import db, bcrypt

from sqlalchemy.orm import validates
import re

class Model(db.Model):
    __tablename__ = "models"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name = db.Column(db.String(50), nullable=False)
    modality = db.Column(db.Integer, nullable=False)
    
    embeddings = db.relationship("Embedding", back_populates="model", passive_deletes=True)

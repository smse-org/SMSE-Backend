from smse_backend import bcrypt
from sqlalchemy.orm import validates
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import Relationship
from smse_backend.models.base import BaseModel

import re


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    contents = Relationship("Content", back_populates="user", passive_deletes=True)
    queries = Relationship("Query", back_populates="user", passive_deletes=True)

    @validates("email")
    def validate_email(self, key, email):
        # Basic email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address")
        return email

    def set_password(self, password):
        """Hash the password for storage"""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Check hashed password"""
        return bcrypt.check_password_hash(self.password_hash, password)

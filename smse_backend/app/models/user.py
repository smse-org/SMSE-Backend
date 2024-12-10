from smse_backend.app import db, bcrypt

# from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
import re


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    #is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    contents = db.relationship("Content", back_populates="user", cascade="all, delete-orphan")

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

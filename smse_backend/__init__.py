from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_name="DevelopmentConfig"):
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config_name == "DevelopmentConfig":
        from smse_backend.config.development import DevelopmentConfig

        config = DevelopmentConfig
    elif config_name == "TestConfig":
        from smse_backend.config.test import TestConfig

        config = TestConfig
    elif config_name == "ProductionConfig":
        from smse_backend.config.production import ProductionConfig

        config = ProductionConfig

    app.config.from_object(config)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    from smse_backend.routes import register_blueprints

    register_blueprints(app)

    return app

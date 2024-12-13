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


def create_app(config_name="development"):
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config_name == "development":
        from smse_backend.app.config.development import DevelopmentConfig

        app.config.from_object(DevelopmentConfig)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    from smse_backend.app.routes import register_blueprints

    register_blueprints(app)

    return app

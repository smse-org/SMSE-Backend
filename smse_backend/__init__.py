from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

swaggerui_blueprint = get_swaggerui_blueprint(
    "/api/docs",  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    "/swagger.json",
    config={"app_name": "SMSE API"},  # Swagger UI config overrides
)


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

    CORS(app, origins=["https://smseai.me", "https://web.smseai.me"])

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Initialize file storage service
    from smse_backend.services.file_storage import FileStorageService
    from smse_backend.services.thumbnail import ThumbnailService

    app.file_storage = FileStorageService()
    app.thumbnail_service = ThumbnailService(app.file_storage)

    # Register blueprints
    from smse_backend.routes import register_blueprints

    register_blueprints(app)
    app.register_blueprint(swaggerui_blueprint)

    # Initialize Celery
    from smse_backend.celery_app import make_celery

    celery = make_celery(app)
    app.celery = celery

    # Schedule cleanup job for temporary query files
    with app.app_context():
        from smse_backend.services.file_cleanup import schedule_cleanup_job

        schedule_cleanup_job()

    return app

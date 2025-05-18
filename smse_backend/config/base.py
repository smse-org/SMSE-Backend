import os


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")

    database_type = os.environ.get("DATABASE_TYPE", "sqlite")

    if database_type == "sqlite":
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    elif database_type == "postgres":
        database_username = os.environ.get("DATABASE_USERNAME", "postgres")
        database_password = os.environ.get("DATABASE_PASSWORD", "postgres")
        database_host = os.environ.get("DATABASE_HOST", "localhost")
        database_port = os.environ.get("DATABASE_PORT", "5432")
        database_name = os.environ.get("DATABASE_NAME", "app")
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{database_username}:{database_password}@{database_host}:{database_port}/{database_name}"
    else:
        raise ValueError(
            "Unsupported database type. Use either 'sqlite' or 'postgres'."
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configurations
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_FOLDER = "./tmp/uploads"
    
    # Celery configurations
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # SMSE configurations
    SMSE_CHECKPOINTS_PATH = os.environ.get("SMSE_CHECKPOINTS_PATH", "./.checkpoints")

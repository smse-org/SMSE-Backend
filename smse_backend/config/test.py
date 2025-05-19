from .base import BaseConfig
import os


class TestConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"

    database_type = os.environ.get("DATABASE_TYPE", "sqlite")

    if database_type == "sqlite":
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    elif database_type == "postgres":
        database_username = os.environ.get("DATABASE_USERNAME", "postgres")
        database_password = os.environ.get("DATABASE_PASSWORD", "postgres")
        database_host = os.environ.get("DATABASE_HOST", "localhost")
        database_port = os.environ.get("DATABASE_PORT", "5432")
        database_name = os.environ.get("TEST_DATABASE_NAME", "test_db")
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{database_username}:{database_password}@{database_host}:{database_port}/{database_name}"
    else:
        raise ValueError(
            "Unsupported database type. Use either 'sqlite' or 'postgres'."
        )

    # Use memory for Celery in tests
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "memory://"
    CELERY_ALWAYS_EAGER = (
        True  # Tasks will be executed locally instead of being sent to the queue
    )

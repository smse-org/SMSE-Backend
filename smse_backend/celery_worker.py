"""
Celery worker entry point.

This file is used to start the Celery worker:
    celery -A smse_backend.celery_worker worker --loglevel=info
"""

from smse_backend import create_app
from smse_backend.celery_app import celery, make_celery

# Create Flask app
flask_app = create_app()
# Update celery with our app context
celery_app = make_celery(flask_app)

# Update the default celery instance with our app-aware celery
celery.conf = celery_app.conf
celery.Task = celery_app.Task

# This makes the app context available to Celery tasks
app = flask_app

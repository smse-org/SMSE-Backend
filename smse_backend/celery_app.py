from celery import Celery


def make_celery(app=None):
    """
    Create a new Celery instance and integrate it with the Flask application.
    """
    celery = Celery(
        app.import_name if app else "smse_backend",
        broker=app.config["CELERY_BROKER_URL"] if app else None,
        backend=app.config["CELERY_RESULT_BACKEND"] if app else None,
        include=["smse_backend.tasks"],
    )

    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


# Create a default celery instance for use outside Flask application
celery = make_celery()

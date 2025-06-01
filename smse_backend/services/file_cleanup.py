from datetime import timedelta
from flask import current_app


def schedule_cleanup_job():
    """
    Schedule a periodic cleanup job for temporary query files.
    This function should be called when the app starts.
    """
    from smse_backend.celery_app import celery as celery_app

    @celery_app.task(name="cleanup_temp_files")
    def cleanup_task():
        with current_app.app_context():
            files_deleted = current_app.file_storage.cleanup_temp_query_files()
            current_app.logger.info(f"Cleaned up {files_deleted} temporary query files")

    # Schedule the task to run daily
    celery_app.conf.beat_schedule = {
        "cleanup-temp-files": {
            "task": "cleanup_temp_files",
            "schedule": timedelta(hours=24),
        },
    }

    return cleanup_task

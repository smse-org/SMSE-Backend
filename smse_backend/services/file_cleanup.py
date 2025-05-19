import os
from datetime import datetime, timedelta
from flask import current_app


def cleanup_temp_query_files(age_in_hours=24):
    """
    Clean up temporary query files older than the specified age.

    Args:
        age_in_hours (int): Age threshold in hours. Files older than this will be deleted.

    Returns:
        int: Number of files deleted
    """
    try:
        queries_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "queries")

        # If directory doesn't exist, nothing to clean up
        if not os.path.exists(queries_dir):
            return 0

        files_deleted = 0
        threshold_time = datetime.now() - timedelta(hours=age_in_hours)

        # Walk through all user directories in queries folder
        for user_dir in os.listdir(queries_dir):
            user_path = os.path.join(queries_dir, user_dir)

            # Skip if not a directory
            if not os.path.isdir(user_path):
                continue

            # Process all files in user directory
            for filename in os.listdir(user_path):
                file_path = os.path.join(user_path, filename)

                # Skip if not a file
                if not os.path.isfile(file_path):
                    continue

                # Check file modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                # If file is older than threshold, delete it
                if mod_time < threshold_time:
                    os.remove(file_path)
                    files_deleted += 1

            # Check if user directory is empty after cleanup
            if not os.listdir(user_path):
                os.rmdir(user_path)

        return files_deleted

    except Exception as e:
        current_app.logger.error(f"Error during temp file cleanup: {str(e)}")
        return 0


def schedule_cleanup_job():
    """
    Schedule a periodic cleanup job for temporary query files.
    This function should be called when the app starts.
    """
    from smse_backend.celery_app import celery as celery_app

    @celery_app.task(name="cleanup_temp_files")
    def cleanup_task():
        with current_app.app_context():
            files_deleted = cleanup_temp_query_files()
            current_app.logger.info(f"Cleaned up {files_deleted} temporary query files")

    # Schedule the task to run daily
    celery_app.conf.beat_schedule = {
        "cleanup-temp-files": {
            "task": "cleanup_temp_files",
            "schedule": timedelta(hours=24),
        },
    }

    return cleanup_task

from smse_backend.tasks import process_file


def schedule_embedding_task(file_path: str, content_id: int = None):
    """
    Schedule a Celery task to create an embedding for a file.

    Args:
        file_path (str): Path to the file
        user_id (int): User ID
        content_id (int, optional): Content ID if already exists

    Returns:
        str: Task ID
    """
    # Schedule the Celery task
    task = process_file.delay(file_path, content_id)
    return task.id

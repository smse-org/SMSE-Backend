from smse_backend.tasks import process_file, process_query
import numpy as np


def schedule_embedding_task(file_path: str, content_id: int = None):
    """
    Schedule a Celery task to create an embedding for a file.

    Args:
        file_path (str): Path to the file
        content_id (int, optional): Content ID if already exists

    Returns:
        str: Task ID
    """
    # Schedule the Celery task
    task = process_file.delay(file_path, content_id)
    return task.id


def generate_query_embedding(query_text: str = None, query_file: str = None):
    """
    Generate an embedding for a query (synchronously for search operations).
    Either query_text or query_file must be provided.

    Args:
        query_text (str, optional): The text query
        query_file (str, optional): Path to a query file

    Returns:
        np.ndarray: The generated embedding vector
        None: If there was an error
    """
    if query_text is not None:
        # Process text query with high priority
        task = process_query.apply_async(args=[query_text, False, None], priority=10)
        result = task.get(timeout=30)  # Wait for completion with a timeout

        if result.get("status") == "success":
            return np.array(result.get("embedding"))
        return None

    elif query_file is not None:
        # Process file query with high priority
        task = process_query.apply_async(args=[None, True, query_file], priority=10)
        result = task.get(timeout=30)  # Wait for completion with a timeout

        if result.get("status") == "success":
            return np.array(result.get("embedding"))
        return None

    return None

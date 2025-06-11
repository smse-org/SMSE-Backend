from smse_backend.tasks import process_file, process_query
import numpy as np
from typing import List


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
        tuple: (np.ndarray, str) - The generated embedding vector and modality
        None: If there was an error
    """
    if query_text is not None:
        # Process text query with high priority
        task = process_query.apply_async(args=[query_text, False, None], priority=10)
        result = task.get(timeout=80)  # Wait for completion with a timeout

        if result.get("status") == "success":
            return np.array(result.get("embedding")), result.get("modality", "text")
        return None, None

    elif query_file is not None:
        # Process file query with high priority
        task = process_query.apply_async(args=[None, True, query_file], priority=10)
        result = task.get(timeout=80)  # Wait for completion with a timeout

        if result.get("status") == "success":
            return np.array(result.get("embedding")), result.get("modality", "text")
        return None, None

    return None, None


def generate_multipart_embedding(embeddings: List[np.ndarray], modalities: List[str]):
    """
    Generate a combined embedding from multiple embeddings by taking their mean.

    Args:
        embeddings (List[np.ndarray]): List of embedding vectors
        modalities (List[str]): List of modalities for each embedding

    Returns:
        tuple: (np.ndarray, str) - The combined embedding vector and primary modality
        None: If there was an error or no embeddings provided
    """
    if not embeddings:
        return None, None

    try:
        # Convert to numpy arrays if they aren't already
        embeddings_array = [np.array(emb) for emb in embeddings]

        # Check that all embeddings have the same dimension
        first_shape = embeddings_array[0].shape
        for i, emb in enumerate(embeddings_array[1:], 1):
            if emb.shape != first_shape:
                raise ValueError(
                    f"Embedding {i} has shape {emb.shape}, expected {first_shape}"
                )

        # Compute the mean of all embeddings
        combined_embedding = np.mean(embeddings_array, axis=0)

        # Determine the primary modality (most common, or first if tie)
        modality_counts = {}
        for modality in modalities:
            modality_counts[modality] = modality_counts.get(modality, 0) + 1

        # Get the most common modality
        primary_modality = max(modality_counts.items(), key=lambda x: x[1])[0]

        return combined_embedding, primary_modality

    except Exception as e:
        print(f"Error combining embeddings: {str(e)}")
        return None, None

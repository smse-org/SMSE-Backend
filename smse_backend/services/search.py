import numpy as np


def search(
    query_embedding: np.ndarray,
) -> list[dict[int, np.ndarray, float]]:  # TODO: Implement search function
    """
    search for files based on a query
    """
    return [
        {"content_id": 1, "embedding": np.random.rand(328), "similarity_score": 0.5}
    ]

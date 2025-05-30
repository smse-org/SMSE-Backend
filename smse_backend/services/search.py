import numpy as np
from flask import current_app
from sqlalchemy.sql import text
from smse_backend import db
import math
from typing import Dict, List


modality_thresholds = {
    "text": {
        "text": 0.65,
        "image": 0.2,
        "audio": 0.2,
    },
    "image": {
        "text": 0.2,
        "image": 0.5,
        "audio": 0.15,
    },
    "audio": {
        "text": 0.1,  # could be even lower like 0.09
        "image": 0.1,
        "audio": 0.5,
    },
}


def softmax(scores: List[float]) -> List[float]:
    """
    Apply softmax normalization to a list of similarity scores.

    Args:
        scores (List[float]): List of similarity scores

    Returns:
        List[float]: Normalized scores that sum to 1
    """
    if not scores:
        return []

    # Shift scores for numerical stability
    max_score = max(scores)
    exp_scores = [math.exp(score - max_score) for score in scores]
    sum_exp_scores = sum(exp_scores)

    # Handle case where all scores are equal (or empty)
    if sum_exp_scores == 0:
        n = len(scores)
        return [1.0 / n] * n if n > 0 else []

    return [exp_score / sum_exp_scores for exp_score in exp_scores]


def min_max_normalize(scores: List[float]) -> List[float]:
    """
    Apply min-max normalization to scale scores between 0 and 1.

    Args:
        scores (List[float]): List of similarity scores

    Returns:
        List[float]: Normalized scores between 0 and 1
    """
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    # Handle case where all scores are equal
    if max_score == min_score:
        return [1.0] * len(scores)

    return [(score - min_score) / (max_score - min_score) for score in scores]


def search_by_modality(
    query_embedding: np.ndarray, user_id: int, modality: str, limit: int = 30
) -> List[Dict]:
    """
    Search for content files of a specific modality based on query embedding.

    Args:
        query_embedding (np.ndarray): The query embedding vector
        modality (str): The modality to search for ("text", "image", "audio")
        limit (int): Maximum number of results to return
        offset (int): Number of results to skip

    Returns:
        List[Dict]: List of dictionaries with content_id and similarity_score
    """
    try:
        # Convert the embedding to a string format compatible with pgvector
        embedding_str = ",".join(map(str, query_embedding))

        # Use raw SQL with pgvector for similarity search, filtering by modality
        sql = text(
            f"""
            SELECT 
                c.id as content_id,
                1-(e.vector <=> '[{embedding_str}]') AS similarity_score
            FROM contents c
            JOIN embeddings e ON c.embedding_id = e.id
            WHERE c.user_id = :user_id
              AND e.vector IS NOT NULL
              AND e.modality = :modality
            ORDER BY 1-(e.vector <=> '[{embedding_str}]') ASC
            LIMIT :limit
            """
        )

        # Execute the query
        result = db.session.execute(
            sql, {"user_id": user_id, "modality": modality, "limit": limit}
        )

        # Process results
        search_results = []
        for row in result:
            search_results.append(
                {
                    "content_id": row.content_id,
                    "similarity_score": float(row.similarity_score),
                    "modality": modality,
                }
            )

        return search_results

    except Exception as e:
        current_app.logger.error(f"Search error for {modality}: {str(e)}")
        return []


def search(
    query_embedding: np.ndarray,
    query_modality: str,
    user_id: int,
    limit: int = 10,
    search_modalities: List[str] = ["text", "image", "audio"],
) -> List[Dict]:
    """
    Search for content files across all modalities based on a query embedding.

    Args:
        query_embedding (np.ndarray): The query embedding vector
        limit (int): Maximum number of results to return

    Returns:
        List[Dict]: List of dictionaries containing content_id, similarity_score, and modality
    """
    try:
        # Search each modality
        all_results = []

        for modality in search_modalities:

            if modality not in ["text", "image", "audio"]:
                current_app.logger.warning(
                    f"Unsupported modality: {modality}. Skipping search."
                )
                continue

            modality_results = search_by_modality(
                query_embedding=query_embedding,
                user_id=user_id,
                modality=modality,
                limit=limit,
            )

            filtered_results = []

            for index, result in enumerate(modality_results):
                print(
                    result["similarity_score"],
                    modality_thresholds[query_modality][modality],
                    index,
                )
                if (
                    not result["similarity_score"]
                    < modality_thresholds[query_modality][modality]
                ):
                    filtered_results.append(result)

            # Skip empty results
            if not modality_results:
                continue

            scores = [result["similarity_score"] for result in filtered_results]

            # Normalize scores using softmax - keeps scores relative within the same modality
            normalized_scores = scores  # min_max_normalize(scores)

            # Update results with normalized scores
            for i, result in enumerate(filtered_results):
                result["normalized_score"] = normalized_scores[i]

            all_results.extend(filtered_results)

        # Sort by normalized score (descending)
        all_results.sort(key=lambda x: x["normalized_score"], reverse=True)

        # Apply pagination
        paginated_results = all_results[0:limit]

        # Filter by threshold and prepare final results
        final_results = [
            {
                "content_id": result["content_id"],
                "similarity_score": result["normalized_score"],
                "modality": result["modality"],
            }
            for result in paginated_results
        ]

        return final_results

    except Exception as e:
        current_app.logger.error(f"Multi-modal search error: {str(e)}")
        # Return empty results on error
        return []

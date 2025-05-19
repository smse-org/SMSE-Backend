import numpy as np
from flask import current_app
from sqlalchemy.sql import text
from smse_backend import db
import math
from typing import Dict, List, Optional


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
    query_embedding: np.ndarray, modality: str, limit: int = 30
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

        current_app.logger.debug(
            f"{modality} search with embedding: {embedding_str[:50]}..."
        )

        # Use raw SQL with pgvector for similarity search, filtering by modality
        sql = text(
            f"""
            SELECT 
                c.id as content_id,
                (e.vector <#> '[{embedding_str}]') * -1 AS similarity_score
            FROM contents c
            JOIN embeddings e ON c.embedding_id = e.id
            WHERE e.vector IS NOT NULL
              AND e.modality = :modality
            ORDER BY e.vector <#> '[{embedding_str}]' ASC
            LIMIT :limit
            """
        )

        # Execute the query
        result = db.session.execute(sql, {"modality": modality, "limit": limit})

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
    limit: int = 10,
    modalities: List[str] = ["text", "image", "audio"],
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

        for modality in modalities:
            modality_results = search_by_modality(
                query_embedding=query_embedding,
                modality=modality,
                limit=limit,
            )

            # Skip empty results
            if not modality_results:
                continue

            # Keep track of scores for normalization within this modality
            scores = [result["similarity_score"] for result in modality_results]

            # Normalize scores using softmax - keeps scores relative within the same modality
            normalized_scores = softmax(scores)

            # Update results with normalized scores
            for i, result in enumerate(modality_results):
                result["normalized_score"] = normalized_scores[i]

            all_results.extend(modality_results)

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

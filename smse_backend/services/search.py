import numpy as np
from flask import current_app
from sqlalchemy.sql import text
from smse_backend import db


def search(
    query_embedding: np.ndarray,
    limit: int = 10,
    threshold: float = 0.6,
    offset: int = 0,
) -> list[dict]:
    """
    Search for content files based on a query embedding using vector similarity.

    Args:
        query_embedding (np.ndarray): The query embedding vector
        limit (int): Maximum number of results to return
        threshold (float): Minimum similarity score threshold (0-1)
        offset (int): Number of results to skip for pagination

    Returns:
        list: List of dictionaries containing content_id and similarity_score
    """
    try:
        # Convert the embedding to a string format compatible with pgvector
        embedding_str = ",".join(map(str, query_embedding))

        current_app.logger.debug(f"Query embedding: {embedding_str}")

        # Use raw SQL to leverage pgvector's similarity search capabilities
        sql = text(
            f"""
            SELECT 
                c.id as content_id,
                (e.vector <#> '[{embedding_str}]') * -1 AS similarity_score
            FROM contents c
            JOIN embeddings e ON c.embedding_id = e.id
            WHERE e.vector IS NOT NULL
            ORDER BY e.vector <#> '[{embedding_str}]' ASC
            LIMIT :limit
            OFFSET :offset
            """
        )
        # Execute the query
        result = db.session.execute(sql, {"limit": limit, "offset": offset})

        # Process results
        search_results = []
        for row in result:
            # Only include results above the threshold
            if row.similarity_score >= threshold:
                search_results.append(
                    {
                        "content_id": row.content_id,
                        "similarity_score": float(row.similarity_score),
                    }
                )

        return search_results

    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        # Return empty results on error
        return []

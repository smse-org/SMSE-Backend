from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from smse_backend import db
from smse_backend.models import Query, SearchRecord, Embedding, Model
from smse_backend.services import create_embedding, search

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["POST"])
@jwt_required()
def search_files():
    current_user_id = get_jwt_identity()
    data = request.json
    query_text = data.get("query")

    if not query_text:
        return jsonify({"message": "Query text is required"}), 400

    # Generate query embedding
    query_embedding = create_embedding(query_text)
    if query_embedding is None:
        return jsonify({"message": "Error creating embedding for query"}), 500

    # Get user chosen model
    model_id = db.session.get(
        Model, 1
    ).id  # TODO: Allow user to choose model (handle user settings)

    # Store the query
    new_query = Query(
        text=query_text,
        user_id=current_user_id,
        embedding=Embedding(vector=query_embedding, model_id=model_id),
    )
    db.session.add(new_query)
    db.session.commit()

    # Fetch relevant files
    search_results = search(query_embedding)

    # Store search results
    for result in search_results:
        content_id = result["content_id"]
        similarity_score = result["similarity_score"]

        new_search_record = SearchRecord(
            similarity_score=similarity_score,
            content_id=content_id,
            query_id=new_query.id,
        )
        db.session.add(new_search_record)

    db.session.commit()

    return (
        jsonify(
            {
                "message": "Search completed successfully",
                "query_id": new_query.id,
                "results": [
                    {
                        "content_id": result["content_id"],
                        "similarity_score": result["similarity_score"],
                    }
                    for result in search_results
                ],
            }
        ),
        201,
    )


@search_bp.route("/search", methods=["GET"])
@jwt_required()
def get_query_history():
    # TODO: Implement pagination
    current_user_id = get_jwt_identity()
    queries = Query.query.filter_by(user_id=current_user_id).all()

    return (
        jsonify(
            [
                {
                    "id": query.id,
                    "text": query.text,
                    "timestamp": query.timestamp,
                }
                for query in queries
            ]
        ),
        200,
    )


@search_bp.route("/search/<int:query_id>", methods=["GET"])
@jwt_required()
def get_search_results_history(query_id):
    current_user_id = get_jwt_identity()
    query = Query.query.filter_by(id=query_id, user_id=current_user_id).first()

    if not query:
        return jsonify({"message": "Query not found"}), 404

    search_records = SearchRecord.query.filter_by(query_id=query_id).all()

    return (
        jsonify(
            {
                "query": {
                    "id": query.id,
                    "text": query.text,
                    "timestamp": query.timestamp,
                },
                "results": [
                    {
                        "content_id": record.content_id,
                        "similarity_score": record.similarity_score,
                        "retrieved_at": record.retrieved_at,
                    }
                    for record in search_records
                ],
            }
        ),
        200,
    )


@search_bp.route("/search/<int:query_id>", methods=["DELETE"])
@jwt_required()
def delete_query(query_id):
    current_user_id = get_jwt_identity()
    query = Query.query.filter_by(id=query_id, user_id=current_user_id).first()

    if not query:
        return jsonify({"message": "Query not found"}), 404

    db.session.delete(query)
    db.session.commit()

    return jsonify({"message": "Query deleted successfully"}), 200

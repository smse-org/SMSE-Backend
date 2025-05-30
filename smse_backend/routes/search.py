from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

from smse_backend import db
from smse_backend.models import Query, SearchRecord, Embedding, Model, Content
from smse_backend.services.search import search
from smse_backend.services.embedding import generate_query_embedding
from smse_backend.services.file_storage import file_storage
from smse_backend.utils.file_extensions import EXTENSION_TO_MODALITY

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["POST"])
@jwt_required()
def search_files():
    current_user_id = get_jwt_identity()

    # Extract pagination parameters
    limit = int(request.args.get("limit", 10))
    modalities = request.args.getlist("modalities")

    if not modalities:
        modalities = ["text", "image", "audio"]

    # Check if it's a text query or a file upload
    if request.is_json:
        # Text-based query
        data = request.json
        query_text = data.get("query")

        if not query_text:
            return jsonify({"message": "Query text is required"}), 400

        # Generate query embedding
        query_embedding, query_modality = generate_query_embedding(
            query_text=query_text
        )
        query_type = "text"
        query_content = query_text

    elif "file" in request.files:
        # File-based query
        file = request.files["file"]

        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        # Validate file type by extension
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in EXTENSION_TO_MODALITY:
            return (
                jsonify(
                    {
                        "message": f"Unsupported file type. Allowed types: {', '.join(EXTENSION_TO_MODALITY.keys())}"
                    }
                ),
                400,
            )

        # Save the file temporarily using file storage service
        file_path, full_path = file_storage.save_query_file(file, current_user_id)

        try:
            # Generate query embedding
            query_embedding, query_modality = generate_query_embedding(
                query_file=full_path
            )
            query_type = "file"
            query_content = file.filename
        except Exception as e:
            # Clean up the file in case of error
            file_storage.delete_file(file_path)
            current_app.logger.error(f"Error processing query file: {str(e)}")
            return jsonify({"message": f"Error processing file: {str(e)}"}), 500

    else:
        return jsonify({"message": "Either query text or file is required"}), 400

    # Check if embedding generation was successful
    if query_embedding is None:
        return jsonify({"message": "Error creating embedding for query"}), 500

    try:
        # Get user chosen model
        model_id = db.session.get(Model, 1).id  # TODO: Allow user to choose model

        # Store the query with its embedding
        new_embedding = Embedding(
            vector=query_embedding,
            model_id=model_id,
            modality=query_modality,
        )
        db.session.add(new_embedding)

        # Create new query record
        new_query = Query(
            text=query_content,
            user_id=current_user_id,
            embedding=new_embedding,
        )
        db.session.add(new_query)
        db.session.commit()

        # Perform the search using the embedding with pagination
        search_results = search(
            query_embedding,
            query_modality,
            current_user_id,
            limit=limit,
            search_modalities=modalities,
        )

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

        # Prepare content details for response
        detailed_results = []
        for result in search_results:
            content_id = result["content_id"]
            content = db.session.get(Content, content_id)

            if content:
                detailed_results.append(
                    {
                        "content_id": content_id,
                        "content_path": content.content_path,
                        "content_tag": content.content_tag,
                        "similarity_score": result["similarity_score"],
                    }
                )

        return (
            jsonify(
                {
                    "message": "Search completed successfully",
                    "query_id": new_query.id,
                    "query_type": query_type,
                    "results": detailed_results,
                    "pagination": {
                        "limit": limit,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({"message": f"Error performing search: {str(e)}"}), 500


@search_bp.route("/search", methods=["GET"])
@jwt_required()
def get_query_history():
    current_user_id = get_jwt_identity()

    # Get pagination parameters
    limit = int(request.args.get("limit", 10))
    offset = int(request.args.get("offset", 0))

    # Get paginated queries
    queries = (
        Query.query.filter_by(user_id=current_user_id)
        .order_by(Query.timestamp.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Get total count for pagination
    total_count = Query.query.filter_by(user_id=current_user_id).count()

    return (
        jsonify(
            {
                "queries": [
                    {
                        "id": query.id,
                        "text": query.text,
                        "timestamp": query.timestamp,
                    }
                    for query in queries
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count,
                },
            }
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

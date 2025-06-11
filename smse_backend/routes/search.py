from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

from smse_backend import db
from smse_backend.models import Query, SearchRecord, Embedding, Model, Content
from smse_backend.services.search import search
from smse_backend.services.embedding import (
    generate_query_embedding,
    generate_multipart_embedding,
)
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

    # Initialize variables for multi-part query
    query_parts = []
    query_embeddings = []
    query_modalities = []
    saved_files = []  # Track files for cleanup
    query_content_parts = []

    try:
        # Handle text query (if present)
        query_text = None
        if request.is_json:
            # Pure JSON request - text only
            data = request.json
            query_text = data.get("query")
        elif request.form:
            # Form data - might have text along with files
            query_text = request.form.get("query")

        if query_text and query_text.strip():
            # Generate text embedding
            text_embedding, text_modality = generate_query_embedding(
                query_text=query_text
            )
            if text_embedding is not None:
                query_embeddings.append(text_embedding)
                query_modalities.append(text_modality)
                query_parts.append("text")
                query_content_parts.append(query_text)

        # Handle file uploads (can be multiple)
        files = request.files.getlist("files") or (
            [request.files["file"]] if "file" in request.files else []
        )

        for file in files:
            if file.filename == "":
                continue  # Skip empty files

            # Validate file type by extension
            file_ext = os.path.splitext(file.filename)[1].lower()

            if file_ext not in EXTENSION_TO_MODALITY:
                # Clean up any previously saved files
                for saved_file in saved_files:
                    current_app.file_storage.delete_file(saved_file)
                return (
                    jsonify(
                        {
                            "message": f"Unsupported file type '{file_ext}' in file '{file.filename}'. Allowed types: {', '.join(EXTENSION_TO_MODALITY.keys())}"
                        }
                    ),
                    400,
                )

            # Save the file temporarily using file storage service
            file_path, full_path = current_app.file_storage.save_query_file(
                file, current_user_id
            )
            saved_files.append(file_path)

            try:
                # Generate query embedding for this file
                file_embedding, file_modality = generate_query_embedding(
                    query_file=full_path
                )
                if file_embedding is not None:
                    query_embeddings.append(file_embedding)
                    query_modalities.append(file_modality)
                    query_parts.append("file")
                    query_content_parts.append(file.filename)
            except Exception as e:
                current_app.logger.error(
                    f"Error processing query file {file.filename}: {str(e)}"
                )
                # Continue processing other files instead of failing completely
                continue

        # Check if we have at least one valid embedding
        if not query_embeddings:
            # Clean up any saved files
            for saved_file in saved_files:
                current_app.file_storage.delete_file(saved_file)
            return (
                jsonify(
                    {
                        "message": "No valid query parts provided. Either query text or files are required"
                    }
                ),
                400,
            )

        # Combine embeddings by taking the mean
        query_embedding, query_modality = generate_multipart_embedding(
            embeddings=query_embeddings, modalities=query_modalities
        )

        # Create query description for storage
        query_content = " + ".join(query_content_parts)
        query_type = "multipart" if len(query_parts) > 1 else query_parts[0]

    except Exception as e:
        # Clean up any saved files in case of error
        for saved_file in saved_files:
            current_app.file_storage.delete_file(saved_file)
        current_app.logger.error(f"Error processing multipart query: {str(e)}")
        return jsonify({"message": f"Error processing query: {str(e)}"}), 500

    # Check if embedding generation was successful
    if query_embedding is None:
        # Clean up any saved files
        for saved_file in saved_files:
            current_app.file_storage.delete_file(saved_file)
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

        print(query_modality, query_embedding)

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

        # Clean up temporary query files after successful search
        for saved_file in saved_files:
            current_app.file_storage.delete_file(saved_file)

        return (
            jsonify(
                {
                    "message": "Search completed successfully",
                    "query_id": new_query.id,
                    "query_type": query_type,
                    "query_parts": {
                        "text": query_text if query_text else None,
                        "files": (
                            [f for f in query_content_parts if f != query_text]
                            if len(query_content_parts) > 1
                            else None
                        ),
                        "total_parts": len(query_parts),
                    },
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
        # Clean up temporary query files in case of error
        for saved_file in saved_files:
            current_app.file_storage.delete_file(saved_file)
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

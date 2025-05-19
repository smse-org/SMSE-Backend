from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from smse_backend import db
from smse_backend.models import Content
from smse_backend.utils.file_extensions import is_allowed_file
import os
import uuid

content_bp = Blueprint("content", __name__)


def get_first_directory(path):
    parts = path.lstrip(os.sep).split(os.sep)  # Remove leading slashes & split
    return parts[0] if parts else None  # Return first part if exists


def get_full_path(file_path):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], file_path)


@content_bp.route("/contents", methods=["POST"])
@jwt_required()
def create_content():
    current_user_id = get_jwt_identity()

    # Check if the post request has the file part
    if "file" not in request.files:
        return jsonify({"msg": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"msg": "No selected file"}), 400

    if file and is_allowed_file(file.filename):
        # Get size from in-memory stream BEFORE saving
        file_stream = file.stream
        file_stream.seek(0, os.SEEK_END)
        file_size_bytes = file_stream.tell()  # size in bytes
        file_stream.seek(0)  # reset stream for future use
        file_size_kb = round(file_size_bytes / 1024, 2)

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(str(current_user_id), unique_filename)
        full_path = get_full_path(file_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)

        try:
            # Create new content record WITHOUT embedding
            new_content = Content(
                content_path=file_path,
                content_tag=True,
                user_id=current_user_id,
                embedding=None,
                content_size=file_size_kb,
            )
            db.session.add(new_content)
            db.session.commit()

            # Schedule the Celery task for processing the file
            from smse_backend.services.embedding import schedule_embedding_task
            from smse_backend.models.task import Task

            task_id = schedule_embedding_task(get_full_path(file_path), new_content.id)

            # Create a new task record
            new_task = Task(
                task_id=task_id,
                status="PENDING",
                content_id=new_content.id,
                user_id=current_user_id,
            )
            db.session.add(new_task)
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Content created successfully",
                        "content": {
                            "id": new_content.id,
                            "content_path": new_content.content_path,
                            "content_tag": new_content.content_tag,
                            "content_size": new_content.content_size,
                            "upload_date": new_content.upload_date,
                        },
                        "task_id": task_id,
                    }
                ),
                201,
            )

        except Exception as e:
            db.session.rollback()
            print(e)
            return jsonify({"message": "Error creating content"}), 500

    return jsonify({"msg": "File type not allowed"}), 400


@content_bp.route("/contents", methods=["GET"])
@jwt_required()
def get_all_contents():
    # TODO: Implement pagination
    current_user_id = get_jwt_identity()
    contents = Content.query.filter_by(user_id=current_user_id).all()

    return (
        jsonify(
            {
                "contents": [
                    {
                        "id": content.id,
                        "content_path": content.content_path,
                        "content_tag": content.content_tag,
                    }
                    for content in contents
                ]
            }
        ),
        200,
    )


@content_bp.route("/contents/<int:content_id>", methods=["GET"])
@jwt_required()
def get_content(content_id):
    """
    Retrieve a specific content by its ID for the current user.

    Args:
        content_id (int): The ID of the content to retrieve.

    Returns:
        Response: JSON response containing the content details or an error message.
    """
    current_user_id = get_jwt_identity()
    content = Content.query.filter_by(id=content_id, user_id=current_user_id).first()

    if not content:
        return jsonify({"message": "Content not found"}), 404

    return (
        jsonify(
            {
                "content": {
                    "id": content.id,
                    "content_path": content.content_path,
                    "content_tag": content.content_tag,
                }
            }
        ),
        200,
    )


@content_bp.route("/contents/<int:content_id>", methods=["PUT"])
@jwt_required()
def update_content(content_id):
    current_user_id = get_jwt_identity()
    content = Content.query.filter_by(id=content_id, user_id=current_user_id).first()

    if not content:
        return jsonify({"message": "Content not found"}), 404

    data = request.get_json()

    try:
        if "content_tag" in data:
            content.content_tag = data["content_tag"]

        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Content updated successfully",
                    "content": {
                        "id": content.id,
                        "content_path": content.content_path,
                        "content_tag": content.content_tag,
                    },
                }
            ),
            200,
        )

    except Exception as _:
        db.session.rollback()
        return jsonify({"message": "Error updating content"}), 500


@content_bp.route("/contents/<int:content_id>", methods=["DELETE"])
@jwt_required()
def delete_content(content_id):
    current_user_id = get_jwt_identity()
    content = Content.query.filter_by(id=content_id, user_id=current_user_id).first()

    if not content:
        return jsonify({"message": "Content not found"}), 404

    try:
        # Delete the actual file
        if os.path.exists(get_full_path(content.content_path)):
            os.remove(get_full_path(content.content_path))
        else:
            print("The file does not exist")  # TODO: Log this

        # Delete the database record
        db.session.delete(content)
        db.session.commit()
        return jsonify({"message": "Content deleted successfully"}), 200

    except Exception as _:
        db.session.rollback()
        return jsonify({"message": "Error deleting content"}), 500


@content_bp.route("/contents/allowed_extensions", methods=["GET"])
def get_allowed_extensions_endpoint():
    """Get the list of allowed file extensions."""
    from smse_backend.utils.file_extensions import get_allowed_extensions

    return jsonify({"allowed_extensions": get_allowed_extensions()}), 200


@content_bp.route("/contents/download", methods=["GET"])
@jwt_required()
def download_content():
    """
    Download a specific content file by its ID or path for the current user.

    Query Params:
        content_id (int, optional): The ID of the content to download.
        file_path (str, optional): The full path of the content to download.

    Returns:
        Response: File response containing the content file or an error message.
    """
    content_id = request.args.get("content_id", type=int)
    file_path = request.args.get("file_path", type=str)

    if content_id is None and file_path is None:
        return jsonify({"message": "Content ID or file path is required"}), 400

    current_user_id = get_jwt_identity()

    if content_id is not None:
        content = Content.query.filter_by(
            id=content_id, user_id=current_user_id
        ).first()
        if not content:
            return jsonify({"message": "Content not found"}), 404
        file_path = content.content_path

    if file_path is not None:
        if get_first_directory(file_path) != current_user_id:
            print(get_first_directory(file_path), current_user_id)
            return jsonify({"message": "Unauthorized access"}), 403

        if not os.path.exists(get_full_path(file_path)):
            return jsonify({"message": "File not found"}), 404

    return send_file(get_full_path(file_path), as_attachment=True)

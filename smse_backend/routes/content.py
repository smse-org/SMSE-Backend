from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from smse_backend import db
from smse_backend.models import Content
from smse_backend.utils.file_extensions import is_allowed_file
from smse_backend.services.file_storage import file_storage
from mimetypes import guess_type
import io

content_bp = Blueprint("content", __name__)


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
        try:
            # Use file storage service to save the file
            file_path, file_size_kb = file_storage.save_uploaded_file(
                file, current_user_id
            )

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

            task_id = schedule_embedding_task(
                file_storage.get_full_path(file_path), new_content.id
            )

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
                        "content_size": content.content_size,
                        "upload_date": content.upload_date,
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
                    "content_size": content.content_size,
                    "upload_date": content.upload_date,
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
        if "content_path" in data:
            content.content_path = data["content_path"]

        if "content_tag" in data:
            content.content_tag = data["content_tag"]

        if "content_size" in data:
            content.content_size = data["content_size"]

        if "upload_date" in data:
            content.upload_date = data[
                "upload_date"
            ]  # Ensure this is in the correct datetime format

        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Content updated successfully",
                    "content": {
                        "id": content.id,
                        "content_path": content.content_path,
                        "content_tag": content.content_tag,
                        "content_size": content.content_size,
                        "upload_date": content.upload_date,
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
        # Delete the actual file using file storage service
        if file_storage.file_exists(content.content_path):
            file_storage.delete_file(content.content_path)
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
        if file_storage.get_first_directory(file_path) != str(current_user_id):
            print(file_storage.get_first_directory(file_path), current_user_id)
            return jsonify({"message": "Unauthorized access"}), 403

        if not file_storage.file_exists(file_path):
            return jsonify({"message": "File not found"}), 404

    # Download file content
    file_content = file_storage.download_file(file_path)
    if file_content is None:
        return jsonify({"message": "Error downloading file"}), 500

    # Create a file-like object from the content
    file_obj = io.BytesIO(file_content)

    return send_file(file_obj, mimetype=guess_type(file_path)[0])

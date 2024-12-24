from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from smse_backend import db
from smse_backend.models import Content, Embedding, Model
from smse_backend.services import create_embedding_from_path
import os
import uuid

ALLOWED_EXTENSIONS = set(
    os.getenv("ALLOWED_EXTENSIONS", "txt,pdf,png,jpg,jpeg,gif,md").split(",")
)

content_bp = Blueprint("content", __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

    if file and allowed_file(file.filename):
        # Create user-specific upload directory
        user_upload_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], str(current_user_id)
        )
        os.makedirs(user_upload_dir, exist_ok=True)

        # Secure the filename and add a random UUID
        # TODO: Handle duplicate files (content)
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(user_upload_dir, unique_filename)
        file.save(file_path)

        try:
            # Get user chosen model
            model_id = db.session.get(
                Model, 1
            ).id  # TODO: Allow user to choose model (handle user settings)

            # Create embedding vector from content
            embedding_vector = create_embedding_from_path(file_path)
            if embedding_vector is None:
                return jsonify({"message": "Error creating embedding for content"}), 500

            # Create new embedding record
            new_embedding = Embedding(
                vector=embedding_vector,
                model_id=model_id,
            )
            db.session.add(new_embedding)

            # Create new content record
            new_content = Content(
                content_path=file_path,
                content_tag=True,
                user_id=current_user_id,
                embedding=new_embedding,
            )
            db.session.add(new_content)
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Content created successfully",
                        "content": {
                            "id": new_content.id,
                            "content_path": new_content.content_path,
                            "content_tag": new_content.content_tag,
                        },
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
        if os.path.exists(content.content_path):
            os.remove(content.content_path)
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
def get_allowed_extensions():
    return jsonify({"allowed_extensions": list(ALLOWED_EXTENSIONS)}), 200

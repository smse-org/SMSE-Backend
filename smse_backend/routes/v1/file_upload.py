from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

upload_bp = Blueprint("upload", __name__)
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "md"}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({"msg": "File is too large"}), 413


@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    # Check if the post request has the file part
    if "file" not in request.files:
        return jsonify({"msg": "No file part"}), 400

    file = request.files["file"]

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == "":
        return jsonify({"msg": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Get current user ID
        current_user_id = get_jwt_identity()

        # Create user-specific upload directory
        user_upload_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], str(current_user_id)
        )
        os.makedirs(user_upload_dir, exist_ok=True)

        # Secure the filename and save
        filename = secure_filename(file.filename)
        file_path = os.path.join(user_upload_dir, filename)
        file.save(file_path)

        return jsonify({"msg": "File uploaded successfully", "filename": filename}), 200

    return jsonify({"msg": "File type not allowed"}), 400

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from smse_backend.models import User
from smse_backend.services.file_storage import file_storage
from smse_backend import db

user_bp = Blueprint("user", __name__)


@user_bp.route("/users/me", methods=["GET"])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@user_bp.route("/users/me", methods=["PUT"])
@jwt_required()
def update_user():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()

    if "username" in data and data["username"] != user.username:
        if User.query.filter_by(username=data["username"]).first():
            return jsonify({"message": "Username already exists"}), 400
        user.username = data["username"]

    if "email" in data and data["email"] != user.email:
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"message": "Email already exists"}), 400
        try:
            user.email = data["email"]
        except ValueError as e:
            return jsonify({"message": str(e)}), 400

    try:
        db.session.commit()
        return jsonify(
            {
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": str(user.created_at),
                },
            }
        )
    except Exception as _:
        db.session.rollback()
        return jsonify({"message": "Error updating user"}), 500


@user_bp.route("/users/me", methods=["DELETE"])
@jwt_required()
def delete_user():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()

        # Delete user directory using file storage service
        file_storage.delete_user_directory(user.id)

        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as _:
        db.session.rollback()
        return jsonify({"message": "Error deleting user"}), 500


@user_bp.route("/user/preferences", methods=["GET"])
@jwt_required()
def get_preferences():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({"preferences": user.preferences or {}}), 200


@user_bp.route("/user/preferences", methods=["PUT"])
@jwt_required()
def update_preferences():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    # Merge or set preferences
    if user.preferences is None:
        user.preferences = {}
    user.preferences = data

    db.session.commit()
    return jsonify({"message": "Preferences updated", "preferences": user.preferences}), 200

@user_bp.route("/user/preferences", methods=["DELETE"])
@jwt_required()
def clear_preferences():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.preferences = {}
    db.session.commit()
    return jsonify({"message": "All preferences cleared"}), 200
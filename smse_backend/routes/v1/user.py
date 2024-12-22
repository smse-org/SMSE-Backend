from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from smse_backend.models import User
from smse_backend import db

user_bp = Blueprint("user", __name__)


@user_bp.route("/users/me", methods=["GET"])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": str(user.created_at),
        }
    )


@user_bp.route("/users/me", methods=["PUT"])
@jwt_required()
def update_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

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
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating user"}), 500


@user_bp.route("/users/me", methods=["DELETE"])
@jwt_required()
def delete_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting user"}), 500

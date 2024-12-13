from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from smse_backend.models import User

# Create a blueprint for main routes
main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    """
    Simple health check endpoint
    """
    return jsonify({"status": "ok", "message": "Welcome to the Flask API"}), 200


@main_bp.route("/user-profile", methods=["GET"])
@jwt_required()
def user_profile():
    """
    Retrieve current user's profile information
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return (
        jsonify(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
            }
        ),
        200,
    )

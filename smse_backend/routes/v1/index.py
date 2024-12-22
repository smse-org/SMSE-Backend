from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from smse_backend.models import User

# Create a blueprint for main routes
main_bp = Blueprint("main", __name__)


@main_bp.route("/health", methods=["GET"])
def index():
    """
    Simple health check endpoint
    """
    return jsonify({"status": "ok", "message": "Welcome to the Flask API"}), 200

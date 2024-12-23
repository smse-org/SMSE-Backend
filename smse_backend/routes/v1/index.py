from flask import Blueprint, jsonify

# Create a blueprint for main routes
main_bp = Blueprint("main", __name__)


@main_bp.route("/health", methods=["GET"])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({"status": "ok", "message": "Welcome to the SMSE API"}), 200

from flask import Blueprint, jsonify

# Create a blueprint for main routes
index_bp = Blueprint("index", __name__)


@index_bp.route("/health", methods=["GET"])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({"status": "ok", "message": "Welcome to the SMSE API"}), 200

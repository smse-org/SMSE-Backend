from .v1 import v1_bp
from flask import Blueprint

main_bp = Blueprint("main", __name__, url_prefix="/api")
main_bp.register_blueprint(v1_bp)


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(main_bp)

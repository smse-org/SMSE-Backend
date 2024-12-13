from .v1 import v1_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(v1_bp)

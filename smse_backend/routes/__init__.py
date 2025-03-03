import flask
from .v1 import v1_bp
from flask import Blueprint, jsonify

main_bp = Blueprint("main", __name__, url_prefix="/api")
main_bp.register_blueprint(v1_bp)


def register_blueprints(app):
    """Register all blueprints with the Flask app."""

    @app.route("/swagger.json")
    def swagger_json():
        return flask.send_file("../swagger.json")

    app.register_blueprint(main_bp)

import flask
from flask import Blueprint
from .auth import auth_bp
from .index import index_bp
from .content import content_bp
from .user import user_bp
from .search import search_bp
from .task import task_bp


main_bp = Blueprint("main", __name__, url_prefix="/api")
main_bp.register_blueprint(auth_bp)
main_bp.register_blueprint(index_bp)
main_bp.register_blueprint(content_bp)
main_bp.register_blueprint(user_bp)
main_bp.register_blueprint(search_bp)
main_bp.register_blueprint(task_bp)


def register_blueprints(app):
    """Register all blueprints with the Flask app."""

    @app.route("/swagger.json")
    def swagger_json():
        return flask.send_file("../swagger.json")

    app.register_blueprint(main_bp)

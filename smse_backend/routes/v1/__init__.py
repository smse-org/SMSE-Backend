from flask import Blueprint
from .auth import auth_bp
from .index import index_bp
from .content import content_bp
from .user import user_bp

v1_bp = Blueprint("v1", __name__, url_prefix="/v1")

v1_bp.register_blueprint(auth_bp)
v1_bp.register_blueprint(index_bp)
v1_bp.register_blueprint(content_bp)
v1_bp.register_blueprint(user_bp)

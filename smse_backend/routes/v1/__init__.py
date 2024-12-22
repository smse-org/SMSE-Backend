from flask import Blueprint
from .auth import auth_bp
from .index import main_bp
from .file_upload import upload_bp
from flask_restx import Api

v1_bp = Blueprint("v1", __name__, url_prefix="/v1")

v1_bp.register_blueprint(auth_bp)
v1_bp.register_blueprint(main_bp)
v1_bp.register_blueprint(upload_bp)

api = Api(v1_bp, version="1.0", title="SMSE API", description="API for SMSE")

"""
라우트 패키지
Flask Blueprint를 사용하여 라우트를 모듈화합니다.
"""
from flask import Flask
import logging

logger = logging.getLogger(__name__)


from .auth import auth_bp
from .meetings import meetings_bp
from .meetings_share import meetings_share_bp
from .meetings_upload import meetings_upload_bp
from .meetings_action_items import meetings_action_items_bp
from .chat import chat_bp
from .summary import summary_bp
from .admin import admin_bp
from .live_record import live_bp
from .google_auth import google_auth_bp
from .health import health_bp


def register_blueprints(app):
    """
    애플리케이션에 모든 Blueprint 등록

    Args:
        app: Flask 애플리케이션 인스턴스
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(meetings_share_bp)
    app.register_blueprint(meetings_upload_bp)
    app.register_blueprint(meetings_action_items_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(live_bp)
    app.register_blueprint(google_auth_bp)
    app.register_blueprint(health_bp)

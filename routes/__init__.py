"""
라우트 패키지
Flask Blueprint를 사용하여 라우트를 모듈화합니다.
"""
from flask import Flask
import logging

logger = logging.getLogger(__name__)


from .auth import auth_bp
from .meetings import meetings_bp
from .chat import chat_bp
from .summary import summary_bp
from .admin import admin_bp
from .live_record import live_bp


def register_blueprints(app):
    """
    애플리케이션에 모든 Blueprint 등록

    Args:
        app: Flask 애플리케이션 인스턴스
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(summary_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(live_bp)


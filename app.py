"""
Minute AI - 회의록 자동 생성 플랫폼
Flask 애플리케이션 메인 파일

아키텍처:
- config.py : 환경 변수 및 설정 중앙화
- database/repositories/ : Repository 인터페이스 + SQLite 구현체
- services/ : 비즈니스 로직 (Repository 인터페이스에 의존)
- routes/ : HTTP 라우트 (Thin Controller)
- utils/ : 데코레이터, 유틸리티

DI 조립: 이 파일의 초기화 섹션에서 Repository → Service → Route 순으로 조립합니다.
DB 전환 시 이 파일의 Repository 생성 부분만 교체하면 됩니다.
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory, Response
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config import config
from services.diarization import diarization_service
from services.firebase_service import initialize_firebase
from database.sqlite_manager import DatabaseManager
from database.vector_manager import vdb_manager
from routes import register_blueprints
from services.user_service import is_admin

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

logger.debug(f"CORS origins config: {config.ALLOWED_ORIGINS} (type: {type(config.ALLOWED_ORIGINS).__name__})")
CORS(app, resources={r"/*": {"origins": config.ALLOWED_ORIGINS}}, supports_credentials=True)

app.config.from_object(config)


# ==================== Firebase 초기화 ====================
try:
    initialize_firebase()
    logger.info("Firebase 초기화 성공")
except Exception as e:
    logger.error(f"Firebase 초기화 실패: {e}")
    logger.warning("로그인 기능이 작동하지 않을 수 있습니다.")


# ==================== DI 조립: Repository → Service ====================
# 1) DatabaseManager (Facade + Singleton) – Repository 접근자 제공
db = DatabaseManager(str(config.DATABASE_PATH))

# 2) VectorDBManager에 DatabaseManager 주입
vdb_manager.db_manager = db

# 3) Repository 인스턴스 (DB 전환 시 여기만 교체)
# db.meeting_repo, db.minutes_repo, db.mindmap_repo,
# db.action_item_repo, db.user_repo  ← SqliteConnection 기반

# 4) Service 인스턴스 (Repository 인터페이스에 의존)
from services.meeting_service import MeetingService
from services.analysis_service import AnalysisService
from services.user_service import UserService

meeting_service = MeetingService(
    meeting_repo=db.meeting_repo,
    minutes_repo=db.minutes_repo,
    mindmap_repo=db.mindmap_repo,
)
analysis_service = AnalysisService(connection=db.connection)
user_service = UserService(connection=db.connection)

logger.info("DI 조립 완료: Repository → Service")


# ==================== Context Processor ====================
@app.context_processor
def inject_user_info():
    """
    모든 템플릿에 사용자 정보 주입

    Returns:
        dict: 템플릿에서 사용 가능한 변수들
    """
    if 'user_id' in session:
        user_id = session['user_id']
        is_user_admin = is_admin(user_id)
        return {
            'current_user_id': user_id,
            'is_admin': is_user_admin,
            'user_name': session.get('name', '사용자'),
            'user_email': session.get('email', ''),
            'user_picture': session.get('profile_picture', '')
        }
    return {
        'current_user_id': None,
        'is_admin': False,
        'user_name': None,
        'user_email': None,
        'user_picture': None
    }


# ==================== Blueprint 등록 ====================
register_blueprints(app)


# ==================== 정적 파일 라우트 ====================
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """
    업로드된 파일 제공 (오디오 파일 스트리밍)

    Args:
        filename: 파일명

    Returns:
        파일 데이터
    """
    return send_from_directory(str(config.UPLOAD_FOLDER), filename)


# ==================== React SPA 서빙 ====================
# 주의: 이 라우트는 마지막에 등록되어야 함 (catch-all 라우트)
# Blueprint 라우트(/api/*, /auth/* 등)가 먼저 매칭되므로 문제없음
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path: str):
    """
    React 빌드 파일 서빙 (SPA 라우팅 지원)
    
    Blueprint 라우트(/api/*, /auth/* 등)와 /uploads/*가 먼저 처리되고,
    매칭되지 않는 모든 경로는 React 앱으로 전달됩니다.
    
    Args:
        path: 요청 경로
        
    Returns:
        정적 파일 또는 index.html (SPA 라우팅)
    """
    logger.debug(f"serve_react_app entry: path={path}")
    
    build_dir = config.FRONTEND_BUILD_DIR
    logger.debug(f"build_dir check: {build_dir} (exists: {build_dir.exists()})")
    
    # 빌드 디렉토리가 없으면 에러 (개발 환경에서는 빌드 필요)
    if not build_dir.exists():
        logger.warning(f"React 빌드 디렉토리가 없습니다: {build_dir}")
        return "React 빌드 파일이 없습니다. 프론트엔드를 빌드해주세요.", 503
    
    # Path traversal 방어
    if path:
        # 상대 경로 탐색 방지
        if '..' in path or path.startswith('/'):
            logger.debug(f"path traversal blocked: path={path}")
            return "Invalid path", 400
        
        file_path = build_dir / path
        logger.debug(f"file path check: {file_path} (exists: {file_path.exists()}, is_file: {file_path.is_file() if file_path.exists() else False})")
        
        if file_path.exists() and file_path.is_file():
            # 정적 파일 서빙
            logger.debug(f"serving static file: path={path}")
            return send_from_directory(str(build_dir), path)
    
    # 그 외의 경우 index.html 반환 (SPA 라우팅)
    logger.debug(f"serving index.html: path={path}")
    return send_from_directory(str(build_dir), 'index.html')


# ==================== 에러 핸들러 ====================
@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return "⛔ 페이지를 찾을 수 없습니다.", 404


@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logger.error(f"❌ 서버 오류: {error}", exc_info=True)
    return "⛔ 서버 오류가 발생했습니다.", 500


# ==================== 애플리케이션 실행 ====================
if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🚀 Minute AI 서버 시작")
    logger.info(f"포트: {config.PORT}")
    logger.info(f"디버그 모드: {config.DEBUG}")
    logger.info("=" * 70)

    app.run(
        host="0.0.0.0",
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )

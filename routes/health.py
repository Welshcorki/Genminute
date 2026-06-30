"""
헬스 체크 엔드포인트
배포 플랫폼(GCP, AWS 등)이나 모니터링 도구가 서버 상태를 확인하기 위한 간단한 API
"""
from flask import Blueprint, jsonify
from datetime import datetime
import os
from config import config

# Blueprint 생성
health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check() -> tuple:
    """
    헬스 체크 엔드포인트
    서버 및 데이터베이스 상태를 확인합니다.
    
    Returns:
        JSON: {"status": "healthy"|"unhealthy", "timestamp": "ISO 형식", "error": "에러 메시지(선택적)"}
        HTTP Status: 200 (정상) 또는 500 (비정상)
    """
    try:
        # 데이터베이스 파일 접근 가능 여부 확인
        db_path = config.DATABASE_PATH
        
        if not os.path.exists(db_path):
            return jsonify({
                "status": "unhealthy",
                "error": "Database file not found",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # 데이터베이스 파일이 읽기/쓰기 가능한지 확인
        if not os.access(db_path, os.R_OK):
            return jsonify({
                "status": "unhealthy",
                "error": "Database file is not readable",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

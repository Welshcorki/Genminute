"""
Google OAuth 2.0 인증 관련 라우트 (로그인 및 캘린더 연동)
"""
from flask import Blueprint, request, url_for, redirect, session, current_app, jsonify
import google_auth_oauthlib.flow
import google.oauth2.credentials
from google.oauth2 import id_token
from google.auth.transport import requests
import json
import os
import logging

from config import config
from database.sqlite_manager import DatabaseManager
from services.user_service import get_or_create_user

logger = logging.getLogger(__name__)

# 개발 환경에서 HTTP를 허용하기 위한 설정 (OAuth 2.0 InsecureTransportError 해결)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Blueprint 생성 (URL Prefix 없음 -> 함수 데코레이터에서 지정)
google_auth_bp = Blueprint('google_auth', __name__)

# 데이터베이스 매니저 초기화
db = DatabaseManager(str(config.DATABASE_PATH))

# OAuth 2.0 설정
# 이 client_config는 Google API Console에서 다운로드한 client_secret.json 파일의 내용과 동일한 구조입니다.
CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "project_id": config.FIREBASE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [
            # 실제 운영 시에는 https 주소 사용
            f"http://localhost:{config.PORT}/oauth2callback",
            f"http://127.0.0.1:{config.PORT}/oauth2callback"
        ]
    }
}

# 필요한 Google API 범위(scope) 정의
# openid, email, profile: 로그인용
# calendar.events: 캘린더 연동용
SCOPES = [
    'openid', 
    'https://www.googleapis.com/auth/userinfo.email', 
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.events'
]


@google_auth_bp.route('/google/login')
def google_login():
    """
    Google 로그인을 시작합니다.
    """
    # 리다이렉트 URI (백엔드 포트 사용)
    # url_for를 사용하면 현재 요청 호스트(localhost 등)에 맞춰 자동 생성됨
    redirect_uri = url_for('google_auth.oauth2callback', _external=True)
    
    # OAuth 2.0 플로우 객체 생성
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    # 사용자를 인증 URL로 리디렉션
    authorization_url, state = flow.authorization_url(
        access_type='offline', # refresh_token을 받기 위해 필수
        prompt='consent', # 항상 동의 화면을 표시하여 refresh_token을 다시 받도록 유도
        include_granted_scopes='true'
    )
    
    # CSRF 방지를 위해 state 값을 세션에 저장
    session['google_oauth_state'] = state
    
    logger.info(f"🔗 Google 로그인 리다이렉트 시작: {redirect_uri}")

    return redirect(authorization_url)


@google_auth_bp.route('/oauth2callback')
def oauth2callback():
    """
    Google 인증 후 리디렉션되는 콜백 URL.
    1. 인증 코드로 토큰 교환
    2. ID 토큰 검증 및 사용자 정보 추출
    3. DB 사용자 조회/생성 및 세션 로그인 처리
    4. 프론트엔드로 리다이렉트
    """
    # CSRF 공격 방지를 위해 state 값 비교
    state = session.get('google_oauth_state')
    if not state or state != request.args.get('state'):
        logger.error("❌ Google 로그인 실패: Invalid state parameter")
        return 'Invalid state parameter', 400

    try:
        # 플로우 객체 재생성
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            state=state,
            redirect_uri=url_for('google_auth.oauth2callback', _external=True)
        )

        # Google로부터 받은 인증 코드로 토큰 교환
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # 획득한 인증 정보
        credentials = flow.credentials
        
        # ID 토큰 검증 및 사용자 정보 추출
        # verify_oauth2_token은 토큰 서명을 검증하고 payload를 반환합니다.
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            config.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
        
        email = id_info.get('email')
        google_id = id_info.get('sub')
        name = id_info.get('name')
        picture = id_info.get('picture')
        
        logger.info(f"✅ Google 인증 성공: {email}")

        # DB에서 사용자 조회 또는 생성
        user = get_or_create_user(
            google_id=google_id,
            email=email,
            name=name,
            profile_picture=picture
        )
        
        # 세션 생성 (로그인 처리)
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['name'] = user.get('name', '')
        session['role'] = user['role']
        session['profile_picture'] = user.get('profile_picture', '')
        session.permanent = True # 브라우저 닫아도 유지 (설정에 따름)

        # 캘린더 연동을 위한 Credentials DB 저장
        creds_json = credentials_to_dict(credentials)
        db.update_user_google_credentials(user['id'], json.dumps(creds_json))
        
        # 프론트엔드 홈으로 리다이렉트 (하드코딩된 포트 대신 설정이나 환경변수 사용 권장)
        # 현재는 Vite 개발 서버 포트(5173) 사용
        frontend_url = "http://localhost:5173/"
        logger.info(f"🚀 프론트엔드로 리다이렉트: {frontend_url}")
        
        return redirect(frontend_url)

    except Exception as e:
        logger.error(f"❌ Google 로그인 콜백 처리 중 오류: {e}", exc_info=True)
        return f"로그인 처리 중 오류가 발생했습니다: {str(e)}", 500


def credentials_to_dict(credentials):
    """
    google.oauth2.credentials.Credentials 객체를 직렬화 가능한 딕셔너리로 변환합니다.
    """
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
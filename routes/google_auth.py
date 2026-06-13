"""
Google OAuth 2.0 — 캘린더 연동 전용 라우트

NOTE: 로그인(Google OAuth) 기능은 Supabase Auth로 전환되었습니다.
이 모듈은 캘린더 API 접근 권한(google.calendar.events)을 획득하고
크리덴셜을 DB에 저장하는 기능만 담당합니다.
"""
import google_auth_oauthlib.flow
import google.oauth2.credentials
import json
import os
import logging

from flask import Blueprint, request, url_for, redirect, session, jsonify

from config import config
from database import get_db_manager

logger = logging.getLogger(__name__)

# 개발 환경(DEBUG)에서만 HTTP를 허용 (OAuth 2.0 InsecureTransportError 해결).
# 프로덕션에서는 HTTPS를 강제해야 하므로 절대 설정하지 않는다.
if config.DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

google_auth_bp = Blueprint('google_auth', __name__)

db = get_db_manager()

# Google OAuth 클라이언트 설정
# project_id는 client_secret.json 스펙의 선택 필드 — 실제 토큰 교환에 미사용
CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "project_id": config.GOOGLE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [
            f"http://localhost:{config.PORT}/oauth2callback",
            f"http://127.0.0.1:{config.PORT}/oauth2callback"
        ]
    }
}

# 캘린더 API 접근 권한 스코프
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.events'
]


@google_auth_bp.route('/google/calendar/authorize')
def google_calendar_authorize():
    """
    Google 캘린더 연동 OAuth 시작.
    이미 Supabase로 로그인한 사용자가 캘린더 API 접근 권한을 추가로 허용할 때 사용합니다.

    Returns:
        Google OAuth 동의 화면으로 리다이렉트
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401

    redirect_uri = url_for('google_auth.oauth2callback', _external=True)

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )

    session['google_oauth_state'] = state

    logger.info(f"🔗 캘린더 연동 OAuth 시작: {redirect_uri}")
    return redirect(authorization_url)


@google_auth_bp.route('/oauth2callback')
def oauth2callback():
    """
    Google OAuth 콜백 — 캘린더 크리덴셜 저장 전용.

    NOTE: 로그인 처리는 Supabase Auth에서 담당합니다.
    이 엔드포인트는 캘린더 API 접근을 위한 OAuth 토큰만 DB에 저장합니다.
    """
    state = session.get('google_oauth_state')
    if not state or state != request.args.get('state'):
        logger.error("❌ Google OAuth 콜백 실패: Invalid state parameter")
        return 'Invalid state parameter', 400

    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            state=state,
            redirect_uri=url_for('google_auth.oauth2callback', _external=True)
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # 캘린더 크리덴셜 DB 저장 (이미 Supabase 세션으로 로그인된 user_id 기준)
        user_id = session.get('user_id')
        if user_id:
            creds_json = credentials_to_dict(credentials)
            db.update_user_google_credentials(user_id, json.dumps(creds_json))
            logger.info(f"✅ 캘린더 크리덴셜 저장 완료: user_id={user_id}")
        else:
            logger.warning("⚠️ 세션에 user_id 없음 — 캘린더 크리덴셜 저장 불가")

        return redirect(config.FRONTEND_URL)

    except Exception as e:
        logger.error(f"❌ Google OAuth 콜백 처리 중 오류: {e}", exc_info=True)
        return f"캘린더 연동 중 오류가 발생했습니다: {str(e)}", 500


def credentials_to_dict(credentials) -> dict:
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
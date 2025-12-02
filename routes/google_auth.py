"""
Google OAuth 2.0 인증 관련 라우트
"""
from flask import Blueprint, request, url_for, redirect, session, current_app
import google_auth_oauthlib.flow
import google.oauth2.credentials
import json
import os

from config import config
from utils.db_manager import DatabaseManager

# 개발 환경에서 HTTP를 허용하기 위한 설정 (OAuth 2.0 InsecureTransportError 해결)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Blueprint 생성
google_auth_bp = Blueprint('google_auth', __name__)

# 데이터베이스 매니저 초기화
db = DatabaseManager(str(config.DATABASE_PATH))

# OAuth 2.0 설정
# 이 client_config는 Google API Console에서 다운로드한 client_secret.json 파일의 내용과 동일한 구조입니다.
CLIENT_CONFIG = {
    "web": {
        "client_id": config.GOOGLE_CLIENT_ID,
        "project_id": config.FIREBASE_PROJECT_ID, # project_id는 firebase 설정과 동일
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [
            # 실제 운영 시에는 https 주소 사용
            "http://localhost:5050/oauth2callback",
            "http://127.0.0.1:5050/oauth2callback"
        ]
    }
}

# 필요한 Google API 범위(scope) 정의
# calendar.events: 캘린더의 이벤트를 읽고 쓸 수 있는 모든 권한
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


@google_auth_bp.route('/google-auth/start')
def start_google_auth():
    """
    Google 인증 절차를 시작합니다. 사용자를 Google 동의 화면으로 리디렉션합니다.
    """
    # OAuth 2.0 플로우 객체 생성
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=url_for('google_auth.oauth2callback', _external=True)
    )

    # 사용자를 인증 URL로 리디렉션
    authorization_url, state = flow.authorization_url(
        access_type='offline', # refresh_token을 받기 위해 필수
        prompt='consent' # 항상 동의 화면을 표시하여 refresh_token을 다시 받도록 유도
    )
    
    # CSRF 방지를 위해 state 값을 세션에 저장
    session['google_oauth_state'] = state

    return redirect(authorization_url)


@google_auth_bp.route('/oauth2callback')
def oauth2callback():
    """
    Google 인증 후 리디렉션되는 콜백 URL.
    인증 코드를 받아 액세스 토큰 및 리프레시 토큰으로 교환하고 DB에 저장합니다.
    """
    # CSRF 공격 방지를 위해 state 값 비교
    state = session.get('google_oauth_state')
    if not state or state != request.args.get('state'):
        return 'Invalid state parameter', 400

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

    # 획득한 인증 정보 (access_token, refresh_token 등)
    credentials = flow.credentials
    
    # DB에 저장하기 위해 직렬화 가능한 JSON 형태로 변환
    creds_json = credentials_to_dict(credentials)

    # 현재 로그인한 사용자의 DB에 인증 정보 업데이트
    user_id = session.get('user_id')
    if not user_id:
        return "User not logged in.", 401
        
    db.update_user_google_credentials(user_id, json.dumps(creds_json))

    # TODO: 사용자에게 "성공적으로 연동되었습니다"와 같은 피드백을 보여주는 페이지로 리디렉션
    # 지금은 간단하게 /notes 페이지로 리디렉션
    return redirect(url_for('meetings.notes'))


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

"""
Firebase Authentication 모듈
- Firebase Admin SDK 초기화 (최초 토큰 검증 시 1회, 지연 초기화)
- ID 토큰 검증

DB 백엔드(DB_TYPE)와 무관하게 로그인 인증은 항상 Firebase를 사용합니다.
"""
import logging
from typing import Optional, Dict

import firebase_admin
from firebase_admin import credentials, auth

from config import config

logger = logging.getLogger(__name__)

# Firebase Admin SDK 초기화 여부 (프로세스당 1회)
_firebase_initialized: bool = False


def initialize_firebase() -> None:
    """
    Firebase Admin SDK 초기화

    Raises:
        FileNotFoundError: 서비스 계정 키 파일이 없을 때
    """
    global _firebase_initialized

    if _firebase_initialized:
        return

    cred_path = config.FIREBASE_CREDENTIALS_PATH

    if not cred_path.exists():
        raise FileNotFoundError(
            f"Firebase Admin SDK 인증 파일을 찾을 수 없습니다: {cred_path}\n"
            "Firebase Console > 프로젝트 설정 > 서비스 계정에서 비공개 키를 발급받아 "
            "해당 경로에 저장하거나 FIREBASE_CREDENTIALS_PATH 환경 변수로 경로를 지정하세요."
        )

    cred = credentials.Certificate(str(cred_path))
    firebase_admin.initialize_app(cred)
    _firebase_initialized = True
    logger.info("✅ Firebase Admin SDK 초기화 완료")


def verify_id_token(id_token: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Firebase ID 토큰 검증

    Args:
        id_token: 프론트엔드에서 받은 Firebase ID Token

    Returns:
        성공 시: {
            'uid': 사용자 고유 ID,
            'email': 이메일,
            'name': 이름,
            'picture': 프로필 사진 URL
        }
        실패 시: None
    """
    try:
        initialize_firebase()

        decoded_token = auth.verify_id_token(id_token)

        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
        }

    except auth.ExpiredIdTokenError:
        # ExpiredIdTokenError는 InvalidIdTokenError의 하위 클래스이므로 먼저 처리
        logger.error("❌ 만료된 ID 토큰")
        return None
    except auth.InvalidIdTokenError:
        logger.error("❌ 유효하지 않은 ID 토큰")
        return None
    except Exception as e:
        logger.error(f"❌ 토큰 검증 실패: {e}")
        return None

"""
Supabase Authentication 모듈
- Supabase SDK를 사용한 Access Token 검증
- 사용자 정보 추출
"""

import logging
from typing import Optional, Dict

from supabase import create_client, Client
from config import config

logger = logging.getLogger(__name__)

# Supabase 클라이언트 (싱글톤)
_supabase_client: Optional[Client] = None


def _get_client() -> Client:
    """Supabase 클라이언트 싱글톤 반환"""
    global _supabase_client

    if _supabase_client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL 또는 SUPABASE_SERVICE_ROLE_KEY가 .env에 설정되지 않았습니다."
            )
        _supabase_client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
        logger.info("✅ Supabase 클라이언트 초기화 완료")

    return _supabase_client


def verify_access_token(access_token: str) -> Optional[Dict[str, str]]:
    """
    Supabase Access Token 검증

    Args:
        access_token: 프론트엔드에서 받은 Supabase Access Token

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
        client = _get_client()

        # Supabase SDK로 토큰 검증 및 사용자 정보 조회
        user_response = client.auth.get_user(access_token)

        if not user_response or not user_response.user:
            logger.error("❌ 유효하지 않은 Access Token")
            return None

        user = user_response.user

        # 사용자 메타데이터에서 정보 추출
        user_metadata = user.user_metadata or {}

        user_info = {
            'uid': user.id,
            'email': user.email,
            'name': user_metadata.get('full_name') or user_metadata.get('name'),
            'picture': user_metadata.get('avatar_url') or user_metadata.get('picture')
        }

        return user_info

    except Exception as e:
        logger.error(f"❌ 토큰 검증 실패: {e}")
        return None

"""
Supabase 연결 관리
supabase-py 클라이언트를 초기화하고 반환합니다.
"""
from supabase import create_client, Client
from config import config
import logging

logger = logging.getLogger(__name__)

class SupabaseConnection:
    """Supabase 데이터베이스 연결 관리"""
    
    def __init__(self):
        url: str = config.SUPABASE_URL
        # Service Role Key를 사용하여 RLS를 우회하고 관리자 권한으로 DB에 접근 (백엔드 전용)
        key: str = config.SUPABASE_SERVICE_ROLE_KEY
        
        if not url or not key:
            raise ValueError("Supabase 연결을 위한 SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY가 필요합니다.")
            
        self._client: Client = create_client(url, key)
        logger.info("✅ Supabase 클라이언트 초기화 완료 (Service Role Key 사용)")

    @property
    def client(self) -> Client:
        return self._client

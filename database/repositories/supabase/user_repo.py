from typing import Optional
from database.repositories.interfaces import UserRepositoryInterface
from database.repositories.supabase.connection import SupabaseConnection
import logging

logger = logging.getLogger(__name__)

class SupabaseUserRepository(UserRepositoryInterface):
    def __init__(self, connection: SupabaseConnection):
        self._client = connection.client

    def update_user_google_credentials(self, user_id: int, credentials_json: str) -> None:
        try:
            self._client.table('users').update({'google_auth_credentials_json': credentials_json}).eq('id', user_id).execute()
        except Exception as e:
            logger.error(f"Supabase 사용자의 Google 인증 정보 업데이트 실패: {e}")

    def get_user_google_credentials(self, user_id: int) -> Optional[str]:
        try:
            response = self._client.table('users').select('google_auth_credentials_json').eq('id', user_id).execute()
            if response.data and response.data[0].get('google_auth_credentials_json'):
                return response.data[0]['google_auth_credentials_json']
            return None
        except Exception as e:
            logger.error(f"Supabase 사용자의 Google 인증 정보 조회 실패: {e}")
            return None

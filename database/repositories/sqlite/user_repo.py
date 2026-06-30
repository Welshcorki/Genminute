"""
SQLite UserRepository 구현체

users 테이블의 Google 인증 정보 관리를 담당합니다.
"""
import logging
from typing import Optional

from database.repositories.interfaces import UserRepositoryInterface
from .connection import SqliteConnection

logger = logging.getLogger(__name__)


class SqliteUserRepository(UserRepositoryInterface):

    def __init__(self, connection: SqliteConnection):
        self._conn_manager = connection

    def update_user_google_credentials(self, user_id: int, credentials_json: str) -> None:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'google_auth_credentials_json' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN google_auth_credentials_json TEXT")
                logger.info("'users' 테이블에 'google_auth_credentials_json' 컬럼 추가 완료")

            cursor.execute("""
                UPDATE users SET google_auth_credentials_json = ? WHERE id = ?
            """, (credentials_json, user_id))
            conn.commit()
            logger.info(f"사용자 {user_id}의 Google 인증 정보 업데이트 완료")
        except Exception as e:
            conn.rollback()
            logger.error(f"사용자 {user_id}의 Google 인증 정보 업데이트 실패: {e}")
            raise
        finally:
            conn.close()

    def get_user_google_credentials(self, user_id: int) -> Optional[str]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT google_auth_credentials_json FROM users WHERE id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row and row['google_auth_credentials_json']:
                return row['google_auth_credentials_json']
            return None
        except Exception as e:
            logger.error(f"사용자 {user_id}의 Google 인증 정보 조회 실패: {e}")
            return None
        finally:
            conn.close()

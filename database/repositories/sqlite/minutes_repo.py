"""
SQLite MinutesRepository 구현체

meeting_minutes 테이블에 대한 CRUD를 담당합니다.
"""
import datetime
import logging
from typing import Optional, Dict

from database.repositories.interfaces import MinutesRepositoryInterface
from .connection import SqliteConnection

logger = logging.getLogger(__name__)


class SqliteMinutesRepository(MinutesRepositoryInterface):

    def __init__(self, connection: SqliteConnection):
        self._conn_manager = connection

    def save_minutes(
        self,
        meeting_id: str,
        title: str,
        meeting_date: str,
        minutes_content: str,
        owner_id: Optional[int] = None,
    ) -> bool:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "SELECT meeting_id FROM meeting_minutes WHERE meeting_id = ?",
                (meeting_id,),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE meeting_minutes
                    SET title = ?, meeting_date = ?, minutes_content = ?, updated_at = ?, owner_id = ?
                    WHERE meeting_id = ?
                """, (title, meeting_date, minutes_content, created_at, owner_id, meeting_id))
                logger.info(f"회의록 업데이트 완료: meeting_id={meeting_id}")
            else:
                cursor.execute("""
                    INSERT INTO meeting_minutes
                    (meeting_id, title, meeting_date, minutes_content, created_at, updated_at, owner_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (meeting_id, title, meeting_date, minutes_content, created_at, created_at, owner_id))
                logger.info(f"회의록 저장 완료: meeting_id={meeting_id}")

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_minutes_by_meeting_id(self, meeting_id: str) -> Optional[Dict]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'"
            )
            if not cursor.fetchone():
                return None

            cursor.execute("""
                SELECT meeting_id, title, meeting_date, minutes_content, created_at, updated_at
                FROM meeting_minutes WHERE meeting_id = ?
            """, (meeting_id,))

            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

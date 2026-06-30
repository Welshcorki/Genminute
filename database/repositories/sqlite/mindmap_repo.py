"""
SQLite MindmapRepository 구현체

meeting_mindmap 테이블에 대한 CRUD를 담당합니다.
"""
import datetime
import logging
from typing import Optional

from database.repositories.interfaces import MindmapRepositoryInterface
from .connection import SqliteConnection

logger = logging.getLogger(__name__)


class SqliteMindmapRepository(MindmapRepositoryInterface):

    def __init__(self, connection: SqliteConnection):
        self._conn_manager = connection

    def save_mindmap(self, meeting_id: str, mindmap_content: str) -> bool:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "SELECT meeting_id FROM meeting_mindmap WHERE meeting_id = ?",
                (meeting_id,),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE meeting_mindmap SET mindmap_content = ?, created_at = ? WHERE meeting_id = ?
                """, (mindmap_content, created_at, meeting_id))
                logger.info(f"마인드맵 업데이트 완료: meeting_id={meeting_id}")
            else:
                cursor.execute("""
                    INSERT INTO meeting_mindmap (meeting_id, mindmap_content, created_at)
                    VALUES (?, ?, ?)
                """, (meeting_id, mindmap_content, created_at))
                logger.info(f"마인드맵 저장 완료: meeting_id={meeting_id}")

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_mindmap_by_meeting_id(self, meeting_id: str) -> Optional[str]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'"
            )
            if not cursor.fetchone():
                return None

            cursor.execute(
                "SELECT mindmap_content FROM meeting_mindmap WHERE meeting_id = ?",
                (meeting_id,),
            )
            row = cursor.fetchone()
            return row['mindmap_content'] if row else None
        finally:
            conn.close()

    def delete_mindmap_by_meeting_id(self, meeting_id: str) -> int:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_mindmap'"
            )
            if not cursor.fetchone():
                return 0

            cursor.execute(
                "DELETE FROM meeting_mindmap WHERE meeting_id = ?", (meeting_id,),
            )
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

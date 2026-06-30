"""
SQLite ActionItemRepository 구현체

meeting_action_items 테이블에 대한 CRUD를 담당합니다.
"""
import datetime
import logging
from typing import Optional, Dict, List

from database.repositories.interfaces import ActionItemRepositoryInterface
from .connection import SqliteConnection

logger = logging.getLogger(__name__)


class SqliteActionItemRepository(ActionItemRepositoryInterface):

    def __init__(self, connection: SqliteConnection):
        self._conn_manager = connection

    def save_action_items(self, meeting_id: str, items: List[Dict]) -> None:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            for item in items:
                cursor.execute("""
                    INSERT INTO meeting_action_items
                    (meeting_id, content, due_date, tool_call_id, calendar_event_id, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (
                    meeting_id,
                    item.get('content') or item.get('summary', ''),
                    item.get('due_date') or item.get('start_time'),
                    item.get('tool_call_id'),
                    item.get('calendar_event_id'),
                ))

            conn.commit()
            logger.info(f"Action Items 저장 완료: meeting_id={meeting_id}, {len(items)}개 항목")
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_action_items_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_action_items'"
            )
            if not cursor.fetchone():
                return []

            cursor.execute("""
                SELECT id, meeting_id, content, due_date, status,
                       tool_call_id, calendar_event_id, created_at, updated_at
                FROM meeting_action_items
                WHERE meeting_id = ?
                ORDER BY created_at ASC
            """, (meeting_id,))

            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Action Items 조회 실패: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def update_action_item_status(self, item_id: int, status: str) -> bool:
        if status not in ('pending', 'done'):
            raise ValueError(f"잘못된 상태 값: {status}")

        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE meeting_action_items SET status = ?, updated_at = ? WHERE id = ?
            """, (status, updated_at, item_id))
            conn.commit()
            logger.info(f"Action Item 상태 업데이트: id={item_id}, status={status}")
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_action_item_meeting_id(self, item_id: int) -> Optional[str]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT meeting_id FROM meeting_action_items WHERE id = ?",
                (item_id,),
            )
            row = cursor.fetchone()
            return row['meeting_id'] if row else None
        except Exception as e:
            logger.error(f"Action Item 회의 ID 조회 실패: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def delete_action_items_by_meeting_id(self, meeting_id: str) -> int:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM meeting_action_items WHERE meeting_id = ?",
                (meeting_id,),
            )
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Action Items 삭제 완료: meeting_id={meeting_id}, {deleted_count}개")
            return deleted_count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

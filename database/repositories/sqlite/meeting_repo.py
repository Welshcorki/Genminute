"""
SQLite MeetingRepository 구현체

meeting_dialogues 테이블에 대한 CRUD를 담당합니다.
"""
import uuid
import datetime
import logging
from typing import Optional, Dict, List

from database.repositories.interfaces import MeetingRepositoryInterface
from .connection import SqliteConnection

logger = logging.getLogger(__name__)


class SqliteMeetingRepository(MeetingRepositoryInterface):

    def __init__(self, connection: SqliteConnection):
        self._conn_manager = connection

    def save_stt_to_db(
        self,
        segments: list,
        audio_filename: str,
        title: str,
        meeting_date: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> str:
        meeting_id = str(uuid.uuid4())
        if meeting_date is None:
            meeting_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            for segment in segments:
                cursor.execute("""
                    INSERT INTO meeting_dialogues
                    (meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title, owner_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    meeting_id, meeting_date, str(segment['speaker']),
                    segment['start_time'], segment['text'],
                    segment['confidence'], audio_filename, title, owner_id,
                ))
            conn.commit()
            logger.info(f"DB 저장 완료: meeting_id={meeting_id}, owner_id={owner_id}")
            return meeting_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_meeting_by_id(self, meeting_id: str) -> list:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC",
                (meeting_id,),
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def get_all_meetings(self) -> list:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT meeting_id, title, MAX(meeting_date) as date,
                       (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file
                FROM meeting_dialogues md
                GROUP BY meeting_id
                ORDER BY date DESC
            """)
            return cursor.fetchall()
        finally:
            conn.close()

    def get_segments_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC",
                (meeting_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_audio_file_by_meeting_id(self, meeting_id: str) -> Optional[str]:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT audio_file FROM meeting_dialogues WHERE meeting_id = ? LIMIT 1",
                (meeting_id,),
            )
            row = cursor.fetchone()
            return row['audio_file'] if row else None
        finally:
            conn.close()

    def update_meeting_title(self, meeting_id: str, new_title: str) -> Dict:
        from database.vector_manager import vdb_manager

        vector_result = vdb_manager.update_metadata_title(meeting_id, new_title)
        if not vector_result['success']:
            logger.warning("ChromaDB 업데이트 실패로 SQLite 업데이트를 건너뜁니다.")
            return {
                'success': False,
                'error': f"ChromaDB 업데이트 실패: {vector_result.get('error', '알 수 없는 오류')}",
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result,
            }

        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE meeting_dialogues SET title = ? WHERE meeting_id = ?",
                (new_title, meeting_id),
            )
            updated_dialogues = cursor.rowcount

            updated_minutes = 0
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE meeting_minutes SET title = ?, updated_at = ? WHERE meeting_id = ?
                """, (new_title, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meeting_id))
                updated_minutes = cursor.rowcount

            conn.commit()
            logger.info(f"제목 업데이트 완료: meeting_id={meeting_id}")
            return {
                'success': True,
                'updated_dialogues': updated_dialogues,
                'updated_minutes': updated_minutes,
                'updated_vector': vector_result,
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"제목 업데이트 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result,
            }
        finally:
            conn.close()

    def update_meeting_date(self, meeting_id: str, new_date: str) -> Dict:
        from database.vector_manager import vdb_manager

        vector_result = vdb_manager.update_metadata_date(meeting_id, new_date)
        if not vector_result['success']:
            logger.warning("ChromaDB 업데이트 실패로 SQLite 업데이트를 건너뜁니다.")
            return {
                'success': False,
                'error': f"ChromaDB 업데이트 실패: {vector_result.get('error', '알 수 없는 오류')}",
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result,
            }

        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE meeting_dialogues SET meeting_date = ? WHERE meeting_id = ?",
                (new_date, meeting_id),
            )
            updated_dialogues = cursor.rowcount

            updated_minutes = 0
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE meeting_minutes SET meeting_date = ?, updated_at = ? WHERE meeting_id = ?
                """, (new_date, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meeting_id))
                updated_minutes = cursor.rowcount

            conn.commit()
            logger.info(f"날짜 업데이트 완료: meeting_id={meeting_id}")
            return {
                'success': True,
                'updated_dialogues': updated_dialogues,
                'updated_minutes': updated_minutes,
                'updated_vector': vector_result,
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"날짜 업데이트 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'updated_dialogues': 0,
                'updated_minutes': 0,
                'updated_vector': vector_result,
            }
        finally:
            conn.close()

    def delete_meeting_data(
        self,
        meeting_id: Optional[str] = None,
        audio_file: Optional[str] = None,
        title: Optional[str] = None,
    ) -> int:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            query = "DELETE FROM meeting_dialogues"
            conditions: list[str] = []
            params: list = []

            if meeting_id:
                conditions.append("meeting_id = ?")
                params.append(meeting_id)
            if audio_file:
                conditions.append("audio_file = ?")
                params.append(audio_file)
            if title:
                conditions.append("title = ?")
                params.append(title)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, tuple(params))
            deleted_rows = cursor.rowcount
            conn.commit()
            logger.info(f"DB 삭제 완료: {deleted_rows}개 행 삭제됨")
            return deleted_rows
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete_meeting_by_id(self, meeting_id: str) -> Dict:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            tables_to_delete = [
                "meeting_dialogues",
                "meeting_minutes",
                "meeting_shares",
                "meeting_mindmap",
                "meeting_action_items",
            ]

            before: Dict[str, int] = {}
            deleted: Dict[str, int] = {}
            after: Dict[str, int] = {}

            for table in tables_to_delete:
                before[table] = self._count_rows(cursor, table, meeting_id)

            for table in tables_to_delete:
                deleted[table] = self._delete_from_table(cursor, table, meeting_id)

            conn.commit()

            for table in tables_to_delete:
                after[table] = self._count_rows(cursor, table, meeting_id)

            all_deleted = all(v == 0 for v in after.values())
            if all_deleted:
                logger.info("SQLite DB 삭제 검증 성공")
            else:
                logger.warning("SQLite DB 삭제 검증 실패: 일부 데이터가 남아있습니다.")

            return {
                "dialogues": deleted.get("meeting_dialogues", 0),
                "minutes": deleted.get("meeting_minutes", 0),
                "shares": deleted.get("meeting_shares", 0),
                "mindmap": deleted.get("meeting_mindmap", 0),
                "before": {k.replace("meeting_", ""): v for k, v in before.items()},
                "after": {k.replace("meeting_", ""): v for k, v in after.items()},
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_user_stats(self, user_id: int, is_admin: bool) -> Dict:
        conn = self._conn_manager.get_connection()
        cursor = conn.cursor()

        try:
            now = datetime.datetime.now()
            month_str = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

            if is_admin:
                cursor.execute(
                    "SELECT COUNT(DISTINCT meeting_id) as count FROM meeting_dialogues WHERE meeting_date >= ?",
                    (month_str,),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(DISTINCT meeting_id) as count FROM meeting_dialogues WHERE owner_id = ? AND meeting_date >= ?",
                    (user_id, month_str),
                )
            monthly_count = cursor.fetchone()['count'] or 0

            if is_admin:
                cursor.execute("""
                    SELECT SUM(max_time) as total_seconds FROM (
                        SELECT meeting_id, MAX(start_time) as max_time FROM meeting_dialogues GROUP BY meeting_id
                    )
                """)
            else:
                cursor.execute("""
                    SELECT SUM(max_time) as total_seconds FROM (
                        SELECT meeting_id, MAX(start_time) as max_time FROM meeting_dialogues WHERE owner_id = ? GROUP BY meeting_id
                    )
                """, (user_id,))

            result = cursor.fetchone()
            total_seconds = result['total_seconds'] if result and result['total_seconds'] else 0

            return {
                "monthly_notes": monthly_count,
                "total_recording_hours": int(total_seconds // 3600),
                "total_recording_minutes": int((total_seconds % 3600) // 60),
                "total_recording_seconds": int(total_seconds),
            }
        finally:
            conn.close()

    # ── private helpers ──

    @staticmethod
    def _table_exists(cursor, table_name: str) -> bool:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None

    @classmethod
    def _count_rows(cls, cursor, table: str, meeting_id: str) -> int:
        if not cls._table_exists(cursor, table):
            return 0
        cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE meeting_id = ?", (meeting_id,))
        return cursor.fetchone()['count']

    @classmethod
    def _delete_from_table(cls, cursor, table: str, meeting_id: str) -> int:
        if not cls._table_exists(cursor, table):
            return 0
        cursor.execute(f"DELETE FROM {table} WHERE meeting_id = ?", (meeting_id,))
        return cursor.rowcount

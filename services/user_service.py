"""
사용자 관리 서비스
- users 테이블 CRUD
- 권한 확인 (admin/user)
- 공유 권한 관리

Repository 인터페이스에 의존합니다 (DIP).
"""

import logging
from typing import Optional, Dict, List

from config import config
from database.repositories.interfaces import (
    MeetingRepositoryInterface,
    UserRepositoryInterface,
)

logger = logging.getLogger(__name__)


class UserService:
    """사용자/권한/공유 관련 비즈니스 로직"""

    def __init__(self, connection):
        """
        Args:
            connection: DB 연결 관리자 (SqliteConnection 등).
                        직접 쿼리가 필요한 복합 로직용.
        """
        self._conn = connection

    def get_or_create_user(
        self,
        google_id: str,
        email: str,
        name: str = None,
        profile_picture: str = None,
    ) -> Dict:
        conn = self._conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
            user = cursor.fetchone()

            if user:
                cursor.execute("""
                    UPDATE users SET name = ?, profile_picture = ? WHERE google_id = ?
                """, (name, profile_picture, google_id))
                conn.commit()
                return dict(user)

            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

            if user:
                cursor.execute("""
                    UPDATE users SET google_id = ?, name = ?, profile_picture = ? WHERE email = ?
                """, (google_id, name, profile_picture, email))
                conn.commit()
                logger.info(f"기존 사용자 업데이트: {email}")
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                return dict(cursor.fetchone())

            admin_emails = [e.strip() for e in config.ADMIN_EMAILS if e.strip()]
            role = 'admin' if email in admin_emails else 'user'

            cursor.execute("""
                INSERT INTO users (google_id, email, name, profile_picture, role)
                VALUES (?, ?, ?, ?, ?)
            """, (google_id, email, name, profile_picture, role))
            conn.commit()

            logger.info(f"신규 사용자 생성: {email} (role: {role})")
            return {
                'id': cursor.lastrowid,
                'google_id': google_id,
                'email': email,
                'name': name,
                'profile_picture': profile_picture,
                'role': role,
            }
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
        finally:
            conn.close()

    def is_admin(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        return bool(user and user['role'] == 'admin')

    def can_access_meeting(self, user_id: int, meeting_id: str) -> bool:
        if self.is_admin(user_id):
            return True

        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM meeting_dialogues
                WHERE meeting_id = ? AND owner_id = ?
            """, (meeting_id, user_id))
            if cursor.fetchone()['count'] > 0:
                return True

            cursor.execute("""
                SELECT COUNT(*) as count FROM meeting_shares
                WHERE meeting_id = ? AND shared_with_user_id = ?
            """, (meeting_id, user_id))
            return cursor.fetchone()['count'] > 0
        finally:
            conn.close()

    def can_edit_meeting(self, user_id: int, meeting_id: str) -> bool:
        if self.is_admin(user_id):
            return True

        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT owner_id FROM meeting_dialogues WHERE meeting_id = ? LIMIT 1
            """, (meeting_id,))
            result = cursor.fetchone()
            return bool(result and result['owner_id'] == user_id)
        finally:
            conn.close()

    def get_user_meetings(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 10,
        search_term: str = None,
        start_date: str = None,
        end_date: str = None,
        sort_by: str = 'date_desc',
    ) -> List[Dict]:
        conn = self._conn.get_connection()
        cursor = conn.cursor()

        try:
            where_clauses: list[str] = []
            params: list = []

            admin_mode = self.is_admin(user_id)
            if not admin_mode:
                where_clauses.append(
                    "(SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) = ?"
                )
                params.append(user_id)

            if search_term:
                pattern = f'%{search_term}%'
                where_clauses.append("(md.title LIKE ? OR mm.minutes_content LIKE ?)")
                params.extend([pattern, pattern])

            having_clauses: list[str] = []
            if start_date:
                having_clauses.append("MAX(md.meeting_date) >= ?")
                params.append(start_date)
            if end_date:
                having_clauses.append("MAX(md.meeting_date) <= ?")
                params.append(end_date)

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            having_sql = ("HAVING " + " AND ".join(having_clauses)) if having_clauses else ""

            order_map = {
                'date_desc': 'ORDER BY MAX(md.meeting_date) DESC',
                'date_asc': 'ORDER BY MAX(md.meeting_date) ASC',
                'title_asc': 'ORDER BY md.title ASC',
                'title_desc': 'ORDER BY md.title DESC',
            }
            order_sql = order_map.get(sort_by, order_map['date_desc'])
            offset = (page - 1) * per_page

            query = f"""
                SELECT md.meeting_id, md.title, MAX(md.meeting_date) as meeting_date,
                    (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file,
                    (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as owner_id,
                    mm.minutes_content as summary
                FROM meeting_dialogues md
                LEFT JOIN meeting_minutes mm ON md.meeting_id = mm.meeting_id
                {where_sql}
                GROUP BY md.meeting_id {having_sql} {order_sql}
                LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])

            cursor.execute(query, params)
            result = []
            for row in cursor.fetchall():
                d = dict(row)
                d['date'] = d.pop('meeting_date', None)
                result.append(d)
            return result
        finally:
            conn.close()

    def get_user_meetings_count(
        self,
        user_id: int,
        search_term: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> int:
        conn = self._conn.get_connection()
        cursor = conn.cursor()

        try:
            where_clauses: list[str] = []
            params: list = []

            if not self.is_admin(user_id):
                where_clauses.append(
                    "(SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) = ?"
                )
                params.append(user_id)

            if search_term:
                pattern = f'%{search_term}%'
                where_clauses.append("(md.title LIKE ? OR mm.minutes_content LIKE ?)")
                params.extend([pattern, pattern])

            having_clauses: list[str] = []
            if start_date:
                having_clauses.append("MAX(md.meeting_date) >= ?")
                params.append(start_date)
            if end_date:
                having_clauses.append("MAX(md.meeting_date) <= ?")
                params.append(end_date)

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            having_sql = ("HAVING " + " AND ".join(having_clauses)) if having_clauses else ""

            query = f"""
                SELECT COUNT(*) as count FROM (
                    SELECT md.meeting_id FROM meeting_dialogues md
                    LEFT JOIN meeting_minutes mm ON md.meeting_id = mm.meeting_id
                    {where_sql} GROUP BY md.meeting_id {having_sql}
                )
            """
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()

    def get_shared_meetings(self, user_id: int) -> List[Dict]:
        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT md.meeting_id, md.title, MAX(md.meeting_date) as meeting_date,
                    (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file,
                    (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as owner_id,
                    mm.minutes_content as summary
                FROM meeting_dialogues md
                INNER JOIN meeting_shares s ON md.meeting_id = s.meeting_id
                LEFT JOIN meeting_minutes mm ON md.meeting_id = mm.meeting_id
                WHERE s.shared_with_user_id = ?
                GROUP BY md.meeting_id
                ORDER BY meeting_date DESC
            """, (user_id,))

            result = []
            for row in cursor.fetchall():
                d = dict(row)
                d['date'] = d.pop('meeting_date', None)
                result.append(d)
            return result
        finally:
            conn.close()

    def share_meeting(self, meeting_id: str, owner_id: int, shared_with_email: str) -> Dict:
        conn = self._conn.get_connection()
        cursor = conn.cursor()

        try:
            shared_user = self.get_user_by_email(shared_with_email)
            if not shared_user:
                return {'success': False, 'message': '해당 이메일의 사용자를 찾을 수 없습니다.'}
            if shared_user['id'] == owner_id:
                return {'success': False, 'message': '본인에게는 공유할 수 없습니다.'}

            cursor.execute("SELECT owner_id FROM meeting_dialogues WHERE meeting_id = ? LIMIT 1", (meeting_id,))
            result = cursor.fetchone()
            if not result:
                return {'success': False, 'message': '회의를 찾을 수 없습니다.'}
            if result['owner_id'] != owner_id:
                return {'success': False, 'message': '회의 소유자만 공유할 수 있습니다.'}

            cursor.execute("""
                SELECT COUNT(*) as count FROM meeting_shares
                WHERE meeting_id = ? AND shared_with_user_id = ?
            """, (meeting_id, shared_user['id']))
            if cursor.fetchone()['count'] > 0:
                return {'success': False, 'message': '이미 공유된 사용자입니다.'}

            cursor.execute("""
                INSERT INTO meeting_shares (meeting_id, owner_id, shared_with_user_id, permission)
                VALUES (?, ?, ?, 'read')
            """, (meeting_id, owner_id, shared_user['id']))
            conn.commit()

            logger.info(f"회의 공유 완료: {meeting_id} → {shared_with_email}")
            return {'success': True, 'message': f'{shared_with_email}에게 공유되었습니다.'}
        except Exception as e:
            logger.error(f"회의 공유 실패: {e}")
            return {'success': False, 'message': f'공유 실패: {str(e)}'}
        finally:
            conn.close()

    def get_shared_users(self, meeting_id: str) -> List[Dict]:
        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT u.id, u.email, u.name, u.profile_picture,
                       s.permission, s.created_at as shared_at
                FROM meeting_shares s
                JOIN users u ON s.shared_with_user_id = u.id
                WHERE s.meeting_id = ?
                ORDER BY s.created_at DESC
            """, (meeting_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def remove_share(self, meeting_id: str, owner_id: int, shared_user_id: int) -> Dict:
        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT owner_id FROM meeting_minutes WHERE meeting_id = ?", (meeting_id,))
            result = cursor.fetchone()
            if not result or result['owner_id'] != owner_id:
                return {'success': False, 'message': '회의 소유자만 공유를 제거할 수 있습니다.'}

            cursor.execute("""
                DELETE FROM meeting_shares
                WHERE meeting_id = ? AND owner_id = ? AND shared_with_user_id = ?
            """, (meeting_id, owner_id, shared_user_id))
            conn.commit()

            if cursor.rowcount > 0:
                return {'success': True, 'message': '공유가 제거되었습니다.'}
            return {'success': False, 'message': '공유 정보를 찾을 수 없습니다.'}
        finally:
            conn.close()

    def get_user_accessible_meeting_ids(self, user_id: int) -> List[str]:
        conn = self._conn.get_connection()
        cursor = conn.cursor()
        try:
            if self.is_admin(user_id):
                cursor.execute("SELECT DISTINCT meeting_id FROM meeting_dialogues")
            else:
                cursor.execute("""
                    SELECT DISTINCT md.meeting_id FROM meeting_dialogues md
                    LEFT JOIN meeting_shares s ON md.meeting_id = s.meeting_id
                    WHERE md.owner_id = ? OR s.shared_with_user_id = ?
                """, (user_id, user_id))

            meeting_ids = [row['meeting_id'] for row in cursor.fetchall()]
            logger.info(f"사용자 {user_id} 접근 가능한 노트: {len(meeting_ids)}개")
            return meeting_ids
        finally:
            conn.close()


# ── 하위 호환 모듈-레벨 함수 ──
# 기존 코드(`from services.user_service import can_access_meeting` 등)가
# 깨지지 않도록 유지합니다. 새 코드에서는 UserService 클래스를 사용하세요.

def _get_service() -> UserService:
    from database.sqlite_manager import DatabaseManager
    db = DatabaseManager(str(config.DATABASE_PATH))
    return UserService(db.connection)


def get_or_create_user(google_id, email, name=None, profile_picture=None):
    return _get_service().get_or_create_user(google_id, email, name, profile_picture)

def get_user_by_id(user_id):
    return _get_service().get_user_by_id(user_id)

def get_user_by_email(email):
    return _get_service().get_user_by_email(email)

def is_admin(user_id):
    return _get_service().is_admin(user_id)

def can_access_meeting(user_id, meeting_id):
    return _get_service().can_access_meeting(user_id, meeting_id)

def can_edit_meeting(user_id, meeting_id):
    return _get_service().can_edit_meeting(user_id, meeting_id)

def get_user_meetings(user_id, page=1, per_page=10, search_term=None, start_date=None, end_date=None, sort_by='date_desc'):
    return _get_service().get_user_meetings(user_id, page, per_page, search_term, start_date, end_date, sort_by)

def get_user_meetings_count(user_id, search_term=None, start_date=None, end_date=None):
    return _get_service().get_user_meetings_count(user_id, search_term, start_date, end_date)

def get_shared_meetings(user_id):
    return _get_service().get_shared_meetings(user_id)

def share_meeting(meeting_id, owner_id, shared_with_email):
    return _get_service().share_meeting(meeting_id, owner_id, shared_with_email)

def get_shared_users(meeting_id):
    return _get_service().get_shared_users(meeting_id)

def remove_share(meeting_id, owner_id, shared_user_id):
    return _get_service().remove_share(meeting_id, owner_id, shared_user_id)

def get_user_accessible_meeting_ids(user_id):
    return _get_service().get_user_accessible_meeting_ids(user_id)

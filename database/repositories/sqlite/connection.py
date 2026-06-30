"""
SQLite 연결 관리 및 테이블 초기화

모든 SQLite Repository가 공유하는 연결 관리 클래스입니다.
DB 전환 시 이 클래스와 Repository 구현체만 교체합니다.
"""
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)


class SqliteConnection:
    """SQLite 데이터베이스 연결 관리"""

    def __init__(self, db_path: str):
        self._db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    @property
    def db_path(self) -> str:
        return self._db_path

    def get_connection(self) -> sqlite3.Connection:
        """새 SQLite 연결을 반환합니다. 호출자가 close() 책임."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_tables(self) -> None:
        """앱 시작 시 한 번 호출하여 모든 테이블을 생성합니다."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_dialogues (
                    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT NOT NULL,
                    meeting_date TEXT,
                    speaker_label TEXT,
                    start_time REAL,
                    segment TEXT,
                    confidence REAL,
                    audio_file TEXT,
                    title TEXT,
                    owner_id INTEGER
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_minutes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    meeting_date TEXT,
                    minutes_content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    owner_id INTEGER
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_mindmap (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT UNIQUE NOT NULL,
                    mindmap_content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_id TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    profile_picture TEXT,
                    role TEXT DEFAULT 'user',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_shares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT NOT NULL,
                    owner_id INTEGER NOT NULL,
                    shared_with_user_id INTEGER NOT NULL,
                    permission TEXT DEFAULT 'read',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id),
                    FOREIGN KEY (shared_with_user_id) REFERENCES users(id),
                    UNIQUE(meeting_id, shared_with_user_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    due_date TEXT,
                    status TEXT DEFAULT 'pending',
                    tool_call_id TEXT,
                    calendar_event_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_id ON meeting_dialogues(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_owner_id ON meeting_dialogues(owner_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_meeting ON meeting_shares(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON meeting_action_items(meeting_id)")

            self._create_admin_users(cursor)

            conn.commit()
            logger.info("✅ 데이터베이스 테이블 초기화 완료")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 데이터베이스 테이블 초기화 실패: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def _create_admin_users(cursor: sqlite3.Cursor) -> None:
        from config import config
        admin_emails = config.ADMIN_EMAILS

        if not admin_emails:
            return

        for email in admin_emails:
            if not email.strip():
                continue
            try:
                cursor.execute("""
                    INSERT INTO users (google_id, email, name, role)
                    VALUES (?, ?, ?, 'admin')
                """, (f"admin_{email}", email, "Admin User"))
                logger.info(f"✅ Admin 사용자 생성: {email}")
            except sqlite3.IntegrityError:
                pass

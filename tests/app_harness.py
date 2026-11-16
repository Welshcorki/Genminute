"""
앱 수준 테스트 공용 하네스

실제 Flask 앱(app.py)을 임시 SQLite DB로 한 번만 부팅하고, 라우트 테스트들이 공유합니다.
- 실제 DB(database/minute_ai.db)는 건드리지 않습니다 (import 전에 경로 교체).
- 벡터 DB와 LLM 호출은 각 테스트에서 mock으로 대체해야 합니다.
- 전체 의존성(chromadb, torch 등)과 .env가 없으면 app_module이 None이 되고,
  AppRouteTestBase를 상속한 테스트는 건너뜁니다.

사용법 (tests/ 가 sys.path에 있어야 하므로 아래 두 줄을 먼저 실행):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from app_harness import AppRouteTestBase, insert_user
"""
import atexit
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import Config

_db_fd, DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

app_module = None
SKIP_REASON: str = ""

try:
    # 실제 DB를 건드리지 않도록 앱 import 전에 경로를 교체
    Config.DB_TYPE = "sqlite"
    Config.DATABASE_PATH = Path(DB_PATH)

    import app as app_module

    if str(getattr(app_module.db, "db_path", "")) != DB_PATH:
        # 다른 코드가 먼저 DB 싱글톤을 만든 경우 — 실제 DB 보호를 위해 건너뜀
        SKIP_REASON = "DB 싱글톤이 이미 다른 경로로 초기화됨"
        app_module = None
except Exception as e:  # 의존성/환경 변수 미비
    SKIP_REASON = f"앱 import 불가: {type(e).__name__}: {e}"
    app_module = None


@atexit.register
def _cleanup_temp_db() -> None:
    try:
        os.unlink(DB_PATH)
    except OSError:
        pass


def insert_user(email: str, role: str = "user") -> int:
    """임시 DB에 사용자를 추가하고 id를 반환"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO users (google_id, email, name, role) VALUES (?, ?, ?, ?)",
            (f"gid-{email}", email, email.split("@")[0], role),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


@unittest.skipIf(app_module is None, SKIP_REASON)
class AppRouteTestBase(unittest.TestCase):
    """클래스마다 일반 사용자 1명과 관리자 1명을 만들어 두는 라우트 테스트 베이스"""

    @classmethod
    def setUpClass(cls):
        cls.app = app_module.app
        cls.db = app_module.db
        suffix = cls.__name__.lower()
        cls.user_id = insert_user(f"user-{suffix}@example.com", "user")
        cls.admin_id = insert_user(f"admin-{suffix}@example.com", "admin")

    def setUp(self):
        self.client = self.app.test_client()

    def login_as(self, user_id: int) -> None:
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id

    def logout(self) -> None:
        with self.client.session_transaction() as sess:
            sess.clear()

    def create_meeting(
        self,
        text: str = "회의 내용입니다. " * 20,
        owner_id: Optional[int] = None,
        title: str = "테스트 회의",
        audio_file: str = "test.wav",
    ) -> str:
        segments = [{"speaker": "1", "start_time": 0.0, "text": text, "confidence": 0.9}]
        return self.db.save_stt_to_db(
            segments, audio_file, title, "2026-01-01 10:00:00",
            owner_id=owner_id if owner_id is not None else self.user_id,
        )

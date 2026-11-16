"""
앱 수준 라우트 스모크 테스트

실제 Flask 앱(app.py)을 임시 SQLite DB로 부팅해 라우팅과 권한을 검증합니다.
외부 API(Gemini/OpenAI 호출)는 mock으로 대체하며, 벡터 DB에는 쓰지 않습니다.

테스트 항목:
- 페이지 경로(/, /login, /notes ...)가 레거시 템플릿이 아닌 React SPA로 전달되는지
- 비로그인 요청 처리 (페이지: /login 리다이렉트, API: 401)
- 관리자 페이지 권한 및 렌더링
- /api/summarize: 요약과 함께 마인드맵이 재생성되는지

전체 의존성(chromadb, torch 등)과 .env가 필요하므로, 앱을 import할 수 없는 환경에서는 건너뜁니다.
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import Config

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)

app_module = None
SKIP_REASON = ""

try:
    # 실제 DB(database/minute_ai.db)를 건드리지 않도록 import 전에 경로를 교체
    Config.DB_TYPE = "sqlite"
    Config.DATABASE_PATH = Path(_db_path)

    import app as app_module

    if str(getattr(app_module.db, "db_path", "")) != _db_path:
        # 다른 테스트가 먼저 DB 싱글톤을 만든 경우 — 실제 DB 보호를 위해 건너뜀
        SKIP_REASON = "DB 싱글톤이 이미 다른 경로로 초기화됨"
        app_module = None
except Exception as e:  # 의존성/환경 변수 미비
    SKIP_REASON = f"앱 import 불가: {type(e).__name__}: {e}"
    app_module = None


def tearDownModule():
    try:
        os.unlink(_db_path)
    except OSError:
        pass


def _insert_user(email: str, role: str) -> int:
    conn = sqlite3.connect(_db_path)
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
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.app
        cls.db = app_module.db
        suffix = cls.__name__.lower()
        cls.user_id = _insert_user(f"user-{suffix}@example.com", "user")
        cls.admin_id = _insert_user(f"admin-{suffix}@example.com", "admin")

    def setUp(self):
        self.client = self.app.test_client()

    def login_as(self, user_id: int):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id


class TestSpaRouting(AppRouteTestBase):
    """페이지 경로는 Blueprint(레거시 템플릿)가 아니라 SPA catch-all이 받아야 한다"""

    SPA_PATHS = ["/", "/login", "/notes", "/notes/some-id", "/shared-notes", "/record"]

    def test_page_paths_resolve_to_spa(self):
        adapter = self.app.url_map.bind("localhost")
        for path in self.SPA_PATHS:
            with self.subTest(path=path):
                endpoint, _ = adapter.match(path, method="GET")
                self.assertEqual(endpoint, "serve_react_app")

    def test_api_paths_still_resolve_to_blueprints(self):
        adapter = self.app.url_map.bind("localhost")
        self.assertEqual(adapter.match("/api/me", method="GET")[0], "auth.get_current_user")
        self.assertEqual(adapter.match("/notes_json", method="GET")[0], "meetings.notes_json")

    def test_page_paths_do_not_require_login(self):
        # 로그인 여부 판단은 SPA(AuthContext)가 하므로 서버는 리다이렉트하지 않는다
        for path in self.SPA_PATHS:
            with self.subTest(path=path):
                res = self.client.get(path)
                self.assertNotIn(res.status_code, (301, 302, 401))


class TestLoginRequired(AppRouteTestBase):
    def test_api_without_session_returns_401_json(self):
        res = self.client.get("/api/stats")

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["redirect"], "/login")

    def test_admin_page_without_session_redirects_to_spa_login(self):
        res = self.client.get("/retriever")

        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.headers["Location"].endswith("/login"))


class TestAdminPages(AppRouteTestBase):
    ADMIN_PAGES = [
        "/retriever", "/summary_template", "/test-summary", "/test-stt",
        "/test-minutes", "/test-mindmap", "/script-input",
    ]

    def test_non_admin_gets_403(self):
        self.login_as(self.user_id)
        for path in self.ADMIN_PAGES:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_admin_can_render_pages(self):
        self.login_as(self.admin_id)
        for path in self.ADMIN_PAGES:
            with self.subTest(path=path):
                res = self.client.get(path)
                self.assertEqual(res.status_code, 200)
                # 내비게이션이 SPA 경로를 가리키는지
                self.assertIn('href="/notes"', res.get_data(as_text=True))


class TestSummarize(AppRouteTestBase):
    """수동 요약(/api/summarize)은 업로드 파이프라인과 같은 구현을 써야 한다"""

    def _create_meeting(self, text: str) -> str:
        segments = [{"speaker": "1", "start_time": 0.0, "text": text, "confidence": 0.9}]
        return self.db.save_stt_to_db(
            segments, "test.wav", "테스트 회의", "2026-01-01 10:00:00", owner_id=self.user_id,
        )

    def _patch_llm_and_vector(self, summary="### 요약", mindmap="# 마인드맵"):
        from services.upload_service import upload_service
        return mock.patch.multiple(
            upload_service,
            stt_manager=mock.Mock(**{
                "subtopic_generate.return_value": summary,
                "extract_mindmap_keywords.return_value": mindmap,
            }),
            vdb_manager=mock.Mock(),
        )

    def test_summarize_saves_summary_and_regenerates_mindmap(self):
        from services.upload_service import upload_service
        meeting_id = self._create_meeting("회의 내용입니다. " * 20)
        self.login_as(self.user_id)

        with self._patch_llm_and_vector(mindmap="# 새 마인드맵"):
            res = self.client.post(f"/api/summarize/{meeting_id}")
            vdb_mock = upload_service.vdb_manager

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["summary"], "### 요약")
        vdb_mock.add_meeting_as_subtopic.assert_called_once()
        self.assertEqual(self.db.get_mindmap_by_meeting_id(meeting_id), "# 새 마인드맵")

    def test_summarize_too_short_returns_400(self):
        meeting_id = self._create_meeting("짧음")
        self.login_as(self.user_id)

        with self._patch_llm_and_vector():
            res = self.client.post(f"/api/summarize/{meeting_id}")

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])

    def test_summarize_llm_failure_returns_500(self):
        meeting_id = self._create_meeting("회의 내용입니다. " * 20)
        self.login_as(self.user_id)

        with self._patch_llm_and_vector(summary=""):
            res = self.client.post(f"/api/summarize/{meeting_id}")

        self.assertEqual(res.status_code, 500)
        self.assertFalse(res.get_json()["success"])

    def test_summarize_without_access_returns_403(self):
        meeting_id = self._create_meeting("회의 내용입니다. " * 20)
        other_id = _insert_user("other-summarize@example.com", "user")
        self.login_as(other_id)

        with self._patch_llm_and_vector():
            res = self.client.post(f"/api/summarize/{meeting_id}")

        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()

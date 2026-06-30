"""
Repository 계층 단위 테스트

인메모리 SQLite를 사용하여 외부 의존 없이 테스트합니다.
테스트 항목:
- MeetingRepository: CRUD, 통계
- MinutesRepository: 저장/조회
- MindmapRepository: 저장/조회/삭제
- ActionItemRepository: CRUD
- UserRepository: Google 인증 정보 CRUD
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.repositories.sqlite.connection import SqliteConnection
from database.repositories.sqlite.meeting_repo import SqliteMeetingRepository
from database.repositories.sqlite.minutes_repo import SqliteMinutesRepository
from database.repositories.sqlite.mindmap_repo import SqliteMindmapRepository
from database.repositories.sqlite.action_item_repo import SqliteActionItemRepository
from database.repositories.sqlite.user_repo import SqliteUserRepository


class RepositoryTestBase(unittest.TestCase):
    """각 Repository 테스트에서 공유하는 SQLite 인메모리 DB 세팅"""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn_manager = SqliteConnection(self.db_path)
        self.conn_manager.initialize_tables()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _insert_user(self, email="test@example.com", role="user"):
        conn = self.conn_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (google_id, email, name, role) VALUES (?, ?, ?, ?)",
            (f"gid_{email}", email, "Test User", role),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id


class TestMeetingRepository(RepositoryTestBase):

    def setUp(self):
        super().setUp()
        self.repo = SqliteMeetingRepository(self.conn_manager)

    def test_save_and_get_meeting(self):
        segments = [
            {"speaker": "A", "start_time": 0.0, "text": "안녕하세요", "confidence": 0.95},
            {"speaker": "B", "start_time": 1.5, "text": "반갑습니다", "confidence": 0.92},
        ]
        meeting_id = self.repo.save_stt_to_db(segments, "test.wav", "테스트 회의")
        self.assertIsNotNone(meeting_id)

        rows = self.repo.get_meeting_by_id(meeting_id)
        self.assertEqual(len(rows), 2)

    def test_get_all_meetings(self):
        segments = [{"speaker": "A", "start_time": 0.0, "text": "hello", "confidence": 0.9}]
        self.repo.save_stt_to_db(segments, "a.wav", "회의1")
        self.repo.save_stt_to_db(segments, "b.wav", "회의2")

        all_meetings = self.repo.get_all_meetings()
        self.assertEqual(len(all_meetings), 2)

    def test_get_segments_by_meeting_id(self):
        segments = [{"speaker": "A", "start_time": 0.0, "text": "test", "confidence": 0.9}]
        mid = self.repo.save_stt_to_db(segments, "x.wav", "title")

        result = self.repo.get_segments_by_meeting_id(mid)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)

    def test_get_audio_file(self):
        segments = [{"speaker": "A", "start_time": 0.0, "text": "test", "confidence": 0.9}]
        mid = self.repo.save_stt_to_db(segments, "audio.mp3", "title")

        audio = self.repo.get_audio_file_by_meeting_id(mid)
        self.assertEqual(audio, "audio.mp3")

    def test_delete_meeting_data(self):
        segments = [{"speaker": "A", "start_time": 0.0, "text": "test", "confidence": 0.9}]
        mid = self.repo.save_stt_to_db(segments, "x.wav", "title")

        deleted = self.repo.delete_meeting_data(meeting_id=mid)
        self.assertEqual(deleted, 1)

        rows = self.repo.get_meeting_by_id(mid)
        self.assertEqual(len(rows), 0)

    def test_delete_meeting_by_id(self):
        segments = [{"speaker": "A", "start_time": 0.0, "text": "test", "confidence": 0.9}]
        mid = self.repo.save_stt_to_db(segments, "x.wav", "title")

        result = self.repo.delete_meeting_by_id(mid)
        self.assertIn("dialogues", result)
        self.assertEqual(result["dialogues"], 1)

    def test_get_user_stats(self):
        user_id = self._insert_user()
        segments = [{"speaker": "A", "start_time": 60.0, "text": "test", "confidence": 0.9}]
        self.repo.save_stt_to_db(segments, "x.wav", "title", owner_id=user_id)

        stats = self.repo.get_user_stats(user_id, is_admin=False)
        self.assertEqual(stats["monthly_notes"], 1)
        self.assertGreaterEqual(stats["total_recording_seconds"], 0)


class TestMinutesRepository(RepositoryTestBase):

    def setUp(self):
        super().setUp()
        self.repo = SqliteMinutesRepository(self.conn_manager)

    def test_save_and_get_minutes(self):
        self.repo.save_minutes("mid1", "제목", "2025-01-01", "회의록 내용")

        result = self.repo.get_minutes_by_meeting_id("mid1")
        self.assertIsNotNone(result)
        self.assertEqual(result['minutes_content'], "회의록 내용")

    def test_update_existing_minutes(self):
        self.repo.save_minutes("mid1", "제목", "2025-01-01", "첫 번째 내용")
        self.repo.save_minutes("mid1", "제목", "2025-01-01", "업데이트된 내용")

        result = self.repo.get_minutes_by_meeting_id("mid1")
        self.assertEqual(result['minutes_content'], "업데이트된 내용")

    def test_get_nonexistent_minutes(self):
        result = self.repo.get_minutes_by_meeting_id("nonexistent")
        self.assertIsNone(result)


class TestMindmapRepository(RepositoryTestBase):

    def setUp(self):
        super().setUp()
        self.repo = SqliteMindmapRepository(self.conn_manager)

    def test_save_and_get_mindmap(self):
        self.repo.save_mindmap("mid1", "# 마인드맵 내용")

        result = self.repo.get_mindmap_by_meeting_id("mid1")
        self.assertEqual(result, "# 마인드맵 내용")

    def test_delete_mindmap(self):
        self.repo.save_mindmap("mid1", "content")
        deleted = self.repo.delete_mindmap_by_meeting_id("mid1")
        self.assertEqual(deleted, 1)

        result = self.repo.get_mindmap_by_meeting_id("mid1")
        self.assertIsNone(result)


class TestActionItemRepository(RepositoryTestBase):

    def setUp(self):
        super().setUp()
        self.repo = SqliteActionItemRepository(self.conn_manager)

    def test_save_and_get_action_items(self):
        items = [
            {"content": "할 일 1", "due_date": "2025-12-31"},
            {"content": "할 일 2"},
        ]
        self.repo.save_action_items("mid1", items)

        result = self.repo.get_action_items_by_meeting_id("mid1")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['status'], 'pending')

    def test_update_status(self):
        self.repo.save_action_items("mid1", [{"content": "task"}])
        items = self.repo.get_action_items_by_meeting_id("mid1")
        item_id = items[0]['id']

        success = self.repo.update_action_item_status(item_id, "done")
        self.assertTrue(success)

        updated = self.repo.get_action_items_by_meeting_id("mid1")
        self.assertEqual(updated[0]['status'], 'done')

    def test_invalid_status_raises(self):
        self.repo.save_action_items("mid1", [{"content": "task"}])
        items = self.repo.get_action_items_by_meeting_id("mid1")

        with self.assertRaises(ValueError):
            self.repo.update_action_item_status(items[0]['id'], "invalid")

    def test_get_meeting_id_from_item(self):
        self.repo.save_action_items("mid1", [{"content": "task"}])
        items = self.repo.get_action_items_by_meeting_id("mid1")

        meeting_id = self.repo.get_action_item_meeting_id(items[0]['id'])
        self.assertEqual(meeting_id, "mid1")

    def test_delete_action_items(self):
        self.repo.save_action_items("mid1", [{"content": "a"}, {"content": "b"}])
        deleted = self.repo.delete_action_items_by_meeting_id("mid1")
        self.assertEqual(deleted, 2)

        result = self.repo.get_action_items_by_meeting_id("mid1")
        self.assertEqual(len(result), 0)


class TestUserRepository(RepositoryTestBase):

    def setUp(self):
        super().setUp()
        self.repo = SqliteUserRepository(self.conn_manager)

    def test_update_and_get_google_credentials(self):
        user_id = self._insert_user()
        creds = '{"access_token": "abc123"}'

        self.repo.update_user_google_credentials(user_id, creds)
        result = self.repo.get_user_google_credentials(user_id)
        self.assertEqual(result, creds)

    def test_get_nonexistent_credentials(self):
        user_id = self._insert_user()
        result = self.repo.get_user_google_credentials(user_id)
        self.assertIsNone(result)


class TestDatabaseManagerFacade(RepositoryTestBase):
    """DatabaseManager Facade가 Repository에 올바르게 위임하는지 확인"""

    def test_facade_delegates_to_meeting_repo(self):
        from database.sqlite_manager import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False
        dm = DatabaseManager(self.db_path)

        segments = [{"speaker": "A", "start_time": 0.0, "text": "hello", "confidence": 0.9}]
        mid = dm.save_stt_to_db(segments, "test.wav", "title")

        rows = dm.get_meeting_by_id(mid)
        self.assertEqual(len(rows), 1)

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

    def test_facade_delegates_to_minutes_repo(self):
        from database.sqlite_manager import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False
        dm = DatabaseManager(self.db_path)

        dm.save_minutes("mid1", "title", "2025-01-01", "content")
        result = dm.get_minutes_by_meeting_id("mid1")
        self.assertIsNotNone(result)

        DatabaseManager._instance = None
        DatabaseManager._initialized = False


if __name__ == '__main__':
    unittest.main()

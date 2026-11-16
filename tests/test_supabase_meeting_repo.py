"""
Supabase MeetingRepository 단위 테스트 (네트워크 없음)

Supabase 클라이언트와 벡터 DB를 mock으로 대체해, Repository가 벡터 DB의
실제 존재하는 메서드만 호출하는지와 삭제 시 재귀가 없는지를 검증합니다.

벡터 DB mock은 VectorDBManager를 spec으로 사용하므로, 존재하지 않는 메서드를
호출하면 AttributeError로 테스트가 실패합니다.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

SKIP_REASON = ""
try:
    from database.vector_manager import VectorDBManager
    from database.repositories.supabase import meeting_repo as repo_module
    from database.repositories.supabase.meeting_repo import SupabaseMeetingRepository
except Exception as e:  # supabase/chromadb 미설치 또는 환경 변수 미비
    SKIP_REASON = f"Supabase repo import 불가: {type(e).__name__}: {e}"
    repo_module = None


@unittest.skipIf(repo_module is None, SKIP_REASON)
class TestSupabaseMeetingRepositoryVectorSync(unittest.TestCase):
    def setUp(self):
        self.client = mock.MagicMock()
        connection = mock.Mock()
        connection.client = self.client
        self.repo = SupabaseMeetingRepository(connection)

        self.vdb = mock.Mock(spec=VectorDBManager)
        patcher = mock.patch.object(repo_module, "vdb_manager", self.vdb)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_update_title_syncs_vector_metadata(self):
        result = self.repo.update_meeting_title("m1", "새 제목")

        self.assertTrue(result["success"])
        self.vdb.update_metadata_title.assert_called_once_with("m1", "새 제목")

    def test_update_date_syncs_vector_metadata(self):
        result = self.repo.update_meeting_date("m1", "2026-01-01 10:00:00")

        self.assertTrue(result["success"])
        self.vdb.update_metadata_date.assert_called_once_with("m1", "2026-01-01 10:00:00")

    def test_delete_does_not_call_back_into_vector_manager(self):
        # vdb_manager._delete_all_meeting_data → repo.delete_meeting_by_id 순서로 호출되므로
        # repo가 다시 delete_from_collection('all')을 부르면 무한 재귀가 된다.
        result = self.repo.delete_meeting_by_id("m1")

        self.assertTrue(result["success"])
        self.vdb.delete_from_collection.assert_not_called()

    def test_delete_removes_rows_from_all_tables(self):
        self.repo.delete_meeting_by_id("m1")

        tables = [call.args[0] for call in self.client.table.call_args_list]
        self.assertEqual(
            sorted(tables),
            sorted([
                "meeting_dialogues", "meeting_minutes", "meeting_mindmap",
                "meeting_action_items", "meeting_shares",
            ]),
        )


if __name__ == "__main__":
    unittest.main()

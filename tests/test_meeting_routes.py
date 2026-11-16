"""
회의 관련 라우트 스모크 테스트 (SQLite 백엔드)

리팩토링 전후로 동작이 유지되는지 확인하기 위한 안전망입니다.
벡터 DB(ChromaDB)는 mock으로 대체하며 실제 컬렉션과 uploads/ 폴더는 건드리지 않습니다.

테스트 항목:
- 회의 조회 / 목록 / 통계와 접근 권한
- 제목·날짜 수정 (벡터 DB 메타데이터 동기화 포함)
- 회의 삭제 (관계형 DB + 벡터 DB + 미디어 파일)
- 공유 / 공유 해제
- Action Item 조회 / 상태 변경
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_harness import AppRouteTestBase, insert_user


def _vector_update_ok(*args, **kwargs) -> dict:
    return {"success": True, "updated_chunks": 0, "updated_subtopics": 0}


class MeetingRouteTestBase(AppRouteTestBase):
    """소유자(user)·타인(other)·관리자(admin) 3명을 두고 벡터 DB를 mock으로 대체"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_id = insert_user(f"other-{cls.__name__.lower()}@example.com")
        cls.other_email = f"other-{cls.__name__.lower()}@example.com"

    def setUp(self):
        super().setUp()
        from database.vector_manager import vdb_manager
        self.vdb = vdb_manager

        self.mock_update_title = self._patch_vdb("update_metadata_title", side_effect=_vector_update_ok)
        self.mock_update_date = self._patch_vdb("update_metadata_date", side_effect=_vector_update_ok)

    def _patch_vdb(self, name: str, **kwargs) -> mock.Mock:
        patcher = mock.patch.object(self.vdb, name, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked


class TestMeetingRead(MeetingRouteTestBase):
    def test_owner_can_read_meeting(self):
        meeting_id = self.create_meeting(title="주간 회의")
        self.login_as(self.user_id)

        res = self.client.get(f"/api/meeting/{meeting_id}")

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertTrue(body["can_edit"])
        self.assertEqual(len(body["transcript"]), 1)
        self.assertIn("speaker_share", body)

    def test_other_user_cannot_read_meeting(self):
        meeting_id = self.create_meeting()
        self.login_as(self.other_id)

        self.assertEqual(self.client.get(f"/api/meeting/{meeting_id}").status_code, 403)

    def test_admin_can_read_any_meeting(self):
        meeting_id = self.create_meeting()
        self.login_as(self.admin_id)

        res = self.client.get(f"/api/meeting/{meeting_id}")

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["can_edit"])

    def test_unauthenticated_read_returns_401(self):
        meeting_id = self.create_meeting()

        self.assertEqual(self.client.get(f"/api/meeting/{meeting_id}").status_code, 401)

    def test_notes_json_lists_only_own_meetings(self):
        own_id = self.create_meeting(title="내 회의")
        self.create_meeting(title="남의 회의", owner_id=self.other_id)
        self.login_as(self.user_id)

        res = self.client.get("/notes_json?per_page=100")

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        ids = [m["meeting_id"] for m in body["meetings"]]
        self.assertIn(own_id, ids)
        self.assertEqual(body["pagination"]["total"], len(ids))
        titles = [m["title"] for m in body["meetings"]]
        self.assertNotIn("남의 회의", titles)

    def test_stats_endpoint(self):
        self.create_meeting()
        self.login_as(self.user_id)

        res = self.client.get("/api/stats")

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])
        self.assertIsInstance(res.get_json()["stats"], dict)


class TestMeetingUpdate(MeetingRouteTestBase):
    def test_owner_updates_title(self):
        meeting_id = self.create_meeting(title="옛 제목")
        self.login_as(self.user_id)

        res = self.client.post(f"/api/update_title/{meeting_id}", json={"title": "새 제목"})

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])
        self.mock_update_title.assert_called_once_with(meeting_id, "새 제목")
        rows = self.db.get_meeting_by_id(meeting_id)
        self.assertEqual(rows[0]["title"], "새 제목")

    def test_empty_title_returns_400(self):
        meeting_id = self.create_meeting()
        self.login_as(self.user_id)

        res = self.client.post(f"/api/update_title/{meeting_id}", json={"title": "   "})

        self.assertEqual(res.status_code, 400)
        self.mock_update_title.assert_not_called()

    def test_other_user_cannot_update_title(self):
        meeting_id = self.create_meeting(title="옛 제목")
        self.login_as(self.other_id)

        res = self.client.post(f"/api/update_title/{meeting_id}", json={"title": "탈취"})

        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.db.get_meeting_by_id(meeting_id)[0]["title"], "옛 제목")

    def test_vector_failure_leaves_title_unchanged(self):
        meeting_id = self.create_meeting(title="옛 제목")
        self.login_as(self.user_id)
        self.mock_update_title.side_effect = lambda *a, **k: {"success": False, "error": "chroma down"}

        res = self.client.post(f"/api/update_title/{meeting_id}", json={"title": "새 제목"})

        self.assertFalse(res.get_json()["success"])
        self.assertEqual(self.db.get_meeting_by_id(meeting_id)[0]["title"], "옛 제목")

    def test_owner_updates_date(self):
        meeting_id = self.create_meeting()
        self.login_as(self.user_id)

        res = self.client.post(f"/api/update_date/{meeting_id}", json={"date": "2026-02-03T09:30"})

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])
        self.mock_update_date.assert_called_once()
        self.assertTrue(self.db.get_meeting_by_id(meeting_id)[0]["meeting_date"].startswith("2026-02-03"))


class TestMeetingDelete(MeetingRouteTestBase):
    def setUp(self):
        super().setUp()
        # 벡터 컬렉션: 삭제 전 2건 → 삭제 후 0건
        self.chunks = mock.Mock()
        self.chunks.get.side_effect = [{"ids": ["c1", "c2"]}, {"ids": []}]
        self.subtopic = mock.Mock()
        self.subtopic.get.side_effect = [{"ids": ["s1"]}, {"ids": []}]

        stores = {
            "chunks": mock.Mock(_collection=self.chunks),
            "subtopic": mock.Mock(_collection=self.subtopic),
        }
        self._patch_vdb("vectorstores", new=stores)

        # uploads 폴더 대신 임시 폴더 사용
        self.upload_dir = tempfile.mkdtemp()
        self._patch_vdb("upload_folder", new=self.upload_dir)
        self.addCleanup(self._remove_upload_dir)

    def _remove_upload_dir(self):
        for name in os.listdir(self.upload_dir):
            os.unlink(os.path.join(self.upload_dir, name))
        os.rmdir(self.upload_dir)

    def _make_audio(self, name: str) -> str:
        path = os.path.join(self.upload_dir, name)
        with open(path, "wb") as f:
            f.write(b"audio")
        return path

    def test_owner_deletes_meeting_everywhere(self):
        audio_path = self._make_audio("del_test.wav")
        meeting_id = self.create_meeting(audio_file="del_test.wav")
        self.db.save_mindmap(meeting_id, "# 마인드맵")
        self.login_as(self.user_id)

        res = self.client.post(f"/api/delete_meeting/{meeting_id}")

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["deleted"]["sqlite_dialogues"], 1)
        self.assertEqual(body["deleted"]["vector_chunks"], 2)
        self.assertEqual(body["deleted"]["vector_subtopic"], 1)
        self.assertEqual(body["deleted"]["audio_file"], "del_test.wav")

        self.assertEqual(len(self.db.get_meeting_by_id(meeting_id)), 0)
        self.assertIsNone(self.db.get_mindmap_by_meeting_id(meeting_id))
        self.chunks.delete.assert_called_once_with(where={"meeting_id": meeting_id})
        self.subtopic.delete.assert_called_once_with(where={"meeting_id": meeting_id})
        self.assertFalse(os.path.exists(audio_path))

    def test_other_user_cannot_delete(self):
        audio_path = self._make_audio("keep_test.wav")
        meeting_id = self.create_meeting(audio_file="keep_test.wav")
        self.login_as(self.other_id)

        res = self.client.post(f"/api/delete_meeting/{meeting_id}")

        self.assertEqual(res.status_code, 403)
        self.assertEqual(len(self.db.get_meeting_by_id(meeting_id)), 1)
        self.chunks.delete.assert_not_called()
        self.assertTrue(os.path.exists(audio_path))

    def test_admin_can_delete_any_meeting(self):
        meeting_id = self.create_meeting(audio_file="no_such_file.wav")
        self.login_as(self.admin_id)

        res = self.client.post(f"/api/delete_meeting/{meeting_id}")

        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.get_json()["deleted"]["audio_file"])
        self.assertEqual(len(self.db.get_meeting_by_id(meeting_id)), 0)


class TestMeetingShare(MeetingRouteTestBase):
    def test_share_grants_read_access_and_unshare_revokes(self):
        meeting_id = self.create_meeting(title="공유할 회의")

        # 공유 전: 타인은 접근 불가
        self.login_as(self.other_id)
        self.assertEqual(self.client.get(f"/api/meeting/{meeting_id}").status_code, 403)

        # 소유자가 공유
        self.login_as(self.user_id)
        res = self.client.post(f"/api/share/{meeting_id}", json={"email": self.other_email})
        self.assertTrue(res.get_json()["success"])

        res = self.client.get(f"/api/shared_users/{meeting_id}")
        shared_ids = [u["id"] for u in res.get_json()["shared_users"]]
        self.assertEqual(shared_ids, [self.other_id])

        # 공유 후: 읽기 가능, 수정 불가, 공유 목록에 노출
        self.login_as(self.other_id)
        res = self.client.get(f"/api/meeting/{meeting_id}")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json()["can_edit"])
        self.assertEqual(
            self.client.post(f"/api/update_title/{meeting_id}", json={"title": "x"}).status_code, 403,
        )
        shared = self.client.get("/api/shared-notes").get_json()["meetings"]
        self.assertIn(meeting_id, [m["meeting_id"] for m in shared])

        # 공유 해제 후: 다시 접근 불가
        self.login_as(self.user_id)
        res = self.client.post(f"/api/unshare/{meeting_id}/{self.other_id}")
        self.assertTrue(res.get_json()["success"])

        self.login_as(self.other_id)
        self.assertEqual(self.client.get(f"/api/meeting/{meeting_id}").status_code, 403)

    def test_share_requires_email(self):
        meeting_id = self.create_meeting()
        self.login_as(self.user_id)

        self.assertEqual(self.client.post(f"/api/share/{meeting_id}", json={}).status_code, 400)

    def test_share_with_unknown_email_fails(self):
        meeting_id = self.create_meeting()
        self.login_as(self.user_id)

        res = self.client.post(f"/api/share/{meeting_id}", json={"email": "nobody@example.com"})

        self.assertFalse(res.get_json()["success"])

    def test_non_owner_cannot_share(self):
        meeting_id = self.create_meeting()
        self.login_as(self.other_id)

        res = self.client.post(f"/api/share/{meeting_id}", json={"email": self.other_email})

        self.assertEqual(res.status_code, 403)


class TestActionItems(MeetingRouteTestBase):
    def _create_meeting_with_item(self) -> tuple[str, int]:
        meeting_id = self.create_meeting()
        self.db.save_action_items(meeting_id, [
            {"task": "보고서 작성", "assignee": "홍길동", "due_date": "2026-01-10"},
        ])
        items = self.db.get_action_items_by_meeting_id(meeting_id)
        return meeting_id, items[0]["id"]

    def test_list_and_update_status(self):
        meeting_id, item_id = self._create_meeting_with_item()
        self.login_as(self.user_id)

        res = self.client.get(f"/api/action_items/{meeting_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()["action_items"]), 1)

        res = self.client.post(f"/api/action_items/{item_id}/status", json={"status": "done"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.db.get_action_items_by_meeting_id(meeting_id)[0]["status"], "done")

    def test_invalid_status_returns_400(self):
        _, item_id = self._create_meeting_with_item()
        self.login_as(self.user_id)

        res = self.client.post(f"/api/action_items/{item_id}/status", json={"status": "weird"})

        self.assertEqual(res.status_code, 400)

    def test_other_user_cannot_access_items(self):
        meeting_id, item_id = self._create_meeting_with_item()
        self.login_as(self.other_id)

        self.assertEqual(self.client.get(f"/api/action_items/{meeting_id}").status_code, 403)
        res = self.client.post(f"/api/action_items/{item_id}/status", json={"status": "done"})
        self.assertEqual(res.status_code, 403)

    def test_unknown_item_returns_404(self):
        self.login_as(self.user_id)

        res = self.client.post("/api/action_items/99999999/status", json={"status": "done"})

        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()

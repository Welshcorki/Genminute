"""
관리자 스크립트 입력(/upload_script) 테스트

음성 파일 없이 화자 표기가 있는 텍스트를 회의로 등록하는 기능입니다.
벡터 DB 저장은 mock으로 대체합니다.

테스트 항목:
- STTManager.parse_script: 지원 형식별 파싱
- /upload_script: 저장 결과, 입력 검증, 권한
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_harness import AppRouteTestBase, app_module, SKIP_REASON

if app_module is not None:
    from services.stt_service import STTManager


@unittest.skipIf(app_module is None, SKIP_REASON)
class TestParseScript(unittest.TestCase):
    def test_numbered_speakers(self):
        segments = STTManager.parse_script("1: 안녕하세요\n2: 반갑습니다\n화자1: 시작하죠")

        self.assertEqual([s["speaker"] for s in segments], [1, 2, 1])
        self.assertEqual(segments[0]["text"], "안녕하세요")
        self.assertEqual([s["start_time"] for s in segments], [0.0, 5.0, 10.0])
        self.assertTrue(all(s["confidence"] == 1.0 for s in segments))

    def test_named_speakers_are_mapped_in_order_of_appearance(self):
        segments = STTManager.parse_script("홍길동: 첫 발언\n김철수: 둘째 발언\n홍길동: 셋째 발언")

        self.assertEqual([s["speaker"] for s in segments], [1, 2, 1])

    def test_bracket_format(self):
        segments = STTManager.parse_script("[1] 대괄호 숫자\n[화자2] 대괄호 화자\n[A] 대괄호 이름")

        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]["speaker"], 1)
        self.assertEqual(segments[1]["speaker"], 2)
        self.assertEqual(segments[2]["text"], "대괄호 이름")

    def test_blank_and_unlabelled_lines_are_skipped(self):
        segments = STTManager.parse_script("1: 유효한 줄\n\n화자 표기 없는 줄\n2: 또 유효한 줄")

        self.assertEqual([s["text"] for s in segments], ["유효한 줄", "또 유효한 줄"])

    def test_text_containing_colon_is_preserved(self):
        segments = STTManager.parse_script("1: 일정은 10:30 입니다")

        self.assertEqual(segments[0]["text"], "일정은 10:30 입니다")


class TestUploadScriptRoute(AppRouteTestBase):
    SCRIPT = "1: 안녕하세요. 회의를 시작하겠습니다.\n2: 네, 준비됐습니다.\n1: 첫 안건부터 보죠."

    def setUp(self):
        super().setUp()
        from database.vector_manager import vdb_manager
        patcher = mock.patch.object(vdb_manager, "add_meeting_as_chunk")
        self.mock_add_chunk = patcher.start()
        self.addCleanup(patcher.stop)

    def test_admin_uploads_script(self):
        self.login_as(self.admin_id)

        res = self.client.post("/upload_script", data={
            "title": "스크립트 회의", "script_text": self.SCRIPT, "meeting_date": "2026-03-04T14:30",
        })

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["segments_count"], 3)
        meeting_id = body["meeting_id"]
        self.assertEqual(body["redirect_url"], f"/notes/{meeting_id}")

        rows = self.db.get_meeting_by_id(meeting_id)
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["speaker_label"] for r in rows], ["1", "2", "1"])
        self.assertEqual(rows[0]["segment"], "안녕하세요. 회의를 시작하겠습니다.")
        self.assertEqual(rows[0]["title"], "스크립트 회의")
        self.assertEqual(rows[0]["meeting_date"], "2026-03-04 14:30:00")
        self.assertEqual(rows[0]["owner_id"], self.admin_id)

        # 벡터 DB에는 DB에서 다시 읽은 세그먼트 전체가 전달된다
        self.mock_add_chunk.assert_called_once()
        kwargs = self.mock_add_chunk.call_args.kwargs
        self.assertEqual(kwargs["meeting_id"], meeting_id)
        self.assertEqual(len(kwargs["segments"]), 3)

    def test_uploaded_script_is_readable_through_meeting_api(self):
        self.login_as(self.admin_id)
        meeting_id = self.client.post(
            "/upload_script", data={"title": "조회 확인", "script_text": self.SCRIPT},
        ).get_json()["meeting_id"]

        res = self.client.get(f"/api/meeting/{meeting_id}")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()["transcript"]), 3)

    def test_default_title(self):
        self.login_as(self.admin_id)

        body = self.client.post("/upload_script", data={"script_text": self.SCRIPT}).get_json()

        self.assertEqual(self.db.get_meeting_by_id(body["meeting_id"])[0]["title"], "스크립트 입력")

    def test_empty_script_returns_400(self):
        self.login_as(self.admin_id)

        res = self.client.post("/upload_script", data={"title": "t", "script_text": "   "})

        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()["success"])
        self.mock_add_chunk.assert_not_called()

    def test_script_without_speaker_labels_returns_400(self):
        self.login_as(self.admin_id)

        res = self.client.post("/upload_script", data={"script_text": "화자 표기가 없는 문장\n또 다른 문장"})

        self.assertEqual(res.status_code, 400)
        self.mock_add_chunk.assert_not_called()

    def test_invalid_date_returns_400(self):
        self.login_as(self.admin_id)

        res = self.client.post("/upload_script", data={"script_text": self.SCRIPT, "meeting_date": "어제"})

        self.assertEqual(res.status_code, 400)
        self.mock_add_chunk.assert_not_called()

    def test_non_admin_gets_403(self):
        self.login_as(self.user_id)

        res = self.client.post("/upload_script", data={"script_text": self.SCRIPT})

        self.assertEqual(res.status_code, 403)
        self.mock_add_chunk.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""
config.py 상수가 실제 코드에 연결되어 있는지 검증

청킹/검색 파라미터는 config.py 한 곳만 바꾸면 반영되어야 합니다.
(이전에는 같은 숫자가 코드에 하드코딩되어 config 값을 바꿔도 효과가 없었음)

벡터 DB와 LLM은 호출하지 않습니다 — 메서드를 가짜 self로 직접 호출합니다.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import config

SKIP_REASON = ""
try:
    from database.vector_manager import VectorDBManager
    from services.chat_service import ChatManager
except Exception as e:  # chromadb / google-genai 미설치 또는 환경 변수 미비
    SKIP_REASON = f"import 불가: {type(e).__name__}: {e}"
    VectorDBManager = None


def _segments(count: int, gap_seconds: float = 5.0) -> list:
    return [
        {"speaker_label": "1", "start_time": i * gap_seconds, "segment": "가" * 100}
        for i in range(count)
    ]


@unittest.skipIf(VectorDBManager is None, SKIP_REASON)
class TestChunkingConstants(unittest.TestCase):
    def test_defaults_match_config(self):
        defaults = VectorDBManager._create_smart_chunks.__defaults__
        self.assertEqual(defaults, (config.CHUNK_SIZE, config.TIME_GAP_THRESHOLD_SECONDS))

    def test_add_meeting_passes_config_values_to_chunker(self):
        fake_self = mock.MagicMock()
        fake_self._create_smart_chunks.return_value = []

        with mock.patch.object(config, "CHUNK_SIZE", 321), \
                mock.patch.object(config, "TIME_GAP_THRESHOLD_SECONDS", 7):
            VectorDBManager.add_meeting_as_chunk(
                fake_self, "m1", "제목", "2026-01-01", "a.wav", _segments(3),
            )

        fake_self._create_smart_chunks.assert_called_once()
        kwargs = fake_self._create_smart_chunks.call_args.kwargs
        self.assertEqual(kwargs["max_chunk_size"], 321)
        self.assertEqual(kwargs["time_gap_threshold"], 7)

    def test_chunk_size_limits_chunk_length(self):
        fake_self = mock.MagicMock()

        small = VectorDBManager._create_smart_chunks(fake_self, _segments(10), max_chunk_size=300)
        large = VectorDBManager._create_smart_chunks(fake_self, _segments(10), max_chunk_size=5000)

        self.assertGreater(len(small), len(large))

    def test_time_gap_splits_chunks(self):
        fake_self = mock.MagicMock()
        # 발화 간격 120초, 각 발화가 200자를 넘도록 구성
        segments = [
            {"speaker_label": "1", "start_time": i * 120.0, "segment": "가" * 250}
            for i in range(4)
        ]

        split = VectorDBManager._create_smart_chunks(
            fake_self, segments, max_chunk_size=100000, time_gap_threshold=60,
        )
        merged = VectorDBManager._create_smart_chunks(
            fake_self, segments, max_chunk_size=100000, time_gap_threshold=600,
        )

        self.assertGreater(len(split), len(merged))


@unittest.skipIf(VectorDBManager is None, SKIP_REASON)
class TestSearchConstants(unittest.TestCase):
    def _fake_chat_manager(self, docs_per_collection: int = 8) -> mock.Mock:
        fake_self = mock.Mock()
        fake_self._search_collection.return_value = [f"doc{i}" for i in range(docs_per_collection)]
        return fake_self

    def test_results_per_collection_follows_config(self):
        for limit in (1, 3, 5):
            with self.subTest(limit=limit), \
                    mock.patch.object(config, "SEARCH_RESULTS_PER_COLLECTION", limit):
                result = ChatManager.search_documents(self._fake_chat_manager(), "질문", meeting_id="m1")

                self.assertEqual(len(result["chunks"]), limit)
                self.assertEqual(len(result["subtopics"]), limit)
                self.assertEqual(result["total_count"], limit * 2)

    def test_search_multiplier_follows_config(self):
        fake_self = self._fake_chat_manager()

        with mock.patch.object(config, "SEARCH_MULTIPLIER", 4):
            ChatManager.search_documents(fake_self, "질문", accessible_meeting_ids=["a", "b", "c"])

        # _search_collection(db_type, query, k, filter_ids)
        k_values = {call.args[2] for call in fake_self._search_collection.call_args_list}
        self.assertEqual(k_values, {12})


if __name__ == "__main__":
    unittest.main()

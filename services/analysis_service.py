"""
회의 분석 서비스
화자별 발언 점유율 등 분석 기능을 제공합니다.

Repository 인터페이스에 의존합니다 (DIP).
"""

from collections import defaultdict
import logging
from typing import Optional, Dict

from database.repositories.interfaces import MeetingRepositoryInterface

logger = logging.getLogger(__name__)


class AnalysisService:
    """회의 데이터 분석 비즈니스 로직"""

    def __init__(self, connection):
        self._conn = connection

    def calculate_speaker_share(self, meeting_id: str) -> Optional[Dict]:
        """특정 회의의 화자별 발언 점유율을 계산합니다 (글자 수 기반)."""
        conn = self._conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT speaker_label, segment FROM meeting_dialogues WHERE meeting_id = ?",
                (meeting_id,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        speaker_text_lengths: dict[str, int] = defaultdict(int)
        total_length = 0

        for row in rows:
            text = row['segment'] or ""
            length = len(text)
            speaker_text_lengths[row['speaker_label']] += length
            total_length += length

        if total_length == 0:
            return None

        sorted_speakers = sorted(
            ((spk, (ln / total_length) * 100) for spk, ln in speaker_text_lengths.items()),
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "labels": [s[0] for s in sorted_speakers],
            "data": [round(s[1], 2) for s in sorted_speakers],
        }


# ── 하위 호환 모듈-레벨 함수 ──

def calculate_speaker_share(meeting_id):
    """하위 호환: 기존 `from services.analysis_service import calculate_speaker_share` 유지"""
    try:
        from config import config
        from database import get_db_manager
        db = get_db_manager()
        
        if config.DB_TYPE == 'supabase':
            from services.supabase_analysis_service import SupabaseAnalysisService
            service = SupabaseAnalysisService(db.connection)
        else:
            service = AnalysisService(db.connection)
            
        return service.calculate_speaker_share(meeting_id)
    except Exception as e:
        logger.error(f"Error in calculate_speaker_share: {e}")
        return None

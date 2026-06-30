"""
Supabase 회의 분석 서비스
"""
from collections import defaultdict
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class SupabaseAnalysisService:
    def __init__(self, connection):
        self._client = connection.client

    def calculate_speaker_share(self, meeting_id: str) -> Optional[Dict]:
        res = self._client.table('meeting_dialogues').select('speaker_label, segment').eq('meeting_id', meeting_id).execute()
        rows = res.data

        if not rows:
            return None

        speaker_text_lengths: dict[str, int] = defaultdict(int)
        total_length = 0

        for row in rows:
            text = row.get('segment') or ""
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

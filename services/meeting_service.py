"""
회의 관련 비즈니스 로직 서비스

Route 핸들러에서 비즈니스 로직을 분리합니다.
Repository 인터페이스에 의존합니다 (DIP).
"""
import logging
from typing import Optional, Dict, List

from database.repositories.interfaces import (
    MeetingRepositoryInterface,
    MinutesRepositoryInterface,
    MindmapRepositoryInterface,
)

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = ('.mp4', '.webm', '.mov', '.avi', '.mkv')


class MeetingService:
    """회의 CRUD + 조회 비즈니스 로직"""

    def __init__(
        self,
        meeting_repo: MeetingRepositoryInterface,
        minutes_repo: MinutesRepositoryInterface,
        mindmap_repo: MindmapRepositoryInterface,
    ):
        self._meeting = meeting_repo
        self._minutes = minutes_repo
        self._mindmap = mindmap_repo

    def get_meeting_detail(self, meeting_id: str) -> Optional[Dict]:
        """회의 상세 데이터를 조회합니다 (전사, 참여자, 화자 점유율 등)."""
        rows = self._meeting.get_meeting_by_id(meeting_id)
        if not rows:
            return None

        transcript = self._build_transcript(rows)
        audio_file = rows[0]['audio_file']

        return {
            "meeting_id": meeting_id,
            "title": rows[0]['title'],
            "meeting_date": rows[0]['meeting_date'],
            "participants": sorted({t['speaker_label'] for t in transcript if t.get('speaker_label')}),
            "audio_url": f"/uploads/{audio_file}",
            "is_video": any(audio_file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS) if audio_file else False,
            "transcript": transcript,
        }

    def get_user_stats(self, user_id: int, is_admin: bool) -> Dict:
        return self._meeting.get_user_stats(user_id, is_admin)

    def update_title(self, meeting_id: str, new_title: str) -> Dict:
        return self._meeting.update_meeting_title(meeting_id, new_title)

    def update_date(self, meeting_id: str, new_date: str) -> Dict:
        return self._meeting.update_meeting_date(meeting_id, new_date)

    def get_mindmap(self, meeting_id: str) -> Optional[str]:
        return self._mindmap.get_mindmap_by_meeting_id(meeting_id)

    def get_minutes(self, meeting_id: str) -> Optional[Dict]:
        return self._minutes.get_minutes_by_meeting_id(meeting_id)

    @staticmethod
    def _build_transcript(rows) -> List[Dict]:
        """DB Row를 프론트엔드 친화적 transcript 리스트로 변환합니다."""
        transcript = []
        for i, row in enumerate(rows):
            seg = dict(row)
            if 'segment' in seg:
                seg['text'] = seg.pop('segment', '')

            if i < len(rows) - 1:
                next_row = dict(rows[i + 1])
                seg['end_time'] = next_row.get('start_time', seg.get('start_time', 0) + 5.0)
            else:
                seg['end_time'] = seg.get('start_time', 0) + 5.0

            transcript.append(seg)
        return transcript

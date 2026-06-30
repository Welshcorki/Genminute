"""
SupabaseManager - Facade
기존 DatabaseManager와 호환되는 인터페이스를 제공하면서, 내부적으로 Supabase Repository를 호출합니다.
"""
import logging
from typing import Optional, Dict, List

from database.repositories.supabase.connection import SupabaseConnection
from database.repositories.supabase.meeting_repo import SupabaseMeetingRepository
from database.repositories.supabase.minutes_repo import SupabaseMinutesRepository
from database.repositories.supabase.mindmap_repo import SupabaseMindmapRepository
from database.repositories.supabase.action_item_repo import SupabaseActionItemRepository
from database.repositories.supabase.user_repo import SupabaseUserRepository

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Supabase 데이터베이스 관리 (Singleton + Facade)"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connection = SupabaseConnection()
        self._meeting_repo = SupabaseMeetingRepository(self._connection)
        self._minutes_repo = SupabaseMinutesRepository(self._connection)
        self._mindmap_repo = SupabaseMindmapRepository(self._connection)
        self._action_item_repo = SupabaseActionItemRepository(self._connection)
        self._user_repo = SupabaseUserRepository(self._connection)

        self._initialized = True
        logger.info("✅ SupabaseManager 초기화 완료")

    # ── Repository 접근자 ──
    @property
    def meeting_repo(self) -> SupabaseMeetingRepository:
        return self._meeting_repo

    @property
    def minutes_repo(self) -> SupabaseMinutesRepository:
        return self._minutes_repo

    @property
    def mindmap_repo(self) -> SupabaseMindmapRepository:
        return self._mindmap_repo

    @property
    def action_item_repo(self) -> SupabaseActionItemRepository:
        return self._action_item_repo

    @property
    def user_repo(self) -> SupabaseUserRepository:
        return self._user_repo

    @property
    def connection(self) -> SupabaseConnection:
        return self._connection

    # ── Facade 메서드 (하위 호환) ──
    def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None, owner_id=None) -> str:
        return self._meeting_repo.save_stt_to_db(segments, audio_filename, title, meeting_date, owner_id)

    def get_meeting_by_id(self, meeting_id) -> list:
        return self._meeting_repo.get_meeting_by_id(meeting_id)

    def get_all_meetings(self) -> list:
        return self._meeting_repo.get_all_meetings()

    def get_segments_by_meeting_id(self, meeting_id) -> List[Dict]:
        return self._meeting_repo.get_segments_by_meeting_id(meeting_id)

    def get_audio_file_by_meeting_id(self, meeting_id) -> Optional[str]:
        return self._meeting_repo.get_audio_file_by_meeting_id(meeting_id)

    def update_meeting_title(self, meeting_id, new_title) -> Dict:
        return self._meeting_repo.update_meeting_title(meeting_id, new_title)

    def update_meeting_date(self, meeting_id, new_date) -> Dict:
        return self._meeting_repo.update_meeting_date(meeting_id, new_date)

    def delete_meeting_data(self, meeting_id=None, audio_file=None, title=None) -> int:
        return self._meeting_repo.delete_meeting_data(meeting_id, audio_file, title)

    def delete_meeting_by_id(self, meeting_id) -> Dict:
        return self._meeting_repo.delete_meeting_by_id(meeting_id)

    def get_user_stats(self, user_id: int, is_admin: bool) -> Dict:
        return self._meeting_repo.get_user_stats(user_id, is_admin)

    def save_minutes(self, meeting_id, title, meeting_date, minutes_content, owner_id=None) -> bool:
        return self._minutes_repo.save_minutes(meeting_id, title, meeting_date, minutes_content, owner_id)

    def get_minutes_by_meeting_id(self, meeting_id) -> Optional[Dict]:
        return self._minutes_repo.get_minutes_by_meeting_id(meeting_id)

    def save_mindmap(self, meeting_id, mindmap_content) -> bool:
        return self._mindmap_repo.save_mindmap(meeting_id, mindmap_content)

    def get_mindmap_by_meeting_id(self, meeting_id) -> Optional[str]:
        return self._mindmap_repo.get_mindmap_by_meeting_id(meeting_id)

    def delete_mindmap_by_meeting_id(self, meeting_id) -> int:
        return self._mindmap_repo.delete_mindmap_by_meeting_id(meeting_id)

    def update_user_google_credentials(self, user_id: int, credentials_json: str) -> None:
        self._user_repo.update_user_google_credentials(user_id, credentials_json)

    def get_user_google_credentials(self, user_id: int) -> Optional[str]:
        return self._user_repo.get_user_google_credentials(user_id)

    def save_action_items(self, meeting_id: str, items: list) -> None:
        self._action_item_repo.save_action_items(meeting_id, items)

    def get_action_items_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        return self._action_item_repo.get_action_items_by_meeting_id(meeting_id)

    def update_action_item_status(self, item_id: int, status: str) -> bool:
        return self._action_item_repo.update_action_item_status(item_id, status)

    def get_action_item_meeting_id(self, item_id: int) -> Optional[str]:
        return self._action_item_repo.get_action_item_meeting_id(item_id)

    def delete_action_items_by_meeting_id(self, meeting_id: str) -> int:
        return self._action_item_repo.delete_action_items_by_meeting_id(meeting_id)

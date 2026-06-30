"""
DatabaseManager - Facade (하위 호환용)

기존 코드(`db.save_stt_to_db(...)` 등)를 깨뜨리지 않으면서
내부적으로 Repository 구현체에 위임합니다.

새로 작성하는 코드에서는 Repository 인터페이스에 직접 의존하세요.
"""
import logging
from typing import Optional, Dict, List

from database.repositories.sqlite.connection import SqliteConnection
from database.repositories.sqlite.meeting_repo import SqliteMeetingRepository
from database.repositories.sqlite.minutes_repo import SqliteMinutesRepository
from database.repositories.sqlite.mindmap_repo import SqliteMindmapRepository
from database.repositories.sqlite.action_item_repo import SqliteActionItemRepository
from database.repositories.sqlite.user_repo import SqliteUserRepository

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite 데이터베이스 관리 (Singleton + Facade)

    기존 호출 코드와의 하위 호환성을 위해 유지됩니다.
    내부적으로 각 Repository 구현체에 위임합니다.
    """
    _instance = None
    _initialized = False

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path=None):
        if self._initialized:
            return

        if db_path is None:
            raise ValueError("DatabaseManager 최초 생성 시 db_path가 필요합니다.")

        self.db_path = db_path
        self._initialized = True

        self._connection = SqliteConnection(db_path)
        self._meeting_repo = SqliteMeetingRepository(self._connection)
        self._minutes_repo = SqliteMinutesRepository(self._connection)
        self._mindmap_repo = SqliteMindmapRepository(self._connection)
        self._action_item_repo = SqliteActionItemRepository(self._connection)
        self._user_repo = SqliteUserRepository(self._connection)

        self._connection.initialize_tables()
        logger.info(f"DatabaseManager 초기화: {db_path}")

    # ── Repository 접근자 (DI를 통해 Service에서 사용) ──

    @property
    def meeting_repo(self) -> SqliteMeetingRepository:
        return self._meeting_repo

    @property
    def minutes_repo(self) -> SqliteMinutesRepository:
        return self._minutes_repo

    @property
    def mindmap_repo(self) -> SqliteMindmapRepository:
        return self._mindmap_repo

    @property
    def action_item_repo(self) -> SqliteActionItemRepository:
        return self._action_item_repo

    @property
    def user_repo(self) -> SqliteUserRepository:
        return self._user_repo

    @property
    def connection(self) -> SqliteConnection:
        return self._connection

    # ── 하위 호환 Facade 메서드 (기존 코드에서 db.xxx() 형태로 사용) ──

    def _get_connection(self):
        """하위 호환: 기존 코드에서 직접 커넥션이 필요한 경우"""
        return self._connection.get_connection()

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

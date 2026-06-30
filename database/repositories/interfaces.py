"""
Repository 인터페이스 정의 (ABC)

Service 계층은 이 인터페이스에만 의존합니다.
구체적인 DB 구현(SQLite, PostgreSQL 등)은 이 인터페이스를 구현합니다.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List


class MeetingRepositoryInterface(ABC):
    """meeting_dialogues 테이블 CRUD"""

    @abstractmethod
    def save_stt_to_db(
        self,
        segments: list,
        audio_filename: str,
        title: str,
        meeting_date: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> str:
        """음성 인식 결과를 저장하고 생성된 meeting_id를 반환합니다."""
        ...

    @abstractmethod
    def get_meeting_by_id(self, meeting_id: str) -> list:
        """meeting_id로 모든 세그먼트를 시간순으로 조회합니다."""
        ...

    @abstractmethod
    def get_all_meetings(self) -> list:
        """모든 회의 목록을 조회합니다 (meeting_id, title, date, audio_file)."""
        ...

    @abstractmethod
    def get_segments_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        """meeting_id로 세그먼트를 dict 리스트로 반환합니다."""
        ...

    @abstractmethod
    def get_audio_file_by_meeting_id(self, meeting_id: str) -> Optional[str]:
        """meeting_id로 오디오 파일명을 조회합니다."""
        ...

    @abstractmethod
    def update_meeting_title(self, meeting_id: str, new_title: str) -> Dict:
        """회의 제목을 업데이트합니다 (SQLite + ChromaDB)."""
        ...

    @abstractmethod
    def update_meeting_date(self, meeting_id: str, new_date: str) -> Dict:
        """회의 날짜를 업데이트합니다 (SQLite + ChromaDB)."""
        ...

    @abstractmethod
    def delete_meeting_data(
        self,
        meeting_id: Optional[str] = None,
        audio_file: Optional[str] = None,
        title: Optional[str] = None,
    ) -> int:
        """조건에 따라 meeting_dialogues 데이터를 삭제합니다."""
        ...

    @abstractmethod
    def delete_meeting_by_id(self, meeting_id: str) -> Dict:
        """meeting_id로 모든 관련 테이블 데이터를 삭제합니다."""
        ...

    @abstractmethod
    def get_user_stats(self, user_id: int, is_admin: bool) -> Dict:
        """사용자 통계를 조회합니다 (이번 달 노트 수, 총 녹음 시간)."""
        ...


class MinutesRepositoryInterface(ABC):
    """meeting_minutes 테이블 CRUD"""

    @abstractmethod
    def save_minutes(
        self,
        meeting_id: str,
        title: str,
        meeting_date: str,
        minutes_content: str,
        owner_id: Optional[int] = None,
    ) -> bool:
        """회의록을 저장(또는 업데이트)합니다."""
        ...

    @abstractmethod
    def get_minutes_by_meeting_id(self, meeting_id: str) -> Optional[Dict]:
        """meeting_id로 회의록을 조회합니다."""
        ...


class MindmapRepositoryInterface(ABC):
    """meeting_mindmap 테이블 CRUD"""

    @abstractmethod
    def save_mindmap(self, meeting_id: str, mindmap_content: str) -> bool:
        """마인드맵을 저장(또는 업데이트)합니다."""
        ...

    @abstractmethod
    def get_mindmap_by_meeting_id(self, meeting_id: str) -> Optional[str]:
        """meeting_id로 마인드맵 내용을 조회합니다."""
        ...

    @abstractmethod
    def delete_mindmap_by_meeting_id(self, meeting_id: str) -> int:
        """meeting_id로 마인드맵을 삭제합니다."""
        ...


class ActionItemRepositoryInterface(ABC):
    """meeting_action_items 테이블 CRUD"""

    @abstractmethod
    def save_action_items(self, meeting_id: str, items: List[Dict]) -> None:
        """Action Item 목록을 저장합니다."""
        ...

    @abstractmethod
    def get_action_items_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        """meeting_id로 Action Item 목록을 조회합니다."""
        ...

    @abstractmethod
    def update_action_item_status(self, item_id: int, status: str) -> bool:
        """Action Item 상태를 업데이트합니다."""
        ...

    @abstractmethod
    def get_action_item_meeting_id(self, item_id: int) -> Optional[str]:
        """Action Item ID로 meeting_id를 조회합니다."""
        ...

    @abstractmethod
    def delete_action_items_by_meeting_id(self, meeting_id: str) -> int:
        """meeting_id로 관련 Action Item을 모두 삭제합니다."""
        ...


class UserRepositoryInterface(ABC):
    """users, meeting_shares 테이블 CRUD"""

    @abstractmethod
    def update_user_google_credentials(self, user_id: int, credentials_json: str) -> None:
        """사용자의 Google OAuth 인증 정보를 저장합니다."""
        ...

    @abstractmethod
    def get_user_google_credentials(self, user_id: int) -> Optional[str]:
        """사용자의 Google OAuth 인증 정보를 조회합니다."""
        ...

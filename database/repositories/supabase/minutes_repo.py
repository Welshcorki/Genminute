from typing import Optional, Dict
from database.repositories.interfaces import MinutesRepositoryInterface
from database.repositories.supabase.connection import SupabaseConnection

class SupabaseMinutesRepository(MinutesRepositoryInterface):
    def __init__(self, connection: SupabaseConnection):
        self._client = connection.client

    def save_minutes(
        self,
        meeting_id: str,
        title: str,
        meeting_date: str,
        minutes_content: str,
        owner_id: Optional[int] = None,
    ) -> bool:
        # Check if exists
        existing = self.get_minutes_by_meeting_id(meeting_id)
        
        data = {
            'meeting_id': meeting_id,
            'title': title,
            'meeting_date': meeting_date,
            'minutes_content': minutes_content,
            'owner_id': owner_id
        }
        
        if existing:
            self._client.table('meeting_minutes').update(data).eq('meeting_id', meeting_id).execute()
        else:
            self._client.table('meeting_minutes').insert(data).execute()
            
        return True

    def get_minutes_by_meeting_id(self, meeting_id: str) -> Optional[Dict]:
        response = self._client.table('meeting_minutes').select('*').eq('meeting_id', meeting_id).execute()
        return response.data[0] if response.data else None

from typing import Optional
from database.repositories.interfaces import MindmapRepositoryInterface
from database.repositories.supabase.connection import SupabaseConnection

class SupabaseMindmapRepository(MindmapRepositoryInterface):
    def __init__(self, connection: SupabaseConnection):
        self._client = connection.client

    def save_mindmap(self, meeting_id: str, mindmap_content: str) -> bool:
        existing = self.get_mindmap_by_meeting_id(meeting_id)
        
        data = {
            'meeting_id': meeting_id,
            'mindmap_content': mindmap_content
        }
        
        if existing:
            self._client.table('meeting_mindmap').update(data).eq('meeting_id', meeting_id).execute()
        else:
            self._client.table('meeting_mindmap').insert(data).execute()
            
        return True

    def get_mindmap_by_meeting_id(self, meeting_id: str) -> Optional[str]:
        response = self._client.table('meeting_mindmap').select('mindmap_content').eq('meeting_id', meeting_id).execute()
        return response.data[0]['mindmap_content'] if response.data else None

    def delete_mindmap_by_meeting_id(self, meeting_id: str) -> int:
        response = self._client.table('meeting_mindmap').delete().eq('meeting_id', meeting_id).execute()
        return len(response.data)

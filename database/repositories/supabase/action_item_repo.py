from typing import Optional, Dict, List
from database.repositories.interfaces import ActionItemRepositoryInterface
from database.repositories.supabase.connection import SupabaseConnection

class SupabaseActionItemRepository(ActionItemRepositoryInterface):
    def __init__(self, connection: SupabaseConnection):
        self._client = connection.client

    def save_action_items(self, meeting_id: str, items: List[Dict]) -> None:
        insert_data = []
        for item in items:
            insert_data.append({
                'meeting_id': meeting_id,
                'content': item.get('content', ''),
                'due_date': item.get('due_date'),
                'status': item.get('status', 'pending'),
                'tool_call_id': item.get('tool_call_id'),
                'calendar_event_id': item.get('calendar_event_id')
            })
            
        if insert_data:
            self._client.table('meeting_action_items').insert(insert_data).execute()

    def get_action_items_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        response = self._client.table('meeting_action_items').select('*').eq('meeting_id', meeting_id).order('created_at').execute()
        return response.data

    def update_action_item_status(self, item_id: int, status: str) -> bool:
        response = self._client.table('meeting_action_items').update({'status': status}).eq('id', item_id).execute()
        return len(response.data) > 0

    def get_action_item_meeting_id(self, item_id: int) -> Optional[str]:
        response = self._client.table('meeting_action_items').select('meeting_id').eq('id', item_id).execute()
        return response.data[0]['meeting_id'] if response.data else None

    def delete_action_items_by_meeting_id(self, meeting_id: str) -> int:
        response = self._client.table('meeting_action_items').delete().eq('meeting_id', meeting_id).execute()
        return len(response.data)

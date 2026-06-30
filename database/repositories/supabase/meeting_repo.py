from typing import Optional, Dict, List
from database.repositories.interfaces import MeetingRepositoryInterface
from database.repositories.supabase.connection import SupabaseConnection
from database.vector_manager import vdb_manager

class SupabaseMeetingRepository(MeetingRepositoryInterface):
    def __init__(self, connection: SupabaseConnection):
        self._client = connection.client

    def save_stt_to_db(
        self,
        segments: list,
        audio_filename: str,
        title: str,
        meeting_date: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> str:
        import uuid
        from datetime import datetime
        meeting_id = str(uuid.uuid4())
        date_str = meeting_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_data = []
        for seg in segments:
            insert_data.append({
                'meeting_id': meeting_id,
                'meeting_date': date_str,
                'speaker_label': seg.get('speaker', 'Speaker'),
                'start_time': seg.get('start', 0.0),
                'segment': seg.get('text', ''),
                'confidence': 1.0,
                'audio_file': audio_filename,
                'title': title,
                'owner_id': owner_id
            })

        if insert_data:
            self._client.table('meeting_dialogues').insert(insert_data).execute()
        return meeting_id

    def get_meeting_by_id(self, meeting_id: str) -> list:
        response = self._client.table('meeting_dialogues').select('*').eq('meeting_id', meeting_id).order('start_time').execute()
        return response.data

    def get_all_meetings(self) -> list:
        # Group by meeting_id in Supabase requires a view or custom query. 
        # Alternatively, fetch distinct or use a subquery. 
        # For simplicity, we fetch all and group in memory (or use an RPC).
        response = self._client.table('meeting_dialogues').select('meeting_id, title, meeting_date, audio_file').execute()
        meetings = {}
        for row in response.data:
            if row['meeting_id'] not in meetings:
                meetings[row['meeting_id']] = row
        return list(meetings.values())

    def get_segments_by_meeting_id(self, meeting_id: str) -> List[Dict]:
        return self.get_meeting_by_id(meeting_id)

    def get_audio_file_by_meeting_id(self, meeting_id: str) -> Optional[str]:
        response = self._client.table('meeting_dialogues').select('audio_file').eq('meeting_id', meeting_id).limit(1).execute()
        return response.data[0]['audio_file'] if response.data else None

    def update_meeting_title(self, meeting_id: str, new_title: str) -> Dict:
        self._client.table('meeting_dialogues').update({'title': new_title}).eq('meeting_id', meeting_id).execute()
        # ChromaDB update
        vdb_manager.update_metadata(meeting_id, {'title': new_title})
        return {"success": True, "message": "제목이 업데이트되었습니다."}

    def update_meeting_date(self, meeting_id: str, new_date: str) -> Dict:
        self._client.table('meeting_dialogues').update({'meeting_date': new_date}).eq('meeting_id', meeting_id).execute()
        # ChromaDB update
        vdb_manager.update_metadata(meeting_id, {'meeting_date': new_date})
        return {"success": True, "message": "날짜가 업데이트되었습니다."}

    def delete_meeting_data(self, meeting_id: Optional[str] = None, audio_file: Optional[str] = None, title: Optional[str] = None) -> int:
        query = self._client.table('meeting_dialogues').delete()
        if meeting_id: query = query.eq('meeting_id', meeting_id)
        if audio_file: query = query.eq('audio_file', audio_file)
        if title: query = query.eq('title', title)
        res = query.execute()
        return len(res.data)

    def delete_meeting_by_id(self, meeting_id: str) -> Dict:
        self._client.table('meeting_dialogues').delete().eq('meeting_id', meeting_id).execute()
        self._client.table('meeting_minutes').delete().eq('meeting_id', meeting_id).execute()
        self._client.table('meeting_mindmap').delete().eq('meeting_id', meeting_id).execute()
        self._client.table('meeting_action_items').delete().eq('meeting_id', meeting_id).execute()
        self._client.table('meeting_shares').delete().eq('meeting_id', meeting_id).execute()
        
        # ChromaDB
        vdb_manager.delete_from_collection('all', meeting_id=meeting_id)
        return {"success": True, "message": "회의가 삭제되었습니다."}

    def get_user_stats(self, user_id: int, is_admin: bool) -> Dict:
        from datetime import datetime
        current_month = datetime.now().strftime("%Y-%m")
        
        # Get total meetings count
        query = self._client.table('meeting_dialogues').select('meeting_id')
        if not is_admin:
            query = query.eq('owner_id', user_id)
        
        res = query.execute()
        meeting_ids = set(r['meeting_id'] for r in res.data)
        total_meetings = len(meeting_ids)
        
        # Calculate monthly meetings
        month_res = self._client.table('meeting_dialogues').select('meeting_id').like('meeting_date', f'{current_month}%')
        if not is_admin:
            month_res = month_res.eq('owner_id', user_id)
        month_ids = set(r['meeting_id'] for r in month_res.execute().data)
        notes_this_month = len(month_ids)
        
        # We don't have exact duration easily without audio files, fallback to default for now
        total_duration = total_meetings * 30  # placeholder
        
        return {
            "total_meetings": total_meetings,
            "notes_this_month": notes_this_month,
            "total_duration": total_duration,
            "total_audio_length": 0
        }

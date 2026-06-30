"""
Supabase 사용자 관리 서비스
- users 테이블 CRUD
- 권한 확인 (admin/user)
- 공유 권한 관리
"""

import logging
from typing import Optional, Dict, List
from config import config

logger = logging.getLogger(__name__)

class SupabaseUserService:
    """사용자/권한/공유 관련 비즈니스 로직 (Supabase 구현)"""

    def __init__(self, connection):
        self._client = connection.client

    def get_or_create_user(
        self,
        google_id: str,
        email: str,
        name: str = None,
        profile_picture: str = None,
    ) -> Dict:
        # Check by google_id
        res = self._client.table('users').select('*').eq('google_id', google_id).execute()
        if res.data:
            user = res.data[0]
            self._client.table('users').update({'name': name, 'profile_picture': profile_picture}).eq('id', user['id']).execute()
            user['name'] = name
            user['profile_picture'] = profile_picture
            return user

        # Check by email
        res = self._client.table('users').select('*').eq('email', email).execute()
        if res.data:
            user = res.data[0]
            self._client.table('users').update({
                'google_id': google_id, 
                'name': name, 
                'profile_picture': profile_picture
            }).eq('id', user['id']).execute()
            logger.info(f"기존 사용자 업데이트: {email}")
            user['google_id'] = google_id
            user['name'] = name
            user['profile_picture'] = profile_picture
            return user

        # Create new user
        admin_emails = [e.strip() for e in config.ADMIN_EMAILS if e.strip()]
        role = 'admin' if email in admin_emails else 'user'

        data = {
            'google_id': google_id,
            'email': email,
            'name': name,
            'profile_picture': profile_picture,
            'role': role
        }
        res = self._client.table('users').insert(data).execute()
        logger.info(f"신규 사용자 생성: {email} (role: {role})")
        return res.data[0]

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        res = self._client.table('users').select('*').eq('id', user_id).execute()
        return res.data[0] if res.data else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        res = self._client.table('users').select('*').eq('email', email).execute()
        return res.data[0] if res.data else None

    def is_admin(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        return bool(user and user.get('role') == 'admin')

    def can_access_meeting(self, user_id: int, meeting_id: str) -> bool:
        if self.is_admin(user_id):
            return True

        # Check ownership
        res = self._client.table('meeting_dialogues').select('owner_id').eq('meeting_id', meeting_id).limit(1).execute()
        if res.data and res.data[0].get('owner_id') == user_id:
            return True

        # Check sharing
        res = self._client.table('meeting_shares').select('id').eq('meeting_id', meeting_id).eq('shared_with_user_id', user_id).execute()
        return len(res.data) > 0

    def can_edit_meeting(self, user_id: int, meeting_id: str) -> bool:
        if self.is_admin(user_id):
            return True
        res = self._client.table('meeting_dialogues').select('owner_id').eq('meeting_id', meeting_id).limit(1).execute()
        return bool(res.data and res.data[0].get('owner_id') == user_id)

    def get_user_meetings(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 10,
        search_term: str = None,
        start_date: str = None,
        end_date: str = None,
        sort_by: str = 'date_desc',
    ) -> List[Dict]:
        # Using Supabase directly for complex grouping and joining is tricky. 
        # In a real app, an RPC (Stored Procedure) is recommended. 
        # For simplicity, we fetch all owned/accessible meetings and filter in Python.
        
        is_admin = self.is_admin(user_id)
        
        # Get meetings
        query = self._client.table('meeting_dialogues').select('meeting_id, title, meeting_date, audio_file, owner_id')
        if not is_admin:
            query = query.eq('owner_id', user_id)
            
        if start_date:
            query = query.gte('meeting_date', start_date)
        if end_date:
            query = query.lte('meeting_date', end_date)
            
        res = query.execute()
        meetings_map = {}
        for row in res.data:
            mid = row['meeting_id']
            if mid not in meetings_map or row['meeting_date'] > meetings_map[mid]['date']:
                meetings_map[mid] = {
                    'meeting_id': mid,
                    'title': row['title'],
                    'date': row['meeting_date'],
                    'audio_file': row['audio_file'],
                    'owner_id': row['owner_id']
                }
                
        meetings = list(meetings_map.values())
        
        # Join with minutes for summary and search
        if meetings:
            mids = [m['meeting_id'] for m in meetings]
            minutes_res = self._client.table('meeting_minutes').select('meeting_id, minutes_content').in_('meeting_id', mids).execute()
            summary_map = {m['meeting_id']: m['minutes_content'] for m in minutes_res.data}
            
            for m in meetings:
                m['summary'] = summary_map.get(m['meeting_id'])
                
        # Filter by search_term
        if search_term:
            term = search_term.lower()
            meetings = [m for m in meetings if (term in (m['title'] or '').lower()) or (term in (m['summary'] or '').lower())]
            
        # Sort
        if sort_by == 'date_desc':
            meetings.sort(key=lambda x: x['date'], reverse=True)
        elif sort_by == 'date_asc':
            meetings.sort(key=lambda x: x['date'])
        elif sort_by == 'title_asc':
            meetings.sort(key=lambda x: x['title'] or '')
        elif sort_by == 'title_desc':
            meetings.sort(key=lambda x: x['title'] or '', reverse=True)
            
        # Pagination
        offset = (page - 1) * per_page
        return meetings[offset:offset+per_page]

    def get_user_meetings_count(
        self,
        user_id: int,
        search_term: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> int:
        # Re-use the same logic as get_user_meetings to get the count
        all_meetings = self.get_user_meetings(user_id, page=1, per_page=999999, search_term=search_term, start_date=start_date, end_date=end_date)
        return len(all_meetings)

    def get_shared_meetings(self, user_id: int) -> List[Dict]:
        res = self._client.table('meeting_shares').select('meeting_id').eq('shared_with_user_id', user_id).execute()
        mids = [r['meeting_id'] for r in res.data]
        if not mids:
            return []
            
        dialogues = self._client.table('meeting_dialogues').select('meeting_id, title, meeting_date, audio_file, owner_id').in_('meeting_id', mids).execute()
        meetings_map = {}
        for row in dialogues.data:
            mid = row['meeting_id']
            if mid not in meetings_map or row['meeting_date'] > meetings_map[mid]['date']:
                meetings_map[mid] = {
                    'meeting_id': mid,
                    'title': row['title'],
                    'date': row['meeting_date'],
                    'audio_file': row['audio_file'],
                    'owner_id': row['owner_id']
                }
                
        meetings = list(meetings_map.values())
        if meetings:
            minutes_res = self._client.table('meeting_minutes').select('meeting_id, minutes_content').in_('meeting_id', mids).execute()
            summary_map = {m['meeting_id']: m['minutes_content'] for m in minutes_res.data}
            for m in meetings:
                m['summary'] = summary_map.get(m['meeting_id'])
                
        meetings.sort(key=lambda x: x['date'], reverse=True)
        return meetings

    def share_meeting(self, meeting_id: str, owner_id: int, shared_with_email: str) -> Dict:
        shared_user = self.get_user_by_email(shared_with_email)
        if not shared_user:
            return {'success': False, 'message': '해당 이메일의 사용자를 찾을 수 없습니다.'}
        if shared_user['id'] == owner_id:
            return {'success': False, 'message': '본인에게는 공유할 수 없습니다.'}

        res = self._client.table('meeting_dialogues').select('owner_id').eq('meeting_id', meeting_id).limit(1).execute()
        if not res.data:
            return {'success': False, 'message': '회의를 찾을 수 없습니다.'}
        if res.data[0]['owner_id'] != owner_id:
            return {'success': False, 'message': '회의 소유자만 공유할 수 있습니다.'}

        share_check = self._client.table('meeting_shares').select('id').eq('meeting_id', meeting_id).eq('shared_with_user_id', shared_user['id']).execute()
        if share_check.data:
            return {'success': False, 'message': '이미 공유된 사용자입니다.'}

        self._client.table('meeting_shares').insert({
            'meeting_id': meeting_id,
            'owner_id': owner_id,
            'shared_with_user_id': shared_user['id'],
            'permission': 'read'
        }).execute()
        
        logger.info(f"회의 공유 완료: {meeting_id} → {shared_with_email}")
        return {'success': True, 'message': f'{shared_with_email}에게 공유되었습니다.'}

    def get_shared_users(self, meeting_id: str) -> List[Dict]:
        shares = self._client.table('meeting_shares').select('*').eq('meeting_id', meeting_id).order('created_at', desc=True).execute()
        if not shares.data:
            return []
            
        user_ids = [s['shared_with_user_id'] for s in shares.data]
        users = self._client.table('users').select('id, email, name, profile_picture').in_('id', user_ids).execute()
        user_map = {u['id']: u for u in users.data}
        
        result = []
        for s in shares.data:
            u = user_map.get(s['shared_with_user_id'])
            if u:
                result.append({
                    'id': u['id'],
                    'email': u['email'],
                    'name': u['name'],
                    'profile_picture': u['profile_picture'],
                    'permission': s['permission'],
                    'shared_at': s['created_at']
                })
        return result

    def remove_share(self, meeting_id: str, owner_id: int, shared_user_id: int) -> Dict:
        res = self._client.table('meeting_dialogues').select('owner_id').eq('meeting_id', meeting_id).limit(1).execute()
        if not res.data or res.data[0]['owner_id'] != owner_id:
            return {'success': False, 'message': '회의 소유자만 공유를 제거할 수 있습니다.'}

        del_res = self._client.table('meeting_shares').delete().eq('meeting_id', meeting_id).eq('owner_id', owner_id).eq('shared_with_user_id', shared_user_id).execute()
        if del_res.data:
            return {'success': True, 'message': '공유가 제거되었습니다.'}
        return {'success': False, 'message': '공유 정보를 찾을 수 없습니다.'}

    def get_user_accessible_meeting_ids(self, user_id: int) -> List[str]:
        if self.is_admin(user_id):
            res = self._client.table('meeting_dialogues').select('meeting_id').execute()
            return list(set(r['meeting_id'] for r in res.data))
            
        res_owned = self._client.table('meeting_dialogues').select('meeting_id').eq('owner_id', user_id).execute()
        res_shared = self._client.table('meeting_shares').select('meeting_id').eq('shared_with_user_id', user_id).execute()
        
        mids = set(r['meeting_id'] for r in res_owned.data)
        mids.update(r['meeting_id'] for r in res_shared.data)
        return list(mids)

"""
회의 공유 관련 라우트 (Thin Controller)
노트 공유, 공유 사용자 조회, 공유 해제
"""
from flask import Blueprint, jsonify, request, session
import logging

from utils.decorators import login_required, api_error_handler
from services.user_service import (
    can_access_meeting,
    can_edit_meeting,
    get_shared_meetings,
    share_meeting,
    get_shared_users,
    remove_share,
)

logger = logging.getLogger(__name__)

meetings_share_bp = Blueprint('meetings_share', __name__)


@meetings_share_bp.route("/api/share/<string:meeting_id>", methods=["POST"])
@login_required
@api_error_handler
def share_meeting_route(meeting_id):
    """노트 공유 (이메일 기반)"""
    user_id = session['user_id']

    if not can_edit_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "공유 권한이 없습니다. (소유자만 공유 가능)"}), 403

    data = request.get_json()
    target_email = data.get('email')
    if not target_email:
        return jsonify({"success": False, "error": "이메일을 입력해주세요."}), 400

    result = share_meeting(meeting_id, user_id, target_email)
    return jsonify(result)


@meetings_share_bp.route("/api/shared_users/<string:meeting_id>")
@login_required
@api_error_handler
def get_shared_users_route(meeting_id):
    """공유받은 사용자 목록 조회"""
    user_id = session['user_id']

    if not can_access_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

    shared_users = get_shared_users(meeting_id)
    return jsonify({"success": True, "shared_users": shared_users})


@meetings_share_bp.route("/api/unshare/<string:meeting_id>/<int:target_user_id>", methods=["POST"])
@login_required
@api_error_handler
def unshare_meeting_route(meeting_id, target_user_id):
    """공유 해제"""
    user_id = session['user_id']

    if not can_edit_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "공유 해제 권한이 없습니다. (소유자만 가능)"}), 403

    result = remove_share(meeting_id, user_id, target_user_id)
    return jsonify(result)


@meetings_share_bp.route("/api/shared-notes", methods=["GET"])
@login_required
@api_error_handler
def get_shared_notes_api():
    """공유받은 노트 목록 조회 (JSON API)"""
    user_id = session['user_id']
    shared_meetings = get_shared_meetings(user_id)

    meetings = [
        {
            'meeting_id': m.get('meeting_id'),
            'title': m.get('title'),
            'date': m.get('date') or m.get('meeting_date'),
            'audio_file': m.get('audio_file'),
            'summary': m.get('summary'),
        }
        for m in shared_meetings
    ]

    return jsonify({'success': True, 'meetings': meetings})

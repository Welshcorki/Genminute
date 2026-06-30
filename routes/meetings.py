"""
회의 관련 핵심 라우트 (Thin Controller)
회의 CRUD, 통계, 마인드맵 등 핵심 기능
(공유, 업로드, Action Items는 별도 모듈로 분리됨)
"""
from flask import Blueprint, render_template, request, jsonify, session
import logging

logger = logging.getLogger(__name__)

from config import config
from database import get_db_manager
from database.vector_manager import vdb_manager
from services.stt_service import STTManager
from utils.decorators import login_required, api_error_handler
from services.user_service import (
    can_access_meeting,
    can_edit_meeting,
    get_user_meetings,
    get_shared_meetings,
)
from services.analysis_service import calculate_speaker_share
from services.meeting_service import MeetingService
from utils.validation import validate_title, parse_meeting_date

meetings_bp = Blueprint('meetings', __name__)

db = get_db_manager()
stt_manager = STTManager()

meeting_service = MeetingService(
    meeting_repo=db.meeting_repo,
    minutes_repo=db.minutes_repo,
    mindmap_repo=db.mindmap_repo,
)


@meetings_bp.route("/")
@login_required
def index():
    """메인 페이지 (파일 업로드 페이지)"""
    return render_template("index.html")


@meetings_bp.route("/api/stats", methods=["GET"])
@login_required
@api_error_handler
def get_user_stats():
    """사용자 통계 조회"""
    user_id = session['user_id']
    from services.user_service import is_admin
    stats = meeting_service.get_user_stats(user_id, is_admin(user_id))
    return jsonify({"success": True, "stats": stats})


@meetings_bp.route("/notes")
@login_required
def notes():
    """내 노트 목록 조회"""
    user_id = session['user_id']
    meetings = get_user_meetings(user_id)
    return render_template("notes.html", meetings=meetings)


@meetings_bp.route("/shared-notes")
@login_required
def shared_notes():
    """공유받은 노트 목록 조회"""
    user_id = session['user_id']
    shared_meetings = get_shared_meetings(user_id)
    return render_template("shared-notes.html", meetings=shared_meetings)


@meetings_bp.route("/view/<string:meeting_id>")
@login_required
def view_meeting(meeting_id):
    """회의록 뷰어 페이지"""
    user_id = session['user_id']
    if not can_access_meeting(user_id, meeting_id):
        return "접근 권한이 없습니다.", 403
    return render_template("viewer.html", meeting_id=meeting_id)


@meetings_bp.route("/api/meeting/<string:meeting_id>")
@login_required
@api_error_handler
def get_meeting_data(meeting_id):
    """회의 데이터 조회 (전사, 요약, 화자 정보 등)"""
    user_id = session['user_id']

    if not can_access_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

    detail = meeting_service.get_meeting_detail(meeting_id)
    if not detail:
        return jsonify({"success": False, "error": "회의를 찾을 수 없습니다."}), 404

    detail["success"] = True
    detail["speaker_share"] = calculate_speaker_share(meeting_id)
    detail["can_edit"] = can_edit_meeting(user_id, meeting_id)
    return jsonify(detail)


@meetings_bp.route("/api/delete_meeting/<string:meeting_id>", methods=["POST"])
@login_required
@api_error_handler
def delete_meeting(meeting_id):
    """회의 삭제 (SQLite, Vector DB, 오디오 파일 모두 삭제)"""
    user_id = session['user_id']

    if not can_edit_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "삭제 권한이 없습니다."}), 403

    result = vdb_manager.delete_from_collection(db_type="all", meeting_id=meeting_id)
    return jsonify(result)


@meetings_bp.route("/api/update_title/<string:meeting_id>", methods=["POST"])
@login_required
@api_error_handler
def update_meeting_title(meeting_id):
    """회의 제목 수정"""
    user_id = session['user_id']

    if not can_edit_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "수정 권한이 없습니다."}), 403

    data = request.get_json()
    new_title = data.get('title', '').strip()

    is_valid, error_message = validate_title(new_title)
    if not is_valid:
        return jsonify({"success": False, "error": error_message}), 400

    result = meeting_service.update_title(meeting_id, new_title)
    return jsonify(result)


@meetings_bp.route("/api/update_date/<string:meeting_id>", methods=["POST"])
@login_required
@api_error_handler
def update_meeting_date(meeting_id):
    """회의 날짜 수정"""
    user_id = session['user_id']

    if not can_edit_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "수정 권한이 없습니다."}), 403

    data = request.get_json()
    new_date = data.get('date', '').strip()
    if not new_date:
        return jsonify({"success": False, "error": "날짜를 입력해주세요."}), 400

    formatted_date = parse_meeting_date(new_date)
    result = meeting_service.update_date(meeting_id, formatted_date)
    return jsonify(result)


@meetings_bp.route("/notes_json")
@login_required
@api_error_handler
def notes_json():
    """노트 목록을 JSON으로 반환 (페이지네이션, 검색, 날짜 필터 지원)"""
    user_id = session['user_id']

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search_term = request.args.get('search', '').strip() or None
    start_date = request.args.get('start_date', '').strip() or None
    end_date = request.args.get('end_date', '').strip() or None
    sort_by = request.args.get('sort_by', 'date_desc')

    from services.user_service import get_user_meetings_count
    total_count = get_user_meetings_count(
        user_id, search_term=search_term,
        start_date=start_date, end_date=end_date,
    )
    meetings = get_user_meetings(
        user_id, page=page, per_page=per_page,
        search_term=search_term, start_date=start_date,
        end_date=end_date, sort_by=sort_by,
    )

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0

    return jsonify({
        "success": True,
        "meetings": meetings,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages,
        },
    })


@meetings_bp.route("/api/mindmap/<string:meeting_id>", methods=["GET"])
@login_required
@api_error_handler
def get_mindmap(meeting_id):
    """마인드맵 조회"""
    user_id = session['user_id']

    if not can_access_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

    mindmap_content = meeting_service.get_mindmap(meeting_id)

    if mindmap_content:
        return jsonify({"success": True, "has_mindmap": True, "mindmap_content": mindmap_content})
    return jsonify({"success": True, "has_mindmap": False, "message": "마인드맵이 아직 생성되지 않았습니다."})

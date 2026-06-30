"""
Action Items 관련 라우트 (Thin Controller)
추출, 목록 조회, 상태 업데이트
"""
from flask import Blueprint, jsonify, request, session
import logging

from config import config
from database import get_db_manager
from utils.decorators import login_required, api_error_handler
from services.user_service import can_access_meeting
from services.upload_service import convert_agent_items_to_db_format
from services.agent_service import AgentService

logger = logging.getLogger(__name__)

meetings_action_items_bp = Blueprint('meetings_action_items', __name__)

db = get_db_manager()

_agent_service = None


def _get_agent_service():
    global _agent_service
    if _agent_service is None:
        try:
            _agent_service = AgentService()
        except Exception as e:
            logger.warning(f"Agent Service 초기화 실패 (선택적 기능): {e}")
    return _agent_service


@meetings_action_items_bp.route("/api/extract_action_items/<string:meeting_id>", methods=["POST"])
@login_required
@api_error_handler
def extract_action_items(meeting_id):
    """Action Item 추출 (수동 트리거)"""
    user_id = session['user_id']

    if not can_access_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

    agent = _get_agent_service()
    if agent is None:
        return jsonify({
            "success": False,
            "error": "Action Item 추출 기능을 사용할 수 없습니다. (Agent Service 초기화 실패)",
        }), 503

    minutes = db.get_minutes_by_meeting_id(meeting_id)
    if not minutes or not minutes.get('minutes_content'):
        segments = db.get_segments_by_meeting_id(meeting_id)
        if not segments:
            return jsonify({"success": False, "error": "회의록 또는 전사본을 찾을 수 없습니다."}), 404
        meeting_text = "\n".join(
            f"{s.get('speaker_label', 'Unknown')}: {s.get('segment', '')}" for s in segments
        )
    else:
        meeting_text = minutes['minutes_content']

    logger.info(f"Action Item 추출 시작: meeting_id={meeting_id}")
    final_state = agent.process(meeting_text, user_id)

    processed_items = final_state.get('processed_items', [])
    if processed_items:
        db_items = convert_agent_items_to_db_format(processed_items)
        db.save_action_items(meeting_id, db_items)
        logger.info(f"Action Items 저장 완료: {len(db_items)}개")

    return jsonify({
        "success": True,
        "message": f"{len(processed_items)}개의 Action Item이 추출되었습니다.",
        "count": len(processed_items),
    })


@meetings_action_items_bp.route("/api/action_items/<string:meeting_id>", methods=["GET"])
@login_required
@api_error_handler
def get_action_items(meeting_id):
    """Action Item 목록 조회"""
    user_id = session['user_id']

    if not can_access_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

    items = db.get_action_items_by_meeting_id(meeting_id)
    return jsonify({"success": True, "action_items": items})


@meetings_action_items_bp.route("/api/action_items/<int:item_id>/status", methods=["POST"])
@login_required
@api_error_handler
def update_action_item_status(item_id):
    """Action Item 상태 업데이트"""
    user_id = session['user_id']

    data = request.get_json()
    status = data.get('status')

    if status not in ('pending', 'done'):
        return jsonify({"success": False, "error": "잘못된 상태 값입니다."}), 400

    meeting_id = db.get_action_item_meeting_id(item_id)
    if not meeting_id:
        return jsonify({"success": False, "error": "Action Item을 찾을 수 없습니다."}), 404

    if not can_access_meeting(user_id, meeting_id):
        return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

    success = db.update_action_item_status(item_id, status)
    if success:
        return jsonify({"success": True, "message": "상태가 업데이트되었습니다."})
    return jsonify({"success": False, "error": "상태 업데이트에 실패했습니다."}), 500

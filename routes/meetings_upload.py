"""
파일 업로드 관련 라우트
SSE 기반 파일 업로드 및 STT 처리
"""
from flask import Blueprint, request, session, Response, stream_with_context
import os
import uuid
import json
import logging
from datetime import datetime

from utils.decorators import login_required
from utils.validation import validate_title
from services.upload_service import upload_service

logger = logging.getLogger(__name__)

meetings_upload_bp = Blueprint('meetings_upload', __name__)


@meetings_upload_bp.route("/upload", methods=["POST"])
@login_required
def upload_and_process():
    """
    파일 업로드 및 STT 처리 (SSE 스트리밍)
    
    Form Data:
        title: 회의 제목
        audio_file: 오디오/비디오 파일
    
    Returns:
        SSE Stream: 실시간 진행 상황
    """
    owner_id = session['user_id']
    
    def generate():
        temp_audio_path = None
        file_path = None
        
        try:
            logger.info("🚀 SSE 생성 시작")
            
            title = request.form.get('title', '').strip()
            is_valid, error_message = validate_title(title)
            if not is_valid:
                yield f"data: {json.dumps({'step': 'error', 'message': error_message})}\n\n"
                return
            
            if 'audio_file' not in request.files:
                yield f"data: {json.dumps({'step': 'error', 'message': '오디오 파일이 없습니다.'})}\n\n"
                return
            
            file = request.files['audio_file']
            if not file.filename:
                yield f"data: {json.dumps({'step': 'error', 'message': '파일명이 없습니다.'})}\n\n"
                return
            
            is_valid, error_message = upload_service.validate_file(file.filename)
            if not is_valid:
                yield f"data: {json.dumps({'step': 'error', 'message': error_message})}\n\n"
                return
            
            meeting_id = uuid.uuid4().hex
            meeting_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                file_path, original_filename, is_video = upload_service.save_uploaded_file(file, meeting_id)
            except Exception as e:
                logger.error(f"❌ 파일 저장 실패: {e}", exc_info=True)
                yield f"data: {json.dumps({'step': 'error', 'message': f'파일 저장 중 오류가 발생했습니다: {str(e)}'})}\n\n"
                return
            
            yield f"data: {json.dumps({'step': 'upload', 'message': '파일 업로드가 완료되었습니다...', 'icon': '📤'})}\n\n"
            
            audio_path_for_stt = file_path
            if is_video:
                logger.info("🎬 비디오 오디오 추출 단계 진입")
                yield f"data: {json.dumps({'step': 'convert', 'message': '비디오를 오디오로 변환 중...', 'icon': '🎬'})}\n\n"
                
                success, temp_audio_path, error_msg = upload_service.convert_video_to_audio(file_path)
                if not success:
                    logger.error(f"❌ 비디오 오디오 추출 실패: {error_msg}")
                    yield f"data: {json.dumps({'step': 'error', 'message': f'오디오 추출 실패: {error_msg}'})}\n\n"
                    return
                
                audio_path_for_stt = temp_audio_path
                logger.info(f"✅ 오디오 추출 완료: {temp_audio_path}")
            
            logger.info(f"🎤 STT 처리 단계 진입: {audio_path_for_stt}")
            yield f"data: {json.dumps({'step': 'stt', 'message': '회의 음성을 텍스트로 변환하고 있습니다...', 'icon': '🎤'})}\n\n"
            
            result = upload_service.process_audio_file(
                audio_path=audio_path_for_stt,
                meeting_id=meeting_id,
                title=title,
                meeting_date=meeting_date,
                owner_id=owner_id,
                original_filename=os.path.basename(file_path)
            )
            logger.info(f"✅ STT 처리 결과: {result}")

            if not result['success']:
                yield f"data: {json.dumps({'step': 'error', 'message': 'STT 처리 실패'})}\n\n"
                return

            actual_meeting_id = result['meeting_id']

            if temp_audio_path:
                upload_service.cleanup_temp_files(temp_audio_path)

            yield f"data: {json.dumps({'step': 'summary', 'message': '회의 내용을 분석하고 요약하고 있습니다...', 'icon': '📝'})}\n\n"

            try:
                result = upload_service.generate_summary(actual_meeting_id)
                logger.info(f"✅ 문단 요약 생성 완료 (meeting_id: {actual_meeting_id})")

                if result.get('success'):
                    yield f"data: {json.dumps({'step': 'mindmap', 'message': '마인드맵을 생성하고 있습니다...', 'icon': '🗺️'})}\n\n"
                    logger.info(f"✅ 마인드맵도 자동 생성되었습니다 (meeting_id: {actual_meeting_id})")

            except Exception as e:
                logger.warning(f"⚠️  문단 요약 생성 실패: {e}", exc_info=True)

            redirect_url = f"/view/{actual_meeting_id}"
            yield f"data: {json.dumps({'step': 'complete', 'message': '노트 생성이 완료되었습니다!', 'redirect': redirect_url, 'icon': '✅'})}\n\n"
        
        except Exception as e:
            error_msg = f"처리 중 오류가 발생했습니다: {str(e)}"
            logger.error(f"❌ 업로드 처리 실패: {e}", exc_info=True)
            
            if temp_audio_path:
                try:
                    upload_service.cleanup_temp_files(temp_audio_path)
                except:
                    pass
            
            yield f"data: {json.dumps({'step': 'error', 'message': error_msg})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

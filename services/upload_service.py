"""
파일 업로드 서비스
오디오/비디오 파일 업로드 및 처리 비즈니스 로직
"""
import os
import uuid
import subprocess
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime

from config import config
from services.stt_service import STTManager
from database import get_db_manager
from database.vector_manager import vdb_manager
from utils.validation import validate_title, parse_meeting_date
from services.agent_service import AgentService

logger = logging.getLogger(__name__)

HALLUCINATION_PHRASES = [
    "이 영상은 유료 광고를 포함하고 있습니다",
    "MBC 뉴스",
    "시청해주셔서 감사합니다",
    "자막",
    "Subtitles by",
    "Transcribed by"
]


def convert_agent_items_to_db_format(processed_items: list) -> list:
    """
    AgentService에서 추출된 Action Item을 DB 저장 형식으로 변환합니다.
    upload_service와 meetings route 양쪽에서 공통으로 사용합니다.

    Args:
        processed_items: AgentService.process() 결과의 'processed_items' 리스트

    Returns:
        DB save_action_items()에 전달할 딕셔너리 리스트
    """
    db_items = []
    for item in processed_items:
        db_items.append({
            'content': item.get('summary', ''),
            'due_date': item.get('start_time'),
            'calendar_event_id': item.get('event_id')
        })
    return db_items


class UploadService:
    """파일 업로드 처리 서비스"""

    def __init__(self):
        self.stt_manager = STTManager()
        self.db = get_db_manager()
        self.vdb_manager = vdb_manager
        self.agent_service = AgentService()

    def validate_file(self, filename: str) -> tuple[bool, str]:
        """파일 검증 (확장자 체크)"""
        if not filename:
            return False, "파일이 없습니다."

        if '.' not in filename:
            return False, "파일 확장자가 없습니다."

        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in config.ALLOWED_EXTENSIONS:
            return False, f"허용되지 않는 파일 형식입니다. (허용: {', '.join(config.ALLOWED_EXTENSIONS)})"

        return True, ""

    def save_uploaded_file(self, file, meeting_id: str) -> tuple[str, str, bool]:
        """
        업로드된 파일 저장

        Returns:
            (file_path, original_filename, is_video)
        """
        original_filename = secure_filename(file.filename)

        unique_id = uuid.uuid4().hex[:8]
        filename = f"{unique_id}_{original_filename}"

        file_path = config.UPLOAD_FOLDER / filename
        file.save(str(file_path))

        extension = original_filename.rsplit('.', 1)[1].lower()
        is_video = (extension in ['mp4', 'webm'])

        logger.info(f"✅ 파일 저장: {file_path} (비디오: {is_video})")

        return str(file_path), original_filename, is_video

    def _run_ffmpeg(self, command: list[str]) -> tuple[bool, str]:
        """
        ffmpeg 명령어를 실행하는 공통 헬퍼

        Returns:
            (success, error_message)
        """
        try:
            logger.info(f"ffmpeg 명령어 실행: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=config.UPLOAD_TIMEOUT_SECONDS
            )

            if result.stdout:
                logger.debug(f"[ffmpeg stdout] {result.stdout[:500]}")
            if result.stderr:
                logger.debug(f"[ffmpeg stderr] {result.stderr[:500]}")

            if result.returncode == 0:
                return True, ""
            else:
                return False, f"ffmpeg 실패: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "변환 타임아웃 (20분 초과)"
        except Exception as e:
            return False, f"변환 중 오류: {str(e)}"

    def convert_video_to_audio(self, video_path: str) -> tuple[bool, str, str]:
        """비디오 파일을 오디오(WAV)로 변환"""
        audio_path = video_path.rsplit('.', 1)[0] + '_converted.wav'

        command = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            audio_path
        ]

        success, error_msg = self._run_ffmpeg(command)
        if success:
            logger.info(f"✅ 비디오 → 오디오 변환 성공: {audio_path}")
            return True, audio_path, ""
        else:
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg

    def convert_webm_to_compatible_format(self, webm_path: str) -> tuple[bool, str, str]:
        """
        WebM 파일을 호환성 높은 포맷으로 변환
        - 비디오 녹화(video_) -> MP4 (H.264/AAC)
        - 마이크 녹음(mic_) -> M4A (AAC 오디오 전용)
        """
        try:
            filename = os.path.basename(webm_path)
            is_video_record = 'video_' in filename

            if is_video_record:
                target_ext = '.mp4'
                command = [
                    'ffmpeg', '-y', '-i', webm_path,
                    '-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac',
                ]
                logger.info(f"🔄 WebM(Video) → MP4 변환 시작: {webm_path}")
            else:
                target_ext = '.m4a'
                command = [
                    'ffmpeg', '-y', '-i', webm_path,
                    '-vn', '-c:a', 'aac',
                ]
                logger.info(f"🔄 WebM(Mic) → M4A 변환 시작: {webm_path}")

            new_path = webm_path.rsplit('.', 1)[0] + target_ext
            command.append(new_path)

            success, error_msg = self._run_ffmpeg(command)
            if success:
                logger.info(f"✅ 변환 성공: {new_path}")
                try:
                    os.remove(webm_path)
                    logger.info("🗑️ 원본 WebM 파일 삭제됨")
                except OSError:
                    pass
                return True, new_path, ""
            else:
                logger.error(f"❌ {error_msg}")
                return False, "", error_msg

        except Exception as e:
            error_msg = f"변환 중 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg

    def process_audio_file(
        self,
        audio_path: str,
        meeting_id: str,
        title: str,
        meeting_date: str,
        owner_id: int,
        original_filename: str = None
    ) -> dict:
        """오디오 파일 STT 처리 및 DB 저장"""
        logger.info(f"🎤 STT 처리 시작: {audio_path}")

        try:
            raw_segments = self.stt_manager.transcribe(audio_path)

            segments = []
            for seg in raw_segments:
                text = seg["text"].strip()
                if any(phrase in text for phrase in HALLUCINATION_PHRASES):
                    logger.warning(f"⚠️ 환각 문구 감지되어 제외됨: {text}")
                    continue

                segments.append({
                    "speaker": seg["speaker"],
                    "start_time": seg["start_time"],
                    "text": text,
                    "confidence": seg.get("confidence", 0.95),
                    "end_time": seg.get("end_time", seg["start_time"] + 5.0)
                })

        except Exception as e:
            logger.error(f"❌ STT 처리 중 오류 발생: {e}", exc_info=True)
            raise ValueError(f"STT 처리 실패: {e}")

        if not segments:
            logger.warning("⚠️ 유효한 대화 내용이 없습니다. (무음 또는 환각)")
            raise ValueError("유효한 음성 내용이 감지되지 않았습니다. (무음 또는 배경음)")

        logger.info(f"✅ STT 완료: {len(segments)}개 세그먼트")

        audio_filename = original_filename or os.path.basename(audio_path)

        saved_meeting_id = self.db.save_stt_to_db(
            segments=segments,
            audio_filename=audio_filename,
            title=title,
            meeting_date=meeting_date,
            owner_id=owner_id
        )

        all_segments = self.db.get_segments_by_meeting_id(saved_meeting_id)

        if all_segments:
            first_segment = all_segments[0]
            self.vdb_manager.add_meeting_as_chunk(
                meeting_id=saved_meeting_id,
                title=first_segment['title'],
                meeting_date=first_segment['meeting_date'],
                audio_file=first_segment['audio_file'],
                segments=all_segments
            )
            logger.info(f"✅ meeting_chunks에 저장 완료 (meeting_id: {saved_meeting_id})")

        self._extract_and_save_action_items(saved_meeting_id, segments, owner_id)

        return {
            'success': True,
            'meeting_id': saved_meeting_id,
            'segments': segments
        }

    def _extract_and_save_action_items(self, meeting_id: str, segments: list, owner_id: int):
        """AgentService로 Action Item을 추출하여 DB에 저장 (실패해도 전체 프로세스 중단 안 함)"""
        try:
            logger.info(f"🤖 Action Item 추출 에이전트 호출 시작 (meeting_id: {meeting_id})")
            full_transcript = " ".join([s['text'] for s in segments])
            final_state = self.agent_service.process(full_transcript, owner_id)

            processed_items = final_state.get('processed_items', [])
            if processed_items:
                db_items = convert_agent_items_to_db_format(processed_items)
                self.db.save_action_items(meeting_id, db_items)
                logger.info(f"✅ Action Items 저장 완료: {len(db_items)}개")

            logger.info(f"✅ Action Item 추출 에이전트 호출 완료 (meeting_id: {meeting_id})")
        except Exception as e:
            logger.warning(f"⚠️ Action Item 추출 에이전트 호출 중 오류 발생: {e}", exc_info=True)

    def generate_summary(self, meeting_id: str) -> dict:
        """문단 요약 생성"""
        logger.info(f"🤖 문단 요약 자동 생성 시작 (meeting_id: {meeting_id})")

        all_segments = self.db.get_segments_by_meeting_id(meeting_id)

        if not all_segments:
            logger.warning(f"⚠️ 세그먼트가 없어 요약을 생략합니다. (meeting_id: {meeting_id})")
            return {'success': False, 'message': 'No segments found'}

        first_segment = all_segments[0]
        transcript_text = " ".join([row['segment'] for row in all_segments])

        if len(transcript_text) < 50:
            logger.warning(f"⚠️ 텍스트가 너무 짧아 요약을 생략합니다. (길이: {len(transcript_text)})")
            return {'success': False, 'message': 'Text too short to summarize'}

        summary_content = self.stt_manager.subtopic_generate(first_segment['title'], transcript_text)

        if not summary_content:
            raise ValueError("요약 생성에 실패했습니다.")

        self.vdb_manager.add_meeting_as_subtopic(
            meeting_id=meeting_id,
            title=first_segment['title'],
            meeting_date=first_segment['meeting_date'],
            audio_file=first_segment['audio_file'],
            summary_content=summary_content
        )
        logger.info(f"✅ 문단 요약 생성 및 저장 완료 (meeting_id: {meeting_id})")

        try:
            logger.info(f"🗺️ 마인드맵 키워드 자동 생성 시작 (meeting_id: {meeting_id})")
            mindmap_content = self.stt_manager.extract_mindmap_keywords(
                summary_content, first_segment['title']
            )
            if mindmap_content:
                self.db.save_mindmap(meeting_id=meeting_id, mindmap_content=mindmap_content)
                logger.info(f"✅ 마인드맵 키워드 생성 및 저장 완료 (meeting_id: {meeting_id})")
            else:
                logger.warning(f"⚠️ 마인드맵 키워드 생성 실패 (meeting_id: {meeting_id})")
        except Exception as mindmap_error:
            logger.warning(f"⚠️ 마인드맵 키워드 자동 생성 중 오류 발생: {mindmap_error}", exc_info=True)

        return {'success': True, 'summary': summary_content}

    def cleanup_temp_files(self, *file_paths):
        """임시 파일 삭제"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"🗑️  임시 파일 삭제: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️  임시 파일 삭제 실패: {file_path} - {e}")


upload_service = UploadService()

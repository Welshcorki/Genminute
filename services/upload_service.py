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
from database.sqlite_manager import DatabaseManager
from database.vector_manager import vdb_manager
from utils.validation import validate_title, parse_meeting_date
from services.agent_service import AgentService
# [NEW] 로컬 STT 서비스 Import (병합 시 경로 확인)
from services.diarization import diarization_service

logger = logging.getLogger(__name__)

# Whisper 환각 문구 블랙리스트 (무음 구간에서 자주 발생)
HALLUCINATION_PHRASES = [
    "이 영상은 유료 광고를 포함하고 있습니다",
    "MBC 뉴스",
    "시청해주셔서 감사합니다",
    "자막",
    "Subtitles by",
    "Transcribed by"
]


class UploadService:
    """파일 업로드 처리 서비스"""

    def __init__(self):
        self.stt_manager = STTManager()
        self.db = DatabaseManager(str(config.DATABASE_PATH))
        self.vdb_manager = vdb_manager
        self.agent_service = AgentService()

    def validate_file(self, filename: str) -> tuple[bool, str]:
        """
        파일 검증

        Args:
            filename: 파일명

        Returns:
            (is_valid, error_message): 검증 결과
        """
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

        Args:
            file: Werkzeug FileStorage 객체
            meeting_id: 회의 ID

        Returns:
            (file_path, original_filename, is_video): 저장된 파일 경로, 원본 파일명, 비디오 여부
        """
        # 파일명 보안 처리
        original_filename = secure_filename(file.filename)

        # UUID 추가 (파일명 충돌 방지)
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{unique_id}_{original_filename}"

        # 파일 저장
        file_path = config.UPLOAD_FOLDER / filename
        file.save(str(file_path))

        # 비디오 파일 여부 확인
        extension = original_filename.rsplit('.', 1)[1].lower()
        is_video = (extension in ['mp4', 'webm'])

        logger.info(f"✅ 파일 저장: {file_path} (비디오: {is_video})")

        return str(file_path), original_filename, is_video

    def convert_video_to_audio(self, video_path: str) -> tuple[bool, str, str]:
        """
        비디오 파일을 오디오 파일로 변환 (ffmpeg 사용)

        Args:
            video_path: 비디오 파일 경로

        Returns:
            (success, audio_path, error_message): 변환 결과
        """
        try:
            # 출력 파일 경로 (같은 위치에 .wav로 저장)
            audio_path = video_path.rsplit('.', 1)[0] + '_converted.wav'

            # ffmpeg 명령어
            command = [
                'ffmpeg',
                '-y',  # 덮어쓰기
                '-i', video_path,
                '-vn',  # 비디오 스트림 제거
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz
                '-ac', '1',  # 모노 채널
                audio_path
            ]

            # 실행 (20분 타임아웃)
            logger.info(f"ffmpeg 명령어 실행: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=config.UPLOAD_TIMEOUT_SECONDS
            )

            # 디버깅을 위한 상세 로그
            if result.stdout:
                logger.debug(f"[ffmpeg stdout] {result.stdout[:500]}") # 너무 길면 자름
            if result.stderr:
                logger.debug(f"[ffmpeg stderr] {result.stderr[:500]}")

            if result.returncode == 0:
                logger.info(f"✅ 비디오 → 오디오 변환 성공: {audio_path}")
                return True, audio_path, ""
            else:
                error_msg = f"ffmpeg 실패: {result.stderr}"
                logger.error(f"❌ {error_msg}")
                return False, "", error_msg

        except subprocess.TimeoutExpired:
            error_msg = "변환 타임아웃 (20분 초과)"
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg

        except Exception as e:
            error_msg = f"변환 중 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg

    def convert_webm_to_compatible_format(self, webm_path: str) -> tuple[bool, str, str]:
        """
        WebM 파일을 호환성 높은 포맷으로 변환
        - 비디오 녹화(video_) -> MP4 (H.264/AAC)
        - 마이크 녹음(mic_) -> M4A (AAC 오디오 전용)
        
        Args:
            webm_path: WebM 파일 경로
            
        Returns:
            (success, new_path, error_message): 변환 결과
        """
        try:
            filename = os.path.basename(webm_path)
            is_video_record = 'video_' in filename
            
            if is_video_record:
                # 비디오 녹화 -> MP4 변환
                target_ext = '.mp4'
                command = [
                    'ffmpeg', '-y', '-i', webm_path,
                    '-c:v', 'libx264', '-preset', 'fast',
                    '-c:a', 'aac',
                    # 출력 파일 경로 설정 (아래에서 추가)
                ]
                logger.info(f"🔄 WebM(Video) → MP4 변환 시작: {webm_path}")
            else:
                # 마이크 녹음 -> M4A (AAC) 변환
                target_ext = '.m4a'
                command = [
                    'ffmpeg', '-y', '-i', webm_path,
                    '-vn', # 비디오 스트림 제거
                    '-c:a', 'aac',
                    # 출력 파일 경로 설정 (아래에서 추가)
                ]
                logger.info(f"🔄 WebM(Mic) → M4A 변환 시작: {webm_path}")

            # 출력 파일 경로 생성
            new_path = webm_path.rsplit('.', 1)[0] + target_ext
            command.append(new_path)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=config.UPLOAD_TIMEOUT_SECONDS
            )
            
            if result.returncode == 0:
                logger.info(f"✅ 변환 성공: {new_path}")
                # 원본 WebM 삭제
                try:
                    os.remove(webm_path)
                    logger.info("🗑️ 원본 WebM 파일 삭제됨")
                except OSError:
                    pass
                    
                return True, new_path, ""
            else:
                error_msg = f"ffmpeg 변환 실패: {result.stderr}"
                logger.error(f"❌ {error_msg}")
                return False, "", error_msg
                
        except Exception as e:
            error_msg = f"변환 중 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg

    def convert_webm_to_mp4(self, webm_path: str) -> tuple[bool, str, str]:
        """
        WebM 파일을 MP4로 변환 (호환성 확보)
        
        Args:
            webm_path: WebM 파일 경로
            
        Returns:
            (success, mp4_path, error_message): 변환 결과
        """
        try:
            # 출력 파일 경로 (확장자만 mp4로 변경)
            mp4_path = webm_path.rsplit('.', 1)[0] + '.mp4'
            
            # ffmpeg 명령어 (Fast Encoding)
            # -c:v libx264: H.264 비디오 코덱 (호환성 좋음)
            # -preset fast: 인코딩 속도 우선
            # -c:a aac: AAC 오디오 코덱
            command = [
                'ffmpeg',
                '-y',
                '-i', webm_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-c:a', 'aac',
                mp4_path
            ]
            
            logger.info(f"🔄 WebM → MP4 변환 시작: {webm_path}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=config.UPLOAD_TIMEOUT_SECONDS
            )
            
            if result.returncode == 0:
                logger.info(f"✅ WebM → MP4 변환 성공: {mp4_path}")
                # 원본 WebM 삭제 (선택 사항, 여기서는 용량 절약을 위해 삭제)
                try:
                    os.remove(webm_path)
                    logger.info("🗑️ 원본 WebM 파일 삭제됨")
                except OSError:
                    pass
                    
                return True, mp4_path, ""
            else:
                error_msg = f"ffmpeg 변환 실패: {result.stderr}"
                logger.error(f"❌ {error_msg}")
                return False, "", error_msg
                
        except Exception as e:
            error_msg = f"MP4 변환 중 오류: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, "", error_msg

    def process_audio_file(
        self,
        audio_path: str,
        meeting_id: str,
        title: str,
        meeting_date: str,
        owner_id: int,
        original_filename: str = None  # [추가] 원본 파일명 (임시 파일명 대신 저장용)
    ) -> dict:
        """
        오디오 파일 STT 처리 및 DB 저장

        Args:
            audio_path: STT 분석할 오디오 파일 경로 (임시 wav일 수 있음)
            meeting_id: 회의 ID
            title: 회의 제목
            meeting_date: 회의 날짜
            owner_id: 소유자 ID
            original_filename: DB에 저장할 실제 원본 파일명 (MP4/M4A 등)

        Returns:
            dict: 처리 결과 (segments, meeting_id 등)
        """
        # STT 처리
        logger.info(f"🎤 STT 처리 시작: {audio_path}")
        
        # -----------------------------------------------------------------
        # [MODIFIED] 로컬 DiarizationService 사용 (기존 LLM 방식 대체)
        # -----------------------------------------------------------------
        # segments = self.stt_manager.transcribe_audio(audio_path)  # [LEGACY]
        
        try:
            # DiarizationService는 내부적으로 ffmpeg 변환, Whisper STT, Pyannote 화자분리를 모두 수행
            # 반환 형식: [{'speaker': 'SPEAKER_00', 'text': '...', 'start': 0.0, 'end': 5.0}, ...]
            raw_segments = diarization_service.transcribe_and_diarize(audio_path)
            
            # DB 저장 형식에 맞게 변환
            # DB 요구사항: segment['speaker'], segment['start_time'], segment['text'], segment['confidence']
            segments = []
            for seg in raw_segments:
                # [FILTER] 환각 문구 필터링
                text = seg["text"].strip()
                is_hallucination = False
                for phrase in HALLUCINATION_PHRASES:
                    if phrase in text:
                        is_hallucination = True
                        break
                
                if is_hallucination:
                    logger.warning(f"⚠️ 환각 문구 감지되어 제외됨: {text}")
                    continue

                segments.append({
                    "speaker": seg["speaker"],
                    "start_time": seg["start"],
                    "text": text,
                    "confidence": 0.95, # 로컬 모델은 confidence 점수 추출이 복잡하므로 기본값 사용
                    "end_time": seg["end"] # (옵션) 끝 시간
                })
                
        except Exception as e:
            logger.error(f"❌ 로컬 STT 처리 중 오류 발생: {e}", exc_info=True)
            raise ValueError(f"STT 처리 실패: {e}")
        # -----------------------------------------------------------------

        if not segments:
            # 환각 필터링 후 남은게 없거나, 원래 없던 경우 -> 조기 종료
            logger.warning("⚠️ 유효한 대화 내용이 없습니다. (무음 또는 환각)")
            raise ValueError("유효한 음성 내용이 감지되지 않았습니다. (무음 또는 배경음)")

        logger.info(f"✅ STT 완료: {len(segments)}개 세그먼트")

        # SQLite DB 저장
        # original_filename이 있으면 그것을 사용, 없으면 audio_path에서 추출
        if original_filename:
            audio_filename = original_filename
        else:
            audio_filename = os.path.basename(audio_path)
            
        saved_meeting_id = self.db.save_stt_to_db(
            segments=segments,
            audio_filename=audio_filename,
            title=title,
            meeting_date=meeting_date,
            owner_id=owner_id
        )

        # Vector DB 저장 (청킹 + 임베딩)
        # DB에서 저장된 세그먼트 다시 조회
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

        # [통합] Action Item 추출을 위해 AgentService 호출
        try:
            logger.info(f"🤖 Action Item 추출 에이전트 호출 시작 (meeting_id: {saved_meeting_id})")
            full_transcript = " ".join([s['text'] for s in segments])
            # process 메서드에 user_id 전달
            final_state = self.agent_service.process(full_transcript, owner_id)
            
            # 추출된 Action Items를 DB에 저장
            processed_items = final_state.get('processed_items', [])
            if processed_items:
                # CalendarEvent 형식을 DB 형식으로 변환
                db_items = []
                for item in processed_items:
                    db_items.append({
                        'content': item.get('summary', ''),
                        'due_date': item.get('start_time'),
                        'calendar_event_id': item.get('event_id')  # 캘린더 이벤트 ID가 있다면
                    })
                
                self.db.save_action_items(saved_meeting_id, db_items)
                logger.info(f"✅ Action Items 저장 완료: {len(db_items)}개")
            
            logger.info(f"✅ Action Item 추출 에이전트 호출 완료 (meeting_id: {saved_meeting_id})")
        except Exception as e:
            logger.warning(f"⚠️ Action Item 추출 에이전트 호출 중 오류 발생: {e}", exc_info=True)
            # 에이전트 호출이 실패해도 전체 프로세스는 중단되지 않음

        return {
            'success': True,
            'meeting_id': saved_meeting_id,
            'segments': segments
        }

    def generate_summary(self, meeting_id: str) -> dict:
        """
        문단 요약 생성

        Args:
            meeting_id: 회의 ID

        Returns:
            dict: 요약 결과
        """
        logger.info(f"🤖 문단 요약 자동 생성 시작 (meeting_id: {meeting_id})")

        # DB에서 모든 세그먼트 조회
        all_segments = self.db.get_segments_by_meeting_id(meeting_id)

        if not all_segments:
            # 세그먼트가 없으면 (무음 등) 요약 스킵
            logger.warning(f"⚠️ 세그먼트가 없어 요약을 생략합니다. (meeting_id: {meeting_id})")
            return {'success': False, 'message': 'No segments found'}

        first_segment = all_segments[0]

        # transcript_text 생성
        transcript_text = " ".join([row['segment'] for row in all_segments])

        # [SAFETY] 텍스트 길이 검사 (환각 방지)
        if len(transcript_text) < 50:
            logger.warning(f"⚠️ 텍스트가 너무 짧아 요약을 생략합니다. (길이: {len(transcript_text)})")
            return {'success': False, 'message': 'Text too short to summarize'}

        # subtopic_generate를 이용해 요약 생성
        summary_content = self.stt_manager.subtopic_generate(first_segment['title'], transcript_text)

        if not summary_content:
            raise ValueError("요약 생성에 실패했습니다.")

        # meeting_subtopic DB에 저장
        self.vdb_manager.add_meeting_as_subtopic(
            meeting_id=meeting_id,
            title=first_segment['title'],
            meeting_date=first_segment['meeting_date'],
            audio_file=first_segment['audio_file'],
            summary_content=summary_content
        )
        logger.info(f"✅ 문단 요약 생성 및 저장 완료 (meeting_id: {meeting_id})")

        # 마인드맵 키워드 자동 생성
        try:
            logger.info(f"🗺️ 마인드맵 키워드 자동 생성 시작 (meeting_id: {meeting_id})")

            mindmap_content = self.stt_manager.extract_mindmap_keywords(
                summary_content,
                first_segment['title']
            )

            if mindmap_content:
                self.db.save_mindmap(
                    meeting_id=meeting_id,
                    mindmap_content=mindmap_content
                )
                logger.info(f"✅ 마인드맵 키워드 생성 및 저장 완료 (meeting_id: {meeting_id})")
            else:
                logger.warning(f"⚠️ 마인드맵 키워드 생성 실패 (meeting_id: {meeting_id})")

        except Exception as mindmap_error:
            logger.warning(f"⚠️ 마인드맵 키워드 자동 생성 중 오류 발생: {mindmap_error}", exc_info=True)
            # 마인드맵 생성 실패해도 요약은 성공으로 처리

        return {
            'success': True,
            'summary': summary_content
        }

    def cleanup_temp_files(self, *file_paths):
        """
        임시 파일 삭제

        Args:
            *file_paths: 삭제할 파일 경로들
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"🗑️  임시 파일 삭제: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️  임시 파일 삭제 실패: {file_path} - {e}")


# 싱글톤 인스턴스
upload_service = UploadService()

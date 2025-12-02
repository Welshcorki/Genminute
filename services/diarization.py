import os
import logging
import torch
import subprocess
import tempfile
from typing import List, Dict, Any
from pathlib import Path

from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from huggingface_hub import login

# 프로젝트 설정 로드
try:
    from config import config
except ImportError:
    # Fallback for standalone testing
    class MockConfig:
        HF_TOKEN = os.getenv("HF_TOKEN")
        LOG_LEVEL = "INFO"
        LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    config = MockConfig()

# 로깅 설정
logger = logging.getLogger("LocalSTT")
if not logger.handlers:
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)

class DiarizationService:
    """
    로컬 STT 및 화자 분리 통합 서비스
    - Faster-Whisper: 텍스트 변환
    - Pyannote.audio: 화자 분리
    - FFmpeg: 오디오 전처리 (WAV 16kHz Mono)
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 디바이스별 최적화 설정
        if self.device == "cuda":
            self.compute_type = "float16"
            self.whisper_model_size = "large-v3"
        else:
            self.compute_type = "int8"
            self.whisper_model_size = "medium" # CPU에서는 medium 권장

        self.whisper_model = None
        self.diarization_pipeline = None
        
        logger.info(f"🚀 Initializing DiarizationService")
        logger.info(f"   • Device: {self.device.upper()}")
        logger.info(f"   • Whisper Model: {self.whisper_model_size}")

    def _load_whisper(self):
        """Whisper 모델 지연 로딩 (Lazy Loading)"""
        if self.whisper_model is None:
            logger.info(f"⏳ Loading Whisper model ({self.whisper_model_size})...")
            try:
                self.whisper_model = WhisperModel(
                    self.whisper_model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                logger.info("✅ Whisper model loaded.")
            except Exception as e:
                logger.error(f"❌ Failed to load Whisper: {e}")
                raise

    def _load_diarization(self):
        """Pyannote 파이프라인 지연 로딩"""
        if self.diarization_pipeline is None:
            token = config.HF_TOKEN
            if not token:
                logger.error("❌ HF_TOKEN not found in config.")
                raise ValueError("Hugging Face Token required for Pyannote.")
            
            logger.info("⏳ Loading Pyannote pipeline...")
            try:
                # Hugging Face 인증 (구버전 호환성 확보를 위해 login() 사용)
                login(token=token)
                
                # Pyannote 모델 로드
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1"
                )
                
                if self.device == "cuda":
                    self.diarization_pipeline.to(torch.device("cuda"))
                    
                logger.info("✅ Pyannote pipeline loaded.")
            except Exception as e:
                logger.error(f"❌ Failed to load Pyannote: {e}")
                raise

    def _convert_to_wav(self, input_path: str) -> str:
        """
        입력 오디오/비디오를 16kHz Mono WAV로 변환 (FFmpeg 사용)
        """
        file_ext = os.path.splitext(input_path)[1].lower()
        
        logger.info(f"🔄 Converting to 16kHz Mono WAV for AI processing...")
        
        # 임시 파일 생성
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # FFmpeg 명령어
        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ac", "1",           # Mono
            "-ar", "16000",       # 16000 Hz
            "-vn",                # No Video
            temp_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"   -> Conversion complete: {temp_path}")
            return temp_path
        except subprocess.CalledProcessError:
            logger.error("❌ FFmpeg conversion failed.")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return input_path # 실패 시 원본 시도
        except FileNotFoundError:
            logger.error("❌ FFmpeg not found.")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return input_path

    def transcribe_and_diarize(self, audio_path: str, language: str = "ko") -> List[Dict[str, Any]]:
        """
        통합 처리 함수: 오디오 -> 텍스트 + 화자 정보 반환
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        processed_audio = self._convert_to_wav(audio_path)
        
        try:
            # 1. STT (Whisper)
            self._load_whisper()
            logger.info(f"🎙️  Step 1: Transcribing...")
            segments_generator, info = self.whisper_model.transcribe(
                processed_audio, 
                beam_size=5, 
                word_timestamps=True, 
                language=language
            )
            whisper_segments = list(segments_generator)
            logger.info(f"   -> Detected language: {info.language}")

            # 2. Diarization (Pyannote)
            self._load_diarization()
            logger.info(f"👥 Step 2: Diarizing speakers...")
            diarization_result = self.diarization_pipeline(processed_audio)
            
            # 3. Merge
            logger.info(f"🔄 Step 3: Merging results...")
            final_result = self._merge_results(whisper_segments, diarization_result)
            
            return final_result
            
        finally:
            # 임시 파일 정리
            if processed_audio != audio_path and os.path.exists(processed_audio):
                try:
                    os.remove(processed_audio)
                    logger.debug(f"🧹 Cleaned up temp file: {processed_audio}")
                except OSError:
                    pass

    def _merge_results(self, whisper_segments, diarization_result) -> List[Dict[str, Any]]:
        """Whisper 세그먼트와 화자 정보를 시간 기준으로 병합"""
        final_segments = []
        
        # 화자 턴 정보 캐싱 (Start, End, Speaker)
        speaker_turns = []
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            speaker_turns.append((turn.start, turn.end, speaker))

        current_entry = {
            "speaker": None,
            "text": [],
            "start": 0.0,
            "end": 0.0
        }

        for segment in whisper_segments:
            for word in segment.words:
                word_mid = (word.start + word.end) / 2
                best_speaker = "Unknown"
                
                # 화자 매칭
                for spk_start, spk_end, spk_label in speaker_turns:
                    if spk_start <= word_mid <= spk_end:
                        best_speaker = spk_label
                        break
                
                # 화자가 바뀌었으면 이전 엔트리 저장 및 새 엔트리 시작
                if current_entry["speaker"] is not None and best_speaker != current_entry["speaker"]:
                    final_segments.append({
                        "speaker": current_entry["speaker"],
                        "text": "".join(current_entry["text"]).strip(),
                        "start": current_entry["start"],
                        "end": current_entry["end"]
                    })
                    current_entry = {
                        "speaker": best_speaker,
                        "text": [word.word],
                        "start": word.start,
                        "end": word.end
                    }
                else:
                    # 첫 시작이거나 화자가 같으면 계속 추가
                    if current_entry["speaker"] is None:
                        current_entry["speaker"] = best_speaker
                        current_entry["start"] = word.start
                    
                    current_entry["text"].append(word.word)
                    current_entry["end"] = word.end

        # 마지막 잔여 데이터 처리
        if current_entry["text"]:
            final_segments.append({
                "speaker": current_entry["speaker"],
                "text": "".join(current_entry["text"]).strip(),
                "start": current_entry["start"],
                "end": current_entry["end"]
            })

        return final_segments

# 싱글톤 인스턴스 (필요시 사용)
diarization_service = DiarizationService()

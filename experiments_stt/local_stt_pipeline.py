import os
import sys
import logging
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from dotenv import load_dotenv

# 부모 디렉토리(프로젝트 루트)를 sys.path에 추가하여 config 모듈 import 가능하게 함
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

# .env 파일 명시적 로드
load_dotenv(root_dir / '.env')

try:
    from config import config
except ImportError:
    # config가 없을 경우를 대비한 폴백 (테스트용)
    class MockConfig:
        HF_TOKEN = os.getenv("HF_TOKEN")
        LOG_LEVEL = "INFO"
        LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    config = MockConfig()

# 로깅 설정
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger("LocalSTT")

class LocalSTTPipeline:
    """
    로컬 STT 실험용 파이프라인 (Pyannote 3.1.1 호환)
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # GPU 여부에 따른 모델 설정 최적화
        if self.device == "cuda":
            self.compute_type = "float16"
            self.whisper_model_size = "large-v3"
        else:
            self.compute_type = "int8"
            self.whisper_model_size = "medium" # CPU에서는 medium 권장

        self.whisper_model = None
        self.diarization_pipeline = None
        
        logger.info("="*50)
        logger.info(f"🚀 Initializing Local STT Pipeline (Stable)")
        logger.info(f"   • Device: {self.device.upper()}")
        logger.info(f"   • Whisper Model: {self.whisper_model_size}")
        logger.info(f"   • Compute Type: {self.compute_type}")
        logger.info("="*50)

    def _load_whisper(self):
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
        if self.diarization_pipeline is None:
            token = config.HF_TOKEN
            if not token:
                logger.error("❌ HF_TOKEN not found in config or env.")
                raise ValueError("Hugging Face Token required for Pyannote.")
            
            logger.info("⏳ Loading Pyannote pipeline...")
            try:
                from huggingface_hub import login
                login(token=token)
                
                # Pyannote 3.1.1은 use_auth_token을 사용합니다.
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1"
                )
                if self.device == "cuda":
                    self.diarization_pipeline.to(torch.device("cuda"))
                logger.info("✅ Pyannote pipeline loaded.")
            except Exception as e:
                logger.error(f"❌ Failed to load Pyannote: {e}")
                raise

    def run(self, audio_path: str):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 오디오 전처리 (WAV 변환)
        # Pyannote/SoundFile 호환성을 위해 mp4 등을 wav로 변환
        processed_audio = self._convert_to_wav(audio_path)
        
        try:
            # 1. STT (Whisper)
            self._load_whisper()
            logger.info(f"🎙️  Step 1: Transcribing {os.path.basename(processed_audio)}...")
            segments_generator, info = self.whisper_model.transcribe(
                processed_audio, 
                beam_size=5, 
                word_timestamps=True, 
                language="ko"
            )
            whisper_segments = list(segments_generator)
            logger.info(f"   -> Transcription done. Detected language: {info.language}")

            # 2. Diarization (Pyannote)
            self._load_diarization()
            logger.info(f"👥 Step 2: Diarizing speakers...")
            diarization_result = self.diarization_pipeline(processed_audio)
            logger.info(f"   -> Diarization done.")

            # 3. Merge
            logger.info(f"🔄 Step 3: Merging results...")
            final_result = self._merge_results(whisper_segments, diarization_result)
            
            return final_result
            
        finally:
            # 임시 파일 정리 (원본이 아닐 경우에만)
            if processed_audio != audio_path and os.path.exists(processed_audio):
                try:
                    os.remove(processed_audio)
                    logger.info(f"🧹 Cleaned up temporary audio: {processed_audio}")
                except OSError:
                    pass

    def _convert_to_wav(self, input_path: str) -> str:
        """
        입력 오디오/비디오를 16kHz Mono WAV로 변환합니다.
        Pyannote 및 Whisper의 성능 최적화를 위해 필수적입니다.
        """
        import subprocess
        import tempfile
        
        file_ext = os.path.splitext(input_path)[1].lower()
        if file_ext == ".wav":
            return input_path
            
        logger.info(f"🔄 Converting {file_ext} to WAV for compatibility...")
        
        # 임시 파일 생성
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # FFmpeg 명령어 (16kHz, Mono, PCM 16bit)
        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ac", "1",           # Mono
            "-ar", "16000",       # 16000 Hz
            "-vn",                # No Video
            temp_path
        ]
        
        try:
            # ffmpeg 실행 (출력 숨김)
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"   -> Conversion complete: {temp_path}")
            return temp_path
        except subprocess.CalledProcessError:
            logger.error("❌ FFmpeg conversion failed. Make sure FFmpeg is installed.")
            # 실패 시 원본 반환 (운에 맡김)
            return input_path
        except FileNotFoundError:
            logger.error("❌ FFmpeg not found. Please install FFmpeg.")
            return input_path

    def _merge_results(self, whisper_segments, diarization_result):
        """Whisper의 단어 타임스탬프와 Pyannote의 화자 구간을 매핑"""
        final_segments = []
        
        # Pyannote 결과 캐싱
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
                # 단어의 중간 시간값으로 화자 판별 (가장 단순하면서 효과적인 방법)
                word_mid = (word.start + word.end) / 2
                best_speaker = "Unknown"
                
                # 해당 시간에 말하고 있는 화자 찾기
                for spk_start, spk_end, spk_label in speaker_turns:
                    if spk_start <= word_mid <= spk_end:
                        best_speaker = spk_label
                        break
                
                # 화자 변경 감지
                if current_entry["speaker"] is not None and best_speaker != current_entry["speaker"]:
                    # 이전 발화 저장
                    final_segments.append({
                        "speaker": current_entry["speaker"],
                        "text": "".join(current_entry["text"]).strip(),
                        "start": current_entry["start"],
                        "end": current_entry["end"]
                    })
                    # 초기화
                    current_entry = {
                        "speaker": best_speaker,
                        "text": [word.word],
                        "start": word.start,
                        "end": word.end
                    }
                else:
                    # 화자 유지 또는 첫 시작
                    if current_entry["speaker"] is None:
                        current_entry["speaker"] = best_speaker
                        current_entry["start"] = word.start
                    
                    current_entry["text"].append(word.word)
                    current_entry["end"] = word.end # 끝 시간 갱신

        # 마지막 잔여 데이터 저장
        if current_entry["text"]:
            final_segments.append({
                "speaker": current_entry["speaker"],
                "text": "".join(current_entry["text"]).strip(),
                "start": current_entry["start"],
                "end": current_entry["end"]
            })

        return final_segments
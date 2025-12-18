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
    class MockConfig:
        HF_TOKEN = os.getenv("HF_TOKEN")
        LOG_LEVEL = "INFO"
        LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        STT_BACKEND = os.getenv("STT_BACKEND", "auto") # auto, openvino, faster_whisper
    config = MockConfig()

# 로깅 설정
logger = logging.getLogger("LocalSTT")
if not logger.handlers:
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)

class DiarizationService:
    """
    로컬 STT 및 화자 분리 통합 서비스 (Hybrid Engine)
    - Backend 1: Faster-Whisper (CPU/CUDA) - Default
    - Backend 2: OpenVINO (Intel GPU/NPU) - Optimized for Intel
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.backend = self._detect_backend()
        
        # 모델 설정
        if self.backend == "openvino":
            # OpenVINO는 Hugging Face 모델 ID 사용
            # [Modified] 2025-12-04: Memory optimization (distil-whisper)
            self.whisper_model_id = "distil-whisper/distil-large-v3" 
            # Intel Arc GPU 사용 시 "GPU" (대소문자 주의)
            self.ov_device = "GPU" 
        else:
            # Faster-Whisper
            if self.device == "cuda":
                self.compute_type = "float16"
                self.whisper_model_size = "large-v3"
            else:
                self.compute_type = "int8"
                self.whisper_model_size = "medium" # CPU에서는 medium 권장

        self.whisper_pipeline = None # OpenVINO용
        self.whisper_model = None    # Faster-Whisper용
        self.diarization_pipeline = None
        
        logger.info(f"🚀 Initializing DiarizationService")
        logger.info(f"   • Backend: {self.backend.upper()}")
        if self.backend == "openvino":
            logger.info(f"   • Device: {self.ov_device} (Intel Optimization)")
        else:
            logger.info(f"   • Device: {self.device.upper()}")
            logger.info(f"   • Compute Type: {self.compute_type}")

    def _detect_backend(self) -> str:
        """환경에 따라 최적의 백엔드 결정"""
        # 1. 설정 강제
        configured = getattr(config, 'STT_BACKEND', 'auto')
        if configured in ['openvino', 'faster_whisper']:
            return configured
            
        # 2. 자동 감지 (Intel GPU 존재 여부 등 확인은 복잡하므로 라이브러리 유무로 판단)
        try:
            import optimum.intel.openvino
            import openvino
            # OpenVINO가 설치되어 있으면 우선 사용
            logger.info("✨ OpenVINO detected. Switching to Intel optimization mode.")
            return "openvino"
        except ImportError:
            return "faster_whisper"

    def _load_whisper(self):
        """Whisper 모델 지연 로딩"""
        if self.backend == "openvino":
            self._load_whisper_openvino()
        else:
            self._load_whisper_faster()

    def _load_whisper_openvino(self):
        """OpenVINO (Optimum) 모델 로드"""
        if self.whisper_pipeline is None:
            logger.info(f"⏳ Loading Whisper (OpenVINO/Intel) - {self.whisper_model_id}...")
            try:
                from optimum.intel.openvino import OVModelForSpeechSeq2Seq
                from transformers import AutoProcessor, pipeline

                # 모델 로드 (export=True는 최초 1회 변환)
                # 주의: 변환된 모델을 로컬에 저장해두고 쓰는 게 빠름. 여기서는 자동 변환.
                model = OVModelForSpeechSeq2Seq.from_pretrained(
                    self.whisper_model_id, 
                    device=self.ov_device,
                    export=True
                )
                processor = AutoProcessor.from_pretrained(self.whisper_model_id)

                self.whisper_pipeline = pipeline(
                    "automatic-speech-recognition",
                    model=model,
                    tokenizer=processor.tokenizer,
                    feature_extractor=processor.feature_extractor,
                    max_new_tokens=128,
                    chunk_length_s=30,
                    batch_size=16,
                )
                logger.info("✅ Whisper (OpenVINO) loaded.")
            except Exception as e:
                logger.error(f"❌ Failed to load OpenVINO Whisper: {e}")
                logger.warning("⚠️ Falling back to faster-whisper (CPU)...")
                self.backend = "faster_whisper"
                self.compute_type = "int8"
                self.whisper_model_size = "medium"
                self._load_whisper_faster()

    def _load_whisper_faster(self):
        """Existing Faster-Whisper Load"""
        if self.whisper_model is None:
            logger.info(f"⏳ Loading Whisper ({self.whisper_model_size})...")
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
                login(token=token)
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
        """입력 오디오/비디오를 16kHz Mono WAV로 변환"""
        file_ext = os.path.splitext(input_path)[1].lower()
        logger.info(f"🔄 Converting to 16kHz Mono WAV for AI processing...")
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        command = [
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1", "-ar", "16000", "-vn", temp_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"   -> Conversion complete: {temp_path}")
            return temp_path
        except subprocess.CalledProcessError:
            logger.error("❌ FFmpeg conversion failed.")
            if os.path.exists(temp_path): os.remove(temp_path)
            return input_path
        except FileNotFoundError:
            logger.error("❌ FFmpeg not found.")
            if os.path.exists(temp_path): os.remove(temp_path)
            return input_path

    def transcribe_and_diarize(self, audio_path: str, language: str = "ko") -> List[Dict[str, Any]]:
        """통합 처리 함수"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        processed_audio = self._convert_to_wav(audio_path)
        
        try:
            # 1. STT
            self._load_whisper()
            logger.info(f"🎙️  Step 1: Transcribing ({self.backend})...")
            
            whisper_segments = []
            
            if self.backend == "openvino":
                # OpenVINO Inference
                # return_timestamps=True 필수
                prediction = self.whisper_pipeline(processed_audio, return_timestamps=True, generate_kwargs={"language": language})
                # 포맷 변환: {'text': '...', 'chunks': [{'text': '...', 'timestamp': (0.0, 5.0)}]}
                for chunk in prediction['chunks']:
                    start, end = chunk['timestamp']
                    whisper_segments.append({
                        "text": chunk['text'],
                        "start": start,
                        "end": end
                    })
            else:
                # Faster-Whisper Inference
                segments_generator, _ = self.whisper_model.transcribe(
                    processed_audio, beam_size=5, word_timestamps=True, language=language
                )
                # 포맷 변환: Faster-Whisper Segment -> Dict
                for seg in segments_generator:
                    whisper_segments.append({
                        "text": seg.text,
                        "start": seg.start,
                        "end": seg.end
                    })

            # 2. Diarization
            self._load_diarization()
            logger.info(f"👥 Step 2: Diarizing speakers...")
            diarization_result = self.diarization_pipeline(processed_audio)
            
            # 3. Merge
            logger.info(f"🔄 Step 3: Merging results...")
            final_result = self._merge_results(whisper_segments, diarization_result)
            
            return final_result
            
        finally:
            if processed_audio != audio_path and os.path.exists(processed_audio):
                try:
                    os.remove(processed_audio)
                except OSError: pass

    def _merge_results(self, whisper_segments, diarization_result) -> List[Dict[str, Any]]:
        """Whisper 세그먼트와 화자 정보를 병합 (개선된 로직 적용 예정)"""
        final_segments = []
        speaker_turns = []
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            speaker_turns.append((turn.start, turn.end, speaker))

        current_entry = {"speaker": None, "text": [], "start": 0.0, "end": 0.0}

        # Whisper Segment 단위로 처리 (Faster-Whisper와 OpenVINO 포맷 통일됨)
        for seg in whisper_segments:
            # 세그먼트의 중간 시간값으로 화자 판별
            # OpenVINO는 word timestamp를 안 줄 수도 있으므로 segment 단위 매칭
            seg_start = seg['start']
            seg_end = seg['end']
            if seg_end is None: seg_end = seg_start + 1.0 # 방어 코드
            
            mid_time = (seg_start + seg_end) / 2
            best_speaker = "Unknown"
            
            # 해당 시간에 말하고 있는 화자 찾기
            for spk_start, spk_end, spk_label in speaker_turns:
                if spk_start <= mid_time <= spk_end:
                    best_speaker = spk_label
                    break
            
            # 화자 변경 감지
            if current_entry["speaker"] is not None and best_speaker != current_entry["speaker"]:
                final_segments.append({
                    "speaker": current_entry["speaker"],
                    "text": "".join(current_entry["text"]).strip(),
                    "start": current_entry["start"],
                    "end": current_entry["end"]
                })
                current_entry = {
                    "speaker": best_speaker,
                    "text": [seg['text']],
                    "start": seg_start,
                    "end": seg_end
                }
            else:
                if current_entry["speaker"] is None:
                    current_entry["speaker"] = best_speaker
                    current_entry["start"] = seg_start
                
                current_entry["text"].append(seg['text'])
                current_entry["end"] = seg_end

        if current_entry["text"]:
            final_segments.append({
                "speaker": current_entry["speaker"],
                "text": "".join(current_entry["text"]).strip(),
                "start": current_entry["start"],
                "end": current_entry["end"]
            })

        return final_segments

# 싱글톤 인스턴스
diarization_service = DiarizationService()
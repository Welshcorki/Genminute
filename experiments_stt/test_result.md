# 🧪 Genminute STT & Diarization Test Report

**Date:** 2025-12-02  
**Environment:** Windows (Conda `genminute_stt`)  
**Module:** `services/diarization.py`

## 1. 테스트 개요
로컬 STT 및 화자 분리 파이프라인의 안정성과 호환성을 검증하기 위해 수행된 테스트 기록입니다.

## 2. 주요 테스트 항목 및 결과

### ✅ Test 1: 의존성 충돌 해결 (Dependency Resolution)
*   **목표:** `pyannote.audio`와 `huggingface_hub` 간의 API 불일치 해결.
*   **증상:** `TypeError: hf_hub_download() got an unexpected keyword argument 'use_auth_token'`
*   **원인:** Pyannote 3.x는 구형 `use_auth_token` 인자를 사용하지만, 최신 HuggingFace Hub는 이를 제거함.
*   **조치:** `huggingface_hub`를 `0.19.4`로 다운그레이드.
*   **결과:** 인증 및 모델 다운로드 정상 작동 확인.

### ✅ Test 2: 오디오 포맷 호환성 (FFmpeg Preprocessing)
*   **목표:** `.mp4`, `.webm` 등 다양한 포맷 처리를 위한 자동 변환 로직 검증.
*   **증상:** `soundfile.LibsndfileError: Format not recognised` (MP4 직접 로드 시).
*   **조치:** `FFmpeg`를 사용하여 입력 파일을 무조건 `16kHz Mono WAV` 임시 파일로 변환하는 로직 추가.
*   **결과:** `.mp4` 파일 테스트 시 성공적으로 `.wav`로 변환되어 처리됨.

### ✅ Test 3: 파이프라인 통합 동작 (End-to-End)
*   **목표:** 변환 -> STT(Whisper) -> 화자분리(Pyannote) -> 병합 과정의 완결성 확인.
*   **방법:**
    1.  실제 파일 (`e618...mp4`) 테스트: 성공 (한글 텍스트 추출 + 화자 분리 완료).
    2.  더미 파일 (무음 WAV) 테스트: 성공 (에러 없이 빈 리스트 반환).
*   **결과:** 모든 단계가 에러 없이 수행되고, 임시 파일도 정상적으로 정리됨.

## 3. 최종 검증된 환경 (Requirements)
이 테스트를 통과한 의존성 조합은 다음과 같습니다.

```txt
numpy<2.0
torch==2.5.1
torchaudio==2.5.1
huggingface_hub<0.20.0  # Critical for Pyannote 3.3.1
faster-whisper
pyannote.audio==3.3.1
ffmpeg (System installed)
```

## 4. 결론
`services/diarization.py` 모듈은 현재 **Production Ready** 상태입니다.
입력 파일의 확장자에 상관없이 안정적으로 텍스트 변환 및 화자 분리를 수행할 수 있습니다.

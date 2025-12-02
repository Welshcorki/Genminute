# 🎙️ Genminute 로컬 STT 파이프라인 개발 일지

## 📅 2025-12-02 (화) 작업 내역

### 1. 목표
- 외부 API(OpenAI) 의존도를 낮추고, 로컬 환경에서 동작하는 STT 및 화자 분리 시스템 구축.
- `faster-whisper` (고속 STT) + `pyannote.audio` (SOTA 화자 분리) 조합 실험.

### 2. 진행 상황
- [x] **실험 환경 구축:** `experiments_stt/` 폴더 격리 및 파이프라인 코드(`local_stt_pipeline.py`) 작성.
- [x] **라이브러리 이슈 해결 1 (PyTorch 보안):** 
    - PyTorch 2.6+에서 `weights_only=True` 강제 정책으로 인해 구형 모델 로딩 실패 발생.
    - `torch.load`를 Monkey Patching하는 대신, **안정적인 구버전(3.1.1)으로 다운그레이드** 결정.
- [x] **라이브러리 다운그레이드:**
    - `pyannote.audio` -> `3.1.1`
    - `torch` -> `2.3.1`
    - `torchaudio` -> `2.3.1`
- [x] **NumPy 2.0 호환성 문제 해결:**
    - `pyannote.audio` 등 구형 라이브러리는 NumPy 1.x에 의존.
    - `numpy<2.0`으로 다운그레이드하여 `np.NaN` 관련 에러 해결.
- [x] **Hugging Face Hub 인증 이슈 해결 (Dependency Hell 탈출):**
    - **문제:** `pyannote.audio 3.3.1`은 구형 API(`use_auth_token`)를 사용하나, 최신 `huggingface_hub`는 이를 제거함.
    - **시도:** 코드 수정(`token`으로 변경)은 라이브러리 내부 호출 에러로 실패.
    - **해결:** `huggingface_hub<0.20`으로 다운그레이드하여 호환성 확보.
- [x] **최적화된 파이프라인 구축:**
    - **전략:** `WebM/MP4` 등 입력 포맷에 상관없이 `FFmpeg`로 즉시 `16kHz Mono WAV`로 변환하여 처리.
    - **이점:** 불필요한 중간 변환(MP4 저장 등) 제거로 처리 속도 및 호환성 극대화.
- [x] **서비스 모듈화 완료:**
    - `services/diarization.py` 생성 및 단위 테스트 통과.

### 3. 🛠️ 최종 환경 설정 (Golden Set)
- **Python:** 3.11.13
- **NumPy:** < 2.0 (1.26.4)
- **PyTorch:** 2.5.1 (Stable)
- **Pyannote.Audio:** 3.3.1 (Stable)
- **HuggingFace Hub:** 0.19.4 (Compatible with Pyannote 3.3.1)
- **FFmpeg:** 필수

### 4. 🚀 다음 작업 (Action Item)
1.  `app.py`에 API 엔드포인트 연결 (오디오 업로드 -> 분석 결과 반환).
2.  프론트엔드 UI 연동 (진행 상태 표시 등).

---
**작성자:** Gemini CLI Agent
# GenMinute 개발 일지 (Dev Log)

## 2025년 11월 30일 - 실시간 녹음 및 모바일 대응 기능 구현 (Phase 1)

### 1. 개요 (Overview)
기존 파일 업로드 방식의 한계를 극복하고, 대면 회의 및 Zoom 화상 회의를 즉시 기록할 수 있는 '유니버설 웹 레코더' 기능을 구현함. 또한 모바일 환경에서의 사용성을 개선하기 위해 UI/UX를 최적화함.

### 2. 주요 변경 사항 (Changes)

#### 📱 모바일 UI/UX 개선
*   **문제:** 모바일 접속 시 메뉴가 화면을 가리고, 챗봇 사이드바가 자동 개방되어 사용성 저해.
*   **해결:**
    *   `templates/layout.html`: 모바일 전용 헤더(햄버거 메뉴) 및 오버레이 추가.
    *   `static/css/style.css`: 반응형 미디어 쿼리(`max-width: 768px`) 적용. 사이드바 메뉴를 슬라이드 방식으로 변경.
    *   `static/js/script.js`: 모바일 환경 감지 시 챗봇 자동 열림 방지 로직 추가.

#### 🎙️ 실시간 녹음 기능 (GenMinute Live Phase 1)
*   **아키텍처 결정:** '에이전트 Tool' 방식 대신 **'웹앱 모듈 확장'** 방식을 채택하여 모바일 호환성과 OS 독립성 확보.
*   **신규 모듈:**
    *   `routes/live_record.py`: 녹음 페이지 라우팅 (`/record`).
    *   `templates/live/recorder.html`: 마이크/시스템 오디오 탭 기반 녹음 UI. 파형 시각화(Visualizer) 포함.
    *   `static/js/live/recorder.js`: 
        *   `getUserMedia`: 모바일/마이크 녹음.
        *   `getDisplayMedia`: PC 시스템 오디오(Zoom, Youtube 등) 캡처.
        *   녹음 종료 시 `Blob` 데이터를 생성하여 기존 `/upload` 파이프라인으로 전송 (백엔드 수정 최소화).
*   **연동:** 메인 네비게이션에 '실시간 녹음' 메뉴 추가.

### 3. 기술적 특징 (Technical Notes)
*   **시스템 오디오 캡처:** 별도의 드라이버 설치 없이 브라우저의 `getDisplayMedia` API를 활용하여 Zoom 회의 소리를 깨끗하게 녹음 가능.
*   **통합 파이프라인:** 녹음된 데이터는 기존 업로드 로직을 그대로 타므로, STT/요약/마인드맵 생성 등의 후처리 과정이 동일하게 적용됨.

### 4. 향후 계획 (Next Steps)
*   **Phase 2:** WebSocket(`Flask-SocketIO`)을 도입하여 녹음 중 실시간으로 텍스트가 변환되는 '준실시간 미리보기' 기능 구현 예정.

---

## 2025년 11월 30일 - 실시간 녹음/녹화 기능 디버깅 및 개선 (Phase 1 연장)

### 1. 개요 (Overview)
실시간 녹음/녹화 기능의 초기 테스트 과정에서 발생한 문제들을 분석하고 수정하여, 사용자 경험을 개선하고 시스템 안정성을 확보함. 특히 PC 시스템 오디오 캡처 시 비디오 트랙을 포함하여 녹화하는 기능을 추가하고, 서버-클라이언트 간의 에러 리포팅을 강화함.

### 2. 주요 변경 사항 (Changes)

#### 📝 블루프린트 임포트 버그 수정
*   **문제:** `routes/__init__.py`에서 `auth_bp`, `meetings_bp`, `chat_bp` 등 핵심 블루프린트 임포트 누락으로 서버 시작 시 오류 발생 가능성.
*   **해결:** `routes/__init__.py` 파일에 누락된 블루프린트 임포트 구문 추가하여 정상적인 라우트 등록 보장.

#### 📹 실시간 녹음/녹화 기능 개선 (프론트엔드 - `static/js/live/recorder.js`)
*   **PC 시스템 녹화 에러 해결:**
    *   **문제:** `getDisplayMedia`로 얻은 비디오+오디오 스트림을 오디오 전용 `mimeType`으로 `MediaRecorder.start()` 호출 시 `NotSupportedError` 발생.
    *   **해결:** `type`이 'mic'일 때는 오디오 전용 `mimeType`을, 'sys'일 때는 `video/webm`과 같은 비디오+오디오 `mimeType`을 사용하도록 `startRecording` 함수 수정. PC 시스템 녹화 시 `getDisplayMedia` 스트림을 그대로 `MediaRecorder`에 전달하여 비디오 녹화도 가능하도록 변경.
*   **업로드 후 리다이렉트 문제 해결:**
    *   **문제:** `/upload` API 호출 후 서버로부터 SSE 응답을 받지만, `redirect` 필드를 포함한 `complete` 메시지를 제대로 파싱하지 못해 "완료되었으나 이동할 주소를 찾지 못했습니다." 팝업 발생.
    *   **해결:** `fetch` 응답의 SSE 스트림을 파싱하는 로직을 강화하고, `complete` 메시지 수신 시 `redirectUrl`로 정확히 이동하도록 수정. 서버 연결 종료 시 발생하는 알림 메시지 로직을 보완.
*   **PC 시스템 녹화 시 영상 포함 기능 추가:**
    *   **요구사항:** PC 시스템 오디오 캡처 시 음성뿐만 아니라 영상도 함께 녹화하여 화상 회의 기록 기능 강화.
    *   **해결:** `MediaRecorder`의 `mimeType`을 비디오+오디오를 지원하는 `video/webm` 등으로 변경하고, 녹화 완료 후 미리보기 재생 시 `audio` 태그 대신 동적으로 생성된 `video` 태그를 사용하도록 수정.
*   **하이브리드 파일명 적용 (보안 강화 및 확장성 고려):**
    *   **문제:** 기존 파일명은 내용을 파악하기 어렵고, 제목을 그대로 쓰면 보안 위험과 확장성 문제가 있음.
    *   **해결:** `[prefix]_[날짜시간]_[제목].webm` 형식을 시도했으나, 보안과 향후 시리즈 관리 확장성을 고려하여 제목을 제외한 `[UUID]_[prefix]_[날짜시간].mp4` 형식을 최종 채택. 뷰어에서는 DB에 저장된 메타데이터(제목, 날짜)를 사용하여 정보를 표시하도록 설계.

#### 💾 백엔드 파일 처리 로직 보완 (`services/upload_service.py`, `config.py`)
*   **문제:** 프론트엔드에서 `.webm` 파일(특히 시스템 녹화 시 영상 포함)을 업로드해도, 백엔드의 `save_uploaded_file` 함수가 `.mp4`만 비디오로 인식하여 적절한 오디오 추출 로직(`convert_video_to_audio`)을 거치지 않음. 또한 `config.py`의 `ALLOWED_EXTENSIONS`에 `webm`이 누락되어 업로드 자체가 거부되는 문제 발견.
*   **해결:** `config.py`에 `webm` 확장자 허용 추가. `save_uploaded_file` 함수에서 `.webm` 확장자도 비디오 파일로 인식하도록 `is_video` 판단 로직을 확장.
*   **FFmpeg 상세 로깅 추가:** `convert_video_to_audio` 메서드 내 `subprocess.run` 호출 후 `stdout`과 `stderr` 내용을 로그로 출력하여 FFmpeg 실행 결과 디버깅 용이성 확보.
*   **자동 포맷 변환 및 호환성 확보 (표준화):**
    *   **문제:** 다양한 확장자(`.webm` 등)가 업로드되면 뷰어 호환성 문제가 발생할 수 있음.
    *   **해결:** `convert_webm_to_compatible_format` 메서드를 추가하여, 파일명 접두어(`video_`) 유무에 따라 `.webm` 파일을 호환성 높은 `.mp4` (비디오) 또는 `.m4a` (오디오)로 자동 변환하도록 구현.
*   **DB 저장 파일명 불일치 해결:**
    *   **문제:** DB에 최종 변환된 파일명(.mp4/.m4a)이 아닌 STT 임시 파일명(_converted.wav)이 저장되어 뷰어에서 404 오류 발생.
    *   **해결:** `process_audio_file` 메서드에 `original_filename` 인자를 추가하여, DB 저장 시 최종 변환된 파일명을 명시적으로 지정할 수 있도록 수정.

#### 🚨 서버 에러 리포팅 및 라우팅 강화 (`routes/meetings.py`)
*   **문제:** `/upload` API 처리 중 서버에서 예외가 발생하면 클라이언트에 구체적인 에러 메시지를 전달하지 않고 연결이 끊어져, 클라이언트에서 "서버 연결이 종료되었습니다."라는 모호한 메시지만 표시됨.
*   **해결:** `upload_and_process` 함수 내 `generate` 제너레이터의 `try-except` 블록을 수정하여, 예외 발생 시 로그만 출력하는 대신 클라이언트에 에러 정보가 담긴 JSON 메시지(SSE 형식)를 전송하도록 변경.
*   **자동 변환 로직 연결:** 업로드된 파일이 `.webm`인 경우, `upload_and_process` 함수 시작 부분에서 `upload_service.convert_webm_to_compatible_format`을 호출하여 표준 포맷(.mp4/.m4a)으로 변환 후 후속 처리를 진행하도록 수정.

#### 📺 뷰어 호환성 개선 (`static/js/viewer.js`)
*   **문제:** 뷰어가 파일명이나 확장자에 따라 비디오/오디오 플레이어를 선택하는데, `.webm` 파일에 대한 처리가 미흡하여 재생되지 않는 문제 발생.
*   **해결:** 서버에서 표준 포맷(`.mp4`, `.m4a`)으로 변환하여 저장하므로, 뷰어 로직을 단순화하여 `.mp4` 확장자일 경우 비디오 플레이어를, 그 외(`.m4a` 등)일 경우 오디오 플레이어를 사용하도록 수정. 이를 통해 모든 브라우저와 OS에서 완벽한 재생 호환성 확보.

### 3. 현재 상태 (Status)
*   **기능 동작 확인:** PC 환경에서 마이크 녹음 및 시스템 녹화(영상 포함) 기능이 정상 작동하며, 각각 음성만, 또는 영상과 음성이 함께 녹화됨.
*   **자동 변환 및 재생:** 녹화된 `.webm` 파일이 서버 업로드 후 자동으로 `.mp4` 또는 `.m4a`로 변환되며, 뷰어 페이지에서 적절한 플레이어(비디오/오디오)로 정상 재생됨을 확인.
*   **STT 및 요약:** Google Gemini를 이용한 STT 및 요약 생성, 회의록 생성 기능이 정상 작동함.
*   **에러 해결:** FFmpeg 경로 설정 문제 및 OpenAI API Quota Exceeded 문제(임베딩 생성 시 발생)를 확인하고 해결 방안(터미널 재시작, 결제 또는 Gemini 임베딩 전환)을 모색함.

### 4. 다음 계획 (Next Steps)
*   **Phase 2 (준실시간 미리보기):** WebSocket(`Flask-SocketIO`)을 도입하여 녹음 중 실시간으로 텍스트가 변환되는 기능 구현.
*   **파일 시스템 및 DB 구조 고도화 (중장기):**
    *   **보안 강화:** 파일명을 `[UUID].mp4` 형식으로 완전 난수화하여 물리적 파일명에서 민감 정보를 제거.
    *   **사용자 경험 개선:** 파일 다운로드 시 `Content-Disposition` 헤더를 활용하여 사용자가 지정한 제목(`날짜_제목.mp4`)으로 파일이 저장되도록 구현.
    *   **확장성 확보:** DB 스키마에 `series_id` 등을 추가하여, 파일명 의존 없이 DB 관계(Relation)를 통해 '시리즈 회의' 묶기 기능 구현.
*   **OpenAI API 이슈 해결 (보류):** 벡터 임베딩 생성 시 간헐적인 429 에러가 발생했으나 현재는 정상 작동 중이므로, 추후 Gemini 임베딩 모델로의 전환 등 근본적인 해결책을 적용할 예정.

---

## 2025년 12월 02일 - 로컬 STT 파이프라인 개발 및 통합 (Gemini 작업분)

### 1. 목표
- 외부 API(OpenAI) 의존도를 낮추고, 로컬 환경에서 동작하는 STT 및 화자 분리 시스템 구축.
- `faster-whisper` (고속 STT) + `pyannote.audio` (SOTA 화자 분리) 조합 실험.
- **[추가]** 다른 AI가 작업한 '캘린더 연동' 기능과 충돌 없이 병합 및 환경 통합.

### 2. 진행 상황 (로컬 STT 구축)
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
    - **해결:** `huggingface_hub` 버전을 `0.19.4`로 다운그레이드하여 호환성 확보.
- [x] **최적화된 파이프라인 구축:**
    - **전략:** `WebM/MP4` 등 입력 포맷에 상관없이 `FFmpeg`로 즉시 `16kHz Mono WAV`로 변환하여 처리.
    - **이점:** 불필요한 중간 변환(MP4 저장 등) 제거로 처리 속도 및 호환성 극대화.
- [x] **서비스 모듈화 완료:**
    - `services/diarization.py` 생성 및 단위 테스트 통과.

### 3. 🤝 통합 및 환경 설정 (Integration)
- [x] **Git 병합 (Merge):** 다른 AI의 '캘린더 연동 기능' 작업분을 `git pull` 및 `merge` 완료.
- [x] **코드 통합:**
    - `services/upload_service.py`에 캘린더 로직(AgentService)은 유지하고, STT 로직만 `DiarizationService`(로컬)로 교체.
    - `config.py` 복구 및 필수 환경 변수(`HF_TOKEN`, `GOOGLE_CLIENT_ID`) 통합.
- [x] **패키지 환경 통합 (`genminute`):**
    - 기존 웹 서버 환경과 로컬 STT 환경의 의존성 충돌 해결.
    - **해결책:** `huggingface_hub<0.20`, `faster-whisper==1.2.0`으로 버전 고정.
    - 누락된 패키지(`langchain-google-genai`, `google-auth-oauthlib`) 설치 완료.

### 4. 🛠️ 최종 환경 설정 (Golden Set)
- **Python:** 3.11.13
- **NumPy:** < 2.0 (1.26.4)
- **PyTorch:** 2.3.1 (Stable)
- **Pyannote.Audio:** 3.1.1 (Stable)
- **HuggingFace Hub:** 0.19.4 (Compatible)
- **Faster-Whisper:** 1.2.0
- **Flask:** 3.1.2
- **FFmpeg:** 필수

### 5. ✅ 최종 결과 (Completed)
- 서버(`app.py`) 정상 구동 확인.
- 로컬 STT 모듈 초기화 성공 (`🚀 Initializing DiarizationService`).
- **환경 이주 완료:** `genminute_stt` 통합 환경 구축 및 메인 환경으로 승격.
- **파이프라인 최적화 완료:**
    - 업로드 시 MP4 변환 로직 주석 처리 (속도 향상).
    - 무음/환각 문구 필터링 및 요약 스킵 로직 적용 (Fail-Fast).

### 6. 🚀 향후 계획 (Next Steps)
*   **GPU 메모리 최적화 (OpenVINO):**
    - `distil-whisper/distil-large-v3` 경량화 모델 도입.
    - `batch_size=1` 설정을 통한 Intel Arc GPU 메모리 이슈 해결.
*   **화자 분리 정확도 향상:** 화자 매칭 알고리즘 개선.

### 7. ⚠️ 이슈 리포트 (2025-12-03 추가)
*   **증상:** OpenVINO 가속 활성화 후 `openai/whisper-large-v3` 모델 로딩 중 `CL_OUT_OF_RESOURCES` 에러 발생.
*   **해결 계획:** 상기 '향후 계획'의 모델 경량화 적용 예정.

---

## 2025년 12월 02일 - AI 에이전트(Action Item) 기능 개발 및 통합

### 1. 목표
- `ROADMAP.md`의 1단계 과제인 'AI 비서 및 일정 연동' 기능의 핵심부 개발.
- 회의록 텍스트에서 Action Item을 자동으로 인식하고, 외부 도구(Google Calendar)와 연동하는 기반 마련.

### 2. 아키텍처 결정 및 논의
- **'모듈' vs '도구' 논의:** 초기에는 재사용 가능한 '모듈'로 접근했으나, 사용자의 명확한 요구사항에 따라 **LLM의 추론 능력을 활용하는 '지능형 에이전트'**로 방향을 재설정함.
- **LangChain vs LangGraph:** 단순 에이전트 루프의 한계를 인지하고, 복잡한 워크플로우를 명시적으로 제어할 수 있으며 상태 관리에 용이한 **LangGraph를 최종 아키텍처로 채택**함. 이 결정은 `ROADMAP.md`에도 반영하여 공식화함.

### 3. 주요 변경 사항
1.  **`tools/google_calendar_tool.py` 생성:**
    - 에이전트가 사용할 '일정 추가' 도구를 Pydantic 스키마와 함께 정의.
    - 실제 API 호출 대신, LLM의 함수 호출(Function Calling) 능력을 검증하기 위한 시뮬레이션 코드로 구현.

2.  **`services/agent_service.py` 생성:**
    - LangGraph를 사용하여 '추출 및 실행' 워크플로우를 가진 `AgentService` 구현.
    - `StateGraph`를 통해 에이전트의 상태(회의록, 메시지 등)를 관리.
    - `tool_choice="any"` 옵션을 적용하여, LLM이 텍스트로 답변하는 대신 반드시 도구를 호출하도록 강제하여 안정성 확보.

3.  **기존 코드 리팩토링 및 통합:**
    - 기능이 중복되고 혼동을 유발하는 구버전 `schedule_manager/agent.py` 파일 삭제.
    - `services/upload_service.py`의 `process_audio_file` 함수 마지막 단에 `AgentService` 호출 로직을 추가하여, STT 처리 완료 후 자동으로 Action Item 추출 프로세스가 실행되도록 전체 워크플로우에 통합.

### 4. 결과
- 파일 업로드 시, STT 처리부터 LangGraph 에이전트 호출, 그리고 최종적인 (시뮬레이션) 도구 실행까지 이어지는 **End-to-End 파이프라인 구축 완료.**
- Flask 서버 로그를 통해 LLM이 자연어(예: '이번 주 금요일')를 정확한 날짜(`2025-12-05`)로 추론하고, 올바른 인자와 함께 `add_calendar_event` 도구를 호출함을 확인함.

### 5. 다음 단계
- `AgentService`가 단일 Action Item만 처리하는 한계를 개선.
- 실제 Google Calendar API OAuth 2.0 연동 및 사용자 승인 플로우 구현.
- 에이전트의 처리 결과를 사용자에게 시각적으로 피드백하는 UI 구현.

---

## 2025년 12월 02일 (추가) - Google Calendar 연동 파이프라인 구축

### 1. 목표
- 실제 Google Calendar API 연동을 위한 사용자 인증(OAuth 2.0) 기반 마련 및 실제 API 호출 기능 구현.

### 2. 주요 변경 사항
1. **Google OAuth 2.0 설정:**
   - `.env` 및 `config.py`에 Google OAuth 2.0 클라이언트 ID 및 보안 비밀을 환경 변수로 추가.
   - `init_db.py`의 `users` 테이블 스키마에 인증 정보 저장을 위한 `google_auth_credentials_json` 컬럼 추가.
   - `init_db.py`의 `print` 구문을 `logging` 모듈로 대체하여 유니코드 인코딩 오류 해결.

2. **사용자 인증 흐름 구현:**
   - Google 인증을 시작(`.../start`)하고 콜백(`.../oauth2callback`)을 처리하는 `routes/google_auth.py` 블루프린트 생성 및 등록.
   - `utils/db_manager.py`에 사용자 인증 정보를 DB에 저장하고 조회하는 함수 추가.
   - `templates/notes.html`에 인증 시작을 위한 'Google Calendar 연동' 버튼 UI 추가.
   - 개발 환경의 HTTP 연결에서 발생하는 `InsecureTransportError` 해결을 위해 `OAUTHLIB_INSECURE_TRANSPORT` 환경 변수 설정.

3. **실제 API 연동 구현:**
   - `tools/google_calendar_tool.py`의 시뮬레이션 함수를 실제 Google Calendar API(`service.events().insert()`)를 호출하는 코드로 교체.
   - `agent_service.py`와 `upload_service.py`를 수정하여, `user_id`를 도구 함수까지 전달하는 파이프라인 완성.

### 3. 결과
- 사용자가 UI를 통해 Google 계정 접근 권한을 승인하고, 발급된 인증 토큰(Refresh Token)을 데이터베이스에 안전하게 저장하는 전체 인증 파이프라인 구축 완료.
- `redirect_uri_mismatch` 및 `InsecureTransportError` 등 OAuth 2.0 연동 과정에서 발생한 주요 오류 해결.
- AI 에이전트가 실제 사용자 계정의 캘린더에 접근하여 일정을 생성할 수 있는 모든 기술적 기반이 마련됨.

---

## 2025년 12월 04일 - 로컬 STT (OpenVINO) 메모리 최적화 계획 (보류됨)

### 1. 문제 상황
- Intel Arc GPU에서 OpenVINO를 사용하여 STT를 수행할 때, 기본 `batch_size=16` 설정으로 인해 VRAM 부족(`CL_OUT_OF_RESOURCES`) 오류가 발생함.
- CPU로 실행 시 메모리 문제는 없으나 처리 속도가 매우 느림.

### 2. 해결 계획 (To-Be)
- **목표:** GPU 가속의 이점을 살리면서 메모리 오류를 방지.
- **전략:** `batch_size`를 `1`로 줄여 VRAM 사용량을 최소화.
- **작업 내용:**
    - `services/diarization.py` 내 `_load_whisper_openvino` 메서드 수정.
    - `pipeline` 호출 시 `batch_size=1` 파라미터 적용.
    - **주의:** 모델은 한국어 지원을 위해 `openai/whisper-large-v3` (또는 `medium`)을 유지해야 함. (`distil-whisper`는 영어 전용이므로 사용 불가)

### 3. 결정 사항
- 현재는 다른 우선순위 작업에 집중하기 위해 이 최적화 작업을 **보류**하고, 추후 성능 개선 단계에서 진행하기로 함.

---

## 2025년 12월 04일 - Action Item DB 저장 구조 설계 (보류됨)

### 1. 개요
- AI 에이전트가 캘린더에 등록한 일정(Action Item)을 데이터베이스에 영구 저장하여, UI에서 이력을 조회할 수 있도록 하는 기능을 설계함.
- 현재는 설계를 확정하고 기록만 남긴 뒤, 실제 구현은 추후 진행하기로 결정함.

### 2. 설계 내용 (To-Be)

#### 1) 데이터베이스 스키마 (`meeting_action_items` 테이블)
- **목적:** 회의별로 생성된 Action Item과 외부 도구(Calendar) 연동 결과를 저장.
- **구조:**
  ```sql
  CREATE TABLE IF NOT EXISTS meeting_action_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      meeting_id TEXT NOT NULL,       -- 회의 ID (Foreign Key)
      content TEXT NOT NULL,          -- 할 일 내용 (예: "기획안 제출")
      due_date TEXT,                  -- 마감 기한 (예: "2025-12-10 14:00")
      status TEXT DEFAULT 'pending',  -- 상태 (pending, done, failed)
      tool_call_id TEXT,              -- (선택) 연동된 도구의 추적 ID
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```

#### 2) 백엔드 로직 변경 (`utils/db_manager.py`)
- `_initialize_tables()`: 위 테이블 생성 SQL 추가.
- `save_action_items(meeting_id, items)`: 에이전트 실행 결과 리스트를 받아 DB에 저장하는 함수 추가.
- `get_action_items_by_meeting_id(meeting_id)`: UI 표시를 위한 조회 함수 추가.
- `delete_meeting_by_id(meeting_id)`: 회의 삭제 시 연관된 Action Item도 함께 삭제되도록 수정.

#### 3) 파이프라인 흐름
1.  오디오 업로드 & STT
2.  Agent 실행 (캘린더 등록)
3.  **[NEW]** 등록된 일정 정보를 `meeting_action_items`에 저장
4.  Viewer 페이지에서 해당 정보 조회 및 표시

### 3. 향후 계획
- 이 설계는 `ROADMAP.md`의 'AI 비서' 고도화 단계에서 우선적으로 구현될 예정임.

---

## 2025년 12월 10일 - 작업 요약 (Refactoring)

### 1. 구조 리팩토링 (Layered Architecture 적용)
* **utils/ 내 파일을 역할별로 분리:**
    - `services/`: `stt_service.py`, `chat_service.py`, `analysis_service.py`, `user_service.py`, `firebase_service.py`, `agent_service.py`
    - `database/`: `sqlite_manager.py`, `vector_manager.py`
    - `tools/`: `google_calendar_tool.py`, `generate_roadmap_mindmap.py`
* 전체 프로젝트 import 경로 수정 완료.

### 2. 코드 품질 개선
* **Logging:** `services/upload_service.py`, `services/agent_service.py`, `tools/` 내 파일들의 `print()`를 `logger`로 교체.
* **Config:** `services/agent_service.py` 등에서 `load_dotenv` 제거 및 `config` 모듈 사용 통일.

### 3. 에러 처리
* `services/stt_service.py`의 `_parse_mmss_to_seconds` 등 일부 메서드에서 `except:` (Bare except) 제거 및 구체적 예외 처리 적용.

### 4. 다음 예정 작업
* 남은 bare except 구문 수정.
* 프론트엔드 React 전환 시작.
* 로컬 STT 기능 정식 통합.

---

## 2025년 12월 11일 - 예외 처리 개선 및 작업 우선순위 조정

### 1. 목표
- 코드 안정성 향상 및 디버깅 용이성을 위해 모든 'bare except'(`except:`) 구문을 찾아 구체적인 예외 처리로 변경함.
- 프로젝트의 다음 단계로 프론트엔드 개선(React 전환)에 집중하기 위해 STT 관련 작업을 후순위로 조정.

### 2. 변경 사항 (Refactoring)
#### `services/stt_service.py`
*   `_parse_mmss_to_seconds`: `except:` → `except (ValueError, IndexError):`
    - 시간 문자열 파싱 중 발생할 수 있는 포맷 오류만 잡도록 수정.
*   `generate_minutes`: `except:` → `except ValueError:`
    - 날짜 문자열 파싱 오류만 잡도록 수정.

#### `services/upload_service.py`
*   `convert_webm_to_compatible_format`: `except:` → `except OSError:`
    - `os.remove` 실패(파일 없음, 권한 부족 등)만 잡도록 수정.
*   `convert_webm_to_mp4`: `except:` → `except OSError:`
    - 동일하게 파일 삭제 실패 시의 예외 처리 구체화.

### 3. 검증
*   `services/` 및 `database/` 디렉토리 내 주요 파일(`sqlite_manager.py`, `vector_manager.py`, `agent_service.py`) 전수 검사 완료.
*   추가적인 bare except 구문 없음 확인.

### 4. 다음 계획 (Priorities Changed)
*   **프론트엔드 React 전환 (Phase 2 Start) [최우선]:**
    - Vite 프로젝트 초기화.
    - 기존 Jinja2 템플릿의 UI 컴포넌트화.
*   **로컬 STT 기능 정식 통합 [보류]:**
    - 프론트엔드 전환 완료 후 또는 필요 시 병행 진행하는 것으로 조정됨.

---

## 2025년 12월 11일 (2차) - 프론트엔드 React 전환 기초 공사 (Phase 2 Start)

### 1. 목표
- Flask + Jinja2 기반의 기존 웹 구조를 Vite + React + TypeScript 기반의 SPA(Single Page Application)로 전환하여 사용자 경험 및 개발 효율성을 극대화함.
- 프론트엔드(React)와 백엔드(Flask) 간의 API 통신 및 OAuth 로그인 연동을 완료함.

### 2. 진행 상황 (Frontend Setup)
#### 프로젝트 초기화 및 환경 설정
*   **Vite 프로젝트 생성:** `frontend` 디렉토리에 React + TypeScript 템플릿으로 프로젝트 초기화.
*   **필수 라이브러리 설치:** `axios` (API 통신), `react-router-dom` (라우팅), `lucide-react` (아이콘), `tailwindcss` (스타일링).
*   **Tailwind CSS v3 적용:** Tailwind v4 설정 충돌 이슈를 해결하기 위해 안정적인 v3 버전으로 다운그레이드 및 설정 파일(`tailwind.config.js`, `postcss.config.js`) 표준화.

#### UI/UX 기초 구현
*   **라우팅 구조 설계 (`App.tsx`):**
    *   `/` (대시보드), `/login` (로그인), `/notes` (회의록 목록), `/record` (녹음) 경로 설정.
*   **공통 레이아웃 컴포넌트 (`components/Layout.tsx`):**
    *   반응형 헤더 및 사이드바 구현 (모바일 햄버거 메뉴 포함).
    *   `Outlet`을 사용하여 페이지 콘텐츠 렌더링 영역 지정.
    *   헤더 디자인 개선: 헤더 높이 증가, 로고 확대(`h-16`), 'Dark & Gold' 테마 색상 적용.
*   **로그인 페이지 (`pages/Login.tsx`):**
    *   Google 로그인 버튼 중심의 심플한 UI 구현.
*   **메인 대시보드 (`pages/Dashboard.tsx`):**
    *   환영 메시지, 통계 요약 카드, 최근 회의록 미리보기 UI 구현.
    *   디자인 고도화: 배경 그라데이션, 입체감 있는 카드, 세련된 타이포그래피 및 색상(Slate & Amber) 적용.
    *   **실제 데이터 연동:** 로그인한 사용자 이름 및 회의록 목록 표시.

### 3. 백엔드 연동 및 트러블슈팅 (Backend Integration)
#### API 및 보안 설정
*   **CORS 설정:** `flask-cors` 도입하여 프론트엔드(`localhost:5173`)와 백엔드(`localhost:5000`) 간 통신 허용.
*   **API 서비스 모듈 (`frontend/src/services`):** `axios` 인스턴스 설정 및 `authService` 구현.

#### Google OAuth 로그인 연동 (성공)
*   **이슈:** `redirect_uri_mismatch` (구글 콘솔 설정과 코드 불일치), `Invalid state parameter` (도메인 불일치), `NameError` (import 누락).
*   **해결:**
    *   백엔드 포트를 `5000`으로, 프론트엔드 API 호출 주소도 `5000`으로 통일.
    *   구글 콘솔에 `http://localhost:5000/oauth2callback`을 정확히 등록.
    *   백엔드 코드(`routes/google_auth.py`)에서 하드코딩을 제거하고 `url_for`를 사용하여 유연하게 복구.
    *   `app.py` 및 라우트 파일들의 누락된 import 구문(`login_required`, `redirect` 등) 전수 수정.
    *   `meeting.ts`, `auth.ts`의 잘못된 API prefix 수정.
*   **결과:** 프론트엔드에서 구글 로그인 버튼 클릭 시 정상적으로 인증 후 대시보드로 리다이렉트됨 확인.

### 4. 대시보드 용어 및 메시지 변경 제안 (UI Terminology Update Plan)
향후 추가될 멀티 템플릿(회의, 강의, 인터뷰/상담)을 모두 포괄하면서도, GenMinute라는 브랜드 이름과 어울리는 용어들로 UI를 개선할 계획.

**핵심 컨셉:** `회의` → **`노트(Note)`** 또는 **`기록(Record)`**으로 확장

| UI 영역 | 현재 (AS-IS) | **제안 (TO-BE)** | 의도 |
| :--- | :--- | :--- | :--- |
| **환영 서브텍스트** | "오늘도 생산적인 회의를 기록해보세요." | **"회의, 강의, 인터뷰...<br/>모든 대화를 인사이트로 바꿔보세요."** | 사용 범위를 명확히 확장하여 보여줍니다. |
| **액션 버튼** | "새 회의 녹음" | **"새 기록 시작"** | 어떤 상황(수업, 미팅 등)에서도 누를 수 있게 합니다. |
| **통계 카드 1** | "이번 달 회의" | **"이번 달 노트"** | 생성된 모든 종류의 문서를 '노트'로 통칭합니다. |
| **통계 카드 3** | "다음 일정" | **"최근 활동"** 또는 **"저장된 기록"** | 일정이 없는 강의나 인터뷰도 포함할 수 있습니다. |
| **리스트 제목** | "최근 회의록" | **"최근 내 노트"** | 가장 무난하고 직관적입니다. |
| **태그 예시** | #주간회의 | **#마케팅수업, #인터뷰, #아이디어** | 다양한 예시를 보여주어 사용성을 암시합니다. |

### 5. 다음 계획 (Phase 3: Features)
*   **실시간 녹음 기능 (`/record`):** `useRecorder` 훅 및 파형 시각화(Visualizer) 구현.
*   **회의록 상세 뷰어 (`/notes/:id`):** 오디오 플레이어, STT 스크립트, 요약 탭 뷰어 구현.
*   **노트 목록 페이지 (`/notes`):** 검색, 필터링, 페이지네이션 구현.
*   **파일 업로드:** 공통 업로드 모달 및 SSE 진행률 표시 구현.

---

## 2025년 12월 16일 - 노트 목록(Note List) 구현 및 요약 API 연동
   * 백엔드 (`services/user_service.py`): 목록 조회 API가 제목뿐만 아니라 요약 내용(summary)도 함께 반환하도록 SQL
     쿼리(LEFT JOIN) 수정.
   * 프론트엔드 (`frontend/src/pages/NoteList.tsx`):
       * 카드 리스트 형태의 노트 목록 페이지 구현.
       * 제목 및 요약 내용 기반의 실시간 검색 기능 구현.
   * 라우팅: /notes 경로에 실제 페이지 연결.

---

## 2025년 12월 16일 (2차) - 챗봇 UI 개선 및 전체 색상 시스템 통일

### 1. 목표
- 챗봇 입력창 UI를 Gemini 스타일로 개선하여 사용자 경험 향상.
- genminute-dashboard의 색 조합을 전체 애플리케이션에 적용하여 일관된 디자인 시스템 구축.

### 2. 주요 변경 사항

#### 챗봇 입력창 UI 개선
*   **입력창 확장 기능 개선:**
    *   기본값: 1줄로 시작 (기존 4줄에서 변경).
    *   확장하지 않은 상태: 최대 4줄까지 자동 확장.
    *   확장 모드: 사이드바 내부에서 전체 영역 사용 가능.
    *   배경 오버레이 추가: 확장 시 어두운 배경 표시 및 클릭 시 축소.
*   **전송 버튼 스타일 변경:**
    *   사각형 → 원형 버튼으로 변경 (`rounded-full`).
    *   고정 크기: 기본 `w-10 h-10`, 확장 시 `w-12 h-12`.
    *   입력창 높이에 맞춰 늘어나지 않도록 `self-stretch` 제거.
*   **입력창과 버튼 정렬:**
    *   `items-center`로 변경하여 세로 가운데 정렬.
    *   입력창과 전송 버튼의 높이 일치.

#### 대시보드 레이아웃 조정
*   **챗봇 비활성화 시:** 대시보드가 중앙 정렬 (`mx-auto`, `maxWidth: 1280px`).
*   **챗봇 활성화 시:** 대시보드가 원래 너비(1280px)를 유지하면서 왼쪽 정렬 (`marginLeft: 0`, `marginRight: 0`).
*   챗봇이 없는 영역에 최대화되지 않고, 원래 크기 그대로 왼쪽으로 이동.

#### 전체 색상 시스템 통일 (genminute-dashboard 스타일 적용)
*   **색상 매핑:**
    *   `amber-600` → `indigo-600` (Primary 액센트)
    *   `amber-500` → `indigo-500` (Hover 상태)
    *   `amber-700` → `indigo-500` 또는 `indigo-700` (Active 상태)
    *   `amber-50` → `indigo-50` (배경)
    *   `amber-100` → `indigo-100` (라이트 배경)
*   **적용 범위:**
    *   **페이지:** Dashboard, NoteList, NoteDetail, Recorder
    *   **컴포넌트:** GlobalChatSidebar, ChatSidebar, Layout, UploadModal, SummaryView, MindmapView
    *   **요소:** 버튼, 링크, 탭, 포커스 링, 아이콘, 통계 카드
*   **통계 카드 색상:**
    *   카드 1: `indigo` (이번 달 노트)
    *   카드 2: `teal` (총 녹음 시간)
    *   카드 3: `rose` (최근 활동)
*   **대시보드 환영 배너:**
    *   그라데이션: `from-slate-900 via-slate-800 to-indigo-950`
    *   배경 블러: `indigo-500/30`, `teal-500/20` 추가

### 3. 기술적 세부 사항

#### 입력창 높이 조절 로직 (`useEffect`)
```typescript
// 기본 1줄, 최대 4줄까지 자동 확장
const lineHeight = 24;
const padding = 16;
const maxHeight4Lines = lineHeight * 4 + padding;
const minHeight = lineHeight + padding; // 1줄

if (!isExpanded) {
  textareaRef.current.style.height = 
    `${Math.max(minHeight, Math.min(scrollHeight, maxHeight4Lines))}px`;
  textareaRef.current.style.overflowY = 
    scrollHeight > maxHeight4Lines ? 'auto' : 'hidden';
}
```

#### 대시보드 레이아웃 조정 로직
```typescript
// 챗봇 활성화 시
if (isOpen) {
  mainContent.style.marginLeft = '0';
  mainContent.style.marginRight = '0';
  mainContent.style.maxWidth = '1280px'; // 원래 너비 유지
} else {
  // 챗봇 비활성화 시 중앙 정렬
  mainContent.style.marginLeft = 'auto';
  mainContent.style.marginRight = 'auto';
  mainContent.style.maxWidth = '1280px';
}
```

### 4. 변경된 파일 목록
*   `frontend/src/components/GlobalChatSidebar.tsx`
*   `frontend/src/components/ChatSidebar.tsx`
*   `frontend/src/components/Layout.tsx`
*   `frontend/src/pages/Dashboard.tsx`
*   `frontend/src/pages/NoteList.tsx`
*   `frontend/src/pages/NoteDetail.tsx`
*   `frontend/src/pages/Recorder.tsx`
*   `frontend/src/components/UploadModal.tsx`
*   `frontend/src/components/SummaryView.tsx`
*   `frontend/src/components/MindmapView.tsx`

### 5. 결과
*   챗봇 입력창이 더 직관적이고 사용하기 편리한 UI로 개선됨.
*   전체 애플리케이션에서 일관된 indigo/teal/rose 색상 팔레트 적용 완료.
*   genminute-dashboard와 동일한 디자인 시스템으로 통일되어 브랜드 일관성 확보.

---

## 2025년 12월 17일 - Firebase 인증 및 챗봇 기능 복구

### 1. 목표
- Firebase 클라이언트 인증 연동 완료 및 로그인 기능 정상화.
- 누락된 챗봇 서비스 파일 복구 및 전역 챗봇 사이드바 연동.

### 2. 주요 변경 사항

#### 🔐 Firebase 인증 시스템 구현
*   **Firebase 클라이언트 설정 (`frontend/src/config/firebase.ts`):**
    *   백엔드 API (`/api/firebase-config`)에서 Firebase 설정을 동적으로 가져오도록 구현.
    *   `ensureFirebaseInitialized()` 함수를 통한 비동기 초기화 처리.
*   **인증 Context (`frontend/src/contexts/AuthContext.tsx`):**
    *   전역 인증 상태 관리 (isAuthenticated, user, isLoading).
    *   Firebase `onAuthStateChanged`를 통한 인증 상태 감지.
    *   `signInWithGoogle`, `signOut` 함수 제공.
*   **Protected Route (`frontend/src/components/ProtectedRoute.tsx`):**
    *   인증되지 않은 사용자를 `/login`으로 자동 리다이렉트.
*   **로그인 페이지 (`frontend/src/pages/Login.tsx`):**
    *   Firebase Google Popup 로그인 구현.
    *   로딩 및 에러 상태 UI 표시.
*   **백엔드 API (`routes/auth.py`):**
    *   `/api/firebase-config` 엔드포인트 추가하여 프론트엔드에 Firebase 설정 제공.

#### 💬 챗봇 기능 복구
*   **챗봇 서비스 (`frontend/src/services/chat.ts`):**
    *   `chatService.sendMessage(query, meetingId?)` API 서비스 생성.
    *   `ChatSource`, `ChatResponse`, `ChatRequest` 타입 정의.
*   **전역 챗봇 사이드바 (`frontend/src/components/GlobalChatSidebar.tsx`):**
    *   색상 테마 수정: `amber` → `indigo` 팔레트 적용.
    *   타입 오류 수정 (`response.answer` 옵셔널 처리, `start_time` 파싱).
*   **회의별 챗봇 (`frontend/src/components/ChatSidebar.tsx`):**
    *   NoteDetail 페이지용 챗봇 컴포넌트 생성.
    *   특정 `meetingId`를 기반으로 해당 회의만 검색.
    *   회의별 대화 내역 분리 저장 (`chat_history_{meetingId}`).
*   **레이아웃 연동 (`frontend/src/components/Layout.tsx`):**
    *   `GlobalChatSidebar` import 및 렌더링 추가.
    *   `hideOnPages={['/notes/']}` 설정으로 NoteDetail 페이지에서는 숨김.

#### 📐 대시보드 레이아웃 조정
*   **챗봇 비활성화 시:** 대시보드 중앙 정렬 (`marginLeft: auto`, `marginRight: auto`).
*   **챗봇 활성화 시:** 대시보드 왼쪽 정렬 (`marginLeft: 0`, `marginRight: 400px`).
*   부드러운 전환 효과 (`transition: all 0.3s ease`).

### 3. 해결된 이슈
*   **Firebase `invalid_client` 오류:** Google OAuth 클라이언트 시크릿 문제로 발생. Firebase Console에서 Google 로그인 재설정으로 해결.
*   **`GlobalChatSidebar` 미표시:** `Layout.tsx`에 컴포넌트 import 및 렌더링 누락. 추가하여 해결.
*   **타입 오류:** `response.answer` 및 `source.start_time` 타입 불일치. 옵셔널 처리 및 `parseFloat()` 적용.

### 4. 현재 상태
*   ✅ Google 로그인 정상 작동.
*   ✅ 로그인 후 대시보드 이동 정상.
*   ✅ 전역 챗봇 사이드바 (CHAT 탭) 표시 및 열림/닫힘 정상.
*   ✅ 챗봇 활성화 시 대시보드 왼쪽 정렬, 비활성화 시 중앙 정렬.

### 5. 다음 계획
*   NoteDetail 페이지 구현 (SummaryView, MindmapView, ChatSidebar 연동).
*   Recorder 페이지 구현 (useRecorder 훅, AudioVisualizer).
*   파일 업로드 모달 (UploadModal) 연동.

---

## 2025년 12월 17일 (2차) - 핵심 기능 구현 완료 (Upload, Recorder, NoteDetail)

### 1. 목표
- 기존 Vanilla JS 코드를 참고하여 React 프론트엔드의 핵심 기능들을 구현.
- 업로드 모달, 실시간 녹음, 노트 상세 뷰어 기능 완성.

### 2. 주요 변경 사항

#### 📤 파일 업로드 모달 (`frontend/src/components/UploadModal.tsx`)
*   **Drag & Drop 지원:** 파일을 드래그하여 업로드 영역에 놓으면 자동 선택.
*   **파일 선택:** 클릭하여 파일 탐색기에서 선택 가능.
*   **파일 유효성 검사:** 
    *   지원 형식: MP3, WAV, M4A, MP4, WEBM, OGG
    *   최대 크기: 500MB
*   **제목/날짜 입력 폼:** 파일 선택 후 회의 제목 및 날짜 입력.
*   **SSE 진행률 표시:** 
    *   5단계 Step Indicator (업로드 → STT → 분석 → 마인드맵 → 완료)
    *   실시간 진행 메시지 표시.
*   **에러 처리:** 오류 발생 시 에러 메시지 및 재시도 버튼 제공.

#### 🎙️ 실시간 녹음 기능
*   **useRecorder 훅 (`frontend/src/hooks/useRecorder.ts`):**
    *   마이크 녹음 (`getUserMedia`): 대면 회의/강의용.
    *   시스템 오디오 녹화 (`getDisplayMedia`): Zoom/화상회의용.
    *   상태 관리: idle, recording, paused, stopped.
    *   타이머 기능: 녹음 시간 실시간 표시.
    *   AnalyserNode 제공: 파형 시각화용.
*   **AudioVisualizer 컴포넌트 (`frontend/src/components/AudioVisualizer.tsx`):**
    *   Canvas 기반 실시간 파형 시각화.
    *   반응형 크기 조정.
    *   커스텀 색상 지원 (barColor, backgroundColor).
*   **Recorder 페이지 (`frontend/src/pages/Recorder.tsx`):**
    *   녹음 타입 선택 UI (마이크/시스템 오디오).
    *   녹음 중 컨트롤 (일시정지, 재개, 정지, 취소).
    *   녹음 완료 후 미리 듣기 및 업로드.
    *   에러 처리 및 안내 메시지.

#### 📝 노트 상세 뷰어
*   **서비스 파일:**
    *   `frontend/src/services/summary.ts`: 요약 조회/생성 API.
    *   `frontend/src/services/mindmap.ts`: 마인드맵 조회/생성 API.
    *   `frontend/src/services/meeting.ts`: 회의 상세 조회, 삭제 API 추가.
*   **SummaryView 컴포넌트 (`frontend/src/components/SummaryView.tsx`):**
    *   요약 로딩 및 표시.
    *   요약이 없을 경우 생성 버튼.
    *   간단한 마크다운 렌더링 (제목, 리스트).
    *   다시 생성 기능.
*   **MindmapView 컴포넌트 (`frontend/src/components/MindmapView.tsx`):**
    *   계층적 트리 구조 렌더링.
    *   레벨별 스타일 차별화.
    *   펼침/접힘 기능 (2단계까지 기본 펼침).
    *   다시 생성 기능.
*   **NoteDetail 페이지 (`frontend/src/pages/NoteDetail.tsx`):**
    *   **오디오 플레이어:**
        *   재생/일시정지, 음소거, 시간 탐색.
        *   현재 재생 시간 및 전체 시간 표시.
    *   **전사 스크립트 탭:**
        *   화자별 색상 구분 (6가지 색상 순환).
        *   세그먼트 클릭 시 해당 시간으로 이동.
        *   현재 재생 중인 세그먼트 하이라이트 및 자동 스크롤.
    *   **요약 탭:** SummaryView 컴포넌트 연동.
    *   **마인드맵 탭:** MindmapView 컴포넌트 연동.
    *   **챗봇 탭:** ChatSidebar 컴포넌트 연동 (회의별 질의응답).
    *   **회의 정보:** 제목, 날짜, 참석자 수, 총 시간.
    *   **삭제 기능:** 권한이 있는 경우 삭제 버튼 표시.

#### 🔧 라우터 업데이트 (`frontend/src/App.tsx`)
*   Placeholder 컴포넌트를 실제 구현된 컴포넌트로 교체.
*   라우트 파라미터 수정: `/notes/:id` → `/notes/:meetingId`.

### 3. 기술적 세부 사항

#### 녹음 MIME 타입 처리
```typescript
// 마이크: 오디오 전용
if (type === 'mic') {
  mimeType = 'audio/webm;codecs=opus';
}
// 시스템: 비디오 + 오디오
else {
  mimeType = 'video/webm;codecs=vp8,opus';
}
```

#### 회의 상세 데이터 타입
```typescript
interface MeetingDetail {
  success: boolean;
  meeting_id: string;
  title: string;
  meeting_date: string;
  participants: string[];
  audio_url: string;
  transcript: TranscriptSegment[];
  speaker_share: SpeakerShare[];
  can_edit: boolean;
}
```

### 4. 변경된 파일 목록
*   `frontend/src/components/UploadModal.tsx` (전면 재작성)
*   `frontend/src/hooks/useRecorder.ts` (신규)
*   `frontend/src/components/AudioVisualizer.tsx` (신규)
*   `frontend/src/pages/Recorder.tsx` (신규)
*   `frontend/src/services/summary.ts` (신규)
*   `frontend/src/services/mindmap.ts` (신규)
*   `frontend/src/services/meeting.ts` (확장)
*   `frontend/src/components/SummaryView.tsx` (신규)
*   `frontend/src/components/MindmapView.tsx` (신규)
*   `frontend/src/pages/NoteDetail.tsx` (신규)
*   `frontend/src/App.tsx` (라우터 업데이트)

### 5. 현재 상태
*   ✅ 파일 업로드 모달 완성 (Drag&Drop, SSE 진행률).
*   ✅ 실시간 녹음 기능 완성 (마이크/시스템 오디오).
*   ✅ 오디오 시각화 컴포넌트 완성.
*   ✅ 노트 상세 뷰어 완성 (스크립트, 요약, 마인드맵, 챗봇).
*   ✅ 모든 페이지 라우팅 연결 완료.

### 6. 다음 계획
*   실제 백엔드 API 연동 테스트.
*   에러 케이스 및 엣지 케이스 처리 보완.
*   UI/UX 개선 (로딩 상태, 애니메이션 등).
*   모바일 반응형 대응.

---

## 2025년 12월 18일 - 전역 업로드 상태 관리 및 NoteDetail 백엔드 연동

### 1. 목표
- 업로드 진행 상황을 페이지 이동 후에도 확인할 수 있도록 전역 상태 관리 시스템 구현.
- NoteDetail 페이지의 프론트엔드 서비스와 백엔드 API 엔드포인트 매핑 수정.

### 2. 주요 변경 사항

#### 📤 전역 업로드 상태 관리 시스템

*   **UploadContext (`frontend/src/contexts/UploadContext.tsx`):**
    *   `UploadTask` 인터페이스: id, fileName, title, progress, status, errorMessage, meetingId, abortController.
    *   `activeTasks` 상태: 진행 중인 모든 업로드 작업 목록.
    *   `addUpload(file, title, meetingDate)`: 새 업로드 작업 추가 및 백그라운드 처리.
    *   `cancelTask(id)`: 진행 중인 업로드 취소 (AbortController 활용).
    *   `removeTask(id)`: 완료/에러 작업 제거.
    *   `clearCompletedTasks()`: 완료된 모든 작업 일괄 제거.

*   **UploadStatusBar (`frontend/src/components/UploadStatusBar.tsx`):**
    *   화면 우측 하단 고정 위치.
    *   진행 중인 업로드 수 및 완료/에러 수 표시.
    *   각 작업별:
        *   진행률 바 (단계별 퍼센트: upload 10%, stt 50%, chunking 70%, mindmap 90%, complete 100%).
        *   현재 단계 레이블 표시.
        *   취소 버튼 (업로드 중).
        *   결과 보기 버튼 (완료 시, 해당 노트로 이동).
        *   제거 버튼.
    *   접기/펼치기 기능.

*   **UploadModal 수정 (`frontend/src/components/UploadModal.tsx`):**
    *   분석 시작 버튼 클릭 시 모달 즉시 닫힘.
    *   업로드는 Context를 통해 백그라운드에서 진행.
    *   기존 모달 내 진행률 UI 제거 (StatusBar로 이동).

*   **App.tsx 수정:**
    *   `UploadProvider`로 전체 앱 래핑.
    *   `UploadStatusBar` 컴포넌트 전역 렌더링.

#### 🔗 NoteDetail 백엔드 API 연동 수정

*   **요약 서비스 (`frontend/src/services/summary.ts`):**
    *   `getSummary`: `/api/summary/{id}` → `/api/check_summary/{id}` 변경.
    *   `generateSummary`: `/api/summary/{id}/generate` → `/api/summarize/{id}` 변경.
    *   백엔드 응답 구조 (`has_summary`, `summary`) 파싱 로직 추가.

*   **마인드맵 서비스 (`frontend/src/services/mindmap.ts`):**
    *   `parseMarkdownToTree()` 함수 추가: 마크다운 문자열 → `MindmapNode` 트리 구조 변환.
    *   백엔드 응답 (`mindmap_content` 마크다운 문자열) 처리.
    *   `generateMindmap`: 별도 API 없음, 요약 생성 API 호출 후 마인드맵 재조회.

*   **회의 서비스 (`frontend/src/services/meeting.ts`):**
    *   `getMeetingDetail`: `audio_url` 상대 경로 → 전체 URL 변환 (`${api.defaults.baseURL}${audio_url}`).

#### 📅 날짜 입력 UI 개선 (`frontend/src/components/UploadModal.tsx`)

*   확인/취소 버튼이 있는 커스텀 날짜 선택 UI 추가.
*   날짜 선택 시 임시 값(`tempDate`)으로 편집, 확인 시 실제 값 적용.
*   선택된 날짜 옆 X 버튼으로 날짜 삭제 가능.

### 3. 기술적 세부 사항

#### 마크다운 → 트리 변환 알고리즘
```typescript
const parseMarkdownToTree = (markdown: string): MindmapNode | null => {
  const lines = markdown.split('\n').filter(line => line.trim());
  const root: MindmapNode = { title: '회의', children: [] };
  const stack: { node: MindmapNode; level: number }[] = [{ node: root, level: 0 }];

  for (const line of lines) {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (!match) continue;

    const level = match[1].length;
    const title = match[2].trim();
    const newNode: MindmapNode = { title, children: [] };

    // 레벨에 맞는 부모 찾기
    while (stack.length > 1 && stack[stack.length - 1].level >= level) {
      stack.pop();
    }

    // 부모에 추가
    stack[stack.length - 1].node.children!.push(newNode);
    stack.push({ node: newNode, level });
  }

  return root.children && root.children.length === 1 
    ? root.children[0] 
    : root;
};
```

#### Vite + TypeScript 타입 import 주의사항
```typescript
// ❌ 잘못된 방식 (런타임 오류 발생)
import { UploadProgress, uploadFile } from '../services/upload';

// ✅ 올바른 방식
import { uploadFile } from '../services/upload';
import type { UploadProgress } from '../services/upload';
```

### 4. 변경된 파일 목록
*   `frontend/src/contexts/UploadContext.tsx` (신규)
*   `frontend/src/components/UploadStatusBar.tsx` (신규)
*   `frontend/src/components/UploadModal.tsx` (수정)
*   `frontend/src/services/summary.ts` (수정)
*   `frontend/src/services/mindmap.ts` (수정)
*   `frontend/src/services/meeting.ts` (수정)
*   `frontend/src/App.tsx` (수정)

### 5. 현재 상태
*   ✅ 전역 업로드 상태 관리 구현 완료.
*   ✅ 페이지 이동 시에도 업로드 진행 상황 확인 가능.
*   ✅ 업로드 취소/결과 보기 기능 구현.
*   ✅ 요약 서비스 API 엔드포인트 매핑 수정 완료.
*   ✅ 마인드맵 서비스 마크다운 파싱 구현 완료.
*   ✅ 오디오 URL 전체 경로 변환 완료.

### 6. 다음 계획
*   NoteDetail 페이지 실제 테스트 및 버그 수정.
*   NoteList 페이지 백엔드 연동 확인.
*   Dashboard 통계 API 연동.
*   Recorder 페이지 백엔드 연동.

---

## 2025년 12월 18일 (2차) - 대시보드 통계 API 연동 및 UX 개선

### 1. 목표
- 대시보드 통계 카드가 실제 데이터를 표시하도록 API 연동.
- 통계 카드 및 노트 목록 카드에 클릭 인터랙션 추가.
- 린터 오류 수정 및 파비콘 업데이트.

### 2. 주요 변경 사항

#### 📊 통계 API 연동 (`frontend/src/services/meeting.ts`)
*   **API 엔드포인트 수정:** `/api/user/stats` → `/api/stats`
*   **응답 구조 파싱:** 백엔드 응답 `{ success: true, stats: { monthly_notes, total_recording_hours, ... } }`에서 `stats` 객체 추출.
*   **결과:** 대시보드에 이번 달 노트 수, 총 녹음 시간이 정상 표시됨.

#### 🖱️ 대시보드 카드 클릭 기능 (`frontend/src/pages/Dashboard.tsx`)
*   **StatCard 컴포넌트 개선:**
    *   `onClick`, `clickable` props 추가.
    *   `clickable={true}` 시 마우스 호버 효과 (`cursor-pointer`, `hover:border-indigo-200`).
*   **이번 달 노트 카드:** 클릭 시 `/notes` 페이지로 이동.
*   **최근 활동 카드:** 클릭 시 가장 최근 노트 상세 페이지로 이동.
    *   subText 변경: "새로운 인사이트 발견" → "클릭하여 최근 노트 확인".
*   **노트 목록 카드:** 카드 전체 클릭 시 해당 노트 상세 페이지로 이동.
    *   MoreVertical 버튼: `e.stopPropagation()`으로 이벤트 전파 방지 (추후 더보기 메뉴용).

#### 🐛 NoteDetail 린터 오류 수정 (`frontend/src/pages/NoteDetail.tsx`)
*   **원인:** `ChatSidebar` 컴포넌트에 정의되지 않은 `isOpen`, `onClose` props 전달.
*   **해결:** 불필요한 props 제거, `meetingTitle` prop 추가.
*   **변경 전:** `<ChatSidebar meetingId={meetingId!} isOpen={true} onClose={() => ...} />`
*   **변경 후:** `<ChatSidebar meetingId={meetingId!} meetingTitle={meeting.title} />`

#### 🎨 파비콘 업데이트 (`frontend/index.html`)
*   **기존:** Vite 기본 아이콘 (`/vite.svg`)
*   **변경:** GenMinute 로고 (`/logo.png`)
*   **추가 설정:**
    *   `<link rel="apple-touch-icon" href="/logo.png" />`
    *   `<meta name="theme-color" content="#4f46e5" />`
    *   페이지 타이틀: "frontend" → "GenMinute - AI 기반 회의록 자동화"

### 3. 변경된 파일 목록
*   `frontend/src/services/meeting.ts` (수정)
*   `frontend/src/pages/Dashboard.tsx` (수정)
*   `frontend/src/pages/NoteDetail.tsx` (수정)
*   `frontend/index.html` (수정)

### 4. 현재 상태
*   ✅ 대시보드 통계 정상 표시.
*   ✅ 통계 카드 클릭 시 페이지 이동 정상.
*   ✅ 노트 카드 클릭 시 상세 페이지 이동 정상.
*   ✅ NoteDetail 린터 오류 해결.
*   ✅ 파비콘 GenMinute 로고로 변경.

### 5. 다음 계획
*   Recorder 페이지 백엔드 연동 테스트.
*   더보기 메뉴 (MoreVertical) 기능 구현 (삭제, 이름 변경, 공유).
*   NoteList 페이지 검색/필터 기능 개선.

---

## 2025년 12월 18일 (3차) - 타입 오류 수정 및 편집 기능 구현

### 1. 목표
- TypeScript 타입 오류 수정 및 코드 품질 개선.
- 백엔드 API와의 정합성 확보.
- 노트 편집 기능 구현 (제목/날짜 수정, 회의록 탭).
- 메뉴 이름 통일 및 UX 개선.

### 2. 주요 변경 사항

#### 🐛 TypeScript 타입 오류 수정

*   **`useRecorder.ts` - `cursor: 'never'` 타입 오류:**
    *   **원인:** `DisplayMediaStreamConstraints` 전용 속성이 `MediaTrackConstraints` 타입으로 추론됨.
    *   **해결:** `@ts-ignore` 주석 추가.
    *   **변경:** `cursor: 'never' as any` → `// @ts-ignore` + `cursor: 'never'`

*   **`useRecorder.ts` - `webkitAudioContext` 타입 오류:**
    *   **원인:** Safari 비표준 API로 TypeScript 타입 정의 없음.
    *   **해결:** `@ts-ignore` 주석 추가.
    *   **변경:** `(window as any).webkitAudioContext` → `// @ts-ignore` + `window.webkitAudioContext`

*   **`GlobalChatSidebar.tsx` - 타입 단언 개선:**
    *   **원인:** `querySelector` 반환 타입과 `HTMLElement` 타입 불일치.
    *   **해결:** `instanceof HTMLElement` 타입 가드 사용.
    *   **변경:** `const element = mainContent as HTMLElement` → `if (mainContent instanceof HTMLElement)`

#### 🔧 API 엔드포인트 수정

*   **`meeting.ts` - 삭제 API 엔드포인트 수정:**
    *   **원인:** 백엔드는 `POST /api/delete_meeting/{id}`, 프론트엔드는 `DELETE /api/meeting/{id}` 호출.
    *   **해결:** 프론트엔드 엔드포인트를 백엔드와 일치시킴.
    *   **변경:** `api.delete()` → `api.post('/api/delete_meeting/${meetingId}')`

#### ✏️ 노트 편집 기능 구현

*   **제목/날짜 수정 기능 (`frontend/src/services/meeting.ts`):**
    *   `updateMeetingTitle()` 메서드 추가: `POST /api/update_title/{id}`
    *   `updateMeetingDate()` 메서드 추가: `POST /api/update_date/{id}`

*   **NoteDetail 페이지 편집 UI (`frontend/src/pages/NoteDetail.tsx`):**
    *   MoreVertical 메뉴에 "제목 수정", "날짜 수정" 옵션 추가.
    *   인라인 편집 모드: 제목/날짜 클릭 시 입력 필드로 전환.
    *   저장/취소 버튼 제공.
    *   `datetime-local` 입력 필드 사용 (날짜 수정).

*   **회의록 생성/조회 탭:**
    *   `frontend/src/services/minutes.ts` 서비스 파일 생성.
    *   `frontend/src/components/MinutesView.tsx` 컴포넌트 생성.
    *   NoteDetail 페이지에 "회의록" 탭 추가 (요약과 별개).
    *   회의록 생성/재생성 기능 구현.
    *   마크다운 렌더링 (제목, 리스트, 일반 텍스트).

#### 🎨 메뉴 이름 통일 및 UX 개선

*   **메뉴 이름 통일 (`frontend/src/components/Layout.tsx`):**
    *   "회의록" → "내 노트" (NoteList 페이지 제목과 일치).
    *   "녹음" → "기록" (오디오/비디오 모두 포함하는 포괄적 표현).
    *   "홈" 유지.

*   **MoreVertical 버튼 이벤트 전파 방지 (`frontend/src/pages/NoteList.tsx`):**
    *   **원인:** `Link`로 감싸진 MoreVertical 버튼 클릭 시 상세 페이지로 이동.
    *   **해결:** `Link`를 `button`으로 변경, `e.stopPropagation()` 추가.
    *   **추가:** 카드 전체 클릭 시 상세 페이지 이동 기능 추가.

### 3. 변경된 파일 목록

*   `frontend/src/hooks/useRecorder.ts` (타입 오류 수정)
*   `frontend/src/components/GlobalChatSidebar.tsx` (타입 단언 개선)
*   `frontend/src/services/meeting.ts` (삭제 API 수정, 제목/날짜 수정 메서드 추가)
*   `frontend/src/pages/NoteDetail.tsx` (편집 UI, 회의록 탭 추가)
*   `frontend/src/services/minutes.ts` (신규 생성)
*   `frontend/src/components/MinutesView.tsx` (신규 생성)
*   `frontend/src/components/Layout.tsx` (메뉴 이름 통일)
*   `frontend/src/pages/NoteList.tsx` (MoreVertical 버튼 수정)

### 4. 현재 상태
*   ✅ TypeScript 타입 오류 모두 해결.
*   ✅ 삭제 API 엔드포인트 백엔드와 일치.
*   ✅ 제목/날짜 수정 기능 구현 완료.
*   ✅ 회의록 생성/조회 탭 추가 완료.
*   ✅ 메뉴 이름 통일 완료.
*   ✅ MoreVertical 버튼 이벤트 전파 방지 완료.

### 5. 다음 계획 (우선순위)

#### Priority 1: 공유 기능 UI
*   노트 공유 모달 (이메일 기반 공유).
*   공유 사용자 목록 조회 및 해제.
*   NoteDetail의 MoreVertical 메뉴에 "공유" 추가.
*   예상 작업 시간: 4-5시간.

#### Priority 2: AI Agent UI
*   Action Item 추출 및 표시.
*   NoteDetail 페이지에 "Action Items" 탭 추가.
*   Google Calendar 연동 상태 시각화 (선택적).
*   예상 작업 시간: 5-6시간.

#### Priority 3: UX 개선 (선택)
*   오디오 플레이어 고도화 (재생 속도, 구간 반복).
*   검색 및 필터링 개선 (날짜 범위, 태그, 페이지네이션).

---

## 2025년 12월 18일 - Priority 1: 공유 기능 UI 구현 완료

### 1. 개요 (Overview)
백엔드에 이미 구현되어 있던 공유 기능 API를 활용하여 프론트엔드 UI를 구현함. 노트 소유자가 이메일 기반으로 노트를 공유하고, 공유받은 사용자 목록을 조회/관리하며, 공유받은 노트를 별도 페이지에서 확인할 수 있는 기능을 완성함.

### 2. 주요 변경 사항 (Changes)

#### 📧 공유 서비스 레이어 생성 (`frontend/src/services/share.ts`)
*   **신규 생성:** 공유 기능 관련 API 호출을 담당하는 서비스 레이어 구현.
*   **구현 메서드:**
    *   `shareMeeting(meetingId, email)`: 이메일 기반 노트 공유.
    *   `getSharedUsers(meetingId)`: 공유받은 사용자 목록 조회.
    *   `unshareMeeting(meetingId, userId)`: 공유 해제.
    *   `getSharedMeetings()`: 공유받은 노트 목록 조회.
*   **타입 정의:**
    *   `SharedUser`, `ShareResponse`, `SharedUsersResponse`, `SharedMeeting`, `SharedMeetingsResponse` 인터페이스 추가.

#### 🎨 공유 모달 컴포넌트 생성 (`frontend/src/components/ShareModal.tsx`)
*   **신규 생성:** 노트 공유를 위한 모달 컴포넌트 구현.
*   **주요 기능:**
    *   이메일 입력 필드 및 형식 검증 (정규식 사용).
    *   공유 버튼 및 로딩 상태 표시.
    *   공유된 사용자 목록 표시 (프로필 이미지, 이름, 이메일).
    *   공유 해제 기능 (삭제 버튼).
    *   에러/성공 메시지 표시.
    *   Enter 키로 공유 가능.
*   **UI/UX:**
    *   모달 배경 클릭 시 닫기.
    *   모달 내부 클릭 시 이벤트 전파 방지 (`e.stopPropagation()`).
    *   공유 성공 후 자동으로 사용자 목록 새로고침.

#### 📄 NoteDetail 페이지에 공유 메뉴 추가 (`frontend/src/pages/NoteDetail.tsx`)
*   **MoreVertical 메뉴 확장:**
    *   "공유" 옵션 추가 (`Share2` 아이콘 사용).
    *   ShareModal 컴포넌트 연동.
    *   `isShareModalOpen` 상태 추가.
*   **권한 체크:**
    *   `can_edit`이 true일 때만 MoreVertical 메뉴가 표시되므로, 공유 메뉴도 자동으로 권한 체크됨.

#### 📋 공유받은 노트 목록 페이지 생성 (`frontend/src/pages/SharedNoteList.tsx`)
*   **신규 생성:** NoteList와 유사한 구조로 공유받은 노트만 표시하는 페이지 구현.
*   **주요 기능:**
    *   공유받은 노트 목록 조회 및 표시.
    *   검색 기능 (제목, 요약 내용 검색).
    *   "공유받음" 뱃지 표시.
    *   노트 카드 클릭 시 상세 페이지 이동.
*   **UI/UX:**
    *   빈 상태 메시지 (공유받은 노트가 없을 때).
    *   검색 결과가 없을 때 안내 메시지.

#### 🛣️ 라우팅 및 네비게이션 추가
*   **`frontend/src/App.tsx`:**
    *   `/shared-notes` 라우트 추가.
    *   `SharedNoteList` 컴포넌트 import 및 라우팅 설정.
*   **`frontend/src/components/Layout.tsx`:**
    *   데스크톱 네비게이션에 "공유받은 노트" 메뉴 추가 (`Share2` 아이콘).
    *   모바일 네비게이션에도 동일 메뉴 추가.
    *   활성 상태 표시 (`isActive('/shared-notes')`).

#### 🔧 백엔드 API 추가 및 수정 (`routes/meetings.py`)
*   **신규 API 엔드포인트:**
    *   `GET /api/shared-notes`: 공유받은 노트 목록 조회 (JSON API).
    *   기존 `/shared-notes` 라우트는 HTML 템플릿을 반환했으나, 프론트엔드 SPA를 위해 JSON API 추가.
*   **버그 수정:**
    *   `unshare_meeting_route`에서 `remove_share()` 함수 호출 시 `owner_id` 파라미터 누락 문제 해결.
    *   `remove_share(meeting_id, user_id, target_user_id)` 형태로 수정.

### 3. 기술적 특징 (Technical Notes)

#### 모달 컴포넌트 패턴
*   **배경 오버레이 + 중앙 정렬:**
    *   `fixed inset-0`로 전체 화면 덮기.
    *   `z-index` 계층: 배경(z-40) < 모달(z-50).
    *   `flex items-center justify-center`로 중앙 정렬.
    *   배경 클릭 시 닫기, 모달 내부 클릭 시 이벤트 전파 방지.

#### 이메일 검증
*   **프론트엔드 기본 검증:**
    *   정규식: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
    *   빈 문자열 체크 및 `trim()` 처리.
    *   백엔드에서도 추가 검증 필요 (이미 구현됨).

#### 공유받은 데이터 필터링
*   **SQL 쿼리 패턴:**
    *   `INNER JOIN`으로 공유 테이블과 조인.
    *   `WHERE shared_with_user_id = ?`로 공유받은 노트만 조회.
    *   `owner_id != ?`로 본인 노트 제외.
    *   `DISTINCT`로 중복 제거.

### 4. 변경된 파일 목록

#### 백엔드
*   `routes/meetings.py`
    *   `GET /api/shared-notes` 엔드포인트 추가.
    *   `unshare_meeting_route`에서 `remove_share()` 호출 시 `owner_id` 파라미터 추가.

#### 프론트엔드 - 신규 생성
*   `frontend/src/services/share.ts` (공유 서비스 레이어)
*   `frontend/src/components/ShareModal.tsx` (공유 모달 컴포넌트)
*   `frontend/src/pages/SharedNoteList.tsx` (공유받은 노트 목록 페이지)

#### 프론트엔드 - 수정
*   `frontend/src/pages/NoteDetail.tsx`
    *   MoreVertical 메뉴에 "공유" 옵션 추가.
    *   ShareModal 연동 및 상태 관리.
*   `frontend/src/App.tsx`
    *   `/shared-notes` 라우트 추가.
*   `frontend/src/components/Layout.tsx`
    *   데스크톱/모바일 네비게이션에 "공유받은 노트" 메뉴 추가.

### 5. 현재 상태 (Status)
*   ✅ 공유 서비스 레이어 구현 완료.
*   ✅ 공유 모달 컴포넌트 구현 완료 (이메일 검증, 사용자 목록, 공유 해제).
*   ✅ NoteDetail 페이지에 공유 메뉴 추가 완료.
*   ✅ 공유받은 노트 목록 페이지 구현 완료.
*   ✅ 라우팅 및 네비게이션 추가 완료.
*   ✅ 백엔드 API 추가 및 버그 수정 완료.
*   ✅ 모든 TypeScript 타입 오류 없음.
*   ✅ 린터 오류 없음.

### 6. 학습 포인트 및 코드 검증 포인트
*   **LEARNING_POINTS.md에 추가:**
    *   모달 컴포넌트 패턴 (배경 오버레이 + 중앙 정렬).
    *   이메일 검증 정규식.
    *   공유 기능 백엔드-프론트엔드 API 매핑.
    *   공유받은 데이터 필터링 패턴.
*   **CODE_REVIEW_GUIDE.md에 추가:**
    *   백엔드 공유 기능 API 검증 포인트.
    *   ShareModal 컴포넌트 검증 포인트.
    *   share.ts 서비스 검증 포인트.
    *   SharedNoteList 페이지 검증 포인트.
    *   NoteDetail 페이지 공유 메뉴 검증 포인트.

### 7. 다음 계획 (Next Steps)

#### Priority 2: AI 에이전트 UI 연동
*   백엔드 API 엔드포인트 추가 필요:
    *   `POST /api/extract_action_items/{meeting_id}` - Action Item 추출.
    *   `GET /api/action_items/{meeting_id}` - Action Item 조회.
*   프론트엔드 구현:
    *   Action Items 서비스 생성 (`actionItems.ts`).
    *   ActionItemsView 컴포넌트 생성.
    *   NoteDetail 페이지에 "Action Items" 탭 추가.
*   예상 작업 시간: 5-6시간.

#### Priority 3: 검색 및 필터링 고도화
*   날짜 범위 필터 (시작일/종료일 선택 UI).
*   태그 기반 필터 (태그 UI 표시, 태그별 필터링).
*   페이지네이션 (대량 데이터 처리, 페이지 번호 표시).
*   정렬 옵션 (최신순, 제목순, 날짜순).
*   예상 작업 시간: 6-8시간.

#### Priority 4: UX 개선 (선택)
*   오디오 플레이어 고도화 (재생 속도 조절, 구간 반복, 파형 시각화).
*   검색 결과 하이라이팅.
*   로딩 상태 개선 (스켈레톤 UI 또는 로딩 애니메이션).
*   예상 작업 시간: 4-6시간.

---
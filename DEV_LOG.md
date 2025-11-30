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
*   **마우스 커서 숨기기 시도:** `getDisplayMedia` 옵션에 `video: { cursor: "never" }`를 추가하여 마우스 커서가 녹화되지 않도록 시도. (크롬에서 지원되지 않아 적용되지 않음).

#### 💾 백엔드 파일 처리 로직 보완 (`services/upload_service.py`)
*   **문제:** 프론트엔드에서 `.webm` 파일(특히 시스템 녹화 시 영상 포함)을 업로드해도, 백엔드의 `save_uploaded_file` 함수가 `.mp4`만 비디오로 인식하여 적절한 오디오 추출 로직(`convert_video_to_audio`)을 거치지 않음.
*   **해결:** `save_uploaded_file` 함수에서 `.webm` 확장자도 비디오 파일로 인식하도록 `is_video` 판단 로직을 확장.
*   **FFmpeg 상세 로깅 추가:** `convert_video_to_audio` 메서드 내 `subprocess.run` 호출 후 `stdout`과 `stderr` 내용을 로그로 출력하여 FFmpeg 실행 결과 디버깅 용이성 확보.

#### 🚨 서버 에러 리포팅 강화 (`routes/meetings.py`)
*   **문제:** `/upload` API 처리 중 서버에서 예외가 발생하면 클라이언트에 구체적인 에러 메시지를 전달하지 않고 연결이 끊어져, 클라이언트에서 "서버 연결이 종료되었습니다."라는 모호한 메시지만 표시됨.
*   **해결:** `upload_and_process` 함수 내 `generate` 제너레이터의 `try-except` 블록을 수정하여, 예외 발생 시 로그만 출력하는 대신 클라이언트에 에러 정보가 담긴 JSON 메시지(SSE 형식)를 전송하도록 변경. 이를 통해 클라이언트가 서버 에러 원인을 파악할 수 있도록 디버깅 용이성 개선.
*   **디버깅 로그 추가:** `upload_and_process` 함수 및 내부 `generate` 함수 곳곳에 `logger.info`를 사용하여 실행 흐름과 주요 변수 값(특히 `is_video`, `file_path`)을 추적할 수 있는 디버그 로그를 추가.

### 3. 현재 상태 (Status)
*   **기능 동작 확인:** PC 환경에서 마이크 녹음 및 시스템 녹화(영상 포함) 기능 모두 정상 작동하며, 각각 음성만, 또는 영상과 음성이 함께 녹화되는 것을 확인.
*   **오류 진단:** FFmpeg 설치 및 PATH 설정 완료 후에도 분석 시작 버튼 클릭 시 "서버 연결이 종료되었습니다." 메시지가 여전히 발생. 이는 FFmpeg 관련 로그가 서버 터미널에 전혀 나타나지 않는 현상과 연관되어 있으며, `convert_video_to_audio` 함수가 호출되지 않거나 그 이전에 문제가 발생했을 가능성이 높음. STT 엔진과의 연결 또는 대용량 파일 처리 과정에서의 문제도 여전히 의심됨. 마우스 커서 숨기기는 크롬 브라우저의 제약으로 인해 적용되지 않음.

### 4. 다음 계획 (Next Steps)
*   **STT 연결 문제 디버깅:** 추가된 디버그 로그(`routes/meetings.py`, `services/upload_service.py`)를 통해 서버의 실행 흐름을 면밀히 분석하고, 어느 단계에서 오류가 발생하는지 정확히 파악. `stt.py` 내부의 Google Gemini API 호출 로직 및 파일 처리 방식(File API 사용 여부 등)을 재검토.
*   Phase 2 (준실시간 미리보기) 기능 구현 준비.
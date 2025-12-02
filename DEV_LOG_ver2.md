# 개발 일지 v2

---

## 2025-12-02: AI 에이전트(Action Item) 기능 개발 및 통합

### 목표
- `ROADMAP.md`의 1단계 과제인 'AI 비서 및 일정 연동' 기능의 핵심부 개발.
- 회의록 텍스트에서 Action Item을 자동으로 인식하고, 외부 도구(Google Calendar)와 연동하는 기반 마련.

### 아키텍처 결정 및 논의
- **'모듈' vs '도구' 논의:** 초기에는 재사용 가능한 '모듈'로 접근했으나, 사용자의 명확한 요구사항에 따라 **LLM의 추론 능력을 활용하는 '지능형 에이전트'**로 방향을 재설정함.
- **LangChain vs LangGraph:** 단순 에이전트 루프의 한계를 인지하고, 복잡한 워크플로우를 명시적으로 제어할 수 있으며 상태 관리에 용이한 **LangGraph를 최종 아키텍처로 채택**함. 이 결정은 `ROADMAP.md`에도 반영하여 공식화함.

### 주요 변경 사항
1.  **`tools/google_calendar_tool.py` 생성:**
    - 에이전트가 사용할 '일정 추가' 도구를 Pydantic 스키마와 함께 정의.
    - 실제 API 호출 대신, LLM의 함수 호출(Function Calling) 능력을 검증하기 위한 시뮬레이션 코드로 구현.

2.  **`services/agent_service.py` 생성:**
    - LangGraph를 사용하여 '추출 및 실행' 워크플로우를 가진 `AgentService` 구현.
    - `StateGraph`를 통해 에이전트의 상태(회의록, 메시지 등)를 관리.
    - `tool_choice="any"` 옵션을 적용하여, LLM이 텍스트로 답변하는 대신 반드시 도구를 호출하도록 강제하여 안정성 확보.

3.  **기존 코드 리팩토링 및 통합:**
    - 기능이 중복되고 혼동을 유발하는 구버전 `schedule_manager/agent.py` 파일 삭제.
    *   `services/upload_service.py`의 `process_audio_file` 함수 마지막 단에 `AgentService` 호출 로직을 추가하여, STT 처리 완료 후 자동으로 Action Item 추출 프로세스가 실행되도록 전체 워크플로우에 통합.

### 결과
- 파일 업로드 시, STT 처리부터 LangGraph 에이전트 호출, 그리고 최종적인 (시뮬레이션) 도구 실행까지 이어지는 **End-to-End 파이프라인 구축 완료.**
- Flask 서버 로그를 통해 LLM이 자연어(예: '이번 주 금요일')를 정확한 날짜(`2025-12-05`)로 추론하고, 올바른 인자와 함께 `add_calendar_event` 도구를 호출함을 확인함.

### 다음 단계
- `AgentService`가 단일 Action Item만 처리하는 한계를 개선.
- 실제 Google Calendar API OAuth 2.0 연동 및 사용자 승인 플로우 구현.
- 에이전트의 처리 결과를 사용자에게 시각적으로 피드백하는 UI 구현.

---
## 2025-12-02 (추가): Google Calendar 연동 파이프라인 구축

### 목표
- 실제 Google Calendar API 연동을 위한 사용자 인증(OAuth 2.0) 기반 마련 및 실제 API 호출 기능 구현.

### 주요 변경 사항
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

### 결과
- 사용자가 UI를 통해 Google 계정 접근 권한을 승인하고, 발급된 인증 토큰(Refresh Token)을 데이터베이스에 안전하게 저장하는 전체 인증 파이프라인 구축 완료.
- `redirect_uri_mismatch` 및 `InsecureTransportError` 등 OAuth 2.0 연동 과정에서 발생한 주요 오류 해결.
- AI 에이전트가 실제 사용자 계정의 캘린더에 접근하여 일정을 생성할 수 있는 모든 기술적 기반이 마련됨.

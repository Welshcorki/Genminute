# 🗺️ Genminute 고도화 및 리팩토링 로드맵 (2025)

이 문서는 서비스의 핵심 가치인 **AI 비서(Agent)** 기능을 최우선으로 도입하고, 이후 시스템 안정성 및 효율성을 강화하기 위한 계획을 기술합니다.

---

## 1. 📊 현황 진단 (AS-IS)

현재 Genminute는 **실시간 녹음 및 자동 변환 파이프라인(Universal Web Recorder)** 구축을 완료하였으며, 다음과 같은 시스템 구성을 가지고 있습니다.

- **Core AI Engine:** Google Gemini 2.5 Pro (STT, 요약) + Flash (챗봇)
- **Architecture:** Flask (Backend) + SQLite + ChromaDB (RAG) + Firebase Auth
- **New Feature:** Mobile/PC 실시간 녹음, ffmpeg 기반 자동 오디오 변환
- **⚠️ Pain Points (상세 분석):**
  1.  **프론트엔드 아키텍처 혼재:** 
      - Jinja2(SSR)와 Vanilla JS가 혼재되어 사용자 경험(UX)이 매끄럽지 않으며, 상태 관리가 복잡함.
      - **Action:** React/Vite 기반의 SPA 구조로 전환 필요. (Phase 2 완료 ✅)
  2.  **비용 효율성 문제:**
      - Pro 모델 의존도가 높아 1시간 회의 분석 시 약 $1.0 소요 (STT 비중 70% 이상).
      - **Action:** Local STT(Whisper) 또는 Gemini Flash 모델 도입으로 비용 절감 필요.
  3.  **프로젝트 구조 및 코드 복잡도:**
      - 루트 디렉토리 파일 혼재(`mindmap.py`, `app.py` 등), `utils/`와 `services/`의 역할 모호.
      - 실험 코드(`experiments_stt/`)와 프로덕션 코드의 경계 불분명.
      - **Action:** 명확한 계층 분리(Layered Architecture) 및 리팩토링 필요. (완료 ✅)
  4.  **확장성 부족:**
      - 회의록이 실제 업무(일정, 태스크)로 연결되지 않음.
      - Gemini와 OpenAI 키 혼용으로 인한 관리 복잡성.

---

## 2. 🚀 Phase 2: 프론트엔드 전환 (React Migration) [완료 ✅]

Flask + Jinja2 구조를 Vite + React + TypeScript 기반의 SPA로 전환하여 사용자 경험을 혁신합니다.

### ✅ 완료된 작업
- [x] **프로젝트 초기화:** Vite + React + TypeScript 환경 구축.
- [x] **디자인 시스템:** Tailwind CSS v3 기반의 'Dark & Gold' 테마 적용.
- [x] **색상 시스템 통일:** genminute-dashboard 스타일 적용 (amber → indigo/teal/rose 팔레트).
- [x] **API 연동:** Axios 모듈화 및 CORS 설정, 구글 OAuth 2.0 로그인 연동.
- [x] **기초 UI:** 로그인 페이지, 메인 대시보드(데이터 연동 포함) 구현.
- [x] **챗봇 UI 개선:** Gemini 스타일 입력창, 확장/축소 기능, 원형 전송 버튼 구현.

---

## 3. 🛠️ Phase 3: 핵심 기능 구현 (Feature Implementation) [완료 ✅]

전환된 프론트엔드 환경 위에 GenMinute의 핵심 기능들을 이식하고 고도화합니다.

**구현 완료:** 로그인/인증 ✅ → 대시보드 ✅ → 파일 업로드 ✅ → 실시간 녹음 ✅ → 상세 뷰어 ✅

### 0️⃣ 🔐 로그인 및 인증 시스템 (Authentication) [완료 ✅]

**목표:** 백엔드 인증 시스템과 완전히 연동된 프론트엔드 인증 구현.

**진행 상황:**
- [x] **로그인 페이지 UI:** 기본 로그인 폼 및 Google 로그인 버튼 구현.
- [x] **Firebase 인증 연동:** Firebase SDK를 통한 ID 토큰 획득 및 백엔드 전송.
- [x] **API 엔드포인트:** `/api/firebase-config`로 클라이언트 설정 제공.
- [x] **Google OAuth 플로우:** Firebase Google Popup 로그인 구현.
- [x] **Protected Routes:** 인증되지 않은 사용자 자동 로그인 페이지 리다이렉트.
- [x] **인증 상태 관리:** Context API를 통한 전역 인증 상태 관리 (AuthContext).
- [x] **세션 유지:** Firebase `onAuthStateChanged`를 통한 인증 상태 감지.
- [ ] **회원가입 페이지:** 신규 사용자 등록 기능 (선택사항 - Phase 4로 이동).

**상세 스펙:**
*   **Firebase Authentication:** 클라이언트 측 Firebase SDK를 통한 Google 로그인.
*   **ID 토큰 검증:** 백엔드 `/api/login`에 Firebase ID 토큰 전송 및 세션 생성.
*   **Protected Routes:** 인증되지 않은 사용자는 자동으로 `/login`으로 리다이렉트.
*   **인증 Context:** 전역 인증 상태 관리 및 사용자 정보 제공.

**재사용 가능한 기존 코드:**
- 백엔드 인증 API (`routes/auth.py`, `routes/google_auth.py`)
- Firebase 토큰 검증 로직 (`services/firebase_service.py`)
- 사용자 관리 (`services/user_service.py`)

### 1️⃣ 🏠 메인 대시보드 (Dashboard) [완료 ✅]

**목표:** 사용자의 최근 활동을 한눈에 파악하고 빠른 작업을 유도.

**진행 상황:**
- [x] **환영 메시지:** 로그인 유저 이름 표시.
- [x] **빠른 액션 버튼:** `새 기록 시작` (녹음 페이지 이동), `파일 업로드` (모달 연동).
- [x] **통계 카드:** 이번 달 노트 수, 총 녹음 시간, 최근 활동 표시 (데이터 API 연동 완료).
- [x] **통계 카드 인터랙션:** 이번 달 노트 클릭 → 노트 리스트, 최근 활동 클릭 → 최근 노트 상세 페이지 이동.
- [x] **최근 내 노트:** 최근 생성된 노트를 카드 형태로 미리보기, 클릭 시 상세 페이지 이동.
- [x] **디자인 시스템:** genminute-dashboard 색 조합 적용 (indigo/teal/rose).
- [x] **레이아웃 조정:** 챗봇 활성화 시 대시보드 왼쪽 정렬, 비활성화 시 중앙 정렬.
- [x] **전역 챗봇 사이드바:** CHAT 탭을 통한 전역 AI 챗봇 접근 가능.
- [x] **파일 업로드 모달:** 업로드 버튼 클릭 시 모달 열기 및 기능 연동.

**상세 스펙:**
    *   **환영 메시지:** 로그인 유저 이름 표시.
    *   **빠른 액션:** `새 기록 시작` (녹음 페이지 이동), `파일 업로드` (업로드 모달 호출).
    *   **통계 카드:** 이번 달 노트 수, 총 녹음 시간 등 실제 데이터 API 연동.
    *   **최근 내 노트:** 최근 생성된 3개의 노트를 카드 형태로 미리보기.

### 2️⃣ 📤 파일 업로드 (File Upload) [완료 ✅]

**목표:** 대시보드 및 목록 페이지 어디서든 접근 가능한 업로드 기능.

**진행 상황:**
- [x] **Drag & Drop 모달:** 직관적인 파일 업로드 인터페이스.
- [x] **파일 선택 버튼:** 기본 파일 선택 기능.
- [x] **제목 입력 필드:** 회의 제목 입력.
- [x] **날짜 선택:** 회의 날짜 선택 (선택사항).
- [x] **SSE 진행률 표시:** '업로드 -> STT -> 분석 -> 마인드맵 -> 완료' 단계를 실시간 피드백.
- [x] **에러 처리:** 업로드 실패 시 재시도 및 에러 메시지 표시.
- [x] **파일 유효성 검사:** 지원 형식(MP3, WAV, M4A, MP4, WEBM, OGG) 및 크기(500MB) 검사.

**상세 스펙:**
*   **Drag & Drop 모달:** 직관적인 파일 업로드 인터페이스.
*   **실시간 진행률:** SSE(Server-Sent Events)를 연동하여 '업로드 -> 변환 -> STT -> 요약' 단계를 실시간 피드백.

**재사용 가능한 기존 코드:**
- SSE 스트림 파싱 로직 (`static/js/script.js:505-524`)
- 단계별 상태 관리 (`static/js/script.js:538-676`)
- 에러 처리 및 재시도 (`static/js/script.js:606-674`)

### 3️⃣ 🎙️ 실시간 녹음 (Live Recorder) [완료 ✅]

**목표:** 웹 브라우저에서 마이크 및 시스템 오디오를 고품질로 녹음.

**진행 상황:**
- [x] **커스텀 훅:** `useRecorder` 훅을 개발하여 녹음 로직(MediaRecorder, AudioContext) 분리.
- [x] **시각화(Visualizer):** 오디오 파형을 Canvas에 실시간 렌더링 (AudioVisualizer 컴포넌트).
- [x] **타이머:** 녹음 진행 시간 실시간 표시.
- [x] **저장 및 전송:** 녹음 종료 시 `Blob` 생성 및 백엔드 `/upload` API 자동 전송.
- [x] **녹음 타입 선택:** 마이크(대면 회의) / 시스템 오디오(화상회의) 선택 UI.
- [x] **녹음 컨트롤:** 일시정지, 재개, 정지, 취소 기능.
- [x] **미리 듣기:** 녹음 완료 후 업로드 전 미리 듣기 기능.

**상세 스펙:**
    *   **커스텀 훅:** `useRecorder` 훅을 개발하여 녹음 로직(AudioContext) 분리.
    *   **시각화(Visualizer):** 오디오 파형을 Canvas에 실시간 렌더링.
    *   **타이머:** 녹음 진행 시간 실시간 표시.
    *   **저장 및 전송:** 녹음 종료 시 `Blob` 생성 및 백엔드 `/upload` API 자동 전송.

**재사용 가능한 기존 코드:**
- MediaRecorder MIME 타입 선택 (`static/js/live/recorder.js:59-74`)
- 타이머 계산 로직 (`static/js/live/recorder.js:266-276`)
- 파형 시각화 로직 (`static/js/live/recorder.js:279-326`)
- 녹음 완료 후 업로드 (`static/js/live/recorder.js:354-469`)

### 4️⃣ 📄 상세 뷰어 (Note Detail) [완료 ✅]

**목표:** 생성된 회의록(STT, 요약, 마인드맵)을 통합적으로 열람하고 편집.

**진행 상황:**
- [x] **기본 구조:** 헤더, 미디어 플레이어, 탭 네비게이션 구현.
- [x] **스마트 탭:** `스크립트`, `요약`, `마인드맵`, `회의록`, `Action Items`, `AI 채팅` 탭 구성.
- [x] **AI 챗봇:** 해당 노트 내용을 기반으로 한 RAG 질의응답 사이드바 (ChatSidebar).
- [x] **요약/마인드맵 뷰:** SummaryView, MindmapView 컴포넌트 구현.
- [x] **회의록 뷰:** MinutesView 컴포넌트 구현 (요약과 별개).
- [x] **Action Items 뷰:** ActionItemsView 컴포넌트 구현 (Priority 2 완료).
- [x] **색상 시스템:** indigo 기반 색상 팔레트 적용.
- [x] **오디오 플레이어:** 재생/일시정지, 음소거, 시간 탐색, 진행 바.
- [x] **STT 스크립트:** 텍스트 클릭 시 해당 오디오 구간 재생(Sync), 현재 재생 세그먼트 하이라이트.
- [x] **화자별 색상 구분:** 6가지 색상 순환으로 화자 구분.
- [x] **회의 정보 표시:** 제목, 날짜, 참석자 수, 총 시간.
- [x] **편집 기능:** 제목/날짜 수정 (인라인 편집).
- [x] **공유 기능:** 이메일 기반 노트 공유 (ShareModal).
- [x] **삭제 기능:** 권한이 있는 경우 회의록 삭제 가능.
- [ ] **파형 시각화:** 오디오 파형 표시 (향후 개선).
- [ ] **재생 속도 조절:** 0.5x ~ 2x 배속 기능 (향후 개선).
- [ ] **구간 반복:** 특정 구간 반복 재생 (향후 개선).

**상세 스펙:**
    *   **오디오 플레이어:** 파형 시각화, 재생 속도 조절, 구간 반복.
    *   **STT 스크립트:** 화자별 대화 표시, 텍스트 클릭 시 해당 오디오 구간 재생(Sync).
    *   **스마트 탭:** `스크립트`, `요약`, `마인드맵`, `회의록`, `Action Items`, `채팅(AI)` 탭으로 구성.
    *   **AI 챗봇:** 해당 노트 내용을 기반으로 한 RAG 질의응답 사이드바.
    *   **Action Items:** 회의록에서 추출된 할 일 목록 표시 및 완료 상태 관리.

**재사용 가능한 기존 코드:**
- 오디오/비디오 플레이어 자동 선택 (`static/js/viewer.js:79-100`)
- 텍스트-오디오 동기화 (`static/js/viewer.js:193-198`)
- 화자별 색상 팔레트 (`static/js/viewer.js:16, 180-182`)

### 5️⃣ 📝 노트 목록 (Note List) [부분 완료]

**목표:** 사용자의 모든 기록을 효율적으로 조회하고 관리.

**진행 상황:**
- [x] **리스트 UI:** 제목, 날짜, 요약문 표시.
- [x] **검색:** 제목 및 내용 키워드 검색 (프론트엔드 필터링).
- [x] **업로드 버튼:** 노트 목록 페이지에서 파일 업로드 가능.
- [x] **색상 시스템:** indigo 기반 색상 팔레트 적용.
- [ ] **태그 표시:** 태그 UI 및 필터링 기능.
- [ ] **썸네일:** 오디오/비디오 구분 표시.
- [ ] **필터링:** 날짜 범위, 태그, 카테고리별 필터 (Phase 4로 이동).
- [ ] **페이지네이션:** 대량의 데이터를 처리하기 위한 페이징 기능 (Phase 4로 이동).

**상세 스펙:**
*   **리스트 UI:** 제목, 날짜, 태그, 요약문, 썸네일(오디오/비디오 구분) 표시.
*   **검색:** 제목 및 내용 키워드 검색 (백엔드 검색 API 연동).
*   **필터링:** 날짜 범위, 태그, 카테고리별 필터.
*   **페이지네이션:** 대량의 데이터를 처리하기 위한 페이징 기능.

---

## 4. 📅 Phase 4: 기능 고도화 (진행 중)

### 1. AI 에이전트 UI 연동 [완료 ✅]
- [x] **Action Item 추출:** 회의록에서 할 일 자동 추출 결과를 노트 상세 페이지에 표시.
- [x] **Action Item 완료 체크박스:** 완료 상태 관리 기능 추가.
- [x] **데이터베이스 테이블:** `meeting_action_items` 테이블 생성 및 인덱스 추가.
- [x] **백엔드 API:** 
  - `POST /api/extract_action_items/{meeting_id}` - 수동 추출
  - `GET /api/action_items/{meeting_id}` - 목록 조회
  - `POST /api/action_items/{id}/status` - 상태 업데이트
- [x] **프론트엔드 컴포넌트:** ActionItemsView 컴포넌트 구현.
- [x] **NoteDetail 통합:** "Action Items" 탭 추가 및 연동.
- [x] **자동 저장:** `upload_service.py`에서 자동 추출 후 DB 저장.
- [ ] **Google Calendar 연동 상태 시각화:** 캘린더에 등록된 일정 표시 (선택적, 향후 개선).

**상세 구현 내용:**
- **데이터베이스:** `meeting_action_items` 테이블 (id, meeting_id, content, due_date, status, tool_call_id, calendar_event_id)
- **서비스 레이어:** `frontend/src/services/actionItems.ts` (extractActionItems, getActionItems, updateActionItemStatus)
- **컴포넌트:** `frontend/src/components/ActionItemsView.tsx` (목록 표시, 체크박스, 추출 버튼)
- **판단 로그:** [judgment_log_priority2.md](judgment_log_priority2.md) 참고

### 2. 공유 기능 UI [완료 ✅]
- [x] **노트 공유 모달:** 이메일 기반 공유 기능 UI (ShareModal 컴포넌트).
- [x] **공유받은 노트 목록 페이지:** `/shared-notes` 페이지 구현 (SharedNoteList).
- [x] **권한 관리 UI:** 공유 권한 조회 및 해제 기능.
- [x] **백엔드 API:**
  - `POST /api/share/{meeting_id}` - 노트 공유
  - `GET /api/shared_users/{meeting_id}` - 공유 사용자 목록 조회
  - `POST /api/unshare/{meeting_id}/{user_id}` - 공유 해제
  - `GET /api/shared-notes` - 공유받은 노트 목록 조회 (JSON API)

### 3. 검색 및 필터링 고도화 [완료 ✅]
- [x] **날짜 범위 필터:** 시작일/종료일 선택 기능 (2025-12-29 완료).
- [x] **태그 기반 필터:** 선택 사항으로 제외 (2025-12-29 결정).
- [x] **페이지네이션 구현:** 무한 스크롤 방식으로 구현 (2025-12-29 완료).
- [x] **정렬 옵션:** 토글 방식으로 구현 (최신순/오래된 순, 제목 가나다순/역순, 2025-12-29 완료).
- **완료 일자:** 2025-12-29

**상세 구현 내용:**
- **백엔드:**
  - `services/user_service.py`: `get_user_meetings()` 함수에 페이지네이션 및 필터링 파라미터 추가
  - `services/user_service.py`: `get_user_meetings_count()` 함수 추가
  - `routes/meetings.py`: `/notes_json` API 엔드포인트 수정 (쿼리 파라미터 지원)
- **프론트엔드:**
  - `frontend/src/services/meeting.ts`: 페이지네이션 지원 API 호출 함수 수정
  - `frontend/src/pages/NoteList.tsx`: 무한 스크롤, 디바운싱 검색, 날짜 필터 UI 구현
- **기술 스택:**
  - IntersectionObserver API (무한 스크롤)
  - 디바운싱 (500ms 지연)
  - 서버 사이드 검색 및 필터링

---

## 5. 📅 Phase 5: 시스템 최적화 (Future)

### 1. 성능 개선

#### 1.1 대용량 처리 비동기화 [계획 수립 완료]
- **현재 문제점:**
  - 동기 처리로 인한 블로킹 (2-7분 소요)
  - 동시 업로드 시 서버 부하
  - 중간 실패 시 전체 재시작 필요
- **해결 방안:**
  - **Phase 1 (우선):** Redis Queue 기반 경량 비동기화
    - Redis 설치 및 설정
    - 간단한 큐 시스템 구현
    - Worker 프로세스 구현
    - API 엔드포인트 수정 (즉시 응답)
    - 프론트엔드 폴링 방식 상태 확인
    - **예상 작업 시간:** 8-12시간
  - **Phase 2 (향후):** Celery 도입
    - Celery 설정 및 작업 분리
    - 작업 체인 구성
    - 모니터링 도구 (Flower) 설치
    - **예상 작업 시간:** 16-24시간
- **구현 고려사항:**
  - 복잡도 증가 (여러 프로세스 관리)
  - 상태 관리 (Redis 또는 DB)
  - 프론트엔드 변경 (폴링 또는 WebSocket)
  - 인프라 추가 (Redis 서버 운영)
- **기대 효과:**
  - 업로드 후 즉시 응답
  - 동시 업로드 처리 능력 향상
  - 실패 시 자동 재시도
  - Worker 추가로 확장 가능
- **계획 수립 일자:** 2025-12-29

#### 1.2 이미지/썸네일 최적화
- **썸네일 생성 및 캐싱:** 오디오/비디오 파일 썸네일 생성
- **레이지 로딩:** 필요 시에만 이미지 로드

#### 1.3 코드 스플리팅 및 레이지 로딩
- **프론트엔드 최적화:** 번들 크기 감소
- **동적 임포트:** 필요 시에만 컴포넌트 로드

### 2. 비용 최적화
- **로컬 STT 전면 도입:** `services/diarization.py` 정식 통합 (이미 부분 적용됨)
- **OpenAI 의존성 제거:** Gemini 임베딩 전환
- **캐싱 전략 도입:** 자주 사용되는 데이터 캐싱
- **STT/LLM 로컬화 점진 교체:** 현 파이프라인 유지 + 단계별 검증(whisper-turbo 경량화 → 화자분리/단일트랙 → 텍스트 단계 로컬 LLM). Gemma 4·gpt-oss 평가 결과 포함 → [stt_llm_localization_eval.md](../planning/stt_llm_localization_eval.md)

### 3. 검색 고도화
- **하이브리드 검색:** 벡터 검색 + 키워드 검색 결합
- **검색 결과 하이라이팅:** 검색어 강조 표시
- **자동완성 기능:** 검색어 자동완성

---

## 개발 우선순위 요약

### Phase 3 (핵심 기능 구현 완료 ✅)
0. **로그인/인증 시스템** (완료 ✅) - Firebase 연동, Protected Routes, AuthContext, Google Popup 로그인
1. **대시보드 완성** (완료 ✅) - 통계 API 연동, 전역 챗봇 연동, 파일 업로드 모달 연동
2. **파일 업로드 모달** (완료 ✅) - Drag & Drop, SSE 진행률 표시, 파일 유효성 검사
3. **실시간 녹음 기능** (완료 ✅) - useRecorder 훅, 파형 시각화, 마이크/시스템 오디오 지원
4. **노트 상세 뷰어** (완료 ✅) - 오디오 플레이어, STT 스크립트 동기화, 요약/마인드맵/챗봇 탭
5. **챗봇 기능** (완료 ✅) - 전역 챗봇 사이드바, 회의별 챗봇 (ChatSidebar), chat.ts 서비스
6. **디자인 시스템 통일** (완료 ✅) - genminute-dashboard 색 조합 적용 (indigo/teal/rose)

### Phase 3.5: 버그 수정 및 편집 기능 (완료 ✅)

**완료된 작업:**
- [x] **TypeScript 타입 오류 수정:** `useRecorder.ts` (cursor, webkitAudioContext), `GlobalChatSidebar.tsx` (타입 단언 개선)
- [x] **API 엔드포인트 수정:** 삭제 API (`DELETE` → `POST`)
- [x] **제목/날짜 수정 기능:** NoteDetail 페이지 MoreVertical 메뉴에 편집 옵션 추가
- [x] **회의록 생성/조회 탭:** 요약과 별개의 회의록 탭 추가
- [x] **메뉴 이름 통일:** "회의록" → "내 노트", "녹음" → "기록"
- [x] **MoreVertical 버튼 이벤트 전파 방지:** NoteList 페이지 수정
- [x] **공유 기능 UI:** 이메일 기반 노트 공유 모달 및 공유받은 노트 목록 페이지 구현
- [x] **Action Items UI:** AI 에이전트가 추출한 Action Item을 UI에서 조회 및 관리 기능 구현

### Phase 4: 기능 고도화 (진행 중)

#### Priority 1: 공유 기능 UI [완료 ✅]
- [x] **노트 공유 모달:** 이메일 기반 공유 기능 UI
  - `POST /api/share/{meeting_id}` - 이메일 기반 공유
  - `GET /api/shared_users/{meeting_id}` - 공유 사용자 목록 조회
  - `POST /api/unshare/{meeting_id}/{user_id}` - 공유 해제
  - NoteDetail 페이지의 MoreVertical 메뉴에 "공유" 추가
- [x] **공유받은 노트 목록 페이지:** `/shared-notes` 페이지 구현
  - `SharedNoteList.tsx` 컴포넌트 생성
  - 네비게이션에 "공유받은 노트" 메뉴 추가
- **완료 일자:** 2025년 12월 18일

#### Priority 2: AI 에이전트 UI 연동 [완료 ✅]
- [x] **데이터베이스 테이블:** `meeting_action_items` 테이블 생성 및 인덱스 추가
- [x] **백엔드 API 엔드포인트:**
  - `POST /api/extract_action_items/{meeting_id}` - 수동 추출
  - `GET /api/action_items/{meeting_id}` - 목록 조회
  - `POST /api/action_items/{id}/status` - 상태 업데이트
- [x] **데이터베이스 함수:** save_action_items, get_action_items_by_meeting_id, update_action_item_status
- [x] **자동 저장 연동:** `upload_service.py`에서 agent_service.process() 결과 자동 저장
- [x] **프론트엔드 서비스:** `frontend/src/services/actionItems.ts` 생성
- [x] **프론트엔드 컴포넌트:** `frontend/src/components/ActionItemsView.tsx` 생성
- [x] **NoteDetail 통합:** "Action Items" 탭 추가 및 연동
- [x] **UI/UX:** 완료 체크박스, 추출 버튼, 빈 상태 메시지, 로딩 상태
- [ ] **Google Calendar 연동 상태 시각화:** 캘린더에 등록된 일정 표시 (선택적, 향후 개선)
- **완료 일자:** 2025년 12월 ([judgment_log_priority2.md](judgment_log_priority2.md) 참고)
- **판단 로그:** [judgment_log_priority2.md](judgment_log_priority2.md)에 상세 기록

#### Priority 3: 검색 및 필터링 고도화 [진행 중]
- [x] **날짜 범위 필터:** 시작일/종료일 선택 기능 (2025-12-29 완료)
- [ ] **태그 기반 필터:** 태그별 노트 필터링
- [x] **페이지네이션 구현:** 무한 스크롤 방식으로 구현 (2025-12-29 완료)
- [x] **정렬 옵션:** 토글 방식으로 구현 (최신순/오래된 순, 제목 가나다순/역순, 2025-12-29 완료)
- **완료 일자:** 2025-12-29 (일부 기능 완료)

#### 노트 상세 페이지 및 녹음 기능 개선 [완료 ✅]
- [x] **세그먼트 선택 로직 개선:** 사용자 선택 우선, 조건부 가장 가까운 세그먼트 (2025-12-29 완료)
- [x] **STT 언어 자동 감지:** Whisper 자동 언어 감지 기능 적용 (2025-12-29 완료)
- [x] **오디오 duration 처리:** NaN/Infinity 문제 해결 (2025-12-29 완료)
- [x] **React key prop 최적화:** 동적 요소의 고유 key 보장 (2025-12-29 완료)
- [x] **Recorder 페이지 안정화:** 오디오 플레이어 깜빡임 문제 해결 (2025-12-29 완료)
- [x] **전역 업로드 상태 통합:** UploadContext를 통한 일관된 UX (2025-12-29 완료)
- **완료 일자:** 2025-12-29

#### Priority 4: UX 개선 [완료 ✅]
- [x] **재생 속도 조절:** 0.5x ~ 2.0x (2025-12-29 완료)
- [x] **구간 반복 재생:** A-B 마커 방식 (2025-12-29 완료)
- [x] **파형 시각화:** WaveSurfer.js 통합 (2025-12-29 완료)
- [x] **영상 재생 기능:** 비디오 파일 재생 지원 (2025-12-29 완료)
- **완료 일자:** 2025-12-29

### Phase 5: 시스템 최적화 (장기)
- 시스템 최적화 (Celery/Redis, 비용 최적화, 검색 고도화)

---

---

## 부록: GenMinute Live (실시간 녹음) 상세 계획

> **원본**: `GenMinute_upgrade.md` 내용 통합

### 목표
1. 모바일 현장 녹음: 스마트폰 브라우저로 대면 회의 녹음
2. 화상 회의(Zoom) 연동: PC 시스템 오디오 캡처
3. 통합 파이프라인: 파일/마이크/시스템 오디오를 단일 처리 파이프라인으로 통합

### 아키텍처 전략: "유니버설 웹 레코더"
- 웹 표준 기술(WebRTC, MediaRecorder API)만 사용
- 모바일 녹음: `getUserMedia({ audio: true })`
- PC/Zoom 녹음: `getDisplayMedia({ video: true, audio: true })`

### 기술 방식 결정
- **채택**: 웹앱 모듈 확장 방식 (에이전트 Tool 방식 대비 모바일 호환성, Zoom 캡처 용이)
- **Phase 1**: 유니버설 레코더 UI/UX 구현 (완료 ✅)
- **Phase 2**: 준실시간 미리보기 (WebSocket 연동)

---

## 참고사항

- **기존 코드 재사용:** Jinja2 템플릿의 핵심 로직(SSE 파싱, 녹음, 뷰어)을 React 컴포넌트로 변환 시 최대한 보존.
- **점진적 전환:** 기존 Jinja2 템플릿과의 호환성 유지하며 단계적으로 전환.
- **백엔드 API 재사용:** 기존 Flask 엔드포인트 최대한 활용.

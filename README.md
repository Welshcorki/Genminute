# Genminute

AI 기반 회의록 자동 생성 시스템

회의 음성/영상을 업로드하면 자동으로 음성인식(STT), 회의록 생성, 마인드맵 생성, RAG 기반 챗봇을 제공하는 웹 애플리케이션입니다.

## 문서 안내

- **PRD (제품 요구사항)**: [docs/planning/PRD.md](docs/planning/PRD.md)
- **실행 가이드**: [docs/guides/setup_guide.md](docs/guides/setup_guide.md)
- **배포 이슈**: [docs/guides/deployment_issues.md](docs/guides/deployment_issues.md)
- **로드맵**: [docs/development/roadmap.md](docs/development/roadmap.md)
- **비용 예측**: [docs/planning/cost_estimate.md](docs/planning/cost_estimate.md)
- **개발 로그**: [docs/development/dev_log.md](docs/development/dev_log.md)
- **학습 포인트**: [docs/development/learning_points.md](docs/development/learning_points.md)
- **아카이브**: [docs/archive/](docs/archive/) (인수인계 문서, Cursor 대화 내보내기 등)

## 주요 기능

### 1. 음성/영상 파일 업로드 및 전사
- **지원 포맷**: WAV, MP3, M4A, FLAC, MP4, WEBM (최대 500MB, 클라이언트 측 검증만)
- **자동 화자 분리**: 
  - Google Gemini를 활용한 화자 구분 (SPEAKER_00, SPEAKER_01...)
  - 또는 로컬 STT (faster-whisper + pyannote.audio) 옵션
- **언어 자동 감지**: Whisper 모델의 자동 언어 감지 기능
- **타임스탬프**: 각 발언에 정확한 시간 정보 (초 단위)
- **신뢰도 점수**: 각 세그먼트별 전사 정확도 (0.0 ~ 1.0)
- **영상 변환**: ffmpeg를 통한 자동 오디오 추출
- **자동 포맷 변환**: WebM → MP4/M4A 자동 변환

### 2. 실시간 녹음 및 화상 회의 기록 (Universal Web Recorder)
- **모바일 현장 녹음**: 스마트폰 마이크를 통한 대면 회의 실시간 녹음
- **PC 시스템 녹화**: Zoom, Google Meet 등 화상 회의 화면 및 시스템 오디오 캡처
- **파형 시각화**: 실시간 오디오 파형 시각화 (Canvas 기반)
- **자동 포맷 변환**: WebM(브라우저 녹음) → MP4/M4A(표준 포맷) 자동 변환으로 완벽한 재생 호환성 확보
- **하이브리드 파일명**: `[UUID]_[날짜시간].mp4` 형식으로 보안과 가독성 동시 확보

### 3. AI 기반 회의록 자동 생성
- **단락 요약**: 주제별로 그룹화된 요약문 (마크다운 ### 헤더 형식)
- **정식 회의록**:
  - 회의 정보 (제목, 날짜, 참석자)
  - 전체 요약
  - 주요 논의 사항
  - 액션 아이템 (담당자, 기한)
  - 향후 계획
- **인용 표시**: `[cite: 1, 2]` 형식으로 출처 추적

### 3. 마인드맵 시각화
- 회의 내용의 핵심 키워드를 계층적 마인드맵으로 자동 생성
- Markmap 라이브러리를 활용한 인터랙티브 시각화
- 확대/축소, 드래그 가능한 SVG 렌더링

### 4. AI 챗봇 (RAG 기반)
- **Retrieval-Augmented Generation (RAG)** 아키텍처
- ChromaDB 벡터 데이터베이스를 활용한 의미 기반 검색
- 회의록 청크 및 주제별 요약에서 관련 정보 추출
- Gemini를 통한 실시간 답변 생성
- 출처 인용 (회의 정보, 타임스탬프)
- 전역 챗봇: 모든 회의록 검색
- 회의별 챗봇: 특정 회의록만 검색

### 5. 회의록 관리
- **제목/날짜 수정**: 인라인 편집 기능 (소유자 전용)
- **공유 기능**: 
  - 이메일 기반 회의록 공유 (소유자 전용)
  - 공유받은 사용자 목록 조회 및 관리
  - 공유 해제 기능
  - 공유받은 노트 별도 목록 페이지
- **접근 제어**: 소유자/공유 사용자/관리자 역할 기반 권한
- **화자 비중 분석**: 발언 분량 시각화 (Chart.js)
- **오디오/비디오 재생**: 
  - 타임스탬프 동기화 재생
  - 재생 속도 조절 (0.5x ~ 2.0x)
  - 구간 반복 재생 (A-B 마커)
  - 파형 시각화 (WaveSurfer.js, 오디오만)
  - 영상 파일 재생 지원 (MP4, WEBM, MOV, AVI, MKV)
- **검색 및 필터링**:
  - 실시간 검색 (제목, 요약 내용)
  - 날짜 범위 필터 (시작일/종료일)
  - 무한 스크롤 페이지네이션
  - 서버 사이드 검색 및 필터링

### 6. 전역 업로드 상태 관리
- **백그라운드 업로드**: 페이지 이동 후에도 업로드 진행 상황 확인 가능
- **업로드 상태 바**: 화면 우측 하단에 고정 표시
- **진행률 표시**: 단계별 진행률 (업로드 → STT → 분석 → 마인드맵 → 완료)
- **취소 및 결과 보기**: 업로드 취소 및 완료 후 노트로 이동

### 7. AI 에이전트 (Action Item)
- **LangGraph 기반**: 지능형 에이전트로 Action Item 자동 추출 (`langgraph`는 `requirements.txt`에 없어 별도 설치 필요)
- **Google Calendar 연동**: OAuth 2.0 기반 일정 자동 등록
- 회의록에서 Action Item 인식 및 외부 도구 연동

### 8. 사용자 인증
- **Google 계정 로그인**: Supabase Auth (프론트엔드에서 Access Token 발급 → 백엔드 검증)
- **세션 관리**: Flask 세션 기반 (`/api/login`에서 Supabase Access Token 검증 후 세션 생성)
- **관리자 모드**: `ADMIN_EMAILS` 기반 권한, 디버그 도구 및 고급 기능 접근

---

## 기술 스택

### Backend
- **프레임워크**: Flask 3.1+
- **AI/ML**:
  - Google Gemini (STT, 요약, 회의록, 마인드맵, 챗봇 — `GEMINI_MODEL` 환경변수, 기본 `gemini-3-flash`)
  - Faster-Whisper 1.2.0 (로컬 STT 옵션)
  - Pyannote.Audio 3.1+ (화자 분리)
- **벡터 데이터베이스**: ChromaDB + LangChain
- **에이전트 프레임워크**: LangGraph (`requirements.txt` 미포함 — 별도 설치 필요)
- **데이터베이스**: Supabase (PostgreSQL, 관계형 데이터 + Auth), ChromaDB (벡터 임베딩)
  - `DB_TYPE` 환경변수로 `supabase`(기본) / `sqlite` 전환 가능 (Repository 패턴)
- **인증**: Supabase Auth (Access Token 검증)
- **임베딩**: OpenAI Embeddings (`EMBEDDING_MODEL` 환경변수, 기본 text-embedding-ada-002)
- **오디오 처리**: ffmpeg

### Frontend
- **프레임워크**: React 19.2.0 + TypeScript 5.9.3
- **빌드 도구**: Vite 7.2.4
- **라우팅**: React Router DOM 7.10.1
- **스타일링**: Tailwind CSS 3.4.1
- **HTTP 클라이언트**: Axios 1.13.2
- **인증**: Supabase JS 클라이언트 (Google OAuth)
- **아이콘**: Lucide React 0.559.0
- **차트**: Chart.js (화자 비중 시각화)
- **마인드맵**: Markmap (SVG 기반 인터랙티브 렌더링)
- **파형 시각화**: WaveSurfer.js

---

## 프로젝트 구조

```
genminute/
├── app.py                          # Flask 애플리케이션 진입점
├── config.py                       # 중앙 집중식 설정 관리
│
├── routes/                         # HTTP 라우트 핸들러 (Blueprint)
│   ├── __init__.py
│   ├── admin.py                    # 관리자 전용 디버그 기능
│   ├── auth.py                     # 인증 및 사용자 관리
│   ├── chat.py                     # AI 챗봇 Q&A
│   ├── meetings.py                 # 회의록 CRUD 작업
│   ├── summary.py                  # 요약 및 회의록 생성
│   └── google_auth.py              # Google Calendar OAuth
│
├── services/                       # 비즈니스 로직 레이어
│   ├── __init__.py
│   ├── upload_service.py           # 파일 업로드 및 처리 로직
│   ├── stt_service.py              # STT 서비스
│   ├── chat_service.py             # 챗봇 서비스
│   ├── analysis_service.py         # 화자 비중 분석
│   ├── user_service.py              # 사용자 서비스
│   ├── agent_service.py            # AI 에이전트 서비스
│   └── diarization.py              # 로컬 STT 및 화자 분리
│
├── database/                       # 데이터베이스 레이어
│   ├── repositories/               # Repository 구현체 (SQLite/Supabase) 및 테이블 초기화
│   ├── sqlite_manager.py           # SQLite 데이터베이스 작업
│   └── vector_manager.py           # ChromaDB 벡터 데이터베이스
│
├── tools/                          # 외부 도구 연동
│   ├── google_calendar_tool.py     # Google Calendar 도구
│   └── generate_roadmap_mindmap.py # 마인드맵 생성 도구
│
├── frontend/                       # React 프론트엔드 (SPA)
│   ├── src/
│   │   ├── pages/                  # 페이지 컴포넌트
│   │   │   ├── Dashboard.tsx       # 대시보드
│   │   │   ├── NoteList.tsx        # 노트 목록
│   │   │   ├── NoteDetail.tsx      # 노트 상세
│   │   │   ├── SharedNoteList.tsx  # 공유받은 노트 목록
│   │   │   ├── Recorder.tsx        # 실시간 녹음/녹화
│   │   │   └── Login.tsx           # 로그인
│   │   ├── components/             # 재사용 가능한 컴포넌트
│   │   │   ├── Layout.tsx          # 레이아웃 (네비게이션)
│   │   │   ├── ShareModal.tsx      # 공유 모달
│   │   │   ├── MinutesView.tsx     # 회의록 뷰어
│   │   │   ├── SummaryView.tsx     # 요약 뷰어
│   │   │   ├── MindmapView.tsx     # 마인드맵 뷰어
│   │   │   ├── GlobalChatSidebar.tsx # 전역 챗봇 사이드바
│   │   │   ├── ChatSidebar.tsx     # 회의별 챗봇 사이드바
│   │   │   ├── UploadModal.tsx     # 파일 업로드 모달
│   │   │   ├── UploadStatusBar.tsx # 업로드 상태 바
│   │   │   └── AudioVisualizer.tsx # 오디오 파형 시각화
│   │   ├── services/               # API 서비스 레이어
│   │   │   ├── api.ts              # Axios 인스턴스
│   │   │   ├── auth.ts             # 인증 서비스
│   │   │   ├── meeting.ts          # 회의록 서비스
│   │   │   ├── share.ts            # 공유 서비스
│   │   │   ├── chat.ts             # 챗봇 서비스
│   │   │   ├── summary.ts          # 요약 서비스
│   │   │   ├── mindmap.ts          # 마인드맵 서비스
│   │   │   └── minutes.ts          # 회의록 서비스
│   │   ├── contexts/               # React Context
│   │   │   ├── AuthContext.tsx     # 인증 상태 관리
│   │   │   └── UploadContext.tsx   # 업로드 상태 관리
│   │   ├── hooks/                  # 커스텀 훅
│   │   │   └── useRecorder.ts      # 녹음/녹화 훅
│   │   └── config/                  # 설정
│   │       └── supabase.ts         # Supabase 클라이언트 설정
│   ├── package.json                # Node.js 종속성
│   └── vite.config.ts              # Vite 빌드 설정
│
├── templates/                      # Jinja2 HTML 템플릿 (레거시)
│   ├── layout.html                 # 기본 레이아웃
│   ├── index.html                  # 업로드 페이지
│   ├── viewer.html                 # 회의록 뷰어
│   └── ...
│
├── static/                         # 정적 파일 (레거시)
│   ├── css/
│   │   └── style.css               # 메인 스타일시트
│   └── js/
│       ├── script.js               # 챗봇 UI 로직
│       └── viewer.js               # 뷰어 페이지 로직
│
├── database/                       # 데이터베이스 저장소
│   ├── minute_ai.db                # SQLite 데이터베이스
│   └── vector_db/                  # ChromaDB 영구 저장소
│
├── uploads/                        # 업로드된 오디오/비디오 파일
├── requirements.txt                # Python 패키지 종속성
├── .env                            # 환경 변수 (비공개)
└── README.md                       # 프로젝트 문서 (본 파일)
```

---

## 데이터베이스 스키마

### SQLite (minute_ai.db)

#### meeting_dialogues
회의 전사 세그먼트 저장
```sql
- segment_id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT (UUID, 세그먼트 그룹화)
- meeting_date: TEXT (YYYY-MM-DD HH:MM:SS)
- speaker_label: TEXT (예: "1", "2", "3")
- start_time: REAL (시작 시간, 초)
- segment: TEXT (전사 텍스트)
- confidence: REAL (0.0 ~ 1.0)
- audio_file: TEXT (파일명)
- title: TEXT (회의 제목)
- owner_id: INTEGER (users 외래키)
```

#### meeting_minutes
생성된 회의록 저장
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT UNIQUE (meeting_dialogues 연결)
- minutes_content: TEXT (마크다운 형식)
- created_at: DATETIME
- owner_id: INTEGER
```

#### meeting_mindmap
마인드맵 데이터 저장
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT UNIQUE
- mindmap_content: TEXT (마크다운 형식)
- created_at: DATETIME
```

#### users
사용자 계정 및 인증
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- google_id: TEXT UNIQUE (Supabase Auth UID)
- email: TEXT UNIQUE
- name: TEXT
- profile_picture: TEXT (URL)
- role: TEXT ('user' 또는 'admin')
- google_auth_credentials_json: TEXT (Google Calendar OAuth 토큰)
- created_at: DATETIME
```

#### meeting_shares
회의록 접근 제어
```sql
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- meeting_id: TEXT (공유되는 회의)
- owner_id: INTEGER (소유자)
- shared_with_user_id: INTEGER (접근 권한을 받은 사용자)
- permission: TEXT ('read')
- created_at: DATETIME
```

### ChromaDB (벡터 데이터베이스)

#### meeting_chunks
스마트 청킹된 회의 전사본 + 임베딩
```python
Metadata:
- meeting_id: UUID
- dialogue_id: meeting_id_chunk_N
- chunk_index: 정수 (순서)
- title: 회의 제목
- meeting_date: YYYY-MM-DD HH:MM:SS
- audio_file: 파일명
- start_time: 시작 시간 (초)
- end_time: 종료 시간 (초)
- speaker_count: 화자 수

Content: 정제된 전사 텍스트 (화자 라벨 및 타임스탬프 제거)
```

#### meeting_subtopic
주제별 단락 요약
```python
Metadata:
- meeting_id: UUID
- meeting_title: 회의 제목
- meeting_date: YYYY-MM-DD HH:MM:SS
- audio_file: 파일명
- main_topic: ### 헤더에서 추출
- summary_index: 정수 (순서)

Content: "### 주제\n* 포인트 1\n* 포인트 2..." 형식
```

---

## API 엔드포인트

### 인증 (auth.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/login` | GET | 불필요 | 로그인 페이지 표시 |
| `/api/login` | POST | 불필요 | Supabase Access Token 검증 및 세션 생성 |
| `/api/logout` | POST | 불필요 | 세션 종료 |
| `/api/me` | GET | 필수 | 현재 사용자 정보 조회 |

### 회의록 관리 (meetings.py, meetings_share.py, meetings_upload.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/` | GET | 필수 | 대시보드 페이지 |
| `/notes` | GET | 필수 | 내 회의록 목록 |
| `/shared-notes` | GET | 필수 | 공유받은 회의록 목록 |
| `/view/<meeting_id>` | GET | 필수 | 회의록 뷰어 페이지 |
| `/api/meeting/<meeting_id>` | GET | 필수 | 회의록 데이터 조회 |
| `/notes_json` | GET | 필수 | 회의록 목록 조회 (JSON, 페이지네이션 지원) |
| `/upload` | POST | 필수 | 오디오/비디오 파일 업로드 (SSE 스트리밍, `meetings_upload.py`) |
| `/api/delete_meeting/<meeting_id>` | POST | 필수 | 회의록 삭제 (소유자 전용) |
| `/api/update_title/<meeting_id>` | POST | 필수 | 제목 수정 (소유자 전용) |
| `/api/update_date/<meeting_id>` | POST | 필수 | 날짜 수정 (소유자 전용) |
| `/api/share/<meeting_id>` | POST | 필수 | 이메일로 회의록 공유 (소유자 전용) |
| `/api/shared_users/<meeting_id>` | GET | 필수 | 공유된 사용자 목록 조회 |
| `/api/unshare/<meeting_id>/<user_id>` | POST | 필수 | 공유 해제 (소유자 전용) |
| `/api/shared-notes` | GET | 필수 | 공유받은 노트 목록 조회 (JSON API) |
| `/api/mindmap/<meeting_id>` | GET | 필수 | 마인드맵 데이터 조회 |
| `/api/stats` | GET | 필수 | 사용자 통계 조회 (이번 달 노트 수, 총 녹음 시간 등) |

**쿼리 파라미터 (`/notes_json`):**
- `page`: 페이지 번호 (기본값: 1)
- `per_page`: 페이지당 항목 수 (기본값: 20)
- `search`: 검색어 (제목, 요약 내용)
- `start_date`: 시작일 (YYYY-MM-DD)
- `end_date`: 종료일 (YYYY-MM-DD)

### 요약 및 회의록 (summary.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/api/summarize/<meeting_id>` | POST | 필수 | 단락 요약 생성 |
| `/api/check_summary/<meeting_id>` | GET | 필수 | 요약 존재 여부 확인 |
| `/api/generate_minutes/<meeting_id>` | POST | 필수 | 정식 회의록 생성 |
| `/api/get_minutes/<meeting_id>` | GET | 필수 | 기존 회의록 조회 |

### 챗봇 (chat.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/api/chat` | POST | 필수 | AI 챗봇 Q&A |

### Google Calendar 연동 (google_auth.py)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|----------|--------|------|------|
| `/google/calendar/authorize` | GET | 필수 | Google Calendar OAuth 시작 |
| `/oauth2callback` | GET | 불필요 | OAuth 콜백 처리 |

**요청 예시:**
```json
{
  "query": "예산에 대해 무엇을 논의했나요?",
  "meeting_id": "선택적-특정-회의-ID"
}
```

**응답 예시:**
```json
{
  "success": true,
  "answer": "회의 내용 기반 AI 생성 답변",
  "sources": [
    {
      "type": "chunk",
      "meeting_id": "...",
      "title": "...",
      "meeting_date": "...",
      "start_time": 0,
      "end_time": 120
    }
  ]
}
```

---

## 설치 및 실행

### 1. 사전 요구사항
- Python 3.11 이상 (로컬 STT 사용 시)
- **ffmpeg (필수)**: 비디오/오디오 변환을 위해 반드시 설치되어 있어야 하며, 시스템 PATH에 등록되어야 합니다.
- SQLite 3.x
- Node.js 18 이상 (프론트엔드 빌드용)

### 2. 환경 설정

#### 2.1 가상환경 생성
```bash
conda env create -f environment_crossplatform.yml
conda activate genminute
```

#### 2.2 환경 변수 설정
[.env.example](.env.example)을 `.env`로 복사한 뒤 값을 채웁니다. 전체 변수와 설명은 `.env.example`을 참조하세요.
```bash
cp .env.example .env
```
필수 변수(`config.validate()` 기준):
- `FLASK_SECRET_KEY` — `python -c "import secrets; print(secrets.token_hex(32))"`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — Supabase 대시보드 > Project Settings > API
- `GOOGLE_API_KEY` — Gemini (STT/요약/회의록/챗봇)
- `OPENAI_API_KEY` — 벡터 DB 임베딩 (`EMBEDDING_MODEL`)

조건부 필수:
- `HF_TOKEN` — `STT_ENGINE=local`일 때
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — Google Calendar 연동 사용 시

프론트엔드(Vite) 빌드용: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`

#### 2.3 Supabase 설정
인증과 관계형 데이터는 Supabase(PostgreSQL)를 사용합니다.
1. [Supabase](https://supabase.com) 프로젝트 생성
2. Authentication > Providers에서 Google 로그인 활성화
3. Project Settings > API에서 `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_ANON_KEY` 확인
4. 테이블 스키마는 [docs/database/supabase_schema.sql](docs/database/supabase_schema.sql) 참조

> 참고: `DB_TYPE=sqlite`로 설정하면 Supabase 없이 로컬 SQLite로도 구동할 수 있습니다(Repository 패턴).

### 3. 프론트엔드 빌드 및 실행

#### 3.1 프론트엔드 종속성 설치
```bash
cd frontend
npm install
```

#### 3.2 프론트엔드 개발 서버 실행 (선택사항)
```bash
# 프론트엔드만 별도로 개발할 때
npm run dev
```

#### 3.3 프론트엔드 프로덕션 빌드
```bash
# 프로덕션 빌드 생성 (dist 폴더에 생성됨)
npm run build
```

### 4. 백엔드 애플리케이션 실행
```bash
# 프로젝트 루트에서
python app.py
```

브라우저에서 `http://localhost:5000` 접속

**참고:** 
- Supabase(`DB_TYPE=supabase`) 사용 시 테이블 스키마는 [docs/database/supabase_schema.sql](docs/database/supabase_schema.sql)을 Supabase SQL Editor에서 실행하여 준비합니다.
- `DB_TYPE=sqlite` 사용 시 SQLite 테이블은 `app.py` 실행 시 자동 생성됩니다.
- 프론트엔드는 빌드된 `dist` 폴더의 정적 파일을 Flask가 서빙합니다.
- 개발 환경에서는 프론트엔드 개발 서버(`npm run dev`)와 백엔드 서버를 동시에 실행하고, 프록시 설정을 통해 연동할 수 있습니다.

---

## 주요 워크플로우

### 1. 회의록 생성 워크플로우
```
1. 사용자가 오디오/비디오 파일 업로드 또는 실시간 녹음
   ↓
2. 파일 저장 (/uploads/<uuid>_<filename>)
   ↓
3. (영상인 경우) ffmpeg로 오디오 추출
   ↓
4. STT 처리 (Gemini 또는 로컬 STT)
   → 화자 분리 + 타임스탬프 + 신뢰도
   → 언어 자동 감지
   ↓
5. SQLite에 세그먼트 저장 (meeting_dialogues)
   ↓
6. 스마트 청킹 + 임베딩 → ChromaDB (meeting_chunks)
   ↓
7. Gemini로 단락 요약 생성
   ↓
8. 주제별 요약 임베딩 → ChromaDB (meeting_subtopic)
   ↓
9. Gemini로 마인드맵 키워드 추출
   ↓
10. SQLite에 마인드맵 저장 (meeting_mindmap)
   ↓
11. (선택) AI 에이전트로 Action Item 추출 및 Google Calendar 연동
```

### 2. 챗봇 쿼리 워크플로우
```
1. 사용자가 질문 입력
   ↓
2. 접근 가능한 회의록 ID 조회
   → 소유 + 공유받은 회의록
   ↓
3. 벡터 검색 (meeting_chunks + meeting_subtopic)
   → 각각 상위 3개 문서
   ↓
4. 컨텍스트 포맷팅 (메타데이터 포함)
   ↓
5. Gemini로 답변 생성
   → 컨텍스트 기반만 사용
   ↓
6. 출처 정보 추출
   → 회의 ID, 제목, 날짜, 타임스탬프
   ↓
7. JSON 응답 반환 (답변 + 출처)
```

---

## 핵심 알고리즘

### 스마트 청킹
```python
def _create_smart_chunks(segments, max_chunk_size=1000, time_gap_threshold=60):
    """
    청크 분할 조건:
    1. 청크 크기가 max_chunk_size 초과
    2. 시간 간격 > time_gap_threshold (주제 변경 감지)
    3. 화자 변경 AND 청크 크기 > 500자

    → 의미적 일관성 유지 + 검색 품질 향상
    """
```

### RAG 파이프라인
```python
def process_query(query, meeting_id, accessible_meeting_ids):
    # 1. 벡터 검색 (청크 + 요약)
    chunks = vdb_manager.search("chunks", query, k=3, filter_criteria=...)
    subtopics = vdb_manager.search("subtopic", query, k=3, filter_criteria=...)

    # 2. 컨텍스트 생성
    context = format_context(chunks + subtopics)

    # 3. AI 답변 생성
    answer = gemini_generate(query, context)

    # 4. 출처 추출
    sources = extract_sources(chunks + subtopics)

    return answer, sources
```

---

## 보안 고려사항

### 인증
- Flask 세션 기반 상태 관리
- 256비트 랜덤 시크릿 키

### 권한 제어
- 라우트 레벨 데코레이터 (`@login_required`, `@admin_required`)
- 데이터베이스 레벨 권한 체크 (`can_access_meeting`, `can_edit_meeting`)
- 쿼리 필터링 (accessible_meeting_ids)

### 입력 검증
- 파일 타입 화이트리스트 (wav, mp3, m4a, flac, mp4, webm)
- 파일 크기 제한 (500MB, 클라이언트 측 검증만)
- 날짜 형식 검증
- 이메일 형식 검증 (공유 기능)

### SQL 인젝션 방지
- 전체 코드에 파라미터화된 쿼리 사용
- SQL 문자열 연결 없음

### 파일 업로드 보안
- `werkzeug.secure_filename()` 사용
- UUID 접두사로 이름 충돌 방지
- 별도 업로드 디렉토리

---

## 성능 최적화

### 데이터베이스
- 자주 쿼리되는 컬럼에 인덱스 (meeting_id, owner_id)
- SQLite Row factory로 딕셔너리 접근
- DatabaseManager 싱글톤 패턴

### 벡터 데이터베이스
- 스마트 청킹으로 문서 수 감소
- ChromaDB의 효율적인 임베딩 저장
- 필터링된 검색으로 연산 감소

### 캐싱
- 싱글톤 매니저 (STT, Chat, Vector DB)

### 비동기 처리
- SSE 스트리밍으로 긴 작업 처리
- 요약 생성 백그라운드 처리
- 비블로킹 오디오 변환 (subprocess)
- **계획 중**: Redis Queue 기반 비동기 처리 시스템 (Phase 1: 경량 비동기화)

### 프론트엔드 최적화
- React 메모이제이션 (`useMemo`, `useCallback`)
- 무한 스크롤로 대량 데이터 효율적 로딩
- 디바운싱 검색 (500ms)
- Blob URL 메모리 관리 (`URL.revokeObjectURL`)

---

## 배포 고려사항

### 환경 변수
`.env` 파일에 필수 항목 (전체는 [.env.example](.env.example) 참조):
```
FLASK_SECRET_KEY=<256비트 랜덤 hex>
FLASK_DEBUG=False
FLASK_PORT=5000

SUPABASE_URL=<Supabase 프로젝트 URL>
SUPABASE_SERVICE_ROLE_KEY=<Supabase Service Role Key>

GOOGLE_API_KEY=<Google Gemini API 키>
OPENAI_API_KEY=<OpenAI API 키 (임베딩)>

ALLOWED_ORIGINS=https://your-domain.com
FRONTEND_URL=https://your-domain.com
ADMIN_EMAILS=admin1@example.com,admin2@example.com
```

### 시스템 종속성
- Python 3.11+ (로컬 STT 사용 시)
- ffmpeg (영상 변환용)
- SQLite 3.x
- Node.js 18+ (프론트엔드 빌드용)

### 프로덕션 권장사항
- Gunicorn 또는 uWSGI 사용 (Flask 개발 서버 대신)
- 리버스 프록시 설정 (Nginx)
- HTTPS 활성화
- 데이터베이스 백업 설정 (SQLite → 클라우드 스토리지)
- API 사용량 모니터링 (Gemini, OpenAI 할당량)
- 로깅 집계 설정 (예: Sentry)
- Redis 서버 (비동기 처리 시스템 도입 시)

---

## 문제 해결

### 1. ffmpeg 오류
```bash
# ffmpeg가 설치되어 있는지 확인
which ffmpeg  # Mac/Linux
where ffmpeg  # Windows

# 없으면 설치 필요
# Mac: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

### 2. DB 오류 (테이블 없음 등)
```bash
# Supabase: docs/database/supabase_schema.sql 을 Supabase SQL Editor에서 실행했는지 확인

# SQLite(DB_TYPE=sqlite) 사용 시: app.py 실행 시 자동 생성됨.
# 완전 재생성이 필요하면 DB 파일 삭제 후 재실행
rm database/minute_ai.db
python app.py
```

### 3. ChromaDB 오류
```bash
# ChromaDB 데이터베이스 초기화
rm -rf database/vector_db
python app.py  # 자동으로 재생성됨
```

### 4. Supabase 인증 오류
```bash
# .env의 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 설정 확인
# 프론트엔드 .env의 VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY 확인
# Supabase 대시보드 > Authentication > Providers에서 Google 로그인 활성화 여부 확인
```

### 5. 프론트엔드 빌드 오류
```bash
# node_modules 재설치
cd frontend
rm -rf node_modules package-lock.json
npm install

# Vite 캐시 삭제
rm -rf node_modules/.vite
```

### 6. 로컬 STT 오류
```bash
# Hugging Face 토큰 확인
echo $HF_TOKEN

# PyTorch 버전 확인 (2.3.1 권장)
python -c "import torch; print(torch.__version__)"

# pyannote.audio 버전 확인 (3.1.1 권장)
python -c "import pyannote.audio; print(pyannote.audio.__version__)"
```

---

## 향후 개선 사항

### 기술 개선
- **비동기 처리 시스템**: Redis Queue 기반 백그라운드 작업 처리 (Phase 1: 경량 비동기화 계획 중)
- 실시간 협업 (WebSocket)
- Celery 도입 (대규모 확장 시)
- Redis 세션 관리
- PostgreSQL 마이그레이션 (프로덕션)
- CDN 정적 자산 제공
- 다국어 UI (i18n)

### 기능 추가
- PDF/DOCX 내보내기
- 공유 이메일 알림
- 편집 버전 히스토리
- 태그 기반 필터링
- 정렬 옵션 (최신순, 제목순, 날짜순)
- 감정 분석
- 주제 모델링
- 회의 템플릿

### AI 개선
- 도메인별 파인튜닝 모델
- 화자 식별 웨이크워드 감지
- 실시간 전사 (스트리밍 STT)
- 멀티모달 분석 (비디오 + 오디오)
- 로컬 STT GPU 최적화 (OpenVINO 메모리 최적화)

---

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

---

## 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [Flask](https://flask.palletsprojects.com/)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)
- [WaveSurfer.js](https://wavesurfer-js.org/)

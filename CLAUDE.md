# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Genminute — AI 기반 회의록 자동 생성 플랫폼. 오디오/영상 업로드(또는 실시간 녹음) → STT + 화자 분리 → 요약 / 정식 회의록 / 마인드맵 생성 → RAG 챗봇 Q&A. Flask 백엔드 + React SPA 프론트엔드.

코드베이스는 한국어 중심입니다(docstring, 주석, 로그 메시지가 한글). 기존 파일을 수정할 때 이 관례를 따르세요.

## 명령어

백엔드 (repo 루트에서 실행):
```bash
python app.py                                # 개발 서버 (host 0.0.0.0, FLASK_PORT, 기본 5000)
python -m unittest tests.test_repositories   # Repository 테스트 실행
python -m unittest discover tests            # 전체 테스트 실행
gunicorn -c gunicorn_config.py wsgi:app      # 프로덕션
```
pytest 설정은 없습니다 — 테스트는 표준 라이브러리 `unittest` 러너를 사용합니다.

프론트엔드 (`frontend/`에서 실행):
```bash
npm install
npm run dev      # Vite 개발 서버 :5173 (백엔드로 프록시)
npm run build    # tsc -b && vite build → frontend/dist (프로덕션에서 Flask가 서빙)
npm run lint     # eslint
```

Flask는 빌드된 SPA를 `frontend/dist`에서 catch-all 라우트로 서빙합니다. 따라서 프로덕션과 유사하게 실행하려면 먼저 `npm run build`가 필요합니다. 프론트엔드 작업 중에는 `npm run dev`와 `python app.py`를 동시에 띄우세요.

## 아키텍처

### 레이어드 / 클린 아키텍처 (최근 리팩토링 — `docs/architecture/14_refactoring_plan.md` 참조)

의존성 흐름은 엄격하며 DI 기반입니다:

```
Route (Thin Controller: 입력 검증, Service 호출, 응답 변환만)
  → Service (비즈니스 로직; Repository *인터페이스*에 의존, 생성자 주입)
    → Repository 인터페이스 (ABC, database/repositories/interfaces.py)
      → Repository 구현체 (SQLite 또는 Supabase)
```

**모든 조립은 `app.py`의 "DI 조립" 섹션에서 일어납니다.** `get_db_manager()`가 DB별 Facade를 반환하며 `.meeting_repo`, `.minutes_repo`, `.mindmap_repo`, `.action_item_repo`, `.user_repo`, `.connection`을 노출합니다. Service는 이 repo들을 생성자로 주입받습니다. DB를 교체하거나 의존성을 재배선하려면 Service가 아니라 `app.py`를 수정하세요. Service는 어떤 구체 DB를 쓰는지 알아서는 안 됩니다.

Repository 메서드를 추가할 때: `interfaces.py`의 ABC에 먼저 추가한 뒤, `database/repositories/sqlite/`와 `database/repositories/supabase/` **양쪽 모두**에 구현하세요.

### DB 백엔드는 교체 가능 — 기본값은 SQLite

`config.DB_TYPE`(env `DB_TYPE`, **기본값 `sqlite`**)가 백엔드를 선택합니다. `database/__init__.py`의 `get_db_manager()`가 팩토리입니다: `supabase` → `SupabaseManager`, 그 외 → SQLite `DatabaseManager`. 일부 Service는 `DB_TYPE`에 따라 `app.py`에서 선택되는 병렬 구현을 가집니다(예: `AnalysisService` vs `SupabaseAnalysisService`, `UserService` vs `SupabaseUserService`).

Supabase 백엔드 코드는 유지되지만 현재 운영 DB는 아닙니다(계속 사용할지 미정, 2026-11 기준 Supabase 프로젝트 없음).

### 인증은 Firebase — DB와 독립

로그인은 `DB_TYPE`과 무관하게 Firebase Authentication을 사용합니다. 프론트엔드(`frontend/src/config/firebase.ts`)가 `/api/firebase-config`로 웹 설정을 받아 Google 팝업 로그인 후 ID 토큰을 `/api/login`에 보내고, 백엔드(`services/firebase_service.py`)가 Admin SDK로 검증해 Flask 세션을 만듭니다. 서비스 계정 키는 `config.FIREBASE_CREDENTIALS_PATH`(기본: 루트의 `firebase-adminsdk.json`, 커밋 금지)입니다.

코드와 README가 다르면 **코드를 신뢰**하세요. `requirements.txt`, `config.py`, `app.py`가 권위 있는 출처입니다.

### STT 엔진도 교체 가능

`config.STT_ENGINE`(env, 기본값 `local`):
- `local` — faster-whisper + pyannote.audio (GPU 권장, `HF_TOKEN` 필요, 무료)
- `gemini` — Gemini API STT + 화자 분리 (GPU 불필요, API 비용 발생)

`config.validate()`는 `STT_ENGINE=local`일 때만 `HF_TOKEN`을 필수로 요구합니다. 로컬 STT/화자 분리 파이프라인은 `services/diarization.py`에 있습니다.

### RAG / 벡터 레이어

ChromaDB(`database/vector_manager.py`, `database/vector_db/`에 영구 저장)가 두 컬렉션을 보관합니다: `meeting_chunks`(스마트 청킹된 전사 텍스트)와 `meeting_subtopic`(주제별 요약), 둘 다 OpenAI 임베딩. `vdb_manager`는 관계형 `db_manager`를 `app.py`에서 주입받습니다. 챗봇 쿼리는 두 컬렉션을 벡터 검색하고, 사용자가 접근 가능한 meeting ID로 필터링한 뒤 Gemini로 답변을 생성합니다. 청킹/검색 파라미터는 `config.py`의 상수입니다(`CHUNK_SIZE`, `TIME_GAP_THRESHOLD_SECONDS`, `SEARCH_RESULTS_PER_COLLECTION`).

### 라우트

Blueprint는 `routes/__init__.py`의 `register_blueprints()`에서 등록됩니다. 회의 기능은 여러 Blueprint로 분리되어 있습니다(`meetings`, `meetings_share`, `meetings_upload`, `meetings_action_items`). 인증/인가는 `utils/decorators.py`의 데코레이터를 사용합니다: `@login_required`, `@admin_required`, `@api_error_handler`(에러 응답을 표준화 — 라우트마다 try/except 대신 이걸 사용). 관리자는 `ADMIN_EMAILS` env로 결정됩니다.

### 프론트엔드 현황

`frontend/`(React 19 + Vite + TS + Tailwind)가 실제 동작하는 SPA입니다. `templates/`(Jinja2)와 `static/`는 **레거시**입니다 — 여기에 기능을 추가하지 마세요.

### 장시간 업로드 처리

업로드/STT/요약은 SSE로 클라이언트에 스트리밍됩니다(`/upload` 흐름). 오디오/영상 파일은 `uploads/`에 `[uuid]_[name]` 형식으로 저장됩니다. ffmpeg(PATH에 있어야 함)가 오디오 추출/정규화 및 브라우저 WebM 녹음 변환을 담당합니다.

## 컨벤션 (`agent/rules/project-rules.md` 기준)

- **문서가 진실의 원천(Source of Truth).** 아키텍처 문서는 `docs/architecture/`에 있습니다.
- **작업 기록은 `/devlog`로만 (사용자가 수동 실행).** `docs/development/dev_log.md`(작업 기록)와 `docs/development/decision_log.md`(결정 카드)는 사용자가 `/devlog`를 실행했을 때만 `.claude/commands/devlog.md`의 절차대로 작성합니다. 그 외에는 이 두 파일에 직접 기록하지 마세요.
- **`/devlog` 알림.** 아래 상황이면 응답 맨 끝에 알림 두 줄을 덧붙이세요.

  첫 줄(상황에 맞는 것 하나):
  - 코드 변경이 포함된 작업을 마쳤을 때: `📝 기록할 변경이 있습니다.`
  - 둘 이상의 안 중에서 하나를 골랐을 때: `📝 결정이 있었습니다: <결정 한 줄>`
  - 사용자가 커밋하려 하거나 커밋 메시지를 요청했는데 기록 전일 때: `📝 커밋 전에 기록을 먼저 남기세요.`
  - 사용자가 세션을 마무리하려는데 기록 전일 때: `📝 아직 기록하지 않은 변경이 있습니다.`

  둘째 줄(항상 동일):
  `   실행: 입력창에 /devlog 입력 후 Enter (일부만 기록: /devlog <주제>) → 끝나면 decision_log.md의 "내 이유" 작성`

  질문 답변, 조사만 한 턴, 문서만 고친 턴에는 알리지 않습니다. 같은 변경에 대해서는 한 번만 알리고, `/devlog` 실행 후에는 새 변경이 생길 때까지 알리지 않습니다.
- **보수적으로** — 기존 동작을 깨지 말고, 갈아엎기보다 확장하세요.
- **철저한 분업화** — 파일을 작게 유지하고 책임별로 분리하세요(회의 라우트/repo가 분리된 이유).
- **타입 힌팅 필수** — Python 입출력에 타입 힌트를 강제하세요.
- **하드코딩 금지** — 설정값과 매직 넘버는 `config.py`로 분리하세요.
- **테스트 필수** — 자동화 테스트가 없는 코드는 '완료'가 아닙니다.
- 직설적이고 토큰 효율적으로. 반사적으로 동의하지 말고 기술적 사실로 반박하세요.
- 지시 없이 AI 도구 메모리 섹션(예: "Gemini Added Memories")을 수정하지 마세요.

## 환경 변수

설정은 `config.py`에 중앙화되어 있습니다(`.env` 로드); `.env.example` 참조. 필수 변수는 `DB_TYPE`/`STT_ENGINE`에 따라 달라지며 `config.validate()`가 이를 열거합니다(항상 필수: `FLASK_SECRET_KEY`, `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`; `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`는 `DB_TYPE=supabase`일 때만). 모든 영상/녹음 업로드에는 PATH에 ffmpeg가 필요합니다.

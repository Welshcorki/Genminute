# 리팩토링 이후 작업 계획 — 인계 문서

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-11-17 |
| 근거 | 2026-11-16 ~ 17 계획 검토 대화 (코드 변경 없음, 검토만 진행) |
| 기준 커밋 | `b88c8ff` — `main`, `cleanup`, `origin/main`, `origin/cleanup`이 모두 이 커밋 |
| 테스트 | `genminute_stt` 환경에서 전체 91건 통과 (2026-11-16 실행) |
| 작업 흐름 | 0~2단계(리팩토링)는 Claude Code 세션 "프로젝트 폴더 구조 리팩토링 계획"에서 진행 중이다. 이 문서의 계획 대화가 끝나면 그 세션으로 돌아가 이어 간다. 그 세션에서 파일을 옮기면 이 문서의 파일 링크·줄 번호도 함께 고친다 |

표기 규칙: 대화에서 실제로 확인하거나 결정한 내용만 적었다. 대화에서 다루지 않아 작성자가 채운 부분은 **(추정)** 으로 표시했다.

---

## 0. 한눈에 보기

| 순서 | 단계 | 상태 |
|---|---|---|
| 0 | 실제 업로드 1회 검증 | 계획 확정, **실행 주체 미정** |
| 1 | 업로드·회의록·챗봇 테스트 + 원본 파일 접근 제한 | 계획 확정 |
| 2 | 서비스 통합 | 계획 확정 (Supabase 코드 삭제 + 서비스의 DB 호출을 repo로 이동, 2026-11-19) |
| 2-A | 저장소를 Firebase로 이전 | 방향 확정 (Firestore, `us-central1`) |
| 3 | 처리 비동기화 | 사용자 승인 |
| 4 | 파일 처리 정리 | 방향 확정, 세부 2건 미정 |
| 5 | 참석자 입력·자동 공유 | 1단계 범위 확정, 2단계 미정 |
| 6 | 화자 이름 지정 | 사용자 승인 (신규) |
| 7 | 회의록 템플릿 개선 | 사용자 승인 (AI 파이프라인 수정 예외) |
| 7-B | 자체 캘린더 → 간트 차트 | 순서 확정 |
| 8 | 배포 + HTTPS | 방식 확정 (Firestore + Hosting + Cloud Run, `us-central1`), 세부 절차는 제안 |
| 9 | 관리자 페이지 React 재구현 → 레거시 철거 → 프론트 정리 → 문서 | 기존 합의 유지 |
| 보류 | PWA, 네이티브 앱 | 정식 서비스 배포 시점에 재검토 |

0~2단계가 리팩토링의 남은 부분이고, 3단계부터가 "리팩토링 이후" 작업이다.

---

## 1. 확정된 계획

### 0단계 — 실제 업로드 1회 검증

- **목적**: 구조를 손대기 전에 "정상 동작 기준"을 확보한다. 패키지 업그레이드 이후 실제 업로드를 한 번도 돌리지 않았다.
- **범위**
  - `STT_ENGINE=gemini`로 먼저, 그다음 `local`로 업로드 1회씩.
  - 업로드 → STT → 검색용 저장 → 할 일 추출 → 요약 → 마인드맵 → 회의록 생성 → 챗봇 질의까지 확인.
  - 회의록 템플릿 문제 중 코드로만 판단한 4건을 실제 결과로 확인한다(7단계 참조): 화자 정보 누락, 지시 충돌, 중괄호·안내문 잔존, 긴 회의 실패.
- **0-0 사전 준비 (2026-11-17 추가)** — 현재 상태로는 Gemini 단계가 전부 실패한다.
  - `.env`의 `GOOGLE_API_KEY`가 무효다(Google이 "API key not valid"로 거절). 결제 연결된 프로젝트에서 새 키를 발급해 교체한다(사용자 작업).
  - 코드 기본값 `gemini-3-flash`는 공식 문서에 없는 모델명이다. `GEMINI_MODEL`을 실제 모델명으로 지정한다(후보: `gemini-3.8-flash`, `gemini-3.6-flash` — 가격 동일).
  - 캘린더 자동 등록을 끈다(사용자 결정). 할 일은 앱 DB에만 저장한다. **(추정)** `config.py`에 설정값을 두고 [tools/google_calendar_tool.py](../../tools/google_calendar_tool.py)에서 API 호출을 건너뛰면 `agent_service.py`를 건드리지 않고 끌 수 있다. 다시 켤지는 자체 캘린더 안이 확정된 뒤 논의한다.
  - **키 교체 후 재확인 (2026-11-17)**: 사용자가 `GOOGLE_API_KEY` 값을 교체했고(프로젝트 `genminute-492814`에서 가져온 키, 변수 이름은 그대로) 모델 목록 조회가 성공했다. `gemini-3-flash`는 404(없는 모델)로 확정. 목록에 `gemini-3.6-flash`, `gemini-3.8-flash`, `gemini-3.5-transcribe`, `gemini-embedding-2`가 있다. `gemini-3.5-transcribe`는 목록상 `generateContent`를 지원한다고 나온다(공식 문서의 "Interactions API" 설명과 다름). 글자 한 단어짜리 `generateContent` 호출은 `gemini-3.5-transcribe`에서 성공했다(음성 호출은 미확인). `gemini-3.6-flash`와 `gemini-3.8-flash`는 4회씩 모두 503("high demand", 일시 혼잡)이라 **호출 성공을 아직 확인하지 못했다** — 키·결제 오류(400/403)는 아니다. 0단계 전에 재시도 필요.
  - **2026-11-19 재확인**: 3.6·3.8 flash와 `gemini-4-hydrogen`은 계속 503, `gemini-4-neon`(11-18 GA, 유료 $3.00/$15.00)은 429 "quota 초과, 요금제·결제를 확인하라". 공식 문서상 3.6·3.8 flash는 둘 다 Stable·종료일 미정이고 API 목록에도 남아 있다(AI Studio 화면에서만 3.6이 빠짐). 11-17~19 공식 변경 기록에 모델 삭제·이름 변경은 없다. **(추정)** 이 키가 무료 등급이라 혼잡 시 503, 무료 한도가 없는 모델은 429가 난다. 사용자가 AI Studio에서 키 등급(유료/Tier 1)과 결제 연결을 확인해야 한다.
  - `gemini-3.5-transcribe` 가격은 바뀌지 않았다. 공식 가격 페이지가 "입력 $2.00 또는 분당 $0.003 / 출력 $12.00 또는 분당 $0.002"로 두 단위를 함께 적는다(합계 분당 약 $0.005). 호출 방식은 공식 가이드 기준 Interactions API(`client.interactions.create`, REST `/v1beta/interactions`)다.
  - **결제(유료 등급) 전환**: 결제 수단은 한 곳(Cloud Billing 계정)만 연결하면 된다. AI Studio의 API 키 화면 "Billing Tier" 칸의 "Set up billing"에서 결제 계정을 만들거나 고르고 선불(최소 $5) 또는 후불을 선택한다. 결제 계정이 연결된 프로젝트는 그 계정의 등급을 물려받는다. 같은 프로젝트라 Firebase도 Blaze로 바뀐다. Tier 1 지출 상한 $250, 10분 누적 지출 $10 초과 시 429. 선불 잔액이 0이면 402.
  - **비용 상한 (2026-11-20 정리)**: 2026-11-20 기준 GCP·AI Studio·Firebase 모두 결제 미연결(사용자 확인). Gemini API는 선불을 고르면 충전액 이상 나가지 않는다. GCP 예산은 알림만 하고 사용을 막지 않는다. Cloud Run·Firestore·Storage에는 자동 상한이 없으므로 8단계 배포 때 Cloud Run 최대 인스턴스 수 제한과 예산 알림을 함께 설정한다. API 키는 서버에서만 쓰고 Generative Language API 전용으로 제한한다 **(추정: 키 유출이 비용 폭주의 주된 경로)**.
  - 설치된 `google-genai` 1.52.0에는 `client.interactions`가 없어, Interactions 방식이 필요하면 복제 환경에서 SDK를 올려야 한다.
- **비교 테스트 (2026-11-17 추가, 사용자 승인)** — 같은 녹음 파일로 실행하고 API 응답의 토큰 사용량을 함께 기록한다.
  - 범위(사용자 확정 2026-11-17): 우선 30분 이내 파일로만 비교한다. 30분 초과 처리(잘라 보내기)는 전용 전사 모델 채택이 정해진 뒤, 기존 파일을 ffmpeg로 이어 붙인 합성 파일로 확인한다(30분 넘는 실제 녹음 없음).
  - 테스트 파일(사용자 지정): `uploads/1차회의_stt선정_251105_160414.m4a` — 4분 36초, 4.3MB, 모노 AAC. 4인, 소규모 회의실에서 스마트폰 녹음. 길이가 짧아 "긴 회의 실패"와 전용 전사 모델의 30분 제한은 이 파일로 확인할 수 없다(긴 파일 별도 필요).
  - 요약의 `[cite: N]` 인용이 실제로 의미가 있는지 확인한다. 코드상으로는 전사문이 번호·화자·시각 없이 한 덩어리로 전달되어([services/upload_service.py:310](../../services/upload_service.py#L310)) AI가 인용할 번호가 없고, 화면([SummaryView.tsx](../../frontend/src/components/SummaryView.tsx))에도 인용을 처리하는 코드가 없다. 프롬프트의 `[cite_start]`([services/stt_service.py:246](../../services/stt_service.py#L246))는 의미 없는 문자열이다. 둘 다 수정 금지 영역이라 고치려면 승인이 필요하다.
  - 전사 3종: 로컬(faster-whisper + pyannote) / Gemini flash 전사(현재 방식) / `gemini-3.5-transcribe`(전용 모델, 사용 승인됨). 화자 구분 정확도, 오인식, 소요 시간, 비용을 비교한다. 전용 모델은 화자 분리 시 요청당 30분 제한, 3인 이상 화자 분리 "실험적", 별도 API(Interactions) 사용이라는 제약이 있다.
  - 전사 외 3종 (2026-11-19 `gemini-4-hydrogen` 추가, 사용자 결정): `gemini-3.6-flash` / `gemini-3.8-flash` / `gemini-4-hydrogen`. 같은 전사문으로 요약·회의록·할 일 추출을 만들어 품질, 토큰 사용량(생각 토큰 포함), 소요 시간을 비교한다. 공식 문서에 세 모델의 벤치마크 수치는 없다(설명 문구만 있음: 3.6 "더 빠르고 저렴", 3.8 "가장 똑똑한 Flash", hydrogen "일상 코딩·에이전트 작업의 속도와 효율").
  - **예상 비용 (2026-11-19 공식 가격 기준, 사용량은 추정)** — 10분 4인 회의 1건 + 챗봇 5문항. 전사 외: 입력 26,300 / 출력 3,600 토큰(이전 추정값). Flash 전사: 음성 19,200(분당 1,920) + 지시문 500 입력, 출력 약 4,000 **(추정)**. 생각 토큰 미포함이라 실제는 더 나올 수 있다.

    | 조합 (전사 + 전사 외) | 2026년 | 2027년부터 |
    |---|---|---|
    | 로컬 STT + 3.6/3.8 flash | $0.033 | $0.066 |
    | 3.6/3.8 flash 전사 + 3.6/3.8 flash | $0.063 | $0.126 |
    | `gemini-3.5-transcribe` + 3.6/3.8 flash | $0.083 | $0.116 |
    | `gemini-3.5-transcribe` + `gemini-4-hydrogen` | $0.117 | $0.117 |
    | hydrogen 전사 + hydrogen | $0.126 | $0.126 |

    - 3.6과 3.8은 가격이 같다. 2027-01-01부터 두 모델 가격이 두 배가 되어 `gemini-4-hydrogen`과 같아진다($1.50/$7.50).
    - `gemini-4-neon`($3.00/$15.00)은 무료 등급이 없고 hydrogen의 두 배라 후보에서 뺐다.
- **건드릴 파일**: 비교용 스크립트 외에는 없음(검증만). `gemini-3.5-transcribe`를 정식 엔진으로 넣는 작업은 비교 결과로 채택이 정해진 뒤 별도로 한다. 로컬 STT가 정상이면 [app.py:20-23](../../app.py#L20-L23)의 주석 처리된 `diarization_service` import를 삭제한다.
- **주의**: Gemini·OpenAI 비용이 소액 발생하고, 할 일 추출 에이전트가 캘린더에 일정을 등록할 수 있다. `local`이 깨져 있으면 그 수리가 최우선이 된다.

### 1단계 — 테스트 보강 + 원본 파일 접근 제한

- **테스트**: `/upload`(SSE), `/api/generate_minutes`, `/api/chat`의 스모크 테스트. LLM과 STT는 가짜로 대체한다. 현재 91건은 조회·수정·삭제·공유·인증 위주라 이 경로가 비어 있다.
- **접근 제한**: `/uploads/<파일명>`에 로그인 확인이 없다([app.py:106](../../app.py#L106)). 요청이 오면 로그인 확인 → 파일이 속한 회의 찾기 → `can_access_meeting`([services/user_service.py:111](../../services/user_service.py#L111))으로 소유자·공유받은 사람·관리자만 통과시킨다.
- **건드릴 파일**
  - [app.py](../../app.py) — `uploaded_file` 라우트
  - [tests/](../../tests/) — 신규 테스트 파일, 기존 [tests/app_harness.py](../../tests/app_harness.py) 재사용
  - **(추정)** 파일명으로 회의를 찾는 조회는 [database/repositories/sqlite/meeting_repo.py](../../database/repositories/sqlite/meeting_repo.py)의 기존 `audio_file` 조건을 쓰거나 메서드를 추가한다. 추가한다면 인터페이스와 Supabase 구현에도 넣어야 한다.

### 2단계 — 서비스 통합

- **범위**
  - DI를 [app.py](../../app.py) 한 곳으로 모은다. 지금은 [app.py:56-68](../../app.py#L56-L68)에서 만든 서비스 3개를 아무도 쓰지 않고, [routes/meetings.py:30](../../routes/meetings.py#L30)이 서비스를 따로 만든다.
  - `get_db_manager()`를 직접 부르는 곳을 주입 방식으로 바꾼다.
  - ~~`UserService`/`SupabaseUserService`, `AnalysisService`/`SupabaseAnalysisService` 2벌을 하나로 합친다.~~ → **Supabase 코드 삭제로 대체 (사용자 승인 2026-11-19: "다시 필요해지면 그때 설정에 맞춰 다시 짠다")**. 계획 세션은 코드 수정 금지라 리팩토링 세션에서 실행한다. 삭제 범위(2026-11-19 grep 기준, 22개 파일에서 125곳 언급):
    - 파일 통째로 삭제: [database/repositories/supabase/](../../database/repositories/supabase/) 전체, [database/supabase_manager.py](../../database/supabase_manager.py), [services/supabase_user_service.py](../../services/supabase_user_service.py), [services/supabase_analysis_service.py](../../services/supabase_analysis_service.py), [tests/test_supabase_meeting_repo.py](../../tests/test_supabase_meeting_repo.py)
    - 분기 제거: [app.py:61-65](../../app.py#L61-L65), [database/__init__.py:24-27](../../database/__init__.py#L24-L27), [services/user_service.py:403-405](../../services/user_service.py#L403-L405), [services/analysis_service.py:73-75](../../services/analysis_service.py#L73-L75)
    - 설정: [config.py](../../config.py)의 `SUPABASE_*` 3개, `validate()`·출력의 supabase 분기, `DB_TYPE` 주석. `.env.example`의 Supabase 항목. `requirements.txt`의 `supabase`
    - 테스트: [tests/test_auth.py:172-186](../../tests/test_auth.py#L172-L186)의 supabase 필수 변수 테스트 2건 삭제·수정
    - 주석 정정: [routes/google_auth.py](../../routes/google_auth.py)의 "Supabase Auth로 전환" 주석 4곳(실제 로그인은 Firebase)
    - 문서: `CLAUDE.md`, `README.md`의 Supabase 설명(9단계 문서 정리 때 함께)
    - `DB_TYPE` 설정 자체는 남긴다. Firestore 구현이 들어오면 `sqlite`/`firestore` 선택에 다시 쓴다.
  - **서비스 안의 DB 호출을 repo로 옮기기 (사용자 확정 2026-11-19, 2026-11-17 제안)**: 배포 DB가 Firestore로 정해져 Supabase 서비스를 합치는 작업은 의미가 없어졌다. 대신 서비스 안의 SQL을 repo로 옮긴다. 현재 [services/user_service.py](../../services/user_service.py)에 DB 직접 호출이 36곳, [services/analysis_service.py](../../services/analysis_service.py)에 4곳 있고, `UserRepositoryInterface`에는 메서드가 2개뿐이다(사용자 조회·생성·공유·권한 확인이 인터페이스 밖에 있음). 이것을 인터페이스로 올려야 Firestore 구현을 하나만 더 쓰면 되고, 그렇지 않으면 `FirestoreUserService`라는 3번째 복제본이 생긴다.
  - 기존 합의에 있던 Facade 위임 정리, repo ↔ `vdb_manager` 순환 참조 해소.
- **건드릴 파일**
  - 라우트: [routes/admin.py](../../routes/admin.py), [routes/google_auth.py](../../routes/google_auth.py), [routes/meetings.py](../../routes/meetings.py), [routes/meetings_action_items.py](../../routes/meetings_action_items.py), [routes/summary.py](../../routes/summary.py), [routes/chat.py](../../routes/chat.py)
  - 서비스: [services/upload_service.py](../../services/upload_service.py), [services/user_service.py](../../services/user_service.py), [services/analysis_service.py](../../services/analysis_service.py), `services/supabase_*_service.py`
  - 기타: [tools/google_calendar_tool.py](../../tools/google_calendar_tool.py), [database/repositories/](../../database/repositories/)

### 3단계 — 처리 비동기화 (사용자 승인)

- **문제**: 업로드부터 요약까지가 하나의 긴 연결(SSE)로 묶여 있다([routes/meetings_upload.py:36](../../routes/meetings_upload.py#L36)). 탭을 닫거나 모바일에서 앱을 내려 연결이 끊기면 서버는 진행 중이던 단계만 마치고 나머지를 중단한다.
- **범위**
  1. 업로드가 끝나면 서버가 바로 "접수됨"으로 응답한다.
  2. 서버가 혼자 STT → 요약 → 마인드맵을 진행하고 진행 상태를 DB에 기록한다.
  3. 화면은 열려 있을 때만 진행 상태를 조회한다. 닫았다 열어도 이어서 보인다.
- **동시 처리 규칙**: STT는 한 줄 대기열(한 번에 하나). STT 이후의 세 갈래(검색용 저장, 할 일 추출, 요약→마인드맵)는 동시에 실행한다.
- **구현 방식**: 서버 안의 작업 스레드 + 상태 테이블. Redis·Celery는 쓰지 않는다.
- **건드릴 파일**
  - [routes/meetings_upload.py](../../routes/meetings_upload.py), [services/upload_service.py](../../services/upload_service.py)
  - **(추정)** 상태 테이블 추가: [database/repositories/sqlite/connection.py](../../database/repositories/sqlite/connection.py)와 인터페이스·양쪽 구현체
  - **(추정)** 화면: [frontend/src/services/upload.ts](../../frontend/src/services/upload.ts), [frontend/src/contexts/UploadContext.tsx](../../frontend/src/contexts/UploadContext.tsx), [frontend/src/components/UploadStatusBar.tsx](../../frontend/src/components/UploadStatusBar.tsx)
- **주의**
  - `STTManager`, `AgentService`가 여러 스레드에서 동시에 불려도 안전한지는 확인하지 않았다.
  - 완료 푸시 알림은 PWA와 함께 논의했던 항목이라 PWA 보류와 함께 빠졌다 **(추정 — 명시적으로 뺀다고 결정하지는 않음)**.
  - 배포가 Cloud Run으로 정해지면 응답 후 CPU가 멈추는 기본 동작 때문에 추가 설정이나 별도 작업 서비스가 필요하다.

### 4단계 — 파일 처리 정리

- **형식 추가**: `3gp`, `amr`, `aac`, `ogg`, `opus`. 현재 허용은 wav, mp3, m4a, flac, mp4, webm, 한도 500MB([config.py:81](../../config.py#L81)).
- **보관 규칙 (사용자 확인: 읽을 수 있는 형식은 그대로, 못 읽는 형식만 변환)**

  | 형식 | 보관 방식 |
  |---|---|
  | mp3, m4a, wav, flac, aac, mp4 | 그대로 |
  | webm (브라우저 녹음) | 재포장만(`ffmpeg -c copy`) — 길이 정보만 추가 |
  | amr, 3gp | m4a로 변환 후 원본 삭제 |
  | ogg, opus | 변환 권고(구형 아이폰 재생 불가 가능성) — **사용자 답 대기** |

  - "읽는 쪽"은 브라우저(재생) 기준이다. STT용으로는 처리 중에만 쓰는 임시 wav 사본을 만들고 끝나면 지운다.
- **같이 고칠 것**
  - 화면과 서버의 허용 목록 불일치: 화면은 `ogg` 허용·`flac` 차단, 서버는 반대([UploadModal.tsx:20](../../frontend/src/components/UploadModal.tsx#L20)). 서버 목록 하나로 통일한다.
  - 영상 여부를 확장자로만 판단한다([services/upload_service.py:97](../../services/upload_service.py#L97)). `3gp`는 영상일 수도 있어 파일 내용을 확인하도록 바꾼다.
  - Gemini STT의 형식 표에 wav, mp3, m4a, flac만 있고 나머지는 wav로 표시해 보낸다([services/stt_service.py:119](../../services/stt_service.py#L119)). **이 파일은 수정 승인 범위 밖이므로**, STT 호출 전에 `upload_service`에서 wav로 변환해 넘기는 방식으로 해결한다.
- **기기 저장 버튼**: 녹음 직후와 노트 상세 화면에 "내 기기에 저장". 녹음 화면은 녹음 데이터를 이미 브라우저에 들고 있다([Recorder.tsx:384](../../frontend/src/pages/Recorder.tsx#L384)).
- **서버 보관 기간**: `config.py` 설정값. 기간이 지나면 원본만 삭제하고 전사·요약·회의록은 유지한다. 삭제된 회의는 재생 버튼 대신 "원본이 삭제되었습니다"를 보여 준다. **기간은 기본 14일, 회의별 "원본 지금 삭제" 버튼을 함께 둔다(사용자 확정 2026-11-17).**
- **모바일 업로드 안내**: 모바일에서 녹음 화면에 들어오면 "기본 녹음 앱으로 녹음한 뒤 업로드하세요" 안내와 업로드 버튼을 보여 준다.
- **건드릴 파일**: [config.py](../../config.py), [services/upload_service.py](../../services/upload_service.py)(`save_uploaded_file`, `convert_webm_to_compatible_format`), [frontend/src/components/UploadModal.tsx](../../frontend/src/components/UploadModal.tsx), [frontend/src/pages/Recorder.tsx](../../frontend/src/pages/Recorder.tsx), [frontend/src/pages/NoteDetail.tsx](../../frontend/src/pages/NoteDetail.tsx)
- **참고**: 기기 저장 버튼과 보관 기간은 작성자가 권고해 계획표에 넣었고 사용자가 반대하지 않았다. 사용자가 밝힌 목적은 "서버 용량과 프라이버시 둘 다"이다.

### 5단계 — 참석자 입력·자동 공유 (1단계 범위)

- **범위**
  - 업로드·녹음 화면에 참석자 이메일 칸을 추가한다.
  - 내 이메일은 로그인 정보로 자동 입력, 이전에 공유했던 사람은 자동완성으로 표시.
  - 회의록이 완성되면 입력된 사람들에게 자동 공유.
  - "대기 중 초대": 현재 공유는 상대가 한 번이라도 로그인한 사용자여야 한다(이메일로 등록 사용자를 찾는 방식). 처음 보는 이메일은 초대를 저장해 두었다가 그 사람이 처음 로그인할 때 연결한다.
- **건드릴 파일**
  - [frontend/src/components/UploadModal.tsx](../../frontend/src/components/UploadModal.tsx), [frontend/src/pages/Recorder.tsx](../../frontend/src/pages/Recorder.tsx)
  - [routes/meetings_share.py](../../routes/meetings_share.py), [services/user_service.py](../../services/user_service.py)(`share_meeting`)
  - **(추정)** 대기 중 초대 저장용 테이블 추가, 로그인 시 연결 처리는 [routes/auth.py](../../routes/auth.py)

- **동의·고지 3겹 (사용자 확정 2026-11-17)** — 공개 배포(8단계) 전에 필요하다.
  1. 첫 로그인 직후 동의 화면: 수집 항목, 원본 보관 14일, Google로의 전송, 삭제 방법을 고지하고 동의 시각·약관 버전을 저장한다. 별도 가입 페이지는 만들지 않는다.
  2. 업로드·녹음 시 확인 체크: "참석자에게 녹음과 AI 처리 사실을 알렸습니다."
  3. 참석자에게 공유될 때 안내 문구(자동 공유와 연결).
  - **(추정)** `users` 테이블에 동의 정보 칸 추가(인터페이스·양쪽 구현체), [routes/auth.py](../../routes/auth.py), 동의 화면·처리방침 페이지 신규. 문구의 법적 적정성은 전문가 확인이 필요하다.

### 6단계 — 화자 이름 지정 (사용자 승인, 신규)

- **범위**: "화자 1" 같은 번호에 이름을 붙이고 전사 화면과 회의록에 반영한다. 현재 이 기능은 없다.
- **건드릴 파일**: 설계를 논의하지 않았다. **(추정)** 회의별 "화자 번호 → 이름" 대응표를 저장하는 테이블과 API, [frontend/src/pages/NoteDetail.tsx](../../frontend/src/pages/NoteDetail.tsx)의 편집 UI.

### 7단계 — 회의록 템플릿 개선 (사용자 승인)

- **승인 범위**: 회의록 생성 프롬프트([services/stt_service.py](../../services/stt_service.py)의 `generate_minutes`)와 그 입력 부분. "AI 파이프라인 수정 금지" 원칙의 건별 예외다. STT, 화자 분리, 할 일 추출 에이전트는 계속 수정 금지.
- **진행 방식**: 수정 전후의 실제 생성 결과를 나란히 보여 주고 확인받는다.
- **고칠 것 (사용자가 수정 대상으로 지목)**
  - 중복 입력: "문단 요약" 자리에 요약이 아니라 검색용으로 잘라 둔 전사문이 들어간다([routes/summary.py:164](../../routes/summary.py#L164)). 같은 내용을 두 번 보내고, 이미 만든 요약은 쓰이지 않는다.
  - 충돌 지시: 템플릿은 "담당자: OOO, 기한: OOO"를 쓰라 하고 규칙은 "담당자를 제외하라"고 한다.
- **0단계 결과로 재확인 후 수정할 것 (코드로만 판단)**
  - AI에게 화자 정보가 가지 않는다. 전사문이 화자 표시 없이 한 덩어리로 전달된다([routes/summary.py:161](../../routes/summary.py#L161)).
  - 빈칸 표기 혼용(`{{회의명}}`과 `{첫 번째 핵심 주제}`)과 뜻이 모호한 마지막 규칙.
  - 긴 회의에 대한 길이 제한 처리 없음.
- **요약 인용을 실제 출처로 만들기 (사용자 승인 2026-11-17 — 요약 프롬프트 `subtopic_generate` 수정 승인 포함)**
  - 현재 `[cite: N]`은 동작하지 않는다. 전사문이 번호 없이 한 덩어리로 전달되어 AI가 번호를 지어내고, 화면도 인용을 해석하지 않는다.
  - 입력: [services/upload_service.py:310](../../services/upload_service.py#L310)에서 전사문을 `[1] 화자 1: 발언` 형식(번호는 1부터, 발언 순서)으로 만들어 보낸다.
  - 프롬프트: [services/stt_service.py:230-255](../../services/stt_service.py#L230-L255)의 입력 형식 설명·인용 규칙·예시를 새 입력 형식에 맞게 고치고 `[cite_start]`를 지운다.
  - **프롬프트 문안 (사용자 확정 2026-11-17 — 이 문안 그대로 적용)**
    - 입력 형식(230~231행): "입력 내용은 여러 화자가 참여하는 원본 대화입니다. 한 줄이 발언 하나이며 `[번호] 화자 N: 발언 내용` 형식입니다. 번호는 1부터 시작하는 발언 순번입니다."
    - 규칙 6(241행): "화자 및 군더더기 제거: `화자 N:` 표시와 '그러니까', '어,', '자,', '[웃음]' 등 군더더기는 요약문에 옮기지 않습니다. 대괄호 번호는 인용에만 사용합니다."
    - 규칙 9(244~247행) 전체 교체:
      - "모든 글머리 항목 끝에, 그 내용의 근거가 된 발언 번호를 `[cite: 번호]` 형식으로 붙입니다."
      - "번호는 입력의 대괄호 안에 있는 번호만 사용합니다. 입력에 없는 번호는 절대 쓰지 않습니다."
      - "여러 발언을 종합한 항목은 `[cite: 3, 4, 7]`처럼 나열합니다. 범위 표기(3-7)는 쓰지 않고, 가장 직접적인 발언 5개 이내로 고릅니다."
      - "근거 발언을 특정할 수 없는 내용은 요약에 쓰지 않습니다."
    - 출력 예시(250~255행)는 유지.
  - 코드 적용은 이 계획 세션에서 하지 않았다(코드 수정 금지 세션). 리팩토링 세션에서 7단계로 적용한다. 번호와 발언의 대응은 `segment_id` 순서에 의존하므로, 발언 삭제·병합 기능이 생기면 순번이 밀린다(현재 그런 기능이 있는지 미확인).
  - 검증: 생성 후 입력에 없는 번호는 서버에서 제거한다.
  - 화면: [frontend/src/components/SummaryView.tsx](../../frontend/src/components/SummaryView.tsx)에서 인용을 누르면 해당 발언으로 이동·재생한다.
  - 기존 요약은 번호가 지어낸 값이므로 재생성 전까지 인용을 숨긴다. 챗봇에 넘길 때는 인용 표시를 뺀다.
- **추가할 항목 (사용자 확정)**: 결정 사항, 참석자(실명 — 5·6단계 결과 사용), 미결 사항·다음 회의 안건.
- **추가하지 않는 항목 (사용자 확정)**: 안건(소제목으로 대체), 장소, 작성자.
- **화면**: 굵은 글씨(`**…**`)가 표시되지 않고 별표가 그대로 보인다([MinutesView.tsx:135](../../frontend/src/components/MinutesView.tsx#L135)).
- **부가 항목 3건 (사용자 확정 2026-11-17: 모두 7단계에 포함)**
  - 일시가 회의 시각이 아니라 업로드 시각이다([routes/meetings_upload.py:64](../../routes/meetings_upload.py#L64)).
  - 제목·날짜를 고쳐도 회의록 본문은 그대로다.
  - 회의록 안의 액션 아이템과 할 일 탭의 목록이 서로 다른 AI 호출로 만들어져 내용이 다를 수 있다. 일원화 방법은 아직 설계하지 않았다.

### 8단계 — 배포 + HTTPS

**방식 확정 (사용자 2026-11-20)**: Firestore + Firebase Hosting + Cloud Run, 모두 `us-central1`. 이 PC의 Docker Desktop은 GenMinute에 쓰지 않는다(사용자의 다른 개인 앱용). VM·Cloudflare Tunnel·Tailscale 안은 버림(3절).

**배포 방식 제안 (작성자 권고, 사용자 확인 전)**

- **이미지**: 저장소 루트에 `Dockerfile`을 둔다. 서버용 패키지 목록(PyTorch·로컬 STT 제외, 1절 C)과 ffmpeg를 이미지에 포함한다. 로컬에 Docker가 없어도 `gcloud run deploy --source .`가 Cloud Build로 이미지를 만들어 Artifact Registry에 올린다.
- **배포 순서**: 처음에는 PC에서 명령으로 수동 배포. 테스트가 안정되면 GitHub Actions로 `main` 머지 시 자동 배포(키 파일 대신 Workload Identity 연동 권장).
- **화면**: `npm run build` → `firebase deploy --only hosting`. `firebase.json`에서 `/api/**`(및 업로드·로그인 경로)를 Cloud Run 서비스로 넘긴다. Flask의 화면 서빙([app.py:161-165](../../app.py#L161-L165))은 로컬 개발용으로 남긴다.
- **비밀값**: `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `FLASK_SECRET_KEY`는 Secret Manager에 넣고 Cloud Run 환경변수로 연결한다.
- **Firebase 관리자 인증 (ADC 확정)**: 지금은 키 파일만 읽는다([services/firebase_service.py:34-44](../../services/firebase_service.py#L34-L44)). Cloud Run에서는 ADC(Application Default Credentials)로 초기화하도록 바꾸면 `firebase-adminsdk.json`을 서버에 올리지 않아도 된다(코드 수정 필요: 키 파일이 있으면 기존대로, 없으면 ADC + `FIREBASE_PROJECT_ID` 명시).
  - 비용: IAM은 공식 문서상 "All use of Identity and Access Management API is free of charge." ID 토큰 검증도 공개키로 로컬에서 처리되어 별도 과금이 없다. ADC로 바꿔도 비용은 달라지지 않는다.
  - Cloud Run 기본 서비스 계정은 프로젝트 편집자(Editor) 권한을 받을 수 있어, 공식 문서도 전용 서비스 계정을 권장한다. GenMinute 전용 서비스 계정에 필요한 권한만 준다.
  - `.dockerignore`를 반드시 만든다. `firebase-adminsdk.json`, `.env`가 이미지에 들어가지 않게 한다(`.gitignore`에만 들어 있고 `.dockerignore`는 아직 없음, 2026-11-20 확인).
  - **확정 (사용자 2026-11-20, 2절 17번)**: ADC + GenMinute 전용 서비스 계정. 키 파일을 Secret Manager에 넣는 안은 버림(3절).
- **Cloud Run 설정**: 최소 인스턴스 0, 최대 인스턴스 2~3(비용 상한), 메모리는 0단계 실측 후 결정. 응답 후 처리 방식에 따라 과금 방식이 정해진다(3단계 설계와 연동).
- **되돌리기**: 별도 테스트 환경 대신 Cloud Run 리비전(트래픽 없이 배포 후 태그 주소로 확인 → 전환)과 Hosting 미리보기 채널을 쓴다.
- **주의**: Hosting을 거치는 요청은 60초 제한이 있다. 3단계(비동기화) 전에는 업로드 SSE가 Hosting 경로에서 끊긴다.

어느 방식이든 공통으로 필요한 것:

- **`.dockerignore` 작성 (필수, 사용자 확정 2026-11-20)**: `.env`, `firebase-adminsdk.json`, `uploads/`, `database/vector_db/`, `*.db`, `frontend/node_modules/`, `.git/`을 이미지에서 뺀다.

- 세션 쿠키를 HTTPS 전용으로 설정.
- `ALLOWED_ORIGINS`, Firebase 승인 도메인, 캘린더 리다이렉트 주소에 새 주소 추가(뒤 둘은 사용자가 콘솔에서 작업).
- **공개 전 필수**: 1단계의 원본 접근 제한 완료, 비로그인 접근 허용 설정(`ENABLE_PUBLIC_ACCESS = true`, [frontend/src/App.tsx](../../frontend/src/App.tsx)) 정리.

### 9단계 — 관리자 페이지·레거시·문서

기존 합의 그대로다. 관리자 페이지를 React로 재구현 → `templates/`·`static/` 철거 → 프론트 정리 → 문서 정정. 문서는 구조가 확정된 뒤 한 번에 고친다. [CLAUDE.md](../../CLAUDE.md)의 규칙 파일 경로(`.cursor/rules/`)가 실제 위치([agent/rules/project-rules.md](../../agent/rules/project-rules.md))와 다른 것도 이때 고친다.

### 추가 단계 (2026-11-17 확정, 위치는 2026-11-19 확정)

**A. 저장소를 Firebase로 이전 — 2단계 직후 (사용자 결정: Firestore, 리전 `us-central1`)**

- 위치 이유: 3단계(비동기화)와 4단계(파일 처리)는 저장 방식에 따라 구현이 달라진다. 먼저 옮겨야 재작업이 없다.

- 대상: SQLite → Firestore, ChromaDB → Firestore 벡터 검색, `uploads/` → Cloud Storage for Firebase(브라우저 직접 업로드), 화면 서빙 → Firebase Hosting(선택). 서버는 Cloud Run `us-central1`.
- 결제: Firebase Blaze = GCP 결제 계정 연결이다. Cloud Run·Storage·Firestore·Gemini API가 같은 결제 계정의 청구서 한 장에 서비스별 항목으로 나온다. OpenAI만 별도 결제다(임베딩 교체 전까지).
- Firestore 위치는 만든 뒤 바꿀 수 없다. Cloud Run과 같은 `us-central1`로 만든다.
- 구현 방식: 기존 repo 인터페이스의 3번째 구현체(`database/repositories/firestore/`)로 추가한다. 로컬 개발·테스트는 SQLite를 계속 쓴다.
- **이전하면서 함께 손볼 기존 DB 문제 (코드로 확인, [connection.py](../../database/repositories/sqlite/connection.py))**
  1. `meetings` 테이블이 없다. 제목·날짜·파일명·소유자가 `meeting_dialogues`의 발언 행마다 반복 저장된다. 처리 상태(3단계), 원본 삭제 예정일(4단계), 참석자(5단계), 프로젝트 묶음(간트)을 둘 자리가 없다 → 회의 1건 = 문서 1개(`meetings/{id}`) + 발언 하위 목록으로 분리.
  2. 주제별 요약이 벡터 DB에만 있다. 벡터 DB를 다시 만들면 요약이 사라진다 → 요약 원문을 회의 문서에 저장.
  3. ID가 정수 자동 증가다(`users.id`, 할 일 `id`, 곳곳의 `owner_id: int`). Firestore에는 자동 증가가 없다 → 사용자 ID는 Firebase UID, 할 일 ID는 문자열. 인터페이스 타입, 세션, `/api/action_items/<int:item_id>/status` 경로가 영향을 받는다.
  4. Google 캘린더 인증 정보(재발급 토큰 포함)가 `users`에 평문으로 저장된다 → 암호화하거나 자체 캘린더 전환 시 제거.
  5. `meeting_action_items`에 소유자·담당자·외래키가 없다(캘린더/간트 단계에서 필드 추가).
  6. 관리자 계정을 `google_id = admin_<이메일>`이라는 가짜 값으로 미리 만든다. 실제 로그인 시 이 행과 합쳐지는지 확인 필요.
  7. repo의 제목·날짜 수정이 벡터 DB까지 직접 고친다(2단계의 순환 참조 해소 항목과 같은 문제).
- 미확인: Firestore 벡터 검색에서 "접근 가능한 회의 ID 목록"으로 걸러 내는 방식. `in` 조건은 값 개수 제한이 있는 것으로 알고 있어(공식 문서 미확인), 회의가 많은 사용자는 다른 필터 설계가 필요할 수 있다.
- Supabase 코드: 2단계에서 삭제(사용자 승인 2026-11-19).

**B. 캘린더 → 간트 — 7단계 직후 (사용자 확정: 이 순서로 진행)**

- 먼저 자체 캘린더(대시보드에서 한눈에 보기), 그다음 간트 차트. 간트 테스트 자료는 `uploads/`의 1~4차 회의 m4a. 네 파일의 녹음일이 모두 2025-11-05라 회의 날짜를 직접 지정해야 한다(7단계 "일시 = 업로드 시각" 수정과 연결).

**C. 서버용 패키지 정리 (2026-11-17 조사, 설치 환경 `genminute_stt` 기준)**

- 코드에서 직접 쓰지 않고 다른 필수 패키지도 요구하지 않음 → 삭제 후보: `graphviz`, `pydot`, `pandas`, `langchain`(묶음 패키지), `langchain-community`.
  - 주의: `langchain-community`는 `self_query` 검색 방식이 내부에서 불러 쓴다(설치된 `langchain_classic/retrievers/self_query/base.py`에서 확인). 챗봇은 `similarity`만 쓰고([routes/chat.py:18](../../routes/chat.py#L18)) `self_query`는 관리자 디버그 경로([routes/admin.py:52](../../routes/admin.py#L52))에서만 선택 가능하다. `self_query` 경로와 `ChatOpenAI`([database/vector_manager.py:48](../../database/vector_manager.py#L48))를 함께 지우면 `langchain-classic`·`langchain-community`가 같이 빠진다.
- 직접 쓰지 않지만 다른 패키지가 자동으로 설치함 → 목록에서 줄만 지워도 설치 결과는 같음: `SQLAlchemy`, `bcrypt`, `PyJWT`, `openai`, `tiktoken`, `requests`, `requests-oauthlib`, `urllib3`, `certifi`, `pytz`, `python-dateutil`, `pydantic-settings`, `PyYAML`, `google-auth-httplib2`, `torchaudio`. 버전 상한을 일부러 건 것이 있는지 확인 후 정리.
- 유지: `cryptography`(Firebase 토큰 검증이 내부에서 사용), `gunicorn`(실행 명령으로 사용).
- 서버(Gemini STT)에서는 `torch`, `torchaudio`, `faster-whisper`, `pyannote.audio`, `huggingface_hub` 고정도 제외 가능 → 서버용 목록을 별도 파일로 분리. Firestore 전환 후에는 `chromadb`, `langchain-chroma`, `supabase`도 서버에서 빠진다.
- 발견: `requirements.txt`는 `huggingface_hub<0.20`인데 실제 환경에는 1.7.1이 설치되어 있다(4절의 "화자 분리 실패 가능성"과 같은 문제).
- 검증 방법: 복제한 가상환경에서 하나씩 빼고 전체 테스트 + 앱 기동 확인.

### 작업 원칙

- AI 파이프라인(`stt_service`, `diarization`, `agent_service`)은 수정 금지. 사용자가 건별로 승인하면 그 범위에 한해 수정할 수 있고, 범위 밖에서 고칠 것이 보이면 보고 후 승인을 받는다.
- 파괴적 작업은 보고 → 승인 후 실행. 각 단계는 별도 커밋.
- 전체 테스트는 `C:\Users\butte\miniconda3\envs\genminute_stt\python.exe -m unittest discover tests`. 기본 `python`에서는 의존성 부족으로 대부분 건너뛴다.

---

## 2. 아직 결정하지 못한 것

| # | 항목 | 선택지 | 비고 |
|---|---|---|---|
| 1 | ~~배포 방식~~ | **확정: Firestore + Firebase Hosting + Cloud Run, 모두 `us-central1`** (2026-11-20). 아래는 당시 선택지 | (가) GCP 가상 서버(VM) + Caddy + 도메인 — 코드 변경 거의 없음, 월 약 2~3만원 고정비 / (나) Cloud Run — HTTPS 자동·거의 무료, 대신 저장 3종 이전과 업로드 방식 변경 필요 / (다) 이 PC + Cloudflare Tunnel — 무료 + 도메인 비용, Windows용 실행기(`waitress`)로 교체 필요 | 작성자 권고는 "지금은 VM, Cloud Run은 정리 후". 사용자는 "생각해 보겠다"고 함. 8단계 전까지만 정하면 된다 |
| 2 | ~~Supabase 코드 삭제~~ | **확정: 삭제** (2026-11-19) | 2단계에서 리팩토링 세션이 실행. 범위는 1절 2단계 |
| 11 | ~~저장소·리전~~ | **확정: Firestore + Firebase Storage, 리전 `us-central1`** (2026-11-17) | 1절 "추가 단계 A". 배포 방식(1번)은 Cloud Run 방향 |
| 12 | ~~캘린더·간트 순서~~ | **확정: 캘린더 → 간트** (2026-11-17) | 1절 "추가 단계 B". 단계 번호 배치는 미정 |
| 13 | ~~추가 단계 A·B의 위치~~ | **확정: A(Firebase)는 2단계 직후, B(캘린더→간트)는 7단계 직후** (2026-11-19) | C(패키지 정리)는 작성자 제안대로 A와 함께 진행 — 미확인 |
| 15 | **`self_query` 검색 방식 삭제** | 삭제 / 유지 | 사용자 보류(2026-11-19, 코드를 아직 보지 않음). 삭제 시 `langchain-classic`·`langchain-community`와 OpenAI 채팅 모델 연결이 함께 빠진다 |
| 17 | ~~배포 시 Firebase 관리자 인증~~ | **확정: ADC + GenMinute 전용 서비스 계정** (2026-11-20) | 키 파일 + Secret Manager 안은 버림(3절). 로컬 개발은 기존 키 파일 유지 |
| 16 | ~~2단계 범위 변경~~ | **확정: 서비스 안의 DB 호출을 repo로 옮기기** (2026-11-19) | Supabase 삭제와 함께 2단계에서 진행. 2-A(Firestore)는 repo 구현만 추가하면 되게 하는 것이 목적 |
| 14 | **서버 임베딩** | EmbeddingGemma 2(양자화) / `gemini-embedding-2` API | 사용자 확정(2026-11-20): 두 모델을 로컬 한국어 검색으로 비교한 뒤 결과를 보고 결정. **2-A 전에 정해야 한다**(Firestore 벡터 색인의 차원이 이 선택으로 정해짐) |
| 3 | **배포 환경의 STT 엔진** | Gemini STT 사용 / 로컬 STT 유지(이 경우 GPU 서버 필요) | VM(GPU 없는 사양)과 Cloud Run 모두 로컬 STT가 사실상 불가. Gemini STT는 원본이 Google API로 전송되어 프라이버시 목적과 관련된다 |
| 4 | **도메인 보유 여부** | 있음 / 구매 / 무료 도메인 | Firebase Hosting의 무료 주소(`genminute-492814.web.app`)로 시작 가능. 자체 도메인은 선택 |
| 5 | **0단계 실행 주체** | 작성자(Claude)가 `uploads/`의 짧은 녹음 사본으로 실행 / 사용자가 직접 실행 | 세 차례 물었으나 답 없음. 비용과 캘린더 등록 가능성 때문에 승인이 필요하다 |
| 6 | ~~브랜치 운영~~ | **확정: `cleanup`에서 작업하고 단계마다 `main`에 합치기** (2026-11-17) | |
| 7 | ~~서버 보관 기간 값~~ | **확정: 기본 14일 + 회의별 "원본 지금 삭제" 버튼** (2026-11-17) | 기간은 `config.py` 설정값. 저장 리전은 `us-central1`로 확정(11번) |
| 8 | ~~ogg·opus 변환 여부~~ | **확정: m4a로 변환** (2026-11-17) | |
| 9 | **참석자 자동 입력 2단계** | Google 캘린더의 진행 중 일정에서 제목·참석자 자동 채움 / 하지 않음 | 현재 캘린더 권한에 읽기가 포함되는지 확인하지 않았다. 없으면 사용자가 Google 동의를 다시 해야 한다 |
| 10 | ~~템플릿 부가 항목 3건~~ | **확정: 7단계에 포함** (2026-11-17) | 일시 = 업로드 시각, 제목·날짜 수정 미반영, 액션 아이템 일원화 |

---

## 3. 검토했다가 버린 안

| 안 | 버린 이유 |
|---|---|
| 원본 파일을 녹음한 기기에만 저장 | 다른 기기에서 재생, 공유받은 사람의 재생, 브라우저 데이터 삭제 후 재생이 모두 불가능해진다. STT가 서버에서 돌아 파일은 어차피 서버에 올라와야 한다. 대신 "기기 저장 버튼 + 서버 보관 기간"으로 대체 |
| 자체 서명 인증서로 HTTPS | 기기마다 경고가 뜨고 로그인·PWA가 불안정하다 |
| Cloud Storage를 디스크처럼 연결해 SQLite·ChromaDB를 그 위에 두기 | 파일 잠금이 안 되어 DB가 깨질 수 있다. 원본 파일 보관에만 쓸 수 있다 |
| 이 PC + Docker Desktop + Tailscale/Cloudflare Tunnel로 배포 | PC를 계속 켜 둬야 하고, Firebase Hosting과 함께 쓰면 주소가 둘로 나뉘어 쿠키·CORS 설정이 늘어난다. 이 PC는 Intel GPU라 Docker 안에서 GPU 가속도 어렵다. Docker Desktop은 사용자의 다른 개인 앱용으로만 쓰기로 함(2026-11-20) |
| Firebase 키 파일을 Secret Manager에 넣어 Cloud Run에 파일로 연결 | 코드 수정은 없지만 비밀값을 읽으려면 ADC가 어차피 필요하고, 만료 없는 관리자 키가 서버에 하나 더 생긴다. 권한도 좁힐 수 없다. ADC로 확정(2026-11-20) |
| GCP VM + Docker | 월 고정비(추정 2~3만원). Firestore 이전이 필요 없다는 장점은 있으나 Cloud Run 조합을 선택(2026-11-20) |
| Supabase를 배포 DB로 사용 | 2026-11-19 Firestore로 결정. Supabase 코드는 삭제하고 필요해지면 새로 작성(사용자 결정) |
| 모바일 녹음 대응(녹음 조각 단위 전송, 이어 올리기, 화면 꺼짐 방지) | 주 사용 환경이 웹(PC)이다. 모바일은 기본 녹음 앱으로 녹음한 뒤 업로드하도록 유도하기로 사용자가 결정 |
| PWA | 모바일이 "업로드와 열람" 용도면 얻는 것이 홈 화면 아이콘과 알림 정도다. 화면이 꺼지면 녹음이 멈추는 제약은 PWA로 해결되지 않는다. 보류 |
| 폰 안에서 STT 직접 실행 | 작은 모델만 돌아가 정확도가 낮고, 화자 분리가 안 되며, 앱을 내리면 멈춘다 |
| 웹 화면을 감싼 앱(백그라운드 녹음 권한용) | 앱 스토어 등록·심사·등록비가 따른다. 네이티브 앱과 함께 정식 서비스 배포 시점에 고려 |
| 비동기화에 Redis·Celery 도입 | 개인 사용 규모에는 작업 스레드와 상태 테이블로 충분하다 |
| 병렬 처리를 별도 단계로 | 전체 시간 대부분이 STT라 줄어드는 시간이 수십 초 수준이다. 3단계 안에서 제한적으로만 적용 |
| 회의록에 장소·작성자 항목 추가 | 녹음에서 알 수 없어 항상 "정보 없음"이 된다 |
| 회의록에 안건 항목 추가 | "핵심 논의 내용"의 소제목으로 대체 |
| `convert_webm_to_compatible_format`를 그대로 다시 연결 | 파일명에 `video_`가 있어야 영상으로 취급해, 현재 녹음 화면의 화면 녹화가 전부 음성 전용으로 바뀐다(dev_log 2026-11-16 실측). 재포장 방식으로 대체 |

---

## 4. 계획이 전제하는 것

### 이미 끝난 것 (커밋 `b88c8ff` 기준)

- 기본 DB를 SQLite로 전환, 인증을 Firebase로 복원. 실제 Google 로그인 확인 완료.
- 버그 수정, 조회·수정·삭제·공유·인증 경로의 스모크 테스트, 죽은 코드 약 4,000줄 삭제, 관리자 스크립트 입력 복구.

### 3단계 이후를 시작하기 전에 끝나 있어야 하는 것

- **0단계**: 실제 업로드가 한 번은 끝까지 돈 것을 확인했어야 한다. 그렇지 않으면 이후 변경으로 생긴 문제와 원래 있던 문제를 구분할 수 없다.
- **1단계**: 업로드·회의록·챗봇 경로에 테스트가 있어야 한다. 3·4·7단계가 바로 이 코드를 바꾼다.
- **2단계**: DI가 `app.py` 한 곳으로 모여 있어야 한다. 3단계는 업로드 서비스를 정리한 직후가 가장 손대기 쉽다고 판단해 이 순서로 잡았다.

### 단계 사이의 의존

- 7단계(템플릿)는 5단계(참석자)와 6단계(화자 이름)가 끝나야 참석자와 담당자를 실명으로 채울 수 있다.
- 8단계(공개 배포)는 1단계의 원본 접근 제한이 끝나 있어야 한다.
- 배포가 Cloud Run으로 정해지면 3단계(응답 후 CPU 정지)와 4단계(파일을 Cloud Storage로, 요청 크기 32MB 제한)의 구현이 달라진다. Cloud Run이 유력해지면 3·4단계 착수 전에 정하는 것이 재작업을 줄인다 **(추정)**.

### 아직 검증되지 않은 사실 (계획이 의존하는 것)

- 로컬 STT의 화자 분리는 pyannote와 huggingface_hub 버전 불일치로 실패할 가능성이 높다(코드로만 확인).
- 패키지 업그레이드 이후 실제 LLM 호출(요약·챗봇·에이전트)은 돌려 보지 않았다.
- 할 일 추출 에이전트의 메시지가 실행마다 중복 누적되는 것으로 보인다(수정 금지 영역이라 미수정).
- 회의록 템플릿 문제 4건은 코드로만 판단했다(7단계).
- Cloud Run의 요청 크기 제한과 GPU 제약은 작성자의 지식에 근거한 것이고 이 대화에서 공식 문서로 확인하지 않았다.

---

## 5. 다음에 바로 논의할 질문

1. **0단계 실제 업로드를 누가 돌리는가?** Claude가 돌려도 되는지, 사용자가 직접 할지. 이 답이 있어야 시작할 수 있다.
2. **브랜치를 어떻게 운영할 것인가?** `cleanup`에서 작업 후 단계마다 `main`에 합칠지.
3. **배포 방식의 방향이 섰는가?** 확정이 아니어도 "Cloud Run 가능성이 높다/낮다" 정도면 3·4단계 설계에 반영할 수 있다.
4. **ogg·opus도 변환 대상에 넣는가?**
5. **서버 보관 기간을 며칠로 할 것인가? 처리 직후 삭제도 선택지로 둘 것인가?**
6. **템플릿 부가 항목 3건(일시, 제목·날짜 반영, 액션 아이템 일원화)을 7단계에 포함하는가?**
7. **참석자 자동 입력 2단계(캘린더에서 자동 채움)를 할 것인가?**

# Genminute PRD (Product Requirements Document)

| 항목 | 내용 |
|---|---|
| **문서 버전** | v1.0 |
| **최종 수정** | 2026-06-12 |
| **상태** | Living Document (구현 현황 반영, 분기별 갱신) |
| **제품명** | Genminute (AI 회의록 자동 생성 플랫폼) |
| **관련 문서** | [로드맵](../development/roadmap.md) · [비용 예측](./cost_estimate.md) · [아키텍처](../architecture/) · [README](../../README.md) |

> 이 문서는 제품의 **목적·요구사항·범위·성공 기준**을 정의하는 단일 기준 문서입니다. 구현 세부는 `docs/architecture/`를, 작업 이력은 `docs/development/dev_log.md`를 참조하세요.

---

## 1. 제품 비전 (Vision)

> **"회의가 끝나는 순간, 회의록·할 일·검색 가능한 지식이 자동으로 완성된다."**

음성/영상 회의를 업로드하거나 실시간 녹음하면, AI가 **전사(STT) → 요약 → 정식 회의록 → 마인드맵 → 할 일(Action Item) → 일정 등록**까지 자동 수행하고, 축적된 회의 내용을 **RAG 챗봇**으로 언제든 질의할 수 있게 한다. 회의의 결과물을 "기록"에서 "실행 가능한 업무 자산"으로 전환하는 것이 핵심 가치다.

---

## 2. 문제 정의 (Problem Statement)

| 문제 | 현실 | Genminute의 해법 |
|---|---|---|
| 회의록 작성이 수작업·고비용 | 1시간 회의 정리에 30분~1시간 소요 | STT+요약 자동화로 분 단위 처리 |
| 누가 무엇을 말했는지 추적 곤란 | 녹취만으로는 화자/시점 불명확 | 화자 분리 + 타임스탬프 + 신뢰도 |
| 회의 결정이 실행으로 안 이어짐 | Action Item이 흩어지고 누락 | LangGraph 에이전트가 할 일 추출 → 캘린더 등록 |
| 과거 회의 내용 검색 불가 | "그때 예산 얼마였지?"에 답 못함 | 벡터 RAG 챗봇으로 전체 회의 질의 |
| 비용 부담 | 클라우드 STT 의존 시 회의당 ~$1 | 로컬 STT 옵션으로 비용 절감 |

---

## 3. 목표 & 비목표 (Goals / Non-Goals)

### 3.1 목표 (Goals)
- **G1.** 업로드/녹음 → 회의록 완성까지 **무인 자동 파이프라인** 제공
- **G2.** 한국어 회의에 대한 **고품질 전사·요약·검색** (다국어 자동 감지 포함)
- **G3.** 회의 결과의 **실행 연계** (Action Item + Google Calendar)
- **G4.** **비용 통제 가능성** — 로컬/클라우드 STT, 임베딩 모델을 설정으로 전환
- **G5.** **소유권·공유 기반 접근 제어**로 팀 단위 사용 지원
- **G6.** DB·인증 백엔드를 교체 가능한 **확장형 아키텍처** 유지

### 3.2 비목표 (Non-Goals) — 현재 범위 밖
- 실시간(스트리밍) 라이브 전사 자막 — *추후 검토(WebSocket 준실시간만 계획)*
- 다자 동시 편집(실시간 협업) — *추후*
- 모바일 네이티브 앱 — *웹(반응형)으로 충분*
- 회의 일정 스케줄링/예약 자체 — *Calendar 등록만, 회의 주최 기능 아님*
- 자체 LLM 파인튜닝/모델 호스팅 — *상용 API + 선택적 로컬 STT*

---

## 4. 타깃 사용자 & 페르소나

| 페르소나 | 니즈 | 핵심 기능 |
|---|---|---|
| **실무 담당자(주 사용자)** | 회의록 작성 시간 절감, 할 일 누락 방지 | 자동 회의록, Action Item, 캘린더 |
| **팀 리더/PM** | 회의 결정사항 추적, 팀 공유 | 공유, 검색, RAG 챗봇 |
| **현장/원격 참석자** | 대면·화상회의 녹음 | 모바일 마이크 녹음, PC 시스템 오디오 캡처 |
| **관리자(Admin)** | 운영·디버깅 | Admin 도구, 전체 노트 접근 |

### 접근 권한 모델 (3단계)
1. **Owner** — 생성자. 조회·수정·삭제·공유 가능
2. **Shared User** — 공유받은 사용자. 읽기 전용
3. **Admin** — `ADMIN_EMAILS` 등록 계정. 전체 접근 + 운영 도구

---

## 5. 핵심 사용자 시나리오 (User Flows)

### 5.1 회의록 생성 (주 흐름)
```
업로드/녹음 → (영상이면 ffmpeg 오디오 추출) → STT(화자분리+타임스탬프)
→ 관계형 DB 저장 → 스마트 청킹+임베딩(벡터 DB) → 주제별 요약 생성
→ 마인드맵 생성 → Action Item 자동 추출 → (SSE로 단계별 진행률 실시간 표시)
→ 노트 상세 페이지에서 열람
```

### 5.2 RAG 챗봇 질의
```
질문 입력 → 접근 가능한 회의 ID로 범위 한정 → 벡터 검색(chunks 3 + subtopic 3)
→ 컨텍스트 구성 → Gemini가 컨텍스트 기반으로만 답변 → 출처(회의/시점) 표시
```

### 5.3 할 일 → 일정 연계
```
회의록 → LangGraph 에이전트가 Action Item 추출 → 목록/체크박스 관리
→ (Google 캘린더 연동 시) OAuth 권한으로 일정 자동 등록
```

---

## 6. 제품 범위 & 기능 요구사항

> 상태 범례: ✅ 구현완료 · 🟡 부분/진행 · 🔜 계획 · ❄️ 보류

### 6.1 입력 & 전사 (Capture & STT)
| ID | 요구사항 | 우선순위 | 상태 |
|---|---|---|---|
| FR-1.1 | 오디오/영상 업로드 (WAV/MP3/M4A/FLAC/MP4/WEBM, ≤500MB) | Must | ✅ |
| FR-1.2 | 실시간 녹음 — 모바일 마이크 / PC 시스템 오디오(화상회의) | Must | ✅ |
| FR-1.3 | WebM → MP4/M4A 자동 변환, 파형 시각화 | Should | ✅ |
| FR-1.4 | 화자 분리 + 발화별 타임스탬프 + 신뢰도 점수 | Must | ✅ |
| FR-1.5 | STT 엔진 전환: `local`(faster-whisper+pyannote) / `gemini` | Must | ✅ |
| FR-1.6 | 언어 자동 감지 | Should | ✅ |

### 6.2 분석 & 생성 (AI Generation)
| ID | 요구사항 | 우선순위 | 상태 |
|---|---|---|---|
| FR-2.1 | 주제별 단락 요약 (마크다운 `###` 구조) | Must | ✅ |
| FR-2.2 | 정식 회의록 (참석자·요약·논의·Action Item·향후계획, `[cite:]` 출처) | Must | ✅ |
| FR-2.3 | 마인드맵 자동 생성 (Markmap 인터랙티브) | Should | ✅ |
| FR-2.4 | Action Item 추출 (LangGraph 에이전트) + 완료 상태 관리 | Must | ✅ |
| FR-2.5 | Google Calendar 일정 자동 등록 (OAuth 2.0) | Should | ✅ |

### 6.3 검색 & 챗봇 (Retrieval)
| ID | 요구사항 | 우선순위 | 상태 |
|---|---|---|---|
| FR-3.1 | RAG 챗봇 — 전역(전체 회의) / 회의별 | Must | ✅ |
| FR-3.2 | 컨텍스트 기반 답변 + 출처(회의·타임스탬프) 표시 | Must | ✅ |
| FR-3.3 | 노트 목록 검색(제목/요약) + 날짜범위 필터 + 정렬 + 무한스크롤 | Should | ✅ |
| FR-3.4 | 하이브리드 검색(벡터+키워드), 검색어 하이라이팅 | Could | 🔜 |

### 6.4 관리 & 협업 (Management)
| ID | 요구사항 | 우선순위 | 상태 |
|---|---|---|---|
| FR-4.1 | 제목/날짜 인라인 편집 (Owner) | Should | ✅ |
| FR-4.2 | 이메일 기반 공유 + 공유 목록/해제 + 공유받은 노트 페이지 | Must | ✅ |
| FR-4.3 | 화자 비중 분석 (Chart.js) | Could | ✅ |
| FR-4.4 | 미디어 재생: 타임스탬프 동기화, 배속(0.5~2x), 구간반복(A-B), 파형/영상 | Should | ✅ |
| FR-4.5 | 전역 업로드 상태바 (페이지 이동 후에도 진행률 유지) | Should | ✅ |
| FR-4.6 | 회의록 PDF/DOCX 내보내기 | Could | 🟡 |

### 6.5 인증 & 권한 (Auth)
| ID | 요구사항 | 우선순위 | 상태 |
|---|---|---|---|
| FR-5.1 | Supabase Auth 기반 Google 로그인 (Access Token 검증→세션) | Must | ✅ |
| FR-5.2 | Owner/Shared/Admin 3단계 권한 (라우트+DB 레벨 이중 체크) | Must | ✅ |

---

## 7. 비기능 요구사항 (NFR)

### 7.1 성능
- **NFR-P1.** 챗봇 응답 평균 **≤ 4초** (현재 ~3.77초)
- **NFR-P2.** 1시간 오디오 처리 중 **SSE 단계별 진행률**을 실시간 제공 (현재 동기 처리 2~7분)
- **NFR-P3.** 노트 목록은 무한스크롤·디바운싱(500ms)으로 대량 데이터 대응

### 7.2 비용 (Cost) — *cost_estimate.md 근거*
- **NFR-C1.** 1시간 회의 기준 클라우드 비용 **$0.8~1.2** (Gemini Pro STT). STT가 70%+ 비중
- **NFR-C2.** `STT_ENGINE=local`로 STT 비용 **≈ $0** 전환 가능해야 함 (GPU 보유 환경)
- **NFR-C3.** 임베딩 모델을 설정(`EMBEDDING_MODEL`)으로 교체 가능 → OpenAI 의존 제거 경로 확보

### 7.3 보안 & 프라이버시
- **NFR-S1.** 모든 사용자 입력 검증(파일 타입 화이트리스트, 크기, 제목 길이, 이메일/날짜 형식)
- **NFR-S2.** 파라미터화 쿼리(SQL 인젝션 방지), `secure_filename` + UUID 업로드
- **NFR-S3.** 비밀정보는 `.env`로만 관리, 커밋 금지. 프로덕션 OAuth는 **HTTPS 강제**(DEBUG에서만 평문 허용)
- **NFR-S4.** 쿼리 단계에서 `accessible_meeting_ids`로 데이터 격리

### 7.4 확장성 & 유지보수
- **NFR-X1.** 레이어드/클린 아키텍처 (Route→Service→Repository 인터페이스→구현체), DI는 `app.py`에서만 조립
- **NFR-X2.** `DB_TYPE`으로 Supabase/SQLite 무중단 전환 (Repository 패턴)
- **NFR-X3.** 원자적 모듈화(파일 비대화 방지), 타입 힌팅 강제, 매직값 `config.py` 집중

---

## 8. 시스템 아키텍처 개요

```
[React SPA (Vite+TS+Tailwind)]  ──HTTPS/JSON, SSE──>  [Flask API]
        │ Supabase JS (Google OAuth)                       │
        ▼                                                  ▼
   [Supabase Auth] <──Access Token 검증──  Route(Thin) → Service(DI) → Repository(ABC)
                                                              │              ├─ SQLite 구현체
                                                              │              └─ Supabase 구현체
                                          ┌───────────────────┼───────────────────┐
                                          ▼                   ▼                   ▼
                                  [Supabase/SQLite]      [ChromaDB]        [STT 엔진]
                                  관계형 데이터          벡터 임베딩       local | gemini
                                                       (chunks/subtopic)   + ffmpeg
```
- **AI 모델:** Gemini(`GEMINI_MODEL`) = 요약·회의록·마인드맵·챗봇 / OpenAI Embeddings = 벡터화(전환 예정)
- **에이전트:** LangGraph(Action Item) + Google Calendar Tool
- 상세: [docs/architecture/14_refactoring_plan.md](../architecture/14_refactoring_plan.md)

---

## 9. 데이터 모델 (요약)

| 엔티티 | 핵심 역할 |
|---|---|
| `users` | 계정(Supabase Auth UID), 역할, Google Calendar OAuth 토큰 |
| `meeting_dialogues` | 전사 세그먼트(화자·시점·신뢰도·소유자) |
| `meeting_minutes` | 생성된 회의록(마크다운) |
| `meeting_mindmap` | 마인드맵(마크다운) |
| `meeting_action_items` | 할 일(내용·기한·상태·calendar_event_id) |
| `meeting_shares` | 공유 접근 제어(owner/shared_with/permission) |
| ChromaDB `meeting_chunks` | 스마트 청킹 전사본 + 임베딩 |
| ChromaDB `meeting_subtopic` | 주제별 요약 + 임베딩 |

스키마: [docs/database/supabase_schema.sql](../database/supabase_schema.sql)

---

## 10. 성공 지표 (Success Metrics)

| 분류 | 지표 | 목표 |
|---|---|---|
| **품질** | 챗봇 답변 성공률 | ≥ 95% (현재 테스트 20문항 100%) |
| **품질** | 전사 화자분리 정확도(체감) | 사용자 수정 빈도 ↓ |
| **속도** | 챗봇 평균 응답 | ≤ 4초 |
| **속도** | 1h 오디오 처리 완료 시간 | 비동기화 후 "즉시 응답 + 백그라운드 완료" |
| **비용** | 회의당 처리 비용 | 로컬 STT 시 ≤ $0.05 |
| **활성도** | 월간 생성 노트 수 / 재방문 | 대시보드 통계로 추적 |

---

## 11. 릴리스 계획 (로드맵 정렬)

| 단계 | 범위 | 상태 |
|---|---|---|
| **Phase 2** | React/Vite SPA 전환 | ✅ 완료 |
| **Phase 3** | 핵심 기능 이식(인증·대시보드·업로드·녹음·뷰어·챗봇) | ✅ 완료 |
| **Phase 4** | 고도화(공유·Action Item·검색/필터·재생 UX) | ✅ 대부분 완료 |
| **Phase 4.x** | 인증/DB **Supabase 전환**, 클린 아키텍처 리팩토링 | ✅ 완료 |
| **Phase 5-A** | **임베딩 Gemini 전환 + ChromaDB→pgvector 통합** (DB 단일화) | 🔜 제안 |
| **Phase 5-B** | 대용량 처리 **비동기화**(Redis Queue→Celery), 즉시 응답 | 🔜 계획 |
| **Phase 5-C** | 하이브리드 검색, 내보내기(PDF/DOCX), 준실시간 미리보기 | ❄️ 후순위 |

---

## 12. 리스크 & 미해결 이슈 (Open Issues)

| # | 항목 | 영향 | 대응 |
|---|---|---|---|
| R1 | **DB 3중화**(Supabase + ChromaDB + SQLite 잔존) | 운영·일관성 부담 | Phase 5-A에서 pgvector 통합 검토 |
| R2 | **임베딩 OpenAI 의존** + 키 비용 만료 이력 | 벡터화 중단 위험 | `EMBEDDING_MODEL` 설정화 완료 → Gemini/BGE-M3 전환 결정 필요(재임베딩 수반) |
| R3 | **동기 처리 블로킹**(2~7분) | 동시 업로드 시 부하 | Phase 5-B 비동기화 |
| R4 | **experiments_stt/ 경계** 모호(stale 코드) | 혼선 | 프로덕션 미import 확인됨, 보존/제거 결정 필요 |
| R5 | 테스트 커버리지 부족(repository 위주) | 회귀 위험 | 서비스/라우트 단위 테스트 확충 |
| R6 | 외부 API(Gemini/OpenAI) 요금·할당량 의존 | 비용·가용성 | 로컬 STT·임베딩 자체호스팅 옵션 유지 |

---

## 13. 의사결정 대기 항목 (Decisions Needed)

1. **임베딩 모델 최종 채택**: gemini-embedding-001(품질·키단일화) vs BGE-M3 자체호스팅(무비용) vs 현행 유지
2. **벡터스토어**: ChromaDB 유지 vs Supabase pgvector 통합
3. **experiments_stt/** 보존 여부 및 위치

**결정 완료**
- **STT/화자분리 방향(2026-06-13)**: 현 파이프라인(faster-whisper + pyannote, local|gemini 투 트랙) **유지**, 이후 단계별로 검증·교체. Gemma 4 12B는 30초 상한·화자분리/타임스탬프 미보장·자체 교정으로 **STT 주엔진 부적합**(텍스트 단계 로컬화 후보), gpt-oss는 텍스트 전용으로 STT 제외 → 상세·점진 교체 계획: [stt_llm_localization_eval.md](./stt_llm_localization_eval.md)

---

## 부록 A. 용어 (Glossary)
- **STT**: Speech-to-Text(음성→텍스트 전사)
- **화자 분리(Diarization)**: 발화자를 구분(SPEAKER_00, 01…)
- **RAG**: 검색 증강 생성. 벡터 검색 결과를 컨텍스트로 LLM 답변 생성
- **스마트 청킹**: 화자 변경·시간 간격·의미 일관성 기준으로 전사본 분할
- **Action Item**: 회의에서 도출된 실행 과제(담당·기한)
- **SSE**: Server-Sent Events(서버→클라이언트 단방향 진행률 스트리밍)
- **Repository 패턴**: DB 접근을 인터페이스(ABC)로 추상화해 구현체 교체 가능

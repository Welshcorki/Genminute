# 🗺️ Genminute 고도화 및 리팩토링 로드맵 (2025)

이 문서는 서비스의 핵심 가치인 **AI 비서(Agent)** 기능을 최우선으로 도입하고, 이후 시스템 안정성 및 효율성을 강화하기 위한 계획을 기술합니다.

---

## 1. 📊 현황 진단 (AS-IS)

현재 Genminute는 **실시간 녹음 및 자동 변환 파이프라인(Universal Web Recorder)** 구축을 완료하였으며, 다음과 같은 시스템 구성을 가지고 있습니다.

- **Core AI Engine:** Google Gemini 2.5 Pro (STT, 요약) + Flash (챗봇)
- **Architecture:** Flask (Backend) + SQLite + ChromaDB (RAG) + Firebase Auth
- **New Feature:** Mobile/PC 실시간 녹음, ffmpeg 기반 자동 오디오 변환
- **⚠️ Pain Points:**
  - **활용성 부족:** 회의록이 생성되지만, 실제 업무(일정 등록, 태스크 관리)로 연결되지 않아 사용자가 수동으로 옮겨 적어야 함.
  - **동기식 처리 한계:** 긴 회의 파일 업로드 시 브라우저 연결 유지 필요.
  - **관리 포인트 이원화:** Gemini와 OpenAI 키가 혼용되어 있음.

---

## 2. 🚀 최우선 과제: 기능 확장 (Feature Expansion)

사용자 경험을 혁신적으로 개선하기 위해 AI 에이전트 기능을 가장 먼저 도입합니다.

### ✅ 과제 1: AI 비서 및 일정 연동 (Agent & Calendar Integration) [Priority 1]
**목표:** 회의록에서 도출된 실행 계획(Action Item)을 실제 업무 도구로 자동 연결하는 '비서' 역할 구현

- [ ] **Action Item 추출 에이전트:** - 회의록 텍스트 분석 → '할 일', '담당자', '마감기한' 구조화된 데이터(JSON) 추출
    - LangGraph를 도입하여 '추출 → 검토 → 실행'의 명확하고 제어 가능한 워크플로우 구현
- [ ] **외부 도구 연동 (Tools):**
    - 📅 **Google Calendar:** 회의 일정 및 마감일 자동 등록 API 연동
    - 📝 **Notion:** 프로젝트 페이지에 태스크(Task) 카드 생성 API 연동
- [ ] **인터랙티브 UI:** - AI가 제안한 일정을 사용자가 승인/수정/거절하는 '검토 인터페이스' 구현

### ✅ 과제 2: 멀티 문서 템플릿 (Document Templates)
**목표:** 회의뿐만 아니라 강의, 인터뷰 등 다양한 음성 기록을 목적에 맞게 문서화

- [ ] **템플릿 엔진 구축:** `utils/templates.py`를 생성하여 프롬프트 팩토리 패턴 구현
- [ ] **다양한 양식 지원:**
    - 🏢 **기본 회의록:** 안건, 결정사항, Action Item 중심
    - 🎓 **강의/세미나 노트:** 핵심 개념(Key Concepts), 요약, Q&A 정리
    - 🎤 **인터뷰/상담 일지:** 질의응답(Q&A) 구조, 핵심 인사이트 추출
- [ ] **UX 개선:** 변환 후 템플릿 재선택 및 재생성 기능 제공

---

## 3. 🛠️ 후속 과제: 시스템 최적화 (System Optimization)

기능 구현 후, 서비스의 안정성과 효율성을 높이기 위해 리팩토링을 진행합니다.

### ✅ 과제 3: 대용량 처리 비동기화 (Background Task)
**목표:** 1시간 이상의 대용량 녹음 파일도 안정적으로 처리하는 견고한 아키텍처 구축

- [ ] **비동기 구조 도입:** SSE(Server-Sent Events) 로직을 **Fire-and-Forget** 방식으로 변경
- [ ] **백그라운드 워커:** 무거운 작업(STT, 요약)을 별도 스레드(Thread) 또는 큐(Queue)로 분리
- [ ] **상태 조회 API:** 클라이언트 폴링(Polling) 구조 적용

### ✅ 과제 4: RAG 검색 품질 강화 (Hybrid Search)
**목표:** 챗봇이 사용자의 질문 의도(의미)와 구체적 키워드(정보)를 모두 정확하게 파악

- [ ] **키워드 검색 도입:** BM25 알고리즘 추가
- [ ] **하이브리드 검색 구현:** 벡터 검색 + 키워드 검색 가중치 결합 (Ensemble)

### ✅ 과제 5: AI 모델 의존성 통일 (OpenAI 완전 제거)
**목표:** Google Cloud 생태계로 100% 통합하여 비용 및 관리 포인트 최적화

- [ ] **임베딩 모델 교체:** `text-embedding-ada-002` (OpenAI) → **`text-embedding-004` (Google Gemini)**
- [ ] **의존성 제거:** `requirements.txt` 및 `.env`에서 OpenAI 관련 삭제

---

## 4. 📅 실행 계획 (Execution Plan)

변경된 우선순위에 따른 개발 순서입니다.

| 순서 | 구분 | 작업명 | 핵심 내용 |
| :--- | :--- | :--- | :--- |
| **Step 1** | **Feature** | **AI 에이전트 (1순위)** | **Action Item 추출 및 캘린더/노션 연동** |
| **Step 2** | **Feature** | **템플릿 시스템** | 강의/인터뷰 등 문서 양식 확장 |
| **Step 3** | **Refactoring** | **백그라운드 처리** | 비동기 파이프라인 구축 (안정성 확보) |
| **Step 4** | **Refactoring** | **검색 품질 강화** | 하이브리드 검색 도입 |
| **Step 5** | **Refactoring** | **OpenAI 걷어내기** | 임베딩 모델 교체 (비용 최적화) |
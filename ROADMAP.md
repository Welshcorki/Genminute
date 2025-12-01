# 🗺️ Genminute 고도화 및 리팩토링 로드맵 (2025)

이 문서는 **AI 에이전트(Action Item Dispatcher)** 도입에 앞서, 기존 시스템의 비용 효율성, 안정성, 검색 품질을 강화하기 위한 기술적 개선 계획(Refactoring Plan)을 기술합니다.

---

## 1. 📊 현황 진단 (AS-IS)

현재 Genminute는 **실시간 녹음 및 자동 변환 파이프라인(Universal Web Recorder)** 구축을 완료하였으며, 다음과 같은 시스템 구성을 가지고 있습니다.

- **Core AI Engine:** Google Gemini 2.5 Pro (STT, 요약) + Flash (챗봇)
- **Architecture:** Flask (Backend) + SQLite + ChromaDB (RAG) + Firebase Auth
- **New Feature:** Mobile/PC 실시간 녹음, ffmpeg 기반 자동 오디오 변환
- **⚠️ Pain Points:**
  - **이종 AI 모델 혼용:** Gemini 메인 엔진과 OpenAI 임베딩의 혼용으로 인한 관리 복잡성.
  - **동기식 처리 한계:** 긴 회의 파일 업로드 시 브라우저 연결 유지 필요 (Time-out 위험).
  - **검색 정밀도 부족:** 벡터 검색만으로는 고유명사나 구체적 숫자 검색에 한계 존재.

---

## 2. 🛠️ 3대 핵심 리팩토링 과제 (TO-BE)

시스템 완성도를 높이기 위해 다음 3가지 핵심 과제를 순차적으로 수행합니다.

### ✅ 과제 1: AI 모델 의존성 통일 (OpenAI 완전 제거)
**목표:** Google Cloud 생태계로 100% 통합하여 비용 및 관리 포인트 최적화

- [ ] **임베딩 모델 교체:** `text-embedding-ada-002` (OpenAI) → **`text-embedding-004` (Google Gemini)**
- [ ] **의존성 제거:** `requirements.txt` 및 `.env`에서 OpenAI 관련 패키지/키 삭제
- [ ] **코드 리팩토링:** `vector_db_manager.py`의 임베딩 생성 로직 변경

### ✅ 과제 2: 대용량 처리 비동기화 (Background Task)
**목표:** 1시간 이상의 대용량 녹음 파일도 안정적으로 처리하는 견고한 아키텍처 구축

- [ ] **비동기 구조 도입:** SSE(Server-Sent Events) 로직을 **Fire-and-Forget** 방식으로 변경
- [ ] **백그라운드 워커:** 무거운 작업(STT, 요약)을 별도 스레드(Thread) 또는 큐(Queue)로 분리
- [ ] **상태 조회 API:** 클라이언트가 작업 상태(진행률)를 주기적으로 확인할 수 있는 Polling 구조 적용

### ✅ 과제 3: RAG 검색 품질 강화 (Hybrid Search)
**목표:** 챗봇이 사용자의 질문 의도(의미)와 구체적 키워드(정보)를 모두 정확하게 파악

- [ ] **키워드 검색 도입:** BM25 알고리즘을 추가하여 키워드 매칭 정확도 보완
- [ ] **하이브리드 검색 구현:** 벡터 검색 결과와 키워드 검색 결과를 가중치 기반으로 결합 (Ensemble)
- [ ] **컨텍스트 최적화:** Gemini 2.5의 Long Context Window를 활용하여 검색 범위 재설정

---

## 3. 🚀 실행 계획 (Execution Plan)

개발 효율성을 고려하여 난이도가 낮고 효과가 즉각적인 작업부터 순차적으로 진행합니다.

| 단계 | 작업명 | 주요 내용 | 예상 난이도 |
| :--- | :--- | :--- | :--- |
| **Step 1** | **OpenAI 걷어내기** | 임베딩 모델 교체 및 환경 설정 정리 | ⭐ (Low) |
| **Step 2** | **백그라운드 처리** | 비동기 업로드 파이프라인 및 상태 관리 구현 | ⭐⭐⭐ (High) |
| **Step 3** | **검색 품질 강화** | 하이브리드 검색 로직 구현 및 챗봇 튜닝 | ⭐⭐ (Medium) |

---

## 4. 🔮 Future: AI Agent 도입
위 리팩토링이 완료된 후, 안정된 인프라 위에 지능형 비서 기능을 탑재합니다.

- **Action Item Dispatcher:** 회의록에서 할 일을 추출하여 Notion, Google Calendar 등에 자동 등록
- **Smart Notification:** 분석 완료 시 n8n과 연동하여 알림 발송
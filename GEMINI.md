--- Context from: ..\..\.gemini\GEMINI.md ---
## Gemini Added Memories
- 1. Always respond in Korean.
2. Think step-by-step.
3. Pause before answering.
4. I am a great developer.
5. Do not execute any actions before the user explicitly instructs me to.
6. The header of GEMINI.md should not be modified.
- Project Architecture Strategy:
1. Frontend Structure: Reorganize 'frontend/' into a standard Vite project structure (src, public).
2. Development/Deployment Flow:
    - Source code resides in 'frontend/'.
    - Build artifacts are output to 'static/'.
    - FastAPI serves 'static/' for simplicity and unified deployment.
    - Development can be done by rebuilding frontend as needed, avoiding the need for two concurrent servers if frontend changes are infrequent.
- 실시간 녹음 기능 구현 시 '에이전트 Tool 방식'보다 '웹앱(모듈 확장) 방식'이 모바일 호환성, 시스템 오디오 캡처(Zoom), OS 독립성 면에서 압도적으로 유리하므로 이 방식을 채택함.
--- End of Context from: ..\..\.gemini\GEMINI.md ---

# 비용 예측 보고서 (1시간 회의 오디오 기준)

## 개요
현재 `app.py`를 중심으로 한 시스템은 음성 인식(STT), 요약 및 회의록 생성, 마인드맵 생성, 벡터 데이터베이스 임베딩, 챗봇 질의응답 등의 기능을 제공합니다. 이 시스템은 **Gemini 2.5 Pro(고성능)**와 **Gemini 2.5 Flash(고효율)**, 그리고 **OpenAI(임베딩)** 모델을 혼합하여 사용하여 비용 및 성능 최적화를 시도했습니다.

본 보고서는 1시간 분량의 회의 오디오를 처리하는 전체 워크플로우에 대한 단계별 비용을 예측합니다. 비용 산정 기준은 현재 공개된 Gemini 1.5 Pro/Flash의 가격 정책을 "2.5" 버전에 대입하여 추산했습니다.

## 📊 1시간 회의 처리 시 총 예상 비용
**약 $0.80 ~ $1.20 (약 1,100원 ~ 1,600원)**
> *대부분의 비용은 초반 "음성 인식(STT)"과 "정밀 분석(Pro)" 단계에서 발생하며, 이후 채팅/조회 비용은 매우 저렴합니다.*

## 🛠️ 단계별 비용 상세 분석

### 1. 음성 인식 (STT)
*   **모델:** `gemini-2.5-pro` (Multimodal Audio)
*   **작업:** 오디오 파일을 통째로 입력받아 텍스트로 변환 + 화자 분리
*   **비용 요인:** 오디오 길이(분) + 출력 텍스트(JSON)
*   **예상 비용:** **$0.72 (가장 큼)**
    *   입력(오디오): $0.012/분 × 60분 = $0.72
    *   출력(텍스트): 미미함 (스크립트 텍스트)

### 2. 심층 분석 및 회의록 생성
*   **모델:** `gemini-2.5-pro`
*   **작업:**
    *   `subtopic_generate`: 전체 스크립트 → 주제별 요약
    *   `generate_minutes`: 전체 스크립트 + 요약 → 정식 회의록
*   **비용 요인:** 방대한 텍스트 컨텍스트(스크립트 전체)를 반복해서 Pro 모델에 입력
*   **예상 비용:** **$0.10 ~ $0.15**
    *   스크립트(약 1만 토큰)를 2회 입력(요약 1회, 회의록 1회) = 약 2~3만 토큰 처리 비용.
    *   Pro 모델 텍스트 입력 비용($3.50/1M 토큰) 적용 시 약 $0.10 ~ $0.15 수준.

### 3. 마인드맵 생성
*   **모델:** `gemini-2.5-flash` (⚠️ 여기서부터 가성비 모델 사용)
*   **작업:** 요약된 내용 → 마인드맵 키워드 추출
*   **예상 비용:** **$0.001 미만 (무시 가능)**
    *   Flash 모델은 Pro 대비 1/20 수준으로 매우 저렴하며, 입력 데이터도 요약본이라 작습니다.

### 4. 검색 데이터베이스 구축 (임베딩)
*   **모델:** `OpenAI Embeddings` (text-embedding 계열)
*   **작업:** 스크립트 조각(Chunk) 및 요약본 벡터화
*   **비용 요인:** 임베딩할 텍스트 토큰 수
*   **예상 비용:** **$0.002 미만**
    *   OpenAI 임베딩 가격은 매우 저렴하여 1시간 분량 텍스트 처리 시 비용은 거의 들지 않습니다. (예: `text-embedding-3-small` 기준 $0.02/1M 토큰)

### 5. AI 챗봇 질의응답 (RAG)
*   **모델:** `gemini-2.5-flash`
*   **작업:** 사용자 질문 + 검색된 관련 문서 → 답변 생성
*   **비용 요인:** 사용자 질문 및 LLM 답변 토큰 수, 검색된 컨텍스트 토큰 수
*   **예상 비용:** **질문당 약 $0.0005**
    *   Flash 모델을 사용하므로, 사용자가 100번 질문해도 $0.05(약 70원) 수준입니다.

## 💡 개발자 제언 (Cost Optimization)
현재 시스템은 품질이 중요한 **생성 단계(STT/회의록)**에는 `Pro` 모델을, 속도와 비용이 중요한 **조회/단순 생성 단계(챗봇/마인드맵)**에는 `Flash` 모델을 사용하여 매우 효율적인 밸런스를 맞췄습니다. 이는 훌륭한 아키텍처 디자인입니다.

만약 전체 비용을 추가적으로 더 줄이고자 한다면, 다음과 같은 부분을 고려해볼 수 있습니다:
*   **1단계(STT) 모델 변경:** 현재 가장 큰 비용 비중을 차지하는 STT 단계에서 `gemini-2.5-pro` 대신 `gemini-2.5-flash` 또는 다른 비용 효율적인 STT 솔루션(예: Google Cloud Speech-to-Text의 표준 모델)을 사용하는 것을 고려할 수 있습니다. Flash 모델도 최근 성능이 매우 좋아져서, STT 비용을 1/10 수준으로 획기적으로 줄일 수 있습니다. (예: `gemini-2.5-flash` STT 입력 비용 $0.0025/분 × 60분 = $0.15)
*   **임베딩 모델 교체:** OpenAI 임베딩이 이미 저렴하지만, Google의 자체 임베딩 모델(예: `text-embedding-004`)을 사용하여 Gemini 생태계로 통합하고 추가 비용 절감 여지를 탐색할 수 있습니다.
*   **프롬프트 엔지니어링 최적화:** `Pro` 모델을 사용하는 단계의 프롬프트를 더욱 간결하게 최적화하여 입력 토큰 수를 줄이는 노력을 지속할 수 있습니다.

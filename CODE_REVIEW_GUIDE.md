# 코드 리뷰 가이드

이 문서는 Phase 3 구현 과정에서 변경/생성된 파일들에 대한 코드 리뷰 기준과 실행 방법을 안내합니다.

---

## 📋 목차

1. [변경/생성된 파일 목록](#변경생성된-파일-목록)
2. [코드 리뷰 기준](#코드-리뷰-기준)
3. [주요 리뷰 포인트](#주요-리뷰-포인트)
4. [실행 방법](#실행-방법)
5. [테스트 체크리스트](#테스트-체크리스트)
6. [문제 해결](#문제-해결)

---

## 📁 변경/생성된 파일 목록

### 백엔드

#### 수정된 파일
- **`routes/meetings.py`**
  - 통계 API 엔드포인트 추가 (`/api/stats`)
  - 이번 달 노트 수, 총 녹음 시간 계산 로직

### 프론트엔드

#### 수정된 파일
- **`frontend/src/pages/Dashboard.tsx`**
  - 통계 API 연동 (`/api/stats` 엔드포인트)
  - 파일 업로드 모달 통합
  - 녹음 시간 포맷팅 함수 추가
  - **StatCard 인터랙션:** 이번 달 노트 → 노트 리스트, 최근 활동 → 최근 노트 상세
  - **노트 카드 클릭:** 전체 카드 클릭 시 상세 페이지 이동

- **`frontend/src/services/meeting.ts`**
  - `getUserStats()` 메서드 추가 (엔드포인트: `/api/stats`)
  - `getMeetingDetail()` 메서드 추가 (오디오 URL 전체 경로 변환 포함)
  - `deleteMeeting()` 메서드 수정 (엔드포인트: `DELETE` → `POST /api/delete_meeting/{id}`)
  - `updateMeetingTitle()` 메서드 추가 (엔드포인트: `POST /api/update_title/{id}`)
  - `updateMeetingDate()` 메서드 추가 (엔드포인트: `POST /api/update_date/{id}`)
  - `UserStats` 인터페이스 추가
  - 백엔드 응답 구조 파싱 (`{ success, stats }` → `stats` 추출)

- **`frontend/src/pages/NoteList.tsx`**
  - 업로드 모달 통합
  - 업로드 완료 시 목록 새로고침
  - **MoreVertical 버튼 수정:** `Link` → `button` 변경, `e.stopPropagation()` 추가
  - **카드 클릭 기능:** 카드 전체 클릭 시 상세 페이지 이동

- **`frontend/src/App.tsx`**
  - `Recorder`, `NoteDetail` 라우팅 추가

#### 새로 생성된 파일

##### 서비스 (Services)
- **`frontend/src/services/upload.ts`**
  - SSE 스트림 파싱 로직
  - 파일 업로드 서비스
  - `UploadProgress`, `UploadOptions` 인터페이스

- **`frontend/src/services/chat.ts`** *(신규)*
  - 챗봇 API 서비스
  - `sendMessage(query, meetingId?)` 메서드
  - `ChatSource`, `ChatResponse`, `ChatRequest` 인터페이스

- **`frontend/src/services/summary.ts`** *(신규)*
  - 요약 조회/생성 API 서비스
  - `getSummary()`, `generateSummary()` 메서드
  - `Summary`, `SummaryResponse` 인터페이스

- **`frontend/src/services/mindmap.ts`** *(신규)*
  - 마인드맵 조회/생성 API 서비스
  - `getMindmap()`, `generateMindmap()` 메서드
  - `MindmapNode`, `MindmapResponse` 인터페이스

- **`frontend/src/services/minutes.ts`** *(신규)*
  - 회의록 조회/생성 API 서비스
  - `getMinutes()`, `generateMinutes()` 메서드
  - `MinutesResponse` 인터페이스

##### 훅 (Hooks)
- **`frontend/src/hooks/useRecorder.ts`** *(전면 재작성)*
  - MediaRecorder API 래핑
  - 마이크 녹음 (`getUserMedia`)
  - 시스템 오디오 녹화 (`getDisplayMedia`)
  - 녹음 상태 관리 (idle, recording, paused, stopped)
  - AnalyserNode 제공 (파형 시각화용)
  - 타이머 기능
  - **타입 오류 수정:** `cursor: 'never'`, `webkitAudioContext` 타입 단언 추가

##### 컴포넌트 (Components)
- **`frontend/src/components/UploadModal.tsx`** *(전면 재작성)*
  - Drag & Drop 파일 업로드 모달
  - 파일 유효성 검사 (형식, 크기)
  - 제목/날짜 입력 폼
  - SSE 5단계 진행률 표시
  - 에러 처리 및 재시도

- **`frontend/src/components/AudioVisualizer.tsx`** *(신규)*
  - Canvas 기반 오디오 파형 시각화
  - AnalyserNode 연동
  - 반응형 크기 조정
  - 커스텀 색상 지원

- **`frontend/src/components/SummaryView.tsx`** *(신규)*
  - 요약 로딩 및 표시
  - 요약 생성 버튼
  - 간단한 마크다운 렌더링
  - 다시 생성 기능

- **`frontend/src/components/MindmapView.tsx`** *(신규)*
  - 계층적 트리 구조 렌더링
  - 레벨별 스타일 차별화
  - 펼침/접힘 기능
  - 다시 생성 기능

- **`frontend/src/components/UploadStatusBar.tsx`** *(신규)*
  - 전역 업로드 진행 상황 표시 바
  - 화면 우측 하단 고정
  - 취소/결과 보기/제거 기능
  - 접기/펼치기 기능

- **`frontend/src/components/GlobalChatSidebar.tsx`** *(수정)*
  - 전역 챗봇 사이드바
  - 확장/축소 입력창
  - indigo 색상 팔레트 적용
  - **타입 단언 개선:** `as HTMLElement` → `instanceof HTMLElement` 타입 가드 사용

- **`frontend/src/components/ChatSidebar.tsx`** *(수정)*
  - 회의별 챗봇 사이드바
  - NoteDetail 페이지 전용

- **`frontend/src/components/MinutesView.tsx`** *(신규)*
  - 회의록 조회 및 표시
  - 회의록 생성 버튼
  - 마크다운 렌더링 (제목, 리스트, 일반 텍스트)
  - 다시 생성 기능

##### Context (전역 상태)
- **`frontend/src/contexts/UploadContext.tsx`** *(신규)*
  - 전역 업로드 상태 관리
  - `addUpload()`, `cancelTask()`, `removeTask()` 메서드
  - `UploadTask` 인터페이스
  - 페이지 이동 시에도 상태 유지

- **`frontend/src/contexts/AuthContext.tsx`** *(신규)*
  - 전역 인증 상태 관리
  - Firebase 연동
  - `signInWithGoogle()`, `signOut()` 메서드

##### 페이지 (Pages)
- **`frontend/src/pages/Recorder.tsx`** *(전면 재작성)*
  - 실시간 녹음 페이지
  - 마이크/시스템 오디오 선택 UI
  - 녹음 컨트롤 (일시정지, 재개, 정지, 취소)
  - 파형 시각화
  - 녹음 완료 후 미리 듣기 및 업로드

- **`frontend/src/pages/NoteDetail.tsx`** *(전면 재작성)*
  - 노트 상세 뷰어 페이지
  - 오디오 플레이어 (재생/일시정지, 음소거, 시간 탐색)
  - 스크립트 탭 (화자별 색상, 클릭 시 시간 이동, 현재 세그먼트 하이라이트)
  - 요약 탭 (SummaryView)
  - 마인드맵 탭 (MindmapView)
  - **회의록 탭 (MinutesView)** - 요약과 별개의 회의록 생성/조회
  - 챗봇 탭 (ChatSidebar)
  - **편집 기능:** MoreVertical 메뉴에 제목/날짜 수정 옵션 추가
  - **인라인 편집:** 제목/날짜 클릭 시 입력 필드로 전환
  - 회의 삭제 기능

---

## ✅ 코드 리뷰 기준

### A. 기능 정확성

#### 백엔드
- [ ] API 엔드포인트가 올바르게 구현되었는가?
- [ ] SQL 쿼리가 정확하고 효율적인가?
- [ ] 권한 체크가 적절한가? (Admin/User 분리)
- [ ] 에러 처리가 충분한가?
- [ ] 날짜 계산 로직이 정확한가?

#### 프론트엔드
- [ ] API 호출이 올바른가?
- [ ] 상태 관리가 적절한가?
- [ ] 타입 정의가 완전한가?
- [ ] 에러 처리가 사용자 친화적인가?

### B. 코드 품질

#### TypeScript
- [ ] 타입이 명확하고 정확한가?
- [ ] `any` 타입 사용이 최소화되었는가?
- [ ] 인터페이스/타입이 재사용 가능한가?

#### React
- [ ] Hooks 사용이 올바른가?
  - 의존성 배열이 정확한가?
  - Cleanup 함수가 있는가?
- [ ] 컴포넌트가 적절히 분리되었는가?
- [ ] Props 타입이 명확한가?

#### 메모리 관리
- [ ] 이벤트 리스너가 정리되는가?
- [ ] 타이머/인터벌이 정리되는가?
- [ ] 스트림이 올바르게 닫히는가?
- [ ] 메모리 누수 가능성이 없는가?

### C. 보안

- [ ] 사용자 입력 검증이 있는가?
  - 파일 형식 검증
  - 파일 크기 제한
  - 제목 입력 검증
- [ ] 권한 체크가 적절한가?
- [ ] 민감한 정보가 노출되지 않는가?
- [ ] XSS 방지가 고려되었는가?

### D. 성능

- [ ] 불필요한 리렌더링이 없는가?
  - `useMemo`, `useCallback` 적절한 사용
- [ ] 대용량 파일 처리 시 문제가 없는가?
- [ ] 비동기 작업이 올바르게 처리되는가?
- [ ] 이미지/미디어 최적화가 고려되었는가?

### E. 사용자 경험

- [ ] 로딩 상태가 표시되는가?
- [ ] 에러 메시지가 명확하고 도움이 되는가?
- [ ] 접근성이 고려되었는가?
  - 키보드 네비게이션
  - 스크린 리더 지원
- [ ] 모바일 반응형이 구현되었는가?

### F. 코드 스타일

- [ ] 네이밍이 일관성 있는가?
- [ ] 주석이 적절한가?
- [ ] 중복 코드가 없는가?
- [ ] 파일 구조가 논리적인가?

---

## 🔍 주요 리뷰 포인트

### 1. 백엔드: `routes/meetings.py` - 통계 API

**위치:** `@meetings_bp.route("/api/stats", methods=["GET"])`

**확인 사항:**
```python
# 1. SQL 쿼리 정확성
# - 이번 달 계산 로직이 정확한가?
# - 총 녹음 시간 계산이 올바른가?
# - NULL 처리가 적절한가?

# 2. 권한 분리
# - Admin과 User 쿼리가 올바르게 분리되었는가?
# - is_admin 함수 호출이 올바른가?

# 3. 에러 처리
# - 예외 처리가 충분한가?
# - 로깅이 적절한가?
# - 사용자에게 명확한 에러 메시지가 반환되는가?
```

**잠재적 문제:**
- 날짜 계산 시 타임존 고려
- 빈 결과 처리 (`total_seconds`가 None일 경우)
- SQL 인젝션 방지 (파라미터화된 쿼리 사용 확인)

### 2. 프론트엔드: `useFileUpload` 훅

**위치:** `frontend/src/hooks/useFileUpload.ts`

**확인 사항:**
```typescript
// 1. Cleanup 함수
// - 컴포넌트 언마운트 시 리소스 정리가 되는가?
// - SSE 스트림이 올바르게 닫히는가?

// 2. 상태 관리
// - 상태 업데이트가 올바른가?
// - Race condition이 없는가?

// 3. 에러 처리
// - 네트워크 오류 처리가 있는가?
// - 파싱 오류 처리가 있는가?
```

**잠재적 문제:**
- 메모리 누수: 스트림이 닫히지 않을 경우
- 중복 업로드 방지 로직 필요 여부
- 진행률 업데이트 성능

### 3. 프론트엔드: `useRecorder` 훅

**위치:** `frontend/src/hooks/useRecorder.ts`

**확인 사항:**
```typescript
// 1. MediaStream 정리
// - 녹음 종료 시 모든 트랙이 정리되는가?
// - 컴포넌트 언마운트 시 정리가 되는가?

// 2. 타이머 관리
// - 타이머가 올바르게 정리되는가?
// - 일시 정지/재개 로직이 정확한가?

// 3. 브라우저 호환성
// - MediaRecorder API 지원 확인
// - MIME 타입 fallback 로직
```

**잠재적 문제:**
- 메모리 누수: MediaStream 트랙이 정리되지 않을 경우
- 타이머 누수: clearInterval이 호출되지 않을 경우
- 브라우저별 MIME 타입 지원 차이

### 4. 프론트엔드: `UploadModal` 컴포넌트

**위치:** `frontend/src/components/UploadModal.tsx`

**확인 사항:**
```typescript
// 1. 파일 검증
// - 파일 형식 검증이 충분한가?
// - 파일 크기 제한이 적절한가?

// 2. 상태 관리
// - 모달 열림/닫힘 상태가 올바른가?
// - 초기화가 적절한가?

// 3. 사용자 경험
// - 드래그 앤 드롭이 직관적인가?
// - 진행률 표시가 명확한가?
// - 에러 메시지가 도움이 되는가?
```

**잠재적 문제:**
- 파일 검증 우회 가능성
- 대용량 파일 업로드 시 UI 블로킹
- 접근성 (키보드 네비게이션, 스크린 리더)

### 5. 프론트엔드: `Recorder` 페이지

**위치:** `frontend/src/pages/Recorder.tsx`

**확인 사항:**
```typescript
// 1. AudioContext 관리
// - AudioContext가 올바르게 생성/정리되는가?
// - 브라우저 호환성 (webkitAudioContext)

// 2. 녹음 완료 후 처리
// - Blob이 올바르게 생성되는가?
// - 업로드 모달 연동이 정확한가?

// 3. 사용자 안내
// - 시스템 오디오 캡처 안내가 명확한가?
// - 에러 메시지가 도움이 되는가?
```

**잠재적 문제:**
- AudioContext 정리 누락
- 브라우저별 getUserMedia/getDisplayMedia 차이
- 녹음 중 페이지 이탈 시 처리

### 6. 프론트엔드: `NoteDetail` 페이지

**위치:** `frontend/src/pages/NoteDetail.tsx`

**확인 사항:**
```typescript
// 1. API 호출
// - 에러 처리가 적절한가? (403, 404 구분)
// - 로딩 상태가 표시되는가?

// 2. 오디오 플레이어
// - 재생/일시정지 동작이 정확한가?
// - 음소거 토글이 올바른가?
// - 시간 탐색(seek)이 정확한가?
// - 이벤트 리스너가 정리되는가?

// 3. 스크립트 동기화
// - 현재 재생 시간에 맞는 세그먼트 하이라이트가 정확한가?
// - 세그먼트 클릭 시 해당 시간으로 이동이 정확한가?
// - 자동 스크롤이 부드럽게 동작하는가?

// 4. 탭 네비게이션
// - 상태 관리가 올바른가?
// - 각 탭 컴포넌트에 올바른 props가 전달되는가?
```

**잠재적 문제:**
- 오디오 이벤트 리스너 정리 누락
- 대용량 스크립트 렌더링 성능
- 화자 색상 배열 범위 초과

### 7. 프론트엔드: `SummaryView` 컴포넌트

**위치:** `frontend/src/components/SummaryView.tsx`

**확인 사항:**
```typescript
// 1. API 호출
// - getSummary 에러 처리가 적절한가?
// - generateSummary 에러 처리가 적절한가?

// 2. 상태 관리
// - 로딩/생성 중 상태가 명확히 구분되는가?
// - 에러 상태가 올바르게 처리되는가?

// 3. 마크다운 렌더링
// - 제목(#, ##, ###) 파싱이 정확한가?
// - 리스트(-, *) 파싱이 정확한가?
// - XSS 방지가 고려되었는가?
```

**잠재적 문제:**
- 마크다운 파싱 불완전 (복잡한 마크다운 미지원)
- XSS 취약점 (사용자 입력이 아닌 AI 생성이므로 낮은 위험)
- 긴 요약문 렌더링 성능

### 8. 프론트엔드: `MindmapView` 컴포넌트

**위치:** `frontend/src/components/MindmapView.tsx`

**확인 사항:**
```typescript
// 1. API 호출
// - getMindmap 에러 처리가 적절한가?
// - generateMindmap 에러 처리가 적절한가?

// 2. 트리 렌더링
// - 재귀적 렌더링이 올바른가?
// - 깊은 중첩에서 성능 문제가 없는가?
// - 펼침/접힘 상태 관리가 올바른가?

// 3. 스타일
// - 레벨별 스타일 차별화가 명확한가?
// - 클릭 가능 영역이 충분한가?
```

**잠재적 문제:**
- 매우 깊은 트리 구조에서 성능 저하
- 매우 많은 노드에서 렌더링 성능
- 펼침/접힘 상태 초기화 시점

### 9. 프론트엔드: `AudioVisualizer` 컴포넌트

**위치:** `frontend/src/components/AudioVisualizer.tsx`

**확인 사항:**
```typescript
// 1. Canvas 관리
// - Canvas 크기 조정이 올바른가?
// - devicePixelRatio 처리가 정확한가?
// - resize 이벤트 리스너가 정리되는가?

// 2. 애니메이션
// - requestAnimationFrame이 정리되는가?
// - 녹음 중지 시 애니메이션이 멈추는가?

// 3. AnalyserNode 연동
// - null 체크가 충분한가?
// - 데이터 배열 크기가 적절한가?
```

**잠재적 문제:**
- requestAnimationFrame 정리 누락 시 메모리 누수
- Canvas 크기 변경 시 깜빡임
- 고주사율 모니터에서 성능

---

## 🚀 실행 방법

### 1. 백엔드 서버 실행

```bash
# 프로젝트 루트에서
# 가상환경 활성화 확인 (터미널에 (genminute_stt) 표시)
python app.py
```

**기본 포트:** `http://localhost:5000` (config.py의 PORT 설정 확인)

**주의사항:**
- 가상환경이 활성화되어 있어야 함
- `pip install -r requirements.txt`로 의존성 설치 필요
- Flask-CORS 패키지가 설치되어 있어야 함

**확인 사항:**
- `.env` 파일이 올바르게 설정되었는가?
- Firebase 초기화가 성공했는가?
- 데이터베이스가 올바르게 초기화되었는가?

### 2. 프론트엔드 개발 서버 실행

```bash
# ⚠️ 중요: 반드시 frontend 폴더로 이동해야 함!
cd frontend

# 의존성 설치 (처음 한 번만, node_modules가 없을 때)
npm install

# 개발 서버 실행
npm run dev
```

**기본 포트:** `http://localhost:5173`

**확인 사항:**
- `frontend/src/services/api.ts`의 `API_BASE_URL`이 `http://localhost:5000`인지 확인
- CORS 설정이 올바른가? (`app.py`에서 `http://localhost:5173` 허용)
- 프로젝트 루트가 아닌 `frontend` 폴더에서 실행해야 함

### 3. 동시 실행 (터미널 2개)

**터미널 1 (백엔드):**
```bash
python app.py
```

**터미널 2 (프론트엔드):**
```bash
cd frontend
npm run dev
```

### 4. 프로덕션 빌드 테스트

```bash
# 프론트엔드 빌드
cd frontend
npm run build

# 빌드 결과 확인
npm run preview
```

---

## 🧪 테스트 체크리스트

### 대시보드 테스트

- [ ] `http://localhost:5173` 접속
- [ ] 로그인 후 대시보드 표시 확인
- [ ] 통계 카드에 실제 데이터 표시 확인
  - 이번 달 노트 수
  - 총 녹음 시간 (시간/분 형식)
- [ ] "파일 업로드" 버튼 클릭 시 모달 열림 확인
- [ ] "새 기록 시작" 버튼 클릭 시 `/record`로 이동 확인

### 파일 업로드 테스트

- [ ] 업로드 모달에서 파일 드래그 앤 드롭
- [ ] 파일 선택 버튼으로 파일 선택
- [ ] 제목 입력 필드에 제목 입력
- [ ] 날짜 선택 (선택사항)
- [ ] 업로드 시작 버튼 클릭
- [ ] SSE 진행률 표시 확인
  - 업로드 → 음성인식 → 요약생성 → 마인드맵 단계
- [ ] 업로드 완료 후 노트 목록으로 이동 확인
- [ ] 에러 발생 시 에러 메시지 표시 확인

**테스트 파일:**
- 오디오 파일: `.wav`, `.mp3`, `.m4a`, `.flac`
- 비디오 파일: `.mp4`
- 파일 크기: 500MB 이하

### 실시간 녹음 테스트

#### 마이크 녹음
- [ ] `/record` 페이지 접속
- [ ] "마이크 녹음" 탭 선택
- [ ] "녹음 시작" 버튼 클릭
- [ ] 브라우저 마이크 권한 요청 확인
- [ ] 녹음 시작 후 타이머 동작 확인
- [ ] 파형 시각화 동작 확인
- [ ] "일시 정지" 버튼 동작 확인
- [ ] "녹음 종료" 버튼 클릭
- [ ] 녹음 완료 후 업로드 섹션 표시 확인
- [ ] 제목 입력 후 "분석 시작하기" 클릭
- [ ] 업로드 모달 열림 확인

#### 시스템 오디오 녹음
- [ ] "PC 시스템 오디오" 탭 선택
- [ ] "녹음 시작" 버튼 클릭
- [ ] 화면 공유 팝업 확인
- [ ] "전체 화면" 또는 "브라우저 탭" 선택
- [ ] "시스템 오디오 공유" 체크박스 활성화
- [ ] 녹음 시작 확인
- [ ] 화면 공유 중지 시 자동 녹음 중지 확인

### 노트 목록 테스트

- [ ] `/notes` 페이지 접속
- [ ] 노트 목록 표시 확인
- [ ] 검색 기능 동작 확인
- [ ] "업로드" 버튼 클릭 시 모달 열림 확인
- [ ] 노트 카드 클릭 시 상세 페이지로 이동 확인

### 노트 상세 뷰어 테스트

- [ ] 노트 목록에서 노트 클릭
- [ ] 회의 정보 헤더 표시 확인 (제목, 날짜, 참석자 수, 총 시간)
- [ ] 오디오 플레이어 표시 확인
  - 재생/일시정지 버튼 동작
  - 음소거 버튼 동작
  - 진행 바 드래그로 시간 탐색
  - 현재 시간/전체 시간 표시
- [ ] 탭 네비게이션 동작 확인
  - **스크립트 탭:**
    - 화자별 색상 구분 표시
    - 세그먼트 클릭 시 해당 시간으로 이동
    - 현재 재생 중인 세그먼트 하이라이트
    - 자동 스크롤
  - **요약 탭:**
    - 요약 로딩 상태 표시
    - 요약이 없을 경우 생성 버튼 표시
    - "요약 생성하기" 버튼 클릭 시 생성 시작
    - 생성 완료 후 요약 표시
    - "다시 생성" 버튼 동작
  - **마인드맵 탭:**
    - 마인드맵 로딩 상태 표시
    - 마인드맵이 없을 경우 생성 버튼 표시
    - "마인드맵 생성하기" 버튼 클릭 시 생성 시작
    - 트리 구조 렌더링 확인
    - 펼침/접힘 버튼 동작
    - "다시 생성" 버튼 동작
  - **챗봇 탭:**
    - ChatSidebar 표시
    - 해당 회의 기반 질의응답 동작
- [ ] 삭제 버튼 (권한이 있는 경우만 표시)
  - 삭제 확인 다이얼로그
  - 삭제 후 노트 목록으로 이동

---

## 🔧 문제 해결

### CORS 오류

**증상:**
```
Access to fetch at 'http://localhost:5000/api/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**해결:**
1. `flask-cors` 패키지가 설치되어 있는지 확인:
   ```bash
   pip list | findstr flask-cors  # Windows
   pip list | grep flask-cors     # Linux/Mac
   ```
2. 설치되어 있지 않다면:
   ```bash
   pip install flask-cors
   # 또는
   pip install -r requirements.txt
   ```
3. `app.py`의 CORS 설정 확인:
   ```python
   CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)
   ```
4. 프론트엔드 포트가 5173인지 확인
5. 백엔드 서버 재시작

### API 연결 오류

**증상:**
```
Network Error
Failed to fetch
```

**해결:**
1. `frontend/src/services/api.ts`의 `API_BASE_URL` 확인:
   ```typescript
   const API_BASE_URL = 'http://localhost:5000';
   ```
2. 백엔드 서버가 실행 중인지 확인
3. 백엔드 포트가 `config.py`의 PORT와 일치하는지 확인
4. 브라우저 개발자 도구 Network 탭에서 요청 확인

### 타입 오류

**증상:**
```
TypeScript compilation errors
```

**해결:**
```bash
cd frontend
npm run lint
```

**주요 확인 사항:**
- 인터페이스 정의가 완전한가?
- `any` 타입 사용 최소화
- Props 타입이 명확한가?

### 빌드 오류

**증상:**
```
Build failed
```

**해결:**
```bash
cd frontend
npm run build
```

**확인 사항:**
- 모든 import 경로가 올바른가?
- 타입 오류가 없는가?
- 환경 변수가 설정되었는가?

### 메모리 누수

**증상:**
- 브라우저 성능 저하
- 메모리 사용량 증가

**확인 사항:**
1. 브라우저 개발자 도구 → Performance 탭
2. 메모리 프로파일링
3. 다음 항목 확인:
   - 이벤트 리스너 정리
   - 타이머/인터벌 정리
   - 스트림 닫기
   - MediaStream 트랙 정리

### 녹음 기능 오류

**증상:**
- 녹음이 시작되지 않음
- 파형이 표시되지 않음

**해결:**
1. 브라우저 콘솔에서 에러 확인
2. 마이크/화면 공유 권한 확인
3. 브라우저 호환성 확인:
   - Chrome/Edge: 권장
   - Firefox: 제한적 지원
   - Safari: 제한적 지원
4. HTTPS 또는 localhost에서만 동작 (getUserMedia/getDisplayMedia)

### 프론트엔드 실행 오류 (package.json 없음)

**증상:**
```
npm error enoent Could not read package.json: Error: ENOENT: no such file or directory
```

**원인:**
- 프로젝트 루트에서 `npm run dev`를 실행했을 때 발생
- `package.json`은 `frontend` 폴더에 있음

**해결:**
```bash
# 1. frontend 폴더로 이동 (중요!)
cd frontend

# 2. 의존성 설치 (처음 한 번만)
npm install

# 3. 개발 서버 실행
npm run dev
```

**확인 사항:**
- 현재 위치가 `frontend` 폴더인지 확인 (`pwd` 또는 `cd` 명령어)
- `frontend/package.json` 파일이 존재하는지 확인
- `frontend/node_modules` 폴더가 있는지 확인

### 백엔드 Flask 모듈 오류

**증상:**
```
ModuleNotFoundError: No module named 'flask'
```

**원인:**
- 가상환경에 Flask가 설치되지 않음
- `requirements.txt`의 패키지들이 설치되지 않음

**해결:**
```bash
# 1. 가상환경 활성화 확인 (터미널에 (genminute_stt) 표시)
# 2. requirements.txt에서 모든 패키지 설치
pip install -r requirements.txt

# 또는 Flask만 먼저 설치
pip install Flask Flask-CORS

# 3. 설치 확인
python -c "import flask; print('Flask 설치됨:', flask.__version__)"
python -c "import flask_cors; print('Flask-CORS 설치됨')"

# 4. 서버 실행
python app.py
```

**주의사항:**
- `requirements.txt`에 많은 패키지가 포함되어 있어 설치에 시간이 걸릴 수 있음 (10-30분)
- PyTorch 등 대용량 패키지 포함

---

## 📝 코드 리뷰 체크리스트

### 백엔드

- [ ] `routes/meetings.py`
  - [ ] SQL 쿼리 정확성
  - [ ] 권한 분리 (Admin/User)
  - [ ] 에러 처리
  - [ ] 로깅

### 프론트엔드 - 서비스

- [ ] `frontend/src/services/upload.ts`
  - [ ] SSE 스트림 파싱
  - [ ] 에러 처리
  - [ ] 타입 정의

- [ ] `frontend/src/services/meeting.ts`
  - [ ] API 메서드 정확성
  - [ ] 타입 정의
  - [ ] 삭제 API 엔드포인트 (`POST /api/delete_meeting/{id}`)
  - [ ] 제목/날짜 수정 API 연동

### 프론트엔드 - 훅

- [ ] `frontend/src/hooks/useFileUpload.ts`
  - [ ] 상태 관리
  - [ ] Cleanup 함수
  - [ ] 에러 처리

- [ ] `frontend/src/hooks/useRecorder.ts`
  - [ ] MediaStream 정리
  - [ ] 타이머 관리
  - [ ] 브라우저 호환성
  - [ ] 타입 오류 수정 (`cursor`, `webkitAudioContext`)

### 프론트엔드 - 컴포넌트

- [ ] `frontend/src/components/UploadModal.tsx`
  - [ ] 파일 검증
  - [ ] 상태 관리
  - [ ] 사용자 경험

- [ ] `frontend/src/components/AudioVisualizer.tsx`
  - [ ] Canvas 렌더링
  - [ ] 성능 최적화
  - [ ] Cleanup 함수

### 프론트엔드 - 페이지

- [ ] `frontend/src/pages/Dashboard.tsx`
  - [ ] API 연동
  - [ ] 상태 관리
  - [ ] UI/UX

- [ ] `frontend/src/pages/Recorder.tsx`
  - [ ] AudioContext 관리
  - [ ] 녹음 완료 처리
  - [ ] 사용자 안내

- [ ] `frontend/src/pages/NoteDetail.tsx`
  - [ ] API 호출
  - [ ] 미디어 플레이어
  - [ ] 탭 네비게이션 (스크립트, 요약, 마인드맵, 회의록, 챗봇)
  - [ ] 제목/날짜 수정 기능
  - [ ] MoreVertical 메뉴 동작

- [ ] `frontend/src/pages/NoteList.tsx`
  - [ ] 업로드 모달 통합
  - [ ] 목록 새로고침
  - [ ] MoreVertical 버튼 이벤트 전파 방지
  - [ ] 카드 클릭 기능

---

## 🎯 다음 단계

코드 리뷰 완료 후:

1. **발견된 문제 수정**
   - 버그 수정
   - 성능 개선
   - 보안 강화

2. **테스트 보완**
   - 단위 테스트 추가
   - 통합 테스트 추가
   - E2E 테스트 추가

3. **문서화**
   - API 문서 업데이트
   - 사용자 가이드 작성
   - 개발자 가이드 보완

4. **향후 기능 구현 (Phase 4)**
   - ~~AudioPlayer 컴포넌트 고도화~~ ✅ 완료
   - ~~TranscriptView 개선 (텍스트-오디오 동기화)~~ ✅ 완료
   - ~~SummaryView 및 MindmapView 구현~~ ✅ 완료
   - ~~ChatSidebar 구현~~ ✅ 완료
   - ~~MinutesView 구현~~ ✅ 완료 (회의록 탭)
   - ~~제목/날짜 수정 기능~~ ✅ 완료
   - **Priority 1: 공유 기능 UI** (백엔드 API 존재)
     - 노트 공유 모달 (이메일 기반)
     - 공유 사용자 목록 조회 및 해제
     - 공유받은 노트 목록 페이지
   - **Priority 2: AI Agent UI** (백엔드 API 존재)
     - Action Item 추출 및 표시
     - Google Calendar 연동 상태 시각화
   - **Priority 3: UX 개선** (선택)
     - 오디오 파형 시각화 (WaveSurfer.js 도입 검토)
     - 재생 속도 조절 (0.5x ~ 2x)
     - 구간 반복 재생
     - 노트 내보내기 (PDF, DOCX)
     - 태그 관리 시스템

5. **성능 최적화 (Phase 5)**
   - 대용량 스크립트 가상화 (react-window)
   - 마인드맵 트리 최적화
   - 이미지/미디어 레이지 로딩
   - 번들 크기 최적화 (코드 스플리팅)

---

## 📚 참고 자료

- [React 공식 문서](https://react.dev/)
- [TypeScript 핸드북](https://www.typescriptlang.org/docs/)
- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

**마지막 업데이트:** 2025-12-18
**작성자:** AI Assistant
**버전:** 2.0 (Phase 3 핵심 기능 구현 완료)


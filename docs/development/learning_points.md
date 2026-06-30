# 📚 학습 포인트 (Learning Points)

이 문서는 프로젝트 개발 과정에서 발견한 언어/기술 스택별 학습 포인트를 기록합니다.

---

## 🔷 TypeScript / React

### 1. Vite + TypeScript에서 Type Import 주의사항

**문제:** Vite 환경에서 `interface`나 `type`을 일반 `import`로 가져오면 런타임 오류 발생.

```typescript
// ❌ 잘못된 방식 (SyntaxError 발생)
import { UploadProgress, uploadFile } from '../services/upload';

// ✅ 올바른 방식
import { uploadFile } from '../services/upload';
import type { UploadProgress } from '../services/upload';
```

**원인:** 
- TypeScript의 `interface`와 `type`은 컴파일 후 JavaScript에서 사라짐.
- Vite의 ESM 번들러가 런타임에 해당 export를 찾지 못함.

**해결:**
- `import type`을 사용하여 타입임을 명시적으로 표기.
- 또는 `isolatedModules: true` 설정 시 자동으로 경고 표시.

**학습일:** 2025-12-18

---

### 2. React Context에서 비동기 초기화 처리

**문제:** Firebase 초기화가 비동기이므로 Context가 준비되기 전에 컴포넌트가 렌더링됨.

```typescript
// ✅ 해결 패턴
const AuthProvider = ({ children }) => {
  const [firebaseReady, setFirebaseReady] = useState(false);
  
  useEffect(() => {
    ensureFirebaseInitialized().then(() => setFirebaseReady(true));
  }, []);
  
  // Firebase 준비 전까지 로딩 표시
  if (!firebaseReady) {
    return <LoadingSpinner />;
  }
  
  return <AuthContext.Provider>{children}</AuthContext.Provider>;
};
```

**학습일:** 2025-12-17

---

### 3. SSE (Server-Sent Events) 스트림 파싱

**문제:** `fetch`로 받은 SSE 응답을 올바르게 파싱해야 함.

```typescript
const response = await fetch('/api/upload', { method: 'POST', body: formData });
const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n\n'); // SSE 메시지는 \n\n으로 구분
  buffer = lines.pop() || ''; // 마지막 불완전한 메시지는 buffer에 유지

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));
      // 데이터 처리
    }
  }
}
```

**핵심 포인트:**
- `\n\n`으로 SSE 메시지 구분
- 불완전한 마지막 메시지는 buffer에 유지
- `stream: true` 옵션으로 스트리밍 디코딩

**학습일:** 2025-12-17

---

### 4. 마크다운 → 트리 구조 변환 알고리즘

**문제:** 마크다운 헤딩(`# ## ###`)을 계층적 트리 구조로 변환해야 함.

```typescript
const parseMarkdownToTree = (markdown: string): MindmapNode | null => {
  const lines = markdown.split('\n').filter(line => line.trim());
  const root: MindmapNode = { title: 'Root', children: [] };
  const stack: { node: MindmapNode; level: number }[] = [{ node: root, level: 0 }];

  for (const line of lines) {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (!match) continue;

    const level = match[1].length;
    const title = match[2].trim();
    const newNode: MindmapNode = { title, children: [] };

    // 현재 레벨보다 높거나 같은 항목을 스택에서 제거
    while (stack.length > 1 && stack[stack.length - 1].level >= level) {
      stack.pop();
    }

    // 부모 노드에 추가
    stack[stack.length - 1].node.children!.push(newNode);
    stack.push({ node: newNode, level });
  }

  return root.children?.[0] || null;
};
```

**핵심 포인트:**
- 스택을 사용하여 현재 부모 추적
- 레벨이 같거나 높은 항목은 스택에서 제거 (형제 또는 상위 항목)
- 레벨이 낮은 항목은 현재 스택 최상단의 자식으로 추가

**학습일:** 2025-12-18

---

## 🐍 Python / Flask

### 1. Flask CORS 설정 (개발 환경)

**문제:** 프론트엔드(`localhost:5173`)와 백엔드(`localhost:5000`)가 다른 포트에서 실행될 때 CORS 오류 발생.

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    'http://localhost:5173',  # Vite 개발 서버
    'http://127.0.0.1:5173'
])
```

**핵심 포인트:**
- `supports_credentials=True`: 쿠키/세션 인증 허용
- `origins`: 허용할 출처 명시
- 프로덕션에서는 실제 도메인으로 변경 필요

**학습일:** 2025-12-11

---

### 2. SSE 응답 생성 (Server-Sent Events)

**문제:** 장시간 처리 작업의 진행 상황을 클라이언트에 실시간 전송.

```python
from flask import Response
import json

def generate():
    for step in ['upload', 'stt', 'analysis', 'complete']:
        yield f"data: {json.dumps({'step': step, 'message': f'{step} 처리 중...'})}\n\n"
        # 실제 처리 로직
        time.sleep(1)

return Response(generate(), mimetype='text/event-stream')
```

**핵심 포인트:**
- MIME 타입: `text/event-stream`
- 메시지 형식: `data: {...}\n\n`
- Generator 함수로 스트리밍

**학습일:** 2025-12-11

---

### 3. 헬스 체크 엔드포인트 (Health Check Endpoint)

**목적:** 배포 플랫폼(GCP, AWS 등)이나 모니터링 도구가 서버 상태를 주기적으로 확인하기 위한 간단한 API 엔드포인트.

**비유:** 병원에서 심박수 모니터링처럼, 배포 플랫폼이 주기적으로 `/health`를 호출하여 서버가 정상 작동하는지 확인합니다. 서버가 응답하지 않으면 자동으로 재시작하거나 알림을 보냅니다.

**구현:**
```python
from flask import jsonify
from datetime import datetime
import os
from config import config

@app.route('/health')
def health_check():
    try:
        # 데이터베이스 파일 접근 가능 여부 확인
        db_path = config.DATABASE_PATH
        if not os.path.exists(db_path):
            return jsonify({
                "status": "unhealthy",
                "error": "Database file not found"
            }), 500
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

**사용 시나리오:**
1. GCP Compute Engine이 주기적으로 `/health` 엔드포인트 호출
2. 서버가 정상 응답 (HTTP 200, `{"status": "healthy"}`) → 서버 정상 작동 중
3. 서버가 응답 없음 또는 오류 응답 → 자동 재시작 또는 알림

**응답 예시:**
```json
// 정상 응답
{
  "status": "healthy",
  "timestamp": "2026-01-13T10:30:00Z"
}

// 비정상 응답
{
  "status": "unhealthy",
  "error": "Database file not found",
  "timestamp": "2026-01-13T10:30:00Z"
}
```

**핵심 포인트:**
- 간단하고 빠른 응답이 중요 (복잡한 로직 지양, 빠른 응답 시간)
- 데이터베이스, 외부 서비스 등 핵심 의존성 상태만 확인
- 배포 플랫폼이 자동 재시작/알림을 위해 사용
- HTTP 상태 코드: 200 (정상) 또는 500 (비정상)
- 인증 불필요 (헬스 체크는 공개 엔드포인트)

**학습일:** 2026-01-13

---

## 🌐 웹 API

### 1. MediaRecorder MIME 타입 선택

**문제:** 마이크 녹음과 시스템 오디오 녹화에 따라 다른 MIME 타입 필요.

```typescript
// 마이크 녹음: 오디오만
const mimeType = 'audio/webm;codecs=opus';

// 시스템 오디오 (화면 공유): 비디오 + 오디오
const mimeType = 'video/webm;codecs=vp8,opus';
```

**핵심 포인트:**
- `getDisplayMedia()`는 비디오 트랙도 포함하므로 비디오 MIME 타입 필요
- `getUserMedia()`는 오디오만 캡처하므로 오디오 MIME 타입 사용
- 브라우저마다 지원하는 코덱이 다를 수 있음

**학습일:** 2025-12-17

---

### 2. Audio URL 경로 변환

**문제:** 백엔드가 상대 경로(`/uploads/...`)를 반환하지만, 프론트엔드는 다른 포트에서 실행됨.

```typescript
// 백엔드 응답
{ audio_url: "/uploads/abc123.mp3" }

// 프론트엔드 변환
if (!data.audio_url.startsWith('http')) {
  data.audio_url = `${api.defaults.baseURL}${data.audio_url}`;
  // 결과: "http://localhost:5000/uploads/abc123.mp3"
}
```

**핵심 포인트:**
- 개발 환경에서는 프론트/백 포트가 다름
- 프로덕션에서는 같은 도메인이므로 상대 경로 그대로 사용 가능
- Axios `baseURL` 활용하여 일관된 처리

**학습일:** 2025-12-18

---

## 🔥 Firebase

### 1. Firebase 동적 설정 로드

**문제:** 프론트엔드 `.env`에 Firebase 설정을 중복 저장하지 않고 백엔드에서 가져오기.

```typescript
// frontend/src/config/firebase.ts
let app: FirebaseApp | null = null;

export const ensureFirebaseInitialized = async () => {
  if (app) return;
  
  const response = await fetch('http://localhost:5000/api/firebase-config');
  const config = await response.json();
  
  app = initializeApp(config);
};
```

**장점:**
- 설정 중복 제거
- 환경별 설정 관리 용이
- 민감 정보 노출 최소화

**학습일:** 2025-12-17

---

### 2. Google OAuth `invalid_client` 오류

**문제:** Firebase Google 로그인 시 `OAuth2 error: invalid_client` 발생.

**원인:**
- OAuth 클라이언트 시크릿 불일치
- Firebase Console과 Google Cloud Console 간 설정 불일치

**해결 과정:**
1. Firebase Console → Authentication → Sign-in method → Google 비활성화 후 재활성화
2. Google Cloud Console에서 OAuth 2.0 클라이언트 ID 확인
3. 승인된 리디렉션 URI에 Firebase Auth 핸들러 URL 등록
   - `https://your-project.firebaseapp.com/__/auth/handler`

**학습일:** 2025-12-17

---

## 📝 일반 개발 패턴

### 1. Context API로 전역 상태 관리

**패턴:** 업로드 작업 상태를 전역으로 관리하여 페이지 이동 시에도 유지.

```typescript
interface UploadTask {
  id: string;
  fileName: string;
  status: 'uploading' | 'complete' | 'error';
  progress: number;
}

const UploadContext = createContext<{
  tasks: UploadTask[];
  addTask: (task: UploadTask) => void;
  cancelTask: (id: string) => void;
} | null>(null);
```

**핵심 포인트:**
- Context + useState로 간단한 전역 상태 관리
- 복잡한 상태는 Redux/Zustand 고려
- Provider를 App 최상단에 배치

**학습일:** 2025-12-18

---

### 2. 프론트엔드-백엔드 API 엔드포인트 매핑

**교훈:** API 엔드포인트가 일치하지 않으면 404/500 오류 발생.

**체크리스트:**
1. 프론트엔드 서비스 파일에서 호출하는 URL 확인
2. 백엔드 라우트 데코레이터 확인 (`@app.route(...)`)
3. HTTP 메서드 일치 확인 (GET vs POST)
4. 응답 구조 일치 확인 (필드명, 타입)

**예시:**
```typescript
// 프론트엔드가 기대하는 응답
{ success: true, summary: "..." }

// 백엔드 실제 응답
{ success: true, has_summary: true, summary: "..." }

// → 응답 파싱 로직 수정 필요
```

**학습일:** 2025-12-18

---

### 5. TypeScript @ts-ignore와 브라우저 비표준 API 처리

**문제:** TypeScript가 인식하지 못하는 브라우저 전용 속성이나 비표준 API 사용 시 타입 오류 발생.

**케이스 1: DisplayMediaStreamConstraints 전용 속성**
```typescript
// ❌ 타입 오류: 'cursor' does not exist on type 'MediaTrackConstraints'
const stream = await navigator.mediaDevices.getDisplayMedia({
  video: {
    cursor: 'never'  // DisplayMediaStreamConstraints 전용 속성
  }
});

// ✅ 해결: @ts-ignore 주석 추가
const stream = await navigator.mediaDevices.getDisplayMedia({
  video: {
    // @ts-ignore - cursor는 DisplayMediaStreamConstraints 전용 속성
    cursor: 'never'
  }
});
```

**케이스 2: Safari 비표준 API (webkitAudioContext)**
```typescript
// ❌ 타입 오류: Property 'webkitAudioContext' does not exist on type 'Window'
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

// ✅ 해결 1: Window 인터페이스 확장
declare global {
  interface Window {
    webkitAudioContext: typeof AudioContext;
  }
}

// ✅ 해결 2: @ts-ignore 사용
const audioContext = new (window.AudioContext || 
  // @ts-ignore - Safari 비표준 API
  window.webkitAudioContext)();
```

**핵심 포인트:**
- `@ts-ignore`는 타입 체크를 우회하지만, 런타임 동작은 보장하지 않음
- 가능하면 타입 정의 확장(`declare global`)이 더 안전함
- 브라우저 호환성을 위해 비표준 API 사용 시 주석으로 이유 명시

**학습일:** 2025-12-18

---

### 6. instanceof를 사용한 타입 가드

**문제:** `querySelector` 등 DOM API는 `Element | null`을 반환하지만, 실제로는 `HTMLElement`가 필요함.

```typescript
// ❌ 타입 단언은 런타임 검증 없음 (위험)
const mainContent = document.querySelector('main') as HTMLElement;
mainContent.style.marginRight = '400px';  // null이면 런타임 오류

// ✅ 타입 가드로 런타임 검증
const mainContent = document.querySelector('main');
if (mainContent instanceof HTMLElement) {
  mainContent.style.marginRight = '400px';  // 안전
}
```

**핵심 포인트:**
- `as` 타입 단언은 컴파일 타임에만 작동 (런타임 검증 없음)
- `instanceof`는 런타임에 실제 타입을 확인 (타입 가드)
- `querySelector`는 `Element | null` 반환, `HTMLElement`가 필요하면 타입 가드 사용

**학습일:** 2025-12-18

---

### 7. 이벤트 전파 방지 (stopPropagation)

**문제:** 자식 요소(버튼) 클릭 시 부모 요소(카드)의 클릭 이벤트도 함께 발생.

```typescript
// 부모 카드: 클릭 시 상세 페이지 이동
<div onClick={() => navigate(`/notes/${meeting.id}`)}>
  <h3>{meeting.title}</h3>
  
  {/* 자식 버튼: 클릭 시 메뉴 열기 */}
  <button onClick={(e) => {
    e.stopPropagation();  // 부모 클릭 이벤트 방지
    setIsMenuOpen(true);
  }}>
    <MoreVertical />
  </button>
</div>
```

**핵심 포인트:**
- `e.stopPropagation()`: 이벤트 버블링 중단 (부모로 전파 방지)
- `e.preventDefault()`: 기본 동작 방지 (링크 이동, 폼 제출 등)
- 두 메서드는 다른 목적이므로 필요에 따라 선택 사용

**학습일:** 2025-12-18

---

### 8. 인라인 편집 UI 패턴

**패턴:** 읽기 모드와 편집 모드를 같은 위치에서 전환하는 UI.

```typescript
const [isEditing, setIsEditing] = useState(false);
const [editValue, setEditValue] = useState('');

// 읽기 모드
{!isEditing ? (
  <h1 onClick={() => setIsEditing(true)}>{title}</h1>
) : (
  // 편집 모드
  <div className="flex items-center gap-2">
    <input
      type="text"
      value={editValue}
      onChange={(e) => setEditValue(e.target.value)}
      onBlur={handleSave}  // 포커스 잃을 때 저장
      onKeyDown={(e) => {
        if (e.key === 'Enter') handleSave();
        if (e.key === 'Escape') setIsEditing(false);
      }}
      autoFocus
    />
    <button onClick={handleSave}>저장</button>
    <button onClick={() => setIsEditing(false)}>취소</button>
  </div>
)}
```

**핵심 포인트:**
- `onBlur`: 포커스 잃을 때 자동 저장 (사용자 경험 향상)
- `onKeyDown`: Enter(저장), Escape(취소) 단축키 지원
- `autoFocus`: 편집 모드 진입 시 자동 포커스

**학습일:** 2025-12-18

---

### 9. 간단한 마크다운 렌더링 (라이브러리 없이)

**패턴:** 기본 마크다운 문법만 필요한 경우 라이브러리 없이 직접 파싱.

```typescript
{markdown.split('\n').map((line, index) => {
  // 제목 처리
  if (line.startsWith('# ')) {
    return <h1 key={index}>{line.substring(2)}</h1>;
  }
  if (line.startsWith('## ')) {
    return <h2 key={index}>{line.substring(3)}</h2>;
  }
  
  // 리스트 처리
  if (line.startsWith('- ') || line.startsWith('* ')) {
    return <li key={index}>{line.substring(2)}</li>;
  }
  
  // 빈 줄
  if (line.trim() === '') {
    return <br key={index} />;
  }
  
  // 일반 텍스트
  return <p key={index}>{line}</p>;
})}
```

**핵심 포인트:**
- 간단한 마크다운만 필요하면 라이브러리 없이 구현 가능
- `split('\n')`으로 줄 단위 파싱
- `startsWith()`로 문법 구분
- 복잡한 마크다운(표, 코드 블록, 링크 등)은 `react-markdown` 같은 라이브러리 사용 권장

**학습일:** 2025-12-18

---

### 10. TypeScript `import` vs `import type` 차이

**문제:** TypeScript에서 타입과 값을 구분하여 import해야 함.

```typescript
// ❌ 잘못된 방식: 타입과 값을 함께 import
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
// ReactNode는 타입인데 런타임 import에 포함됨

// ✅ 올바른 방식: 타입과 값을 분리
import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
```

**차이점:**

| 구분 | `import` | `import type` |
|------|----------|---------------|
| 용도 | 실제 값/함수/클래스 | 타입 정보만 |
| 번들 포함 | ✅ 포함됨 | ❌ 제거됨 |
| 런타임 존재 | ✅ 존재함 | ❌ 존재하지 않음 |
| 사용 예시 | `useState`, `createContext` | `ReactNode`, `User`, `interface` |

**핵심 포인트:**
- **타입은 컴파일 시 제거됨:** `import type`으로 가져온 타입은 JavaScript로 컴파일될 때 완전히 사라짐
- **번들 크기 최적화:** 타입을 `import type`으로 분리하면 불필요한 코드가 번들에 포함되지 않음
- **`verbatimModuleSyntax: true` 설정:** TypeScript 5.0+에서 이 설정이 활성화되면 타입과 값을 명확히 구분해야 함
- **명확성:** 코드만 봐도 타입인지 값인지 구분 가능

**실제 사용 예시:**
```typescript
// 런타임에 필요한 실제 함수들
import { useState, useEffect } from 'react';
import { signInWithPopup } from 'firebase/auth';

// 타입 정보만 필요한 경우
import type { ReactNode } from 'react';
import type { User as FirebaseUser } from 'firebase/auth';

// 사용
interface AuthProviderProps {
  children: ReactNode; // 타입 체크용
}

const [user, setUser] = useState<FirebaseUser | null>(null); // 타입 체크용
```

**학습일:** 2025-12-18

---

### 11. 모달 컴포넌트 패턴 (배경 오버레이 + 중앙 정렬)

**패턴:** 모달을 화면 중앙에 표시하고 배경을 어둡게 처리하는 UI 패턴.

```typescript
// ✅ 표준 모달 패턴
{isOpen && (
  <>
    {/* 배경 오버레이 - 클릭 시 닫기 */}
    <div
      className="fixed inset-0 bg-black/50 z-40"
      onClick={onClose}
    />
    
    {/* 모달 컨테이너 - 중앙 정렬 */}
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()} // 모달 내부 클릭 시 닫히지 않음
      >
        {/* 모달 내용 */}
      </div>
    </div>
  </>
)}
```

**핵심 포인트:**
- `fixed inset-0`: 전체 화면 덮기
- `z-index` 계층: 배경(z-40) < 모달(z-50)
- `flex items-center justify-center`: 중앙 정렬
- `e.stopPropagation()`: 모달 내부 클릭 시 이벤트 전파 방지
- 배경 클릭 시 닫기: `onClick={onClose}`

**학습일:** 2025-12-18

---

### 12. 이메일 검증 정규식

**패턴:** 간단한 이메일 형식 검증 (프론트엔드 기본 검증).

```typescript
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

if (!emailRegex.test(email.trim())) {
  setError('올바른 이메일 형식을 입력해주세요.');
  return;
}
```

**핵심 포인트:**
- `[^\s@]+`: @ 앞에 공백과 @가 없는 문자 1개 이상
- `@`: @ 기호 필수
- `[^\s@]+`: @ 뒤에 공백과 @가 없는 문자 1개 이상
- `\.`: 점(.) 필수 (이스케이프 필요)
- `[^\s@]+`: 도메인 확장자 (공백과 @가 없는 문자 1개 이상)
- **주의:** 완벽한 이메일 검증은 아니지만, 기본적인 형식 검증에는 충분
- 백엔드에서도 추가 검증 필요

**학습일:** 2025-12-18

---

### 13. 공유 기능 백엔드-프론트엔드 API 매핑

**교훈:** 백엔드 함수 시그니처와 프론트엔드 호출이 일치해야 함.

**문제 상황:**
```python
# 백엔드 함수 시그니처
def remove_share(meeting_id: str, owner_id: int, shared_user_id: int) -> Dict:

# 잘못된 호출 (owner_id 누락)
result = remove_share(meeting_id, target_user_id)  # ❌

# 올바른 호출
result = remove_share(meeting_id, user_id, target_user_id)  # ✅
```

**핵심 포인트:**
- 백엔드 함수 파라미터 순서 확인
- 세션에서 가져온 `user_id`를 명시적으로 전달
- 함수 시그니처와 호출부 일치 확인
- 타입 힌트가 있으면 파라미터 순서 확인 용이

**학습일:** 2025-12-18

---

### 14. 공유받은 데이터 필터링 패턴

**패턴:** 백엔드에서 공유받은 데이터만 조회하는 SQL 쿼리 패턴.

```python
# 공유받은 노트만 조회 (본인 노트 제외)
cursor.execute("""
    SELECT DISTINCT
        md.meeting_id,
        md.title,
        MAX(md.meeting_date) as meeting_date,
        ...
    FROM meeting_dialogues md
    INNER JOIN meeting_shares s ON md.meeting_id = s.meeting_id
    WHERE s.shared_with_user_id = ?
      AND md.owner_id != ?  -- 본인 노트 제외
    GROUP BY md.meeting_id
    ORDER BY meeting_date DESC
""", (user_id, user_id))
```

**핵심 포인트:**
- `INNER JOIN`: 공유 테이블과 조인하여 공유된 노트만 조회
- `WHERE shared_with_user_id = ?`: 현재 사용자가 공유받은 노트만
- `owner_id != ?`: 본인이 만든 노트는 제외 (공유받은 것만)
- `DISTINCT`: 중복 제거 (같은 노트가 여러 세그먼트로 나뉘어 있을 수 있음)

**학습일:** 2025-12-18

---

### 15. Agent Service 지연 초기화 패턴

**문제:** Agent Service 초기화 실패 시 전체 서비스에 영향.

**해결 패턴:**
```python
# 지연 초기화 방식
_agent_service = None

def get_agent_service():
    global _agent_service
    if _agent_service is None:
        try:
            _agent_service = AgentService()
        except Exception as e:
            logger.warning(f"Agent Service 초기화 실패: {e}")
            return None
    return _agent_service

# API에서 사용
agent = get_agent_service()
if agent is None:
    return jsonify({"success": False, "error": "..."}), 503
```

**핵심 포인트:**
- 선택적 기능은 지연 초기화로 처리
- 초기화 실패 시 None 반환 및 503 에러
- 전체 서비스 중단 방지

**학습일:** 2025-12 (Priority 2 구현)

---

### 16. CalendarEvent 형식과 DB 형식 변환

**문제:** `agent_service.process()` 결과는 CalendarEvent 형식이지만, DB는 다른 형식을 사용.

**해결 패턴:**
```python
# Agent Service 결과 (CalendarEvent 형식)
processed_items = [
    {
        'summary': '기획안 제출',
        'start_time': '2025-12-10T14:00:00',
        'event_id': 'google_calendar_event_id'
    }
]

# DB 저장 형식으로 변환
db_items = []
for item in processed_items:
    db_items.append({
        'content': item.get('summary', ''),  # summary → content
        'due_date': item.get('start_time'),  # start_time → due_date
        'calendar_event_id': item.get('event_id')
    })

db.save_action_items(meeting_id, db_items)
```

**핵심 포인트:**
- 필드명 매핑: `summary` → `content`, `start_time` → `due_date`
- optional 필드 처리: `.get()` 메서드 사용
- 외부 도구 연동 정보 보존: `calendar_event_id` 저장

**학습일:** 2025-12 (Priority 2 구현)

---

### 17. Action Item 상태 즉시 업데이트 패턴

**패턴:** 체크박스 클릭 시 즉시 API 호출하여 상태 업데이트.

```typescript
const handleToggleStatus = async (item: ActionItem) => {
  const newStatus = item.status === 'pending' ? 'done' : 'pending';
  
  // 낙관적 업데이트 (즉시 UI 반영)
  setActionItems(prev => prev.map(i => 
    i.id === item.id ? { ...i, status: newStatus } : i
  ));
  
  try {
    await actionItemsService.updateActionItemStatus(item.id, newStatus);
  } catch (error) {
    // 실패 시 이전 상태로 복구
    setActionItems(prev => prev.map(i => 
      i.id === item.id ? { ...i, status: item.status } : i
    ));
    setError('상태 업데이트에 실패했습니다.');
  }
};
```

**핵심 포인트:**
- 낙관적 업데이트로 빠른 피드백
- 실패 시 이전 상태로 복구
- 에러 메시지 표시

**학습일:** 2025-12 (Priority 2 구현)

---

### 18. 빈 상태 UI 설계 패턴

**패턴:** 데이터가 없을 때 사용자에게 명확한 액션을 유도하는 UI.

```typescript
{actionItems.length === 0 ? (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <Sparkles className="w-12 h-12 text-slate-400 mb-4" />
    <p className="text-slate-500 mb-4">아직 추출된 Action Item이 없습니다.</p>
    <button
      onClick={handleExtract}
      disabled={isExtracting}
      className="px-4 py-2 bg-indigo-600 text-white rounded-lg"
    >
      {isExtracting ? '추출 중...' : 'Action Item 추출하기'}
    </button>
  </div>
) : (
  // Action Item 목록 표시
)}
```

**핵심 포인트:**
- 중앙 정렬된 빈 상태 메시지
- 아이콘으로 시각적 안내
- 명확한 액션 버튼 제공
- 일관된 디자인 패턴 (MinutesView와 유사)

**학습일:** 2025-12 (Priority 2 구현)

---

### 19. 한국어 날짜 포맷팅 (toLocaleDateString)

**패턴:** ISO 8601 형식 날짜를 한국어 형식으로 변환.

```typescript
const formatDate = (dateString?: string) => {
  if (!dateString) return '마감일 없음';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  // 결과: "2025년 12월 10일 오후 2:00"
};
```

**핵심 포인트:**
- `toLocaleDateString('ko-KR')`로 한국어 형식
- 옵션으로 상세 형식 지정
- 브라우저 기본 기능 활용

**학습일:** 2025-12 (Priority 2 구현)

---

### 20. Action Item ID로 meeting_id 조회 패턴

**문제:** Action Item ID만으로는 권한 체크를 할 수 없음.

**해결 패턴:**
```python
# 1. Action Item ID로 meeting_id 조회
meeting_id = db.get_action_item_meeting_id(item_id)
if not meeting_id:
    return jsonify({"success": False, "error": "Action Item을 찾을 수 없습니다."}), 404

# 2. meeting_id로 권한 체크
if not can_access_meeting(user_id, meeting_id):
    return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

# 3. 권한 확인 후 상태 업데이트
db.update_action_item_status(item_id, status)
```

**핵심 포인트:**
- Action Item ID → meeting_id 조회 → 권한 체크 순서
- 각 단계별 에러 처리
- 명확한 에러 메시지

**학습일:** 2025-12 (Priority 2 구현)

---

### 21. IntersectionObserver를 사용한 무한 스크롤 구현

**문제:** 대량의 데이터를 한 번에 로드하면 성능 저하 및 초기 로딩 시간 증가.

**해결 패턴:**
```typescript
const observerTarget = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (!hasMore || isLoading) return;
  
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        loadMoreMeetings();
      }
    },
    { threshold: 0.1 }
  );
  
  const currentTarget = observerTarget.current;
  if (currentTarget) {
    observer.observe(currentTarget);
  }
  
  return () => {
    if (currentTarget) {
      observer.unobserve(currentTarget);
    }
  };
}, [hasMore, isLoading, currentPage]);
```

**핵심 포인트:**
- `IntersectionObserver`는 뷰포트와 요소의 교차를 감지
- `threshold: 0.1`은 요소가 10% 보일 때 트리거
- cleanup 함수에서 observer 해제 필수
- `useRef`로 DOM 요소 참조 유지

**학습일:** 2025-12-29 (Priority 3 구현)

---

### 22. 디바운싱(Debouncing)을 사용한 검색 최적화

**문제:** 사용자가 타이핑할 때마다 API 호출하면 서버 부하 증가 및 불필요한 요청 발생.

**해결 패턴:**
```typescript
const [searchTerm, setSearchTerm] = useState('');
const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

// 디바운싱: 검색어 변경 후 500ms 대기
useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearchTerm(searchTerm);
  }, 500);
  
  return () => clearTimeout(timer);
}, [searchTerm]);

// 실제 검색은 debouncedSearchTerm 변경 시 실행
useEffect(() => {
  loadMeetings(1, true);
}, [debouncedSearchTerm]);
```

**핵심 포인트:**
- `setTimeout`으로 지연 실행
- cleanup 함수에서 이전 타이머 취소
- 입력값(`searchTerm`)과 실제 검색값(`debouncedSearchTerm`) 분리
- 일반적으로 300-500ms 지연 시간 사용

**학습일:** 2025-12-29 (Priority 3 구현)

---

### 23. SQL WHERE 절과 HAVING 절의 차이

**문제:** 집계 함수(`MAX`, `COUNT` 등)를 WHERE 절에서 사용하면 SQL 오류 발생.

**해결 패턴:**
```python
# ❌ 잘못된 방식
WHERE MAX(md.meeting_date) >= ?

# ✅ 올바른 방식
WHERE md.meeting_date >= ?  # 개별 행 필터링
GROUP BY md.meeting_id
HAVING MAX(md.meeting_date) >= ?  # 그룹 결과 필터링
```

**핵심 포인트:**
- `WHERE`: GROUP BY 이전에 개별 행 필터링
- `HAVING`: GROUP BY 이후에 그룹 결과 필터링
- 집계 함수는 HAVING 절에서만 사용 가능
- 날짜 범위 필터는 `MAX(meeting_date)`를 사용하므로 HAVING 절 필요

**학습일:** 2025-12-29 (Priority 3 구현)

---

### 24. 서버 사이드 검색 vs 클라이언트 사이드 필터링

**문제:** 클라이언트에서 모든 데이터를 받아 필터링하면 초기 로딩 시간 증가 및 메모리 사용량 증가.

**해결 패턴:**
```typescript
// ❌ 클라이언트 사이드 필터링
const filtered = meetings.filter(meeting => 
  meeting.title.includes(searchTerm)
);

// ✅ 서버 사이드 검색
const response = await meetingService.getAllMeetings({
  search: searchTerm,
  page: 1,
  perPage: 10
});
```

**핵심 포인트:**
- 서버 사이드 검색: 데이터베이스에서 필터링하여 필요한 데이터만 전송
- 클라이언트 사이드 필터링: 모든 데이터를 받아 브라우저에서 필터링
- 대량 데이터 처리 시 서버 사이드 검색이 효율적
- 페이지네이션과 함께 사용하면 더욱 효과적

**학습일:** 2025-12-29 (Priority 3 구현)

---

### 8. 오디오-스크립트 세그먼트 동기화 알고리즘

**문제:** 오디오 재생 중 현재 시간에 맞는 스크립트 세그먼트를 정확히 하이라이트하는 것이 어려움. 사용자가 세그먼트를 클릭하거나 재생바를 이동했을 때와 재생 중 자동 선택 간의 충돌 발생.

**해결 방법:**
1. **사용자 선택 우선 원칙:** `userSelectedSegmentId` 상태를 별도로 관리하여 사용자가 명시적으로 선택한 세그먼트는 재생 중에도 우선 적용
2. **정확한 범위 매칭:** 현재 재생 시간이 세그먼트의 `start_time`과 `end_time` 사이에 정확히 있을 때만 선택
3. **조건부 가장 가까운 세그먼트:** 모든 세그먼트 범위에서 임계값(2초) 이상 떨어져 있을 때만 가장 가까운 세그먼트 선택

```typescript
// 사용자 선택 우선
if (userSelectedSegmentId) {
  const userSegment = transcript.find(s => s.id === userSelectedSegmentId);
  if (userSegment && isTimeInRange(currentTime, userSegment)) {
    setActiveSegmentId(userSelectedSegmentId);
    return;
  }
}

// 정확한 범위 매칭
const activeSegment = transcript.find(segment => 
  currentTime >= segment.start_time && currentTime < segment.end_time
);

// 조건부 가장 가까운 세그먼트 (임계값 2초)
if (!activeSegment) {
  const DISTANCE_THRESHOLD = 2.0;
  const closestSegment = transcript.reduce((closest, segment) => {
    const distance = Math.abs(currentTime - segment.start_time);
    const closestDistance = Math.abs(currentTime - closest.start_time);
    return distance < closestDistance ? segment : closest;
  });
  
  const distance = Math.abs(currentTime - closestSegment.start_time);
  if (distance >= DISTANCE_THRESHOLD) {
    setActiveSegmentId(closestSegment.id);
  }
}
```

**핵심 포인트:**
- 사용자 의도와 자동 선택 간의 충돌 방지
- 임계값을 통한 과도한 세그먼트 변경 방지
- 정확한 범위 매칭으로 사용자 경험 개선

**학습일:** 2025-12-29 (노트 상세 페이지 개선)

---

### 9. Blob URL 메모리 관리 (useMemo + useEffect cleanup)

**문제:** `URL.createObjectURL(blob)`로 생성된 Blob URL이 매 렌더링마다 재생성되어 메모리 누수 발생. 또한 컴포넌트 언마운트 시 URL이 해제되지 않아 메모리 누수 가능성.

**해결 방법:**
1. **useMemo로 URL 메모이제이션:** Blob이 변경될 때만 새로운 URL 생성
2. **useEffect cleanup으로 메모리 해제:** 컴포넌트 언마운트 또는 URL 변경 시 `URL.revokeObjectURL` 호출
3. **key prop으로 불필요한 리렌더링 방지:** `<audio>` 요소에 `key={audioUrl}` 추가

```typescript
const PreviewSection = ({ recordedBlob }: { recordedBlob: Blob | null }) => {
  // useMemo로 URL 메모이제이션
  const audioUrl = useMemo(() => {
    if (!recordedBlob) return null;
    return URL.createObjectURL(recordedBlob);
  }, [recordedBlob]);

  // useEffect cleanup으로 메모리 해제
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  if (!audioUrl) return null;

  return (
    <audio 
      key={audioUrl}  // URL 변경 시에만 리렌더링
      src={audioUrl} 
      controls 
    />
  );
};
```

**핵심 포인트:**
- Blob URL은 명시적으로 해제해야 메모리 누수 방지
- `useMemo`로 불필요한 URL 재생성 방지
- `useEffect` cleanup 함수에서 항상 해제 처리

**학습일:** 2025-12-29 (Recorder 페이지 개선)

---

### 10. Whisper 언어 자동 감지

**문제:** 하드코딩된 언어 설정(`language="ko"`)으로 다국어 오디오를 올바르게 전사하지 못함. 한국어 오디오가 영어로 전사되는 문제 발생.

**해결 방법:**
1. **language=None 전달:** Whisper 모델에 `language=None`을 전달하면 자동으로 언어 감지
2. **백엔드 파라미터 전달:** `upload_service.py`에서 `diarization_service.transcribe_and_diarize(audio_path, language=None)` 호출
3. **다양한 백엔드 지원:** OpenVINO와 Faster-Whisper 모두에서 자동 감지 지원

```python
# services/upload_service.py
# language=None으로 설정하여 Whisper가 자동으로 언어를 감지하도록 함
raw_segments = diarization_service.transcribe_and_diarize(audio_path, language=None)

# services/diarization.py
def transcribe_and_diarize(self, audio_path: str, language: str | None = None):
    if self.backend == "openvino":
        generate_kwargs = {}
        if language:
            generate_kwargs["language"] = language
        # language=None이면 자동 감지
        prediction = self.whisper_pipeline(processed_audio, return_timestamps=True, generate_kwargs=generate_kwargs)
    else:
        # Faster-Whisper: language=None이면 자동 감지
        segments_generator, info = self.whisper_model.transcribe(
            processed_audio, 
            beam_size=5, 
            word_timestamps=True, 
            language=language  # None이면 자동 감지
        )
        logger.info(f"   -> Detected language: {info.language}")
```

**핵심 포인트:**
- Whisper 모델은 자동 언어 감지 기능을 내장하고 있음
- `language=None` 전달 시 모델이 오디오의 언어를 자동으로 감지
- 다국어 지원을 위해 하드코딩된 언어 설정 제거

**학습일:** 2025-12-29 (STT 언어 자동 감지 구현)

---

### 11. React Key Prop 최적화

**문제:** 동적으로 생성되는 리스트 요소에서 `key` prop이 중복되거나 충분히 고유하지 않아 React 경고 발생.

**해결 방법:**
1. **요소 타입 접두사 추가:** 동일한 인덱스를 사용하더라도 요소 타입을 접두사로 추가하여 고유성 보장
2. **조건부 key 생성:** ID가 있으면 ID 사용, 없으면 타입+인덱스 조합 사용
3. **마크다운 리스트 올바른 래핑:** 리스트 항목(`<li>`)을 `<ul>` 태그로 올바르게 래핑

```typescript
// ❌ 잘못된 방식 (중복 가능)
{lines.map((line, index) => (
  <h1 key={index}>{line}</h1>  // 다른 타입과 인덱스 충돌 가능
))}

// ✅ 올바른 방식 (타입 접두사 추가)
{lines.map((line, index) => {
  if (line.startsWith('# ')) {
    return <h1 key={`h1-${index}`}>{line}</h1>;
  } else if (line.startsWith('## ')) {
    return <h2 key={`h2-${index}`}>{line}</h2>;
  }
  // ...
})}

// ✅ 조건부 key 생성
{transcript.map((segment, index) => (
  <div key={segment.id ?? `segment-${index}`}>
    {segment.text}
  </div>
))}
```

**핵심 포인트:**
- `key` prop은 리스트 내에서 고유해야 함
- 요소 타입을 접두사로 추가하여 고유성 보장
- ID가 있으면 ID 사용, 없으면 타입+인덱스 조합 사용

**학습일:** 2025-12-29 (React 렌더링 최적화)

---

### 12. 전역 상태 관리 (UploadContext)

**문제:** 파일 업로드와 녹음 업로드가 각각 다른 방식으로 진행 상태를 관리하여 UX 일관성 부족. 녹음 업로드 시 전역 업로드 상태 바가 표시되지 않음.

**해결 방법:**
1. **UploadContext 생성:** 모든 업로드 작업을 하나의 Context에서 관리
2. **통합 업로드 함수:** `addUpload` 함수로 파일 업로드와 녹음 업로드를 동일한 방식으로 처리
3. **전역 상태 바:** `UploadStatusBar` 컴포넌트가 모든 업로드 작업의 진행 상황을 표시

```typescript
// contexts/UploadContext.tsx
interface UploadContextType {
  activeTasks: UploadTask[];
  addUpload: (file: File, title: string, meetingDate?: string) => Promise<string | null>;
  removeTask: (id: string) => void;
  cancelTask: (id: string) => void;
  clearCompletedTasks: () => void;
}

// pages/Recorder.tsx
const { addUpload } = useUpload();

const handleUpload = async () => {
  const file = new File([recordedBlob], fileName, { type: recordedBlob.type });
  const meetingId = await addUpload(file, title.trim());
  if (meetingId) {
    navigate(`/notes/${meetingId}`);
  }
};
```

**핵심 포인트:**
- 전역 상태 관리를 통해 UX 일관성 확보
- 모든 업로드 작업을 하나의 Context에서 관리
- SSE(Server-Sent Events)를 통한 실시간 진행률 업데이트

**학습일:** 2025-12-29 (전역 업로드 상태 관리 통합)

---

## 🚀 배포 및 인프라

### 1. Flask 개발 서버 vs Gunicorn (WSGI 서버)

**문제:** Flask 개발 서버(`app.run()`)는 개발용이며 프로덕션 환경에서 사용하면 성능 및 안정성 문제 발생.

**차이점:**

| 항목 | Flask 개발 서버 | Gunicorn |
|------|----------------|----------|
| **용도** | 개발 환경 | 프로덕션 환경 |
| **동시 처리** | 단일 스레드 (1명만) | 여러 워커 프로세스 (여러 명 동시) |
| **성능** | 느림 | 빠름 |
| **안정성** | 낮음 (개발용) | 높음 (프로덕션용) |
| **디버깅** | 자동 리로드, 디버그 모드 | 디버깅 기능 없음 |
| **실행 방법** | `python app.py` | `gunicorn wsgi:app` |

**비유:** 개발 서버 = 연습용 자전거 (한 명만 탈 수 있음), Gunicorn = 프로덕션 서버 (여러 사람이 동시에 탈 수 있음)

**Gunicorn 설정 파일:**
```python
# gunicorn_config.py
workers = 4              # 워커 프로세스 수 (CPU 코어 수 * 2 + 1)
bind = "127.0.0.1:8000"  # Gunicorn이 리스닝할 주소 (Nginx와 연결)
timeout = 120            # 요청 타임아웃 (초)
accesslog = "logs/access.log"  # 접근 로그
errorlog = "logs/error.log"    # 에러 로그
```

**실행 방법:**
```bash
# 개발 환경
python app.py

# 프로덕션 환경
gunicorn -c gunicorn_config.py wsgi:app
```

**핵심 포인트:**
- Flask 개발 서버는 `app.run()` 사용 (개발용)
- Gunicorn은 WSGI 서버로 프로덕션 환경에서 Flask 앱 실행
- 여러 워커 프로세스로 동시 요청 처리 가능
- `wsgi.py` 파일이 Gunicorn 진입점

**학습일:** 2026-01-13

---

### 2. Nginx 리버스 프록시

**목적:** 사용자 요청을 Gunicorn으로 전달하고, 정적 파일을 직접 서빙하며, HTTPS/SSL을 처리하는 웹 서버.

**비유:** Nginx = 호텔 안내 데스크 (요청을 적절한 곳으로 안내), Gunicorn = 호텔 직원 (실제 업무 처리)

**역할:**
1. 리버스 프록시: 사용자 요청을 Gunicorn으로 전달
2. 정적 파일 서빙: React 빌드 파일, 이미지 등을 직접 서빙 (Gunicorn보다 빠름)
3. HTTPS/SSL 처리: SSL 인증서 관리 및 HTTPS 요청 처리
4. 로드 밸런싱: 여러 Gunicorn 인스턴스에 요청 분산 (확장 시)

**구성:**
```
[사용자 브라우저]
   ↓ HTTP/HTTPS 요청 (포트 80/443)
[Nginx] ← 공개 포트 (외부에서 접근 가능)
   ├─ 정적 파일 직접 서빙 (React 빌드, uploads/)
   └─ API 요청 → [Gunicorn:8000] ← 내부 포트 (외부에서 직접 접근 불가)
```

**Nginx 설정 파일 예시:**
```nginx
# nginx/genminute.conf
server {
    listen 80;  # HTTP 포트
    server_name yourdomain.com;
    
    # 정적 파일 직접 서빙 (React 빌드 파일)
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;  # SPA 라우팅 지원
    }
    
    # 업로드 파일 서빙
    location /uploads/ {
        alias /path/to/uploads/;
    }
    
    # API 요청은 Gunicorn으로 전달
    location /api/ {
        proxy_pass http://127.0.0.1:8000;  # Gunicorn 주소
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # HTTPS로 리다이렉트 (SSL 설정 후)
    # return 301 https://$server_name$request_uri;
}
```

**핵심 포인트:**
- Nginx는 공개 포트(80/443)로 외부 요청 받음
- Gunicorn은 내부 포트(8000)로만 실행 (보안 강화)
- 정적 파일은 Nginx가 직접 서빙 (성능 향상)
- API 요청만 Gunicorn으로 프록시
- `try_files`로 SPA 라우팅 지원 (모든 경로를 `index.html`로)

**학습일:** 2026-01-13

---

### 3. Systemd 서비스 관리

**목적:** Linux 시스템에서 서비스(Gunicorn 등)를 자동 시작, 재시작, 로그 관리하는 시스템 서비스 관리자.

**비유:** Systemd = 자동차의 자동 시동 시스템
- 컴퓨터 부팅 = 시동
- 서비스 시작 = 엔진 시작
- 서비스 죽음 = 엔진 멈춤 → 자동 재시작

**역할:**
1. 자동 시작: 컴퓨터 켜질 때 Gunicorn 자동 실행
2. 자동 재시작: Gunicorn이 죽으면 자동으로 재시작
3. 로그 관리: 서비스 로그를 시스템 로그에 저장
4. 상태 관리: 서비스 시작/중지/재시작 명령 제공

**Systemd 서비스 파일:**
```ini
# systemd/genminute.service
[Unit]
Description=GenMinute Flask Application
After=network.target  # 네트워크 시작 후 실행

[Service]
Type=notify
User=www-data  # 실행 사용자
WorkingDirectory=/path/to/genminute  # 작업 디렉토리
Environment="PATH=/path/to/venv/bin"  # 가상환경 경로
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always  # 항상 재시작
RestartSec=10   # 재시작 전 대기 시간 (초)

[Install]
WantedBy=multi-user.target  # 멀티유저 모드에서 시작
```

**사용 방법:**
```bash
# 서비스 등록
sudo cp systemd/genminute.service /etc/systemd/system/
sudo systemctl daemon-reload

# 서비스 시작
sudo systemctl start genminute

# 자동 시작 설정 (컴퓨터 켜질 때 자동 실행)
sudo systemctl enable genminute

# 서비스 상태 확인
sudo systemctl status genminute

# 서비스 중지
sudo systemctl stop genminute

# 서비스 재시작
sudo systemctl restart genminute

# 로그 확인
sudo journalctl -u genminute -f
```

**Systemd 없이 실행할 때의 문제:**
```bash
# 터미널에서 직접 실행
gunicorn -c gunicorn_config.py wsgi:app

# 문제점:
# ❌ 터미널 닫으면 서비스 중지
# ❌ 컴퓨터 재시작 후 수동으로 다시 실행해야 함
# ❌ 서비스 죽어도 자동 재시작 안 됨
# ❌ 로그 관리 어려움
```

**Systemd 사용 시 장점:**
```bash
# ✅ 터미널 닫아도 계속 실행 (백그라운드)
# ✅ 컴퓨터 재시작 시 자동 시작
# ✅ 서비스 죽으면 자동 재시작
# ✅ 시스템 로그로 통합 관리
# ✅ 서비스 상태 확인/제어 명령 제공
```

**핵심 포인트:**
- Systemd는 Linux 시스템의 서비스 관리자
- 서비스 파일(`.service`)로 서비스 등록
- `systemctl` 명령어로 서비스 제어
- `enable`로 자동 시작 설정
- `journalctl`로 로그 확인
- 프로덕션 환경에서 필수

**학습일:** 2026-01-13

---

### 4. 프로덕션 배포 아키텍처 (Gunicorn + Nginx + Systemd)

**전체 흐름:**

**개발 환경 (현재):**
```
[터미널] → python app.py → [Flask 개발 서버:5000] → [브라우저]
```

**프로덕션 환경 (목표):**
```
[사용자 브라우저]
   ↓ HTTPS (포트 443)
[Nginx:80/443] ← Systemd가 자동 관리
   ├─ 정적 파일 직접 서빙 (React 빌드, uploads/)
   └─ API 요청 → [Gunicorn:8000] ← Systemd가 자동 관리
                        ↓
                   [Flask 앱]
```

**시작 순서:**
1. 컴퓨터 부팅
2. Systemd가 Gunicorn 서비스 자동 시작
3. Nginx 시작 (이미 시스템 서비스)
4. 사용자 접속 → Nginx → Gunicorn → Flask 앱

**각 컴포넌트 역할:**

| 컴포넌트 | 역할 | 포트 | 외부 접근 |
|---------|------|------|----------|
| **Nginx** | 리버스 프록시, 정적 파일 서빙, SSL | 80, 443 | ✅ 가능 |
| **Gunicorn** | WSGI 서버, Flask 앱 실행 | 8000 | ❌ 불가 (내부만) |
| **Systemd** | 서비스 자동 관리 | - | - |

**장점:**
- 자동 시작: 재시작 시 수동 작업 불필요
- 자동 재시작: 문제 발생 시 자동 복구
- 보안: Gunicorn 외부 직접 접근 차단
- 성능: 정적 파일 Nginx 직접 서빙 (Gunicorn보다 빠름)
- 확장성: 여러 Gunicorn 인스턴스로 확장 가능 (로드 밸런싱)

**핵심 포인트:**
- 개발 환경: Flask 개발 서버 직접 사용
- 프로덕션 환경: Gunicorn + Nginx + Systemd 조합
- Nginx는 공개 포트, Gunicorn은 내부 포트
- Systemd로 자동 시작 및 재시작 관리
- 각 컴포넌트의 역할과 포트 이해 중요

**학습일:** 2026-01-13

---

## 🔗 참고 링크

- [Vite TypeScript 설정](https://vitejs.dev/guide/features.html#typescript)
- [React Context API](https://react.dev/learn/passing-data-deeply-with-context)
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Firebase Web 시작하기](https://firebase.google.com/docs/web/setup)
- [Flask-CORS](https://flask-cors.readthedocs.io/)

---

*마지막 업데이트: 2025-12-29 (9차 - 오디오 플레이어 고도화 및 영상 재생 기능 추가)*


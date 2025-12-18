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

## 🔗 참고 링크

- [Vite TypeScript 설정](https://vitejs.dev/guide/features.html#typescript)
- [React Context API](https://react.dev/learn/passing-data-deeply-with-context)
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Firebase Web 시작하기](https://firebase.google.com/docs/web/setup)
- [Flask-CORS](https://flask-cors.readthedocs.io/)

---

*마지막 업데이트: 2025-12-18 (3차)*


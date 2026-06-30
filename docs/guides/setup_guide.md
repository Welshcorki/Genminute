# GenMinute 실행 가이드

이 문서는 GenMinute 프로젝트의 백엔드와 프론트엔드 서버 실행 방법을 안내합니다.

> **원본 위치**: 루트 `SETUP_GUIDE.md` → `docs/guides/setup_guide.md`로 이동

---

## 문제 해결 가이드

### 문제 1: 프론트엔드 서버 실행 오류 (package.json 경로 오류)

**증상:**
```
npm error enoent Could not read package.json: Error: ENOENT: no such file or directory
```

**원인:**
- 프로젝트 루트(`C:\Users\butte\github\Genminute`)에서 `npm run dev`를 실행
- `package.json`은 `frontend` 폴더에 있음

**해결 방법:**

#### 방법 1: frontend 폴더로 이동 후 실행 (권장)

```bash
# 1. 프로젝트 루트에서 frontend 폴더로 이동
cd frontend

# 2. 현재 위치 확인 (Windows)
cd
# 출력: C:\Users\butte\github\Genminute\frontend

# 3. package.json 확인
type package.json
# 또는
dir package.json

# 4. 의존성 설치 (처음 한 번만, node_modules가 없을 때)
npm install

# 5. 개발 서버 실행
npm run dev
```

**예상 출력:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

#### 방법 2: 프로젝트 루트에서 직접 실행 (npm scripts 사용)

프로젝트 루트에 `package.json`을 추가하여 루트에서도 실행 가능하게 할 수 있지만, 현재는 `frontend` 폴더에서 실행하는 것이 권장됩니다.

---

### 문제 2: 백엔드 서버 포트 설정 확인

**현재 상태:**
- 백엔드 서버: `http://localhost:5000` (정상 실행 중)
- 프론트엔드 API URL: `http://localhost:5000` (일치함)
- CORS 설정: `http://localhost:5173` 허용 (일치함)

**포트 설정 확인:**

#### 1. 백엔드 포트 설정

**파일:** `config.py`
```python
PORT: int = int(os.getenv('FLASK_PORT', '5000'))
```

**환경 변수로 변경하려면:**
`.env` 파일에 추가:
```env
FLASK_PORT=5000
```

#### 2. 프론트엔드 API URL 설정

**파일:** `frontend/src/services/api.ts`
```typescript
const API_BASE_URL = 'http://localhost:5000';
```

#### 3. CORS 설정

**파일:** `app.py`
```python
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)
```

**현재 설정 상태:**
- ✅ 백엔드 포트: 5000
- ✅ 프론트엔드 API URL: 5000
- ✅ CORS: 프론트엔드 5173 허용
- ✅ 모든 설정이 일치함

---

## 전체 실행 절차

### 1단계: 백엔드 서버 실행

```bash
# 프로젝트 루트에서
# 가상환경 활성화 확인 (터미널에 (genminute_stt) 표시)

# 의존성 확인
pip list | findstr Flask
pip list | findstr flask-cors

# 없으면 설치
pip install -r requirements.txt

# 서버 실행
python app.py
```

### 2단계: 프론트엔드 서버 실행 (새 터미널)

```bash
# ⚠️ 중요: frontend 폴더로 이동!
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 3단계: 브라우저에서 접속

1. 프론트엔드: `http://localhost:5173`
2. 백엔드 API: `http://localhost:5000`

---

## 참고 문서

- [배포 이슈 분석](deployment_issues.md)
- [비용 예측 보고서](../planning/cost_estimate.md)

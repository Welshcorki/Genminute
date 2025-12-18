# GenMinute 실행 가이드

이 문서는 GenMinute 프로젝트의 백엔드와 프론트엔드 서버 실행 방법을 안내합니다.

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

**포트를 변경하려면:**

만약 백엔드 포트를 다른 번호(예: 5050)로 변경하고 싶다면:

1. `.env` 파일 수정:
   ```env
   FLASK_PORT=5050
   ```

2. `frontend/src/services/api.ts` 수정:
   ```typescript
   const API_BASE_URL = 'http://localhost:5050';
   ```

3. 백엔드 서버 재시작

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

**예상 출력:**
```
🚀 Minute AI 서버 시작
포트: 5000
디버그 모드: False
 * Running on http://127.0.0.1:5000
```

### 2단계: 프론트엔드 서버 실행 (새 터미널)

```bash
# ⚠️ 중요: frontend 폴더로 이동!
cd frontend

# 현재 위치 확인
cd
# 출력이 C:\Users\butte\github\Genminute\frontend 이어야 함

# 의존성 확인 (node_modules 폴더 확인)
dir node_modules

# 없으면 설치
npm install

# 개발 서버 실행
npm run dev
```

**예상 출력:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### 3단계: 브라우저에서 접속

1. 프론트엔드: `http://localhost:5173`
2. 백엔드 API: `http://localhost:5000`

---

## 빠른 진단 명령어

### 프론트엔드 문제 진단

```bash
# 1. 현재 위치 확인
cd
# 출력: C:\Users\butte\github\Genminute\frontend 이어야 함

# 2. package.json 확인
type package.json
# 또는
dir package.json

# 3. node_modules 확인
dir node_modules

# 4. npm 버전 확인
npm --version
```

### 백엔드 문제 진단

```bash
# 1. 가상환경 확인
# 터미널에 (genminute_stt) 표시되어야 함

# 2. Flask 설치 확인
python -c "import flask; print('Flask:', flask.__version__)"

# 3. Flask-CORS 설치 확인
python -c "import flask_cors; print('Flask-CORS 설치됨')"

# 4. 포트 사용 중 확인 (Windows)
netstat -ano | findstr :5000

# 5. Python 경로 확인
python -c "import sys; print(sys.executable)"
```

---

## 문제 해결 체크리스트

### 프론트엔드 실행 오류

- [ ] `cd frontend` 명령어로 폴더 이동했는가?
- [ ] 현재 위치가 `frontend` 폴더인가? (`cd` 명령어로 확인)
- [ ] `frontend/package.json` 파일이 존재하는가?
- [ ] `npm install`을 실행했는가?
- [ ] `node_modules` 폴더가 있는가?
- [ ] 포트 5173이 사용 중이 아닌가?

### 백엔드 포트 설정

- [ ] 백엔드 서버가 포트 5000에서 실행 중인가?
- [ ] `frontend/src/services/api.ts`의 `API_BASE_URL`이 `http://localhost:5000`인가?
- [ ] CORS 설정이 `http://localhost:5173`을 허용하는가?
- [ ] 포트 5000이 다른 프로세스에 의해 사용 중이 아닌가?

---

## 자주 묻는 질문 (FAQ)

### Q1: 프론트엔드를 프로젝트 루트에서 실행할 수 없나요?

**A:** 현재 구조에서는 `frontend` 폴더에서 실행해야 합니다. 루트에서 실행하려면 루트에 `package.json`을 추가하고 스크립트를 설정해야 합니다.

### Q2: 백엔드 포트를 변경하고 싶어요.

**A:** 
1. `.env` 파일에 `FLASK_PORT=원하는포트` 추가
2. `frontend/src/services/api.ts`의 `API_BASE_URL` 수정
3. 서버 재시작

### Q3: 두 서버를 동시에 실행하려면?

**A:** 터미널 2개를 사용하세요:
- 터미널 1: 백엔드 (`python app.py`)
- 터미널 2: 프론트엔드 (`cd frontend && npm run dev`)

### Q4: 포트가 이미 사용 중이라는 오류가 나와요.

**A:**
```bash
# Windows에서 포트 사용 중인 프로세스 확인
netstat -ano | findstr :5000

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID번호> /F
```

---

## 참고사항

- 백엔드 기본 포트: **5000**
- 프론트엔드 기본 포트: **5173** (Vite 기본값)
- API 연결: 프론트엔드(5173) → 백엔드(5000)
- CORS: 백엔드에서 프론트엔드(5173) 허용

---

**마지막 업데이트:** 2025-12-16


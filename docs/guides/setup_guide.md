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

## 로컬 STT 환경 버전 현황 (2026-11-16 기준, `genminute_stt` conda 환경)

프로젝트 작업 이후 시간이 지나며 설치된 패키지가 업데이트되어, `requirements.txt`와 실제 환경 사이에 차이가 생겼습니다.
아래는 `pip list` / `pip check` / import 확인으로 조사한 현재 상태입니다.

| 패키지 | 설치 버전 | `requirements.txt` | 상태 |
|---|---|---|---|
| torch / torchaudio | 2.5.1 | `>=2.0,<3.0` | 일치 |
| faster-whisper | 1.2.0 | `==1.2.0` | 일치 |
| pyannote.audio | 3.3.1 | `>=3.1,<4.0` | 일치 |
| huggingface_hub | **1.7.1** | `<0.20` | **불일치** — 아래 1번 |
| transformers | **5.3.0** | (선택 패키지) | **불일치** — 아래 2번 |
| optimum-intel | 1.26.1 | (선택 패키지) | transformers `>=4.45,<4.56` 요구 |
| openvino | 2025.4.0 | (선택 패키지) | — |
| langgraph | 1.2.22 | `>=1.0,<2.0` | 일치 (2026-11-16 업데이트) |
| langchain / langchain-core | 1.5.0 / 1.8.1 | `>=0.2.0` | 일치 (2026-11-16 업데이트) |
| langchain-classic | 1.0.8 | `>=1.0,<2.0` | 일치 (2026-11-16 업데이트) |

### 1. huggingface_hub 1.x ↔ pyannote.audio 3.x

- `services/diarization.py`는 `huggingface_hub.login`으로 인증한 뒤 `pyannote.audio`의 `Pipeline.from_pretrained`를 호출합니다.
- pyannote.audio 3.3.1은 내부에서 `hf_hub_download(use_auth_token=...)`를 호출하는데, 이 인자는 huggingface_hub 1.0에서 제거되었습니다.
- 따라서 현재 환경(1.7.1)에서는 **화자 분리 모델 로드가 실패할 가능성이 높습니다** (코드 확인 기준, 실제 실행은 미검증).
- 해결 방향(택1, 미적용): ① `pip install "huggingface_hub<1.0"`로 낮춤(다른 패키지 요구 버전 확인 필요) ② pyannote.audio 4.x로 올리고 `requirements.txt` 상한 조정(코드 변경 가능성 있음).

### 2. transformers 5.x ↔ optimum-intel 1.26.x (Intel OpenVINO 가속)

- optimum-intel 1.26.1은 transformers `>=4.45,<4.56`만 지원합니다. 설치된 5.3.0에서는 `import optimum.intel.openvino`가 `No module named 'transformers.onnx'`로 실패합니다.
- `STT_BACKEND=auto`일 때 import 실패는 자동으로 faster-whisper 백엔드로 폴백되므로 앱은 동작합니다(현재 감지 결과: `faster_whisper`, CPU).
- 즉 **현재 환경에서는 OpenVINO 가속이 사용되지 않습니다.** 다시 쓰려면 transformers를 4.55.x로 낮추거나 optimum-intel을 transformers 5.x 지원 버전으로 올려야 합니다(미검증).

### 확인 명령

```bash
pip check                                   # 버전 충돌 목록
pip list | findstr /i "huggingface transformers optimum pyannote torch"
```

---

## 참고 문서

- [배포 이슈 분석](deployment_issues.md)
- [비용 예측 보고서](../planning/cost_estimate.md)

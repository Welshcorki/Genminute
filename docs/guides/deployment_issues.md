# 배포 시 발생 가능한 문제점 분석

분석일: 2025-01-26
프로젝트: GenMinute (Flask + React)

> **원본 위치**: 루트 `DEPLOYMENT_ISSUES.md` → `docs/guides/deployment_issues.md`로 이동

---

## 🔴 심각 (Critical) - 즉시 수정 필요

### 1. CORS 설정 하드코딩
**위치**: `app.py:34`
```python
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)
```
**문제점**: 
- 개발 환경(localhost:5173)만 허용하도록 하드코딩됨
- 프로덕션 도메인에서 API 요청 시 CORS 에러 발생

**해결 방안**: 환경 변수로 허용 오리진 관리
```python
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)
```

---

### 2. 프론트엔드 API URL 하드코딩
**위치**: `frontend/src/services/api.ts:5`
```typescript
const API_BASE_URL = 'http://localhost:5000';
```
**문제점**: 
- 개발 환경 URL이 하드코딩되어 빌드 시 변경 불가
- 프로덕션 환경에서 백엔드 서버에 연결할 수 없음

**해결 방안**: 
- Vite 환경 변수 사용 (`import.meta.env.VITE_API_BASE_URL`)
- 빌드 시 환경 변수 주입
- `vite.config.ts`에 base URL 설정 추가

---

### 3. React 빌드 파일 서빙 미구현
**위치**: `app.py`, `routes/`
**문제점**: 
- Flask가 React 빌드 파일(`frontend/dist/`)을 서빙하는 라우트가 없음
- 현재는 `templates/` 폴더의 HTML만 서빙
- React SPA 라우팅이 작동하지 않을 것

**해결 방안**: (이미 적용됨 - config.py에 FRONTEND_BUILD_DIR, app.py에 serve_react_app 라우트 추가됨)

---

### 4. Firebase Admin SDK 파일 배포 방법 불명확
**위치**: `services/firebase_service.py:27`
**문제점**: 
- `firebase-adminsdk.json` 파일이 `.gitignore`에 포함되어 Git에 커밋되지 않음
- 배포 환경에 파일을 전달하는 방법이 문서화되지 않음
- 환경 변수로 관리하는 방식이 없음

**해결 방안**: 
- 환경 변수로 Firebase 인증 정보 관리 (권장)
- 또는 배포 시 파일 복사 스크립트 제공
- Docker secrets/Kubernetes secrets 활용

---

## 🟡 중요 (High) - 배포 전 수정 권장

### 5. 환경 변수 파일(.env) 배포 방법 부재
**위치**: `config.py:12-13`
**문제점**: `.env` 파일이 `.gitignore`에 포함되어 Git에 커밋되지 않음
**해결 방안**: `.env.example` 파일 생성 및 문서화

### 6. 프로덕션 WSGI 서버 설정 부재
**위치**: `app.py:128-133`
**해결 방안**: `gunicorn_config.py`, `wsgi.py` 생성

### 7. 데이터베이스 경로 및 마이그레이션
**해결 방안**: 환경 변수로 경로 설정, Alembic 등 마이그레이션 스크립트 작성

### 8. 의존성 버전 고정 부족
**해결 방안**: `pip freeze > requirements.txt`로 현재 환경 고정

### 9. 프론트엔드 빌드 설정 미흡
**해결 방안**: Vite 빌드 최적화, 환경 변수 주입 설정

### 10. 로깅 설정 프로덕션 최적화 부족
**해결 방안**: `RotatingFileHandler` 설정, 환경별 로그 레벨

---

## 🟢 개선 권장 (Medium)

### 11. Docker/Docker Compose 부재
### 12. 헬스 체크 엔드포인트 부재 (이미 적용됨 - routes/health.py)
### 13. 정적 파일 경로 하드코딩
### 14. 세션 저장소 설정
### 15. 파일 크기 제한

---

## 📋 체크리스트

배포 전 확인 사항: CORS, API URL, React 서빙, Firebase, .env.example, Gunicorn, DB 경로, requirements 버전, Vite, 로깅, Docker, 헬스 체크, 배포 가이드

---

## 🔧 권장 배포 아키텍처

- **옵션 1**: Nginx → Gunicorn → Flask
- **옵션 2**: Docker Container
- **옵션 3**: Heroku, AWS, GCP, Azure

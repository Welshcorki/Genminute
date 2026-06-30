# Phase 3: Firebase → Supabase Auth 전환 개발 일지

## 2026년 4월 11일 - Auth 전환 작업 시작

### 1. 목표
- Firebase Auth + Admin SDK → Supabase Auth (Google OAuth) 전환
- 프론트엔드 4개 파일 + 백엔드 4개 파일 변경

### 2. 사전 준비 (완료)
- ✅ Supabase 프로젝트 생성
- ✅ Google OAuth 설정 (Google Cloud Console + Supabase Provider)
- ✅ `.env`에 Supabase 키 입력 (URL, Anon Key, Service Role Key)

### 3. 패키지 변경
- ✅ npm: `firebase` 제거 → `@supabase/supabase-js` 설치
- ✅ pip: `supabase` 설치 (PyJWT는 기존 설치됨, firebase-admin은 이후 제거)

### 4. 코드 변경 (진행 중)

#### 프론트엔드
- [x] `firebase.ts` → `supabase.ts` 교체
- [x] `AuthContext.tsx` 수정
- [x] `Login.tsx` 수정
- [x] `auth.ts` 수정

#### 백엔드
- [x] `firebase_service.py` → `supabase_service.py` 교체
- [x] `auth.py` 수정
- [x] `app.py` 수정
- [x] `config.py` 수정

---

## 2026년 4월 24일 - Firebase 잔존 코드 정리 완료

### 5. Firebase 파일 삭제
- [x] `frontend/src/config/firebase.ts` 삭제
- [x] `services/firebase_service.py` 삭제
- [x] `firebase-adminsdk.json` 삭제 (보안)

### 6. config.py 정리
- [x] `validate()` — `SUPABASE_SERVICE_ROLE_KEY` 추가, `HF_TOKEN`/`GOOGLE_CLIENT_ID/SECRET` 조건부 검증으로 변경
- [x] `print_config_status()` — Firebase → Supabase 상태 출력으로 교체
- [x] `GOOGLE_PROJECT_ID` 추가 (캘린더 OAuth 선택 필드)

### 7. google_auth.py 리팩토링 (옵션 B)
- [x] 로그인 관련 코드(`/google/login`, 세션 생성) 제거
- [x] 캘린더 연동(`/google/calendar/authorize`, `/oauth2callback`) 전용으로 유지
- [x] `FIREBASE_PROJECT_ID` → `config.GOOGLE_PROJECT_ID`로 교체

### 8. App.tsx — /auth/callback 라우트 추가
- [x] Supabase OAuth 리다이렉트 수신 경로 등록

### 9. .env.example 업데이트
- [x] Firebase 섹션 제거
- [x] Supabase 섹션 활성화 (주석 해제)
- [x] `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` 프론트엔드 섹션 추가
- [x] `GOOGLE_PROJECT_ID` 추가

### 10. requirements.txt 정리
- [x] `firebase-admin` 제거 → `supabase>=2.0,<3.0` 추가

### 주요 결정 사항
- `google_auth.py` 옵션 B 채택: 구글 캘린더 연동은 향후 기능으로 유지
- `validate()` 조건부 검증: STT_ENGINE=local일 때만 HF_TOKEN 필수
- `supabase` Python SDK는 `genminute_stt` conda 환경에 이미 설치됨

---

## Phase 3-2: 향후 작업
- [ ] **DB 전환**: SQLite → Supabase PostgreSQL
- [ ] **캘린더 연동 UI**: 프론트엔드에서 `/google/calendar/authorize` 호출 버튼 추가
- [x] **통합 테스트**: Google OAuth 로그인 → `/auth/callback` → 메인 페이지 E2E 검증 (2026-04-25 완료)


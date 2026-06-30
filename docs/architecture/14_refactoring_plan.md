# 리팩토링 설계서: 클린 아키텍처 적용

> **최종 수정**: 2026-02-26
> **상태**: **실행 완료** (2026-02-26)
> **선택지 A 확정**: DB 전환(SQLite → 관계형 DB) 확정에 따라 Repository 추상화 포함

## 1. 현재 상태 (As-Is)

### 1.1 문제점 요약

| 문제 | 위치 | 심각도 |
|------|------|--------|
| God Object: DatabaseManager 1106줄 | `database/sqlite_manager.py` | CRITICAL |
| 절차적 함수 나열, DI 없음 | `services/user_service.py` | HIGH |
| Service Locator 안티패턴 (`_get_db()`) | `user_service.py`, `analysis_service.py` | HIGH |
| Route에 비즈니스 로직 잔존 | `routes/meetings.py` 등 | HIGH |
| try/except 보일러플레이트 반복 | 모든 route 파일 | MEDIUM |
| 타입 힌팅 누락 | DatabaseManager 일부 메서드 | MEDIUM |
| SQLite 직접 결합 | 모든 DB 접근 코드 | HIGH (배포 시 전환 필요) |

### 1.2 현재 의존성 흐름

```
Route (Flask Blueprint)
  ├─ 직접 DatabaseManager 싱글톤 생성
  ├─ 직접 Service 함수/클래스 호출
  └─ 비즈니스 로직 인라인 (데이터 변환 등)

Service (함수 모듈 or 클래스)
  ├─ _get_db()로 DatabaseManager 접근 (Service Locator)
  ├─ 직접 db._get_connection() 호출
  └─ 다른 Service 직접 import

DatabaseManager (God Object)
  └─ 6개 테이블의 모든 CRUD를 단일 클래스에서 처리
  └─ SQLite에 직접 결합 (sqlite3.connect)
```

## 2. 목표 상태 (To-Be)

### 2.1 레이어드 아키텍처

```
Route (Thin Controller)
  └─ 입력 검증 + Service 호출 + 응답 변환만 담당

Service (비즈니스 로직)
  └─ 생성자 주입으로 Repository 인터페이스에 의존
  └─ 도메인 로직만 담당
  └─ 구체적인 DB 구현을 알지 못함

Repository Interface (ABC 추상 클래스)
  └─ 도메인별 CRUD 계약 정의

Repository Implementation (SQLite 구현체)
  └─ 인터페이스를 구현한 SQLite 전용 코드
  └─ 나중에 PostgreSQL 구현체를 추가하면 교체 가능
```

**핵심 원칙: 의존성 역전 (DIP)**
- Service는 구체 클래스가 아닌 **인터페이스(ABC)**에 의존
- 어떤 DB를 쓰는지는 app.py의 DI 조립 코드에서만 결정

### 2.2 Repository 추상화 + 구현 분리

#### 2.2.1 인터페이스 (ABC)

각 도메인별로 추상 클래스를 정의합니다:

```python
# database/repositories/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

class MeetingRepositoryInterface(ABC):
    @abstractmethod
    def save_stt_to_db(self, segments: list, audio_filename: str,
                       title: str, meeting_date: str, owner_id: int) -> str: ...
    @abstractmethod
    def get_meeting_by_id(self, meeting_id: str) -> list: ...
    @abstractmethod
    def get_segments_by_meeting_id(self, meeting_id: str) -> list: ...
    # ... 기타 메서드
```

#### 2.2.2 SQLite 구현체

```python
# database/repositories/sqlite/meeting_repo.py
from database.repositories.interfaces import MeetingRepositoryInterface

class SqliteMeetingRepository(MeetingRepositoryInterface):
    def __init__(self, db_path: str):
        self._db_path = db_path

    def save_stt_to_db(self, segments, audio_filename, title, meeting_date, owner_id):
        conn = sqlite3.connect(self._db_path)
        # ... SQLite 전용 구현
```

#### 2.2.3 도메인별 분리

| 인터페이스 | SQLite 구현체 | 테이블 | 메서드 수 |
|-----------|--------------|--------|----------|
| `MeetingRepositoryInterface` | `SqliteMeetingRepository` | meeting_dialogues | 9 |
| `MinutesRepositoryInterface` | `SqliteMinutesRepository` | meeting_minutes | 2 |
| `MindmapRepositoryInterface` | `SqliteMindmapRepository` | meeting_mindmap | 3 |
| `ActionItemRepositoryInterface` | `SqliteActionItemRepository` | meeting_action_items | 5 |
| `UserRepositoryInterface` | `SqliteUserRepository` | users, meeting_shares | 3 |

공통 기반:

| 클래스 | 역할 |
|--------|------|
| `SqliteConnection` | SQLite 연결 관리 (`_get_connection`), 테이블 초기화 |

### 2.3 Service 클래스화 계획

Service는 **인터페이스에만 의존**합니다:

| 현재 | 변경 후 | 주입 의존성 (인터페이스) |
|------|---------|----------------------|
| `user_service.py` (함수들) | `UserService` 클래스 | `UserRepositoryInterface`, `MeetingRepositoryInterface` |
| `analysis_service.py` (함수) | `AnalysisService` 클래스 | `MeetingRepositoryInterface` |
| `upload_service.py` (클래스, DI 없음) | `UploadService` (DI 적용) | `MeetingRepositoryInterface`, `VectorDBManager`, `AgentService` |

```python
# 예시: Service는 인터페이스에만 의존
class UserService:
    def __init__(self,
                 user_repo: UserRepositoryInterface,
                 meeting_repo: MeetingRepositoryInterface):
        self._user_repo = user_repo
        self._meeting_repo = meeting_repo
```

### 2.4 공통 에러 핸들러

```python
# utils/decorators.py에 추가
def api_error_handler(f):
    """Route 핸들러의 공통 예외 처리 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except PermissionError as e:
            return jsonify({"success": False, "error": str(e)}), 403
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except FileNotFoundError as e:
            return jsonify({"success": False, "error": str(e)}), 404
        except Exception as e:
            logger.error(f"API 오류: {e}", exc_info=True)
            return jsonify({"success": False, "error": "서버 내부 오류"}), 500
    return decorated
```

### 2.5 의존성 주입 (DI) 패턴

Flask에 별도 DI 프레임워크 없이 `app.py`에서 조립합니다.
**DB 구현체를 교체하려면 이 파일만 수정하면 됩니다.**

```python
# app.py 초기화 (SQLite 사용 시)
from database.repositories.sqlite.meeting_repo import SqliteMeetingRepository
from database.repositories.sqlite.minutes_repo import SqliteMinutesRepository
# ...

db_path = str(config.DATABASE_PATH)
meeting_repo = SqliteMeetingRepository(db_path)
minutes_repo = SqliteMinutesRepository(db_path)
mindmap_repo = SqliteMindmapRepository(db_path)
action_item_repo = SqliteActionItemRepository(db_path)
user_repo = SqliteUserRepository(db_path)

user_service = UserService(user_repo, meeting_repo)
analysis_service = AnalysisService(meeting_repo)

# Flask app.config에 등록하여 route에서 접근
app.config['meeting_repo'] = meeting_repo
app.config['user_service'] = user_service
# ...
```

나중에 PostgreSQL로 전환 시:

```python
# app.py만 변경 (Service, Route 코드 변경 없음)
from database.repositories.postgres.meeting_repo import PostgresMeetingRepository
# ...

db_url = config.DATABASE_URL  # PostgreSQL 연결 문자열
meeting_repo = PostgresMeetingRepository(db_url)
# ... 나머지 동일
```

## 3. 파일 변경 계획

### 3.1 새로 생성

```
database/
  repositories/
    __init__.py
    interfaces.py                    # ABC 인터페이스 정의 (5개 인터페이스)
    sqlite/
      __init__.py
      connection.py                  # SqliteConnection (연결 관리, 테이블 초기화)
      meeting_repo.py                # SqliteMeetingRepository
      minutes_repo.py                # SqliteMinutesRepository
      mindmap_repo.py                # SqliteMindmapRepository
      action_item_repo.py            # SqliteActionItemRepository
      user_repo.py                   # SqliteUserRepository

services/
  meeting_service.py                 # 회의 데이터 조회 비즈니스 로직 (Route에서 분리)

tests/
  __init__.py
  test_repositories.py               # Repository 단위 테스트 (in-memory SQLite)
  test_services.py                   # Service 단위 테스트 (mock Repository)
```

### 3.2 수정

| 파일 | 변경 내용 |
|------|----------|
| `database/sqlite_manager.py` | Facade로 유지 (하위 호환), 내부는 SQLite Repository에 위임 |
| `services/user_service.py` | `UserService` 클래스로 변경, 인터페이스 DI |
| `services/analysis_service.py` | `AnalysisService` 클래스로 변경, 인터페이스 DI |
| `services/upload_service.py` | DI 적용 (생성자에서 인터페이스 주입) |
| `routes/*.py` | 비즈니스 로직 제거, `app.config`에서 Service 가져와 호출 |
| `utils/decorators.py` | `api_error_handler` 데코레이터 추가 |
| `app.py` | DI 조립 코드 추가 (구현체 선택 지점) |

### 3.3 하위 호환성 전략

**기존 `DatabaseManager`를 Facade로 유지**하여 아직 리팩토링되지 않은 코드가 깨지지 않게 합니다:

```python
class DatabaseManager:
    """하위 호환 Facade - 점진적 마이그레이션 완료 후 제거 예정"""
    def __init__(self, db_path: str = None):
        self._db_path = db_path
        self.meetings = SqliteMeetingRepository(db_path)
        self.minutes = SqliteMinutesRepository(db_path)
        self.mindmaps = SqliteMindmapRepository(db_path)
        self.action_items = SqliteActionItemRepository(db_path)
        self.users = SqliteUserRepository(db_path)

    # 기존 메서드를 위임으로 유지
    def save_stt_to_db(self, *args, **kwargs):
        return self.meetings.save_stt_to_db(*args, **kwargs)

    def get_meeting_by_id(self, meeting_id):
        return self.meetings.get_meeting_by_id(meeting_id)
    # ...
```

## 4. 작업 순서

1. `database/repositories/interfaces.py` - ABC 인터페이스 정의
2. `database/repositories/sqlite/connection.py` - SQLite 연결 관리
3. `database/repositories/sqlite/*.py` - 5개 SQLite Repository 구현
4. `database/sqlite_manager.py` - Facade로 리팩토링 (하위 호환 유지)
5. `utils/decorators.py` - `api_error_handler` 데코레이터 추가
6. Service 클래스화 + DI 적용 (`user_service`, `analysis_service`, `upload_service`)
7. `services/meeting_service.py` - Route에서 비즈니스 로직 추출
8. Route 핸들러 thin controller화
9. `app.py` - DI 조립 코드 추가
10. 테스트 코드 작성
11. `docs/development/dev_log.md` 작업 기록

## 5. DB 전환 시 영향 범위

| 계층 | 전환 시 변경 필요 | 이유 |
|------|------------------|------|
| Route | **없음** | Service 인터페이스만 호출 |
| Service | **없음** | Repository 인터페이스에만 의존 |
| Repository Interface | **없음** | ABC는 DB 독립적 |
| Repository Implementation | **새로 추가** | `database/repositories/postgres/` 폴더 추가 |
| app.py | **1줄씩 변경** | import와 생성자만 교체 |
| 테스트 | **새로 추가** | PostgreSQL 통합 테스트 추가 |

## 6. 리스크

- **하위 호환성**: DatabaseManager Facade 패턴으로 기존 import문이 깨지지 않음
- **순환 의존성**: Service 간 import 순환 주의 (UserService ↔ MeetingService)
- **테스트**: SQLite in-memory로 Repository 테스트, Service는 mock으로 테스트
- **마이그레이션 기간**: Facade가 존재하는 동안 두 가지 경로가 공존하므로, Facade 제거 시점을 명확히 정할 것

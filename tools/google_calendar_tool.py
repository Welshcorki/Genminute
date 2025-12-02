import datetime
import json
from typing import Optional

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.db_manager import DatabaseManager
from config import config

# 데이터베이스 매니저 초기화
db = DatabaseManager(str(config.DATABASE_PATH))

# --- Pydantic 모델 정의 ---
class CalendarEvent(BaseModel):
    """Google Calendar에 이벤트를 추가하기 위한 데이터 모델"""
    summary: str = Field(description="이벤트의 제목 또는 요약. (예: '팀 회의')")
    start_time: datetime.datetime = Field(description="이벤트 시작 시간. ISO 8601 형식. (예: '2025-12-25T10:00:00')")
    end_time: Optional[datetime.datetime] = Field(description="이벤트 종료 시간. ISO 8601 형식. 지정하지 않으면 시작 시간으로부터 1시간으로 자동 설정됩니다.")
    location: Optional[str] = Field(description="이벤트가 열리는 장소. (예: '온라인' 또는 '3층 회의실')")
    description: Optional[str] = Field(description="이벤트에 대한 상세 설명. Action Item의 출처나 관련 링크를 포함할 수 있습니다.")

# --- LangChain 도구 정의 ---

@tool(args_schema=CalendarEvent)
def add_calendar_event(
    summary: str, 
    start_time: datetime.datetime, 
    end_time: Optional[datetime.datetime] = None, 
    location: Optional[str] = None, 
    description: Optional[str] = None,
    user_id: Optional[int] = None  # 실제 로직에서 사용할 user_id, LLM은 이 인자를 채우지 않음
) -> str:
    """
    사용자의 Google Calendar에 새로운 이벤트를 추가합니다.
    성공적으로 호출되면, 생성된 이벤트의 상세 정보를 포함한 확인 메시지를 반환합니다.
    사용자의 인증 정보(user_id)가 없으면, 인증이 필요하다는 메시지를 반환합니다.
    """
    if user_id is None:
        return "오류: 사용자를 식별할 수 없어 캘린더에 접근할 수 없습니다."

    # 1. DB에서 사용자 인증 정보 조회
    credentials_json = db.get_user_google_credentials(user_id)
    if not credentials_json:
        return f"오류: 사용자가 Google Calendar 연동을 하지 않았습니다. 먼저 'Google Calendar 연동' 버튼을 눌러 인증을 완료해주세요."

    try:
        # 2. 인증 정보 객체 생성
        creds_data = json.loads(credentials_json)
        credentials = google.oauth2.credentials.Credentials(**creds_data)

        # 3. Google Calendar API 서비스 빌드
        service = build('calendar', 'v3', credentials=credentials)

        # 종료 시간이 지정되지 않은 경우, 시작 시간으로부터 1시간 뒤로 설정
        if end_time is None:
            end_time = start_time + datetime.timedelta(hours=1)

        # 4. API에 전달할 이벤트 객체 생성
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
        }

        # 5. API 호출하여 이벤트 생성
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        event_url = created_event.get('htmlLink')

        print(f"✅ Google Calendar 이벤트 생성 성공: {event_url}")
        
        return f"성공: '{summary}' 일정이 Google Calendar에 추가되었습니다. 링크: {event_url}"

    except HttpError as error:
        print(f"❌ Google Calendar API 오류 발생: {error}")
        return f"오류: Google Calendar API 호출에 실패했습니다. 에러: {error}"
    except Exception as e:
        print(f"❌ 일정 추가 중 예외 발생: {e}")
        return f"오류: 일정을 추가하는 중 알 수 없는 오류가 발생했습니다. 에러: {e}"


if __name__ == '__main__':
    # 도구가 올바르게 정의되었는지 테스트
    print("--- 도구 스키마 정보 ---")
    print(add_calendar_event.name)
    print(add_calendar_event.description)
    # LLM이 보는 인자 스키마에는 user_id가 포함되지 않음
    print(add_calendar_event.args)

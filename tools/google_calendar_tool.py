import datetime
from typing import Optional
from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

# --- Pydantic 모델 정의 ---
# Pydantic V1을 사용하는 이유는 LangChain의 @tool 데코레이터가 V1 모델과 더 안정적으로 호환되기 때문입니다.

class CalendarEvent(BaseModel):
    """Google Calendar에 이벤트를 추가하기 위한 데이터 모델"""
    summary: str = Field(description="이벤트의 제목 또는 요약. (예: '팀 회의')")
    start_time: datetime.datetime = Field(description="이벤트 시작 시간. ISO 8601 형식. (예: '2025-12-25T10:00:00')")
    end_time: Optional[datetime.datetime] = Field(description="이벤트 종료 시간. ISO 8601 형식. 지정하지 않으면 시작 시간으로부터 1시간으로 자동 설정됩니다.")
    location: Optional[str] = Field(description="이벤트가 열리는 장소. (예: '온라인' 또는 '3층 회의실')")
    description: Optional[str] = Field(description="이벤트에 대한 상세 설명. Action Item의 출처나 관련 링크를 포함할 수 있습니다.")

# --- LangChain 도구 정의 ---

@tool(args_schema=CalendarEvent)
def add_calendar_event(summary: str, start_time: datetime.datetime, end_time: Optional[datetime.datetime] = None, location: Optional[str] = None, description: Optional[str] = None) -> str:
    """
    사용자의 Google Calendar에 새로운 이벤트를 추가합니다.
    
    이 함수는 실제 Google Calendar API를 호출하는 것을 시뮬레이션합니다.
    성공적으로 호출되면, 생성된 이벤트의 상세 정보를 포함한 확인 메시지를 반환합니다.
    """
    
    # 종료 시간이 지정되지 않은 경우, 시작 시간으로부터 1시간 뒤로 설정
    if end_time is None:
        end_time = start_time + datetime.timedelta(hours=1)

    # --- 실제 Google Calendar API 연동 로직이 들어갈 부분 ---
    # 1. 사용자 인증 정보(credentials) 획득 (OAuth 2.0)
    # 2. googleapiclient.discovery.build('calendar', 'v3', credentials=creds) 서비스 객체 생성
    # 3. event = {'summary': summary, 'start': {'dateTime': ...}, ...} 딕셔너리 생성
    # 4. service.events().insert(calendarId='primary', body=event).execute() API 호출
    # ---------------------------------------------------------

    # 여기서는 API 호출을 시뮬레이션하고, 어떤 인자로 호출되었는지 출력합니다.
    print("\n[--- Google Calendar Tool Called ---]")
    print(f"  Summary: {summary}")
    print(f"  Start Time: {start_time.isoformat()}")
    print(f"  End Time: {end_time.isoformat()}")
    print(f"  Location: {location or '미지정'}")
    print(f"  Description: {description or '없음'}")
    print("[---------------------------------]")
    
    return f"성공: '{summary}' 일정이 {start_time.strftime('%Y년 %m월 %d일 %H:%M')}에 Google Calendar에 추가되었습니다."


if __name__ == '__main__':
    # 도구가 올바르게 정의되었는지 테스트
    print("--- 도구 스키마 정보 ---")
    print(add_calendar_event.name)
    print(add_calendar_event.description)
    print(add_calendar_event.args)

    # Pydantic 모델을 사용한 가상 호출 테스트
    print("\n--- 가상 호출 테스트 ---")
    event_data = {
        "summary": "LangGraph 스터디",
        "start_time": datetime.datetime(2025, 1, 1, 14, 0, 0),
        "description": "LangGraph의 기본 개념과 상태 관리 방법에 대해 논의"
    }
    
    # Pydantic 모델로 데이터 유효성 검사
    validated_event = CalendarEvent(**event_data)
    
    # 도구 실행
    result = add_calendar_event.invoke(validated_event.dict())
    print(f"호출 결과: {result}")
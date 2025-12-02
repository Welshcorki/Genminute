import os
import sys
import datetime
from typing import List, TypedDict, Annotated, Dict

# 프로젝트 루트 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from tools.google_calendar_tool import add_calendar_event, CalendarEvent

# --- 1. 상태 정의 (State Definition) ---
class AgentState(TypedDict):
    """
    그래프의 상태를 정의합니다. 각 노드는 이 상태를 읽고 수정합니다.
    """
    original_text: str  # 원본 회의록 텍스트
    current_date: str   # 추론의 기준이 될 현재 날짜
    messages: Annotated[List[BaseMessage], lambda x, y: x + y] # LLM과의 대화 기록
    
    # 추출된 Action Item들을 저장 (Pydantic 모델을 dict로 변환하여 저장)
    extracted_items: List[Dict]
    
    # 처리 완료된 Action Item들을 저장
    processed_items: List[Dict]
    
    # 이 워크플로우를 시작한 사용자의 ID
    user_id: int


# --- 2. 노드 정의 (Node Definition) ---

class AgentService:
    def __init__(self):
        load_dotenv()
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")
        
        # LLM과 Tool 정의
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        self.tools = [add_calendar_event]
        self.llm_with_tools = self.llm.bind_tools(self.tools, tool_choice="any")
        
        # 그래프 생성 및 컴파일
        self.graph = self.build_graph()
        
        # 메모리(체크포인트) 설정: 각 실행 상태를 DB에 저장하여 복원 가능
        self.memory = MemorySaver() # 인메모리 DB 사용, 파일로 변경 가능

        self.app = self.graph.compile(checkpointer=self.memory)

    def build_graph(self):
        """
        LangGraph 상태 머신을 정의하고 빌드합니다.
        """
        graph = StateGraph(AgentState)

        # 노드 추가
        graph.add_node("extract_and_schedule", self.extract_and_schedule_node)
        
        # 시작점 설정
        graph.set_entry_point("extract_and_schedule")
        
        # 모든 노드는 작업 완료 후 종료(END)
        graph.add_edge("extract_and_schedule", END)

        return graph

    def extract_and_schedule_node(self, state: AgentState):
        """
        회의록을 분석하여 Action Item을 추출하고, 관련 도구를 호출하여 처리하는 메인 노드
        """
        messages = state['messages']
        
        # LLM을 호출하여 Action Item을 분석하고 도구 사용 결정
        ai_message = self.llm_with_tools.invoke(messages)
        
        # LLM의 응답을 대화 기록에 추가
        new_messages = messages + [ai_message]
        
        # LLM이 도구를 사용하기로 결정했다면, tool_calls에 정보가 담김
        if ai_message.tool_calls:
            # LLM이 요청한 모든 도구 호출을 순회하며 처리
            processed_in_this_turn = []
            for tool_call in ai_message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']

                print(f"\n>>> LLM decided to call the tool: `{tool_name}` with args: {tool_args}")

                # 실제 도구 실행
                if tool_name == "add_calendar_event":
                    try:
                        # Pydantic 모델로 인자 유효성 검사
                        event = CalendarEvent(**tool_args)
                        
                        # user_id를 포함하여 실제 도구 호출
                        tool_kwargs = event.dict()
                        tool_kwargs['user_id'] = state['user_id']
                        add_calendar_event.invoke(tool_kwargs)
                        
                        # 처리된 아이템을 임시 리스트에 추가
                        processed_in_this_turn.append(event.dict())

                    except Exception as e:
                        print(f"Error calling tool {tool_name} with args {tool_args}: {e}")
                        # 개별 도구 호출 실패가 전체를 중단시키지 않도록 처리
            
            # 이번 턴에 처리된 모든 아이템을 기존 상태에 추가하여 반환
            return {"messages": new_messages, "processed_items": state.get('processed_items', []) + processed_in_this_turn}
        
        # 도구를 사용하지 않은 경우, 단순 메시지만 업데이트
        return {"messages": new_messages}

    def process(self, meeting_text: str, user_id: int):
        """
        주어진 회의록 텍스트에 대해 Action Item 추출 및 처리를 시작합니다.
        """
        current_date = datetime.datetime.now().strftime("%Y년 %m월 %d일")
        
        prompt = f"""
너는 회의록을 분석하여 Action Item을 찾아내고, 주어진 도구를 사용하여 해당 작업을 처리하는 AI 비서야.
현재 날짜는 {current_date}이야. 이 날짜를 기준으로 모든 상대적인 날짜(예: '다음 주 수요일')를 정확한 날짜로 계산해야 해.

아래 회의록 텍스트를 분석해서, 모든 Action Item을 찾고, 각 Action Item에 대해 'add_calendar_event' 도구를 호출하여 일정을 등록해줘.
하나의 Action Item 당 하나의 도구를 호출해야 해.

회의록:
---
{meeting_text}
---
"""
        
        initial_state = {
            "original_text": meeting_text,
            "current_date": current_date,
            "messages": [HumanMessage(content=prompt)],
            "extracted_items": [],
            "processed_items": [],
            "user_id": user_id
        }
        
        # 그래프 실행
        # config는 실행을 고유하게 식별하는 ID. 동일 ID로 재실행 시 이전 상태에서 이어감.
        config = {"configurable": {"thread_id": "meeting-123"}}
        final_state = self.app.invoke(initial_state, config=config)
        
        return final_state


# --- 테스트 실행 ---
if __name__ == '__main__':
    sample_minutes = """
    # 2025년 1분기 마케팅 전략 회의

    ## 논의 내용
    - 김민준 팀장: 새로운 소셜 미디어 캠페인 '프로젝트 썬라이즈'를 제안합니다. 예산안 검토가 필요합니다.
    - 이서연 대리: 캠페인 콘텐츠 제작은 저희 팀이 맡겠습니다. 다음 주 수요일까지 초안을 공유하겠습니다.
    - 박준호 부장: 아주 좋습니다. 예산안은 회계팀과 협의해서 이번 주 금요일까지 확정해 주세요. 김민준 팀장님이 담당입니다.
    - 최은지 사원: 신규 기능 홍보를 위한 블로그 포스팅도 필요합니다. 제가 초안을 작성해서 다음주 월요일까지 공유하겠습니다.
    
    ## 결정 사항
    - '프로젝트 썬라이즈' 캠페인 진행 승인.
    """
    
    print("--- Agent Service Initializing ---")
    agent_service = AgentService()
    
    print("\n--- Processing Meeting Minutes ---")
    final_state = agent_service.process(sample_minutes)
    
    print("\n--- Final State ---")
    # LLM의 최종 응답 메시지 출력
    print("LLM Final Message:", final_state['messages'][-1].content)
    # 처리된 아이템(캘린더에 등록된) 정보 출력
    print("Processed Items:", final_state['processed_items'])
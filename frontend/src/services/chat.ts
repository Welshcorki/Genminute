import api from './api';

/**
 * 챗봇 출처 정보 타입
 */
export interface ChatSource {
  type: 'chunk' | 'subtopic';
  meeting_id: string;
  title: string;
  meeting_date?: string;
  start_time?: string;
  end_time?: string;
  subtopic_title?: string;
}

/**
 * 챗봇 응답 타입
 */
export interface ChatResponse {
  success: boolean;
  answer?: string;
  sources?: ChatSource[];
  error?: string;
}

/**
 * 챗봇 요청 타입
 */
export interface ChatRequest {
  query: string;
  meeting_id?: string; // 특정 회의에 대한 질문인 경우
}

/**
 * 챗봇 서비스
 */
export const chatService = {
  /**
   * 챗봇에 질문을 보내고 답변을 받습니다.
   * @param query 질문 내용
   * @param meetingId 특정 회의 ID (선택사항)
   * @returns 챗봇 응답
   */
  sendMessage: async (query: string, meetingId?: string): Promise<ChatResponse> => {
    const payload: ChatRequest = { query };
    
    if (meetingId) {
      payload.meeting_id = meetingId;
    }

    const response = await api.post<ChatResponse>('/api/chat', payload);
    return response.data;
  },
};

export default chatService;


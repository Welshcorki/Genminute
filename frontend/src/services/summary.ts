/**
 * 요약 서비스
 * - 회의 요약 조회
 * - 요약 생성 요청
 */
import api from './api';

export interface Summary {
  id?: number;
  meeting_id: string;
  summary_text: string;
  created_at?: string;
}

export interface SummaryResponse {
  success: boolean;
  summary?: string;
  error?: string;
}

export const summaryService = {
  /**
   * 회의 요약 조회
   * 백엔드 API: /api/check_summary/<meeting_id>
   */
  getSummary: async (meetingId: string): Promise<SummaryResponse> => {
    try {
      const response = await api.get(`/api/check_summary/${meetingId}`);
      // 백엔드 응답: { success, has_summary, summary? }
      if (response.data.has_summary) {
        return { success: true, summary: response.data.summary };
      }
      return { success: true, summary: undefined };
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { success: false, error: '요약이 없습니다.' };
      }
      throw error;
    }
  },

  /**
   * 요약 생성 요청
   * 백엔드 API: /api/summarize/<meeting_id>
   */
  generateSummary: async (meetingId: string): Promise<SummaryResponse> => {
    const response = await api.post(`/api/summarize/${meetingId}`);
    return response.data;
  },
};

export default summaryService;


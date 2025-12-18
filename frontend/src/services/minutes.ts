import api from './api';

export interface MinutesResponse {
  success: boolean;
  minutes?: string;
  has_minutes?: boolean;
  message?: string;
  error?: string;
  created_at?: string;
  updated_at?: string;
}

export const minutesService = {
  /**
   * 회의록 조회
   */
  getMinutes: async (meetingId: string): Promise<MinutesResponse> => {
    try {
      const response = await api.get(`/api/get_minutes/${meetingId}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { success: false, has_minutes: false, error: '회의록이 없습니다.' };
      }
      throw error;
    }
  },

  /**
   * 회의록 생성 요청
   */
  generateMinutes: async (meetingId: string): Promise<MinutesResponse> => {
    const response = await api.post(`/api/generate_minutes/${meetingId}`);
    return response.data;
  },
};

export default minutesService;


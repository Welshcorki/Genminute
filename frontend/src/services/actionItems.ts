import api from './api';

export interface ActionItem {
  id: number;
  meeting_id: string;
  content: string;
  due_date?: string;
  status: 'pending' | 'done';
  tool_call_id?: string;
  calendar_event_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ExtractActionItemsResponse {
  success: boolean;
  message?: string;
  count?: number;
  error?: string;
}

export interface GetActionItemsResponse {
  success: boolean;
  action_items: ActionItem[];
  error?: string;
}

export interface UpdateActionItemStatusResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export const actionItemsService = {
  // Action Item 추출 (수동 트리거)
  extractActionItems: async (meetingId: string): Promise<ExtractActionItemsResponse> => {
    try {
      const response = await api.post<ExtractActionItemsResponse>(`/api/extract_action_items/${meetingId}`);
      return response.data;
    } catch (error: any) {
      console.error('Action Item 추출 실패:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Action Item 추출 중 오류가 발생했습니다.'
      };
    }
  },

  // Action Item 목록 조회
  getActionItems: async (meetingId: string): Promise<ActionItem[]> => {
    try {
      const response = await api.get<GetActionItemsResponse>(`/api/action_items/${meetingId}`);
      if (response.data.success && response.data.action_items) {
        return response.data.action_items;
      }
      return [];
    } catch (error: any) {
      console.error('Action Items 조회 실패:', error);
      return [];
    }
  },

  // Action Item 상태 업데이트
  updateActionItemStatus: async (itemId: number, status: 'pending' | 'done'): Promise<UpdateActionItemStatusResponse> => {
    try {
      const response = await api.post<UpdateActionItemStatusResponse>(`/api/action_items/${itemId}/status`, { status });
      return response.data;
    } catch (error: any) {
      console.error('Action Item 상태 업데이트 실패:', error);
      return {
        success: false,
        error: error.response?.data?.error || '상태 업데이트 중 오류가 발생했습니다.'
      };
    }
  },
};


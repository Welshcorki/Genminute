import api from './api';

export interface SharedUser {
  id: number;
  email: string;
  name: string;
  profile_picture?: string;
  permission: string;
  shared_at: string;
}

export interface ShareResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface SharedUsersResponse {
  success: boolean;
  shared_users: SharedUser[];
  error?: string;
}

export interface SharedMeeting {
  meeting_id: string;
  title: string;
  date: string;
  audio_file?: string;
  summary?: string;
}

export interface SharedMeetingsResponse {
  success: boolean;
  meetings: SharedMeeting[];
  error?: string;
}

export const shareService = {
  // 노트 공유 (이메일 기반)
  shareMeeting: async (meetingId: string, email: string): Promise<ShareResponse> => {
    const response = await api.post(`/api/share/${meetingId}`, { email });
    return response.data;
  },

  // 공유받은 사용자 목록 조회
  getSharedUsers: async (meetingId: string): Promise<SharedUser[]> => {
    try {
      const response = await api.get<SharedUsersResponse>(`/api/shared_users/${meetingId}`);
      if (response.data.success && response.data.shared_users) {
        return response.data.shared_users;
      }
      return [];
    } catch (error) {
      console.error('공유 사용자 조회 실패:', error);
      return [];
    }
  },

  // 공유 해제
  unshareMeeting: async (meetingId: string, userId: number): Promise<ShareResponse> => {
    const response = await api.post(`/api/unshare/${meetingId}/${userId}`);
    return response.data;
  },

  // 공유받은 노트 목록 조회
  getSharedMeetings: async (): Promise<SharedMeeting[]> => {
    try {
      const response = await api.get<SharedMeetingsResponse>('/api/shared-notes');
      if (response.data.success && response.data.meetings) {
        return response.data.meetings;
      }
      return [];
    } catch (error) {
      console.error('공유받은 노트 조회 실패:', error);
      return [];
    }
  },
};

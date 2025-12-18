import api from './api';

export interface Meeting {
  meeting_id: string;
  title: string;
  date: string;
  audio_file?: string;
  summary?: string; // 목록 조회 시 요약본이 있을 수도 있고 없을 수도 있음
}

export interface TranscriptSegment {
  id: number;
  meeting_id: string;
  speaker_label: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence?: number;
}

export interface SpeakerShare {
  speaker_label: string;
  percentage: number;
  total_duration: number;
}

export interface MeetingDetail {
  success: boolean;
  meeting_id: string;
  title: string;
  meeting_date: string;
  participants: string[];
  audio_url: string;
  transcript: TranscriptSegment[];
  speaker_share: SpeakerShare[];
  can_edit: boolean;
}

export interface UserStats {
  monthly_notes: number;
  total_recording_hours: number;
  total_recording_minutes: number;
}

export const meetingService = {
  // 모든 회의 목록 조회
  getAllMeetings: async (): Promise<Meeting[]> => {
    const response = await api.get('/notes_json');
    return response.data.meetings;
  },

  // 최근 회의 목록 조회 (일단 전체 조회 후 프론트에서 자르거나, 추후 백엔드에 limit 파라미터 추가)
  getRecentMeetings: async (): Promise<Meeting[]> => {
    const response = await api.get('/notes_json');
    // 최신순 정렬은 백엔드 쿼리에서 이미 되어 있음 (ORDER BY date DESC)
    return response.data.meetings.slice(0, 3); // 상위 3개만 반환
  },

  // 사용자 통계 조회
  getUserStats: async (): Promise<UserStats> => {
    try {
      const response = await api.get('/api/stats');
      // 백엔드 응답 구조: { success: true, stats: { monthly_notes, total_recording_hours, ... } }
      if (response.data.success && response.data.stats) {
        return response.data.stats;
      }
      return {
        monthly_notes: 0,
        total_recording_hours: 0,
        total_recording_minutes: 0
      };
    } catch {
      // API가 없는 경우 기본값 반환
      return {
        monthly_notes: 0,
        total_recording_hours: 0,
        total_recording_minutes: 0
      };
    }
  },

  // 회의 상세 조회
  getMeetingDetail: async (meetingId: string): Promise<MeetingDetail> => {
    const response = await api.get(`/api/meeting/${meetingId}`);
    const data = response.data;
    
    // 오디오 URL을 전체 경로로 변환 (백엔드 서버 주소 포함)
    if (data.audio_url && !data.audio_url.startsWith('http')) {
      data.audio_url = `${api.defaults.baseURL}${data.audio_url}`;
    }
    
    return data;
  },

  // 회의 삭제
  deleteMeeting: async (meetingId: string): Promise<{ success: boolean }> => {
    const response = await api.post(`/api/delete_meeting/${meetingId}`);
    return response.data;
  },

  // 회의 제목 수정
  updateMeetingTitle: async (meetingId: string, newTitle: string): Promise<{ success: boolean; error?: string }> => {
    const response = await api.post(`/api/update_title/${meetingId}`, { title: newTitle });
    return response.data;
  },

  // 회의 날짜 수정
  updateMeetingDate: async (meetingId: string, newDate: string): Promise<{ success: boolean; error?: string }> => {
    const response = await api.post(`/api/update_date/${meetingId}`, { date: newDate });
    return response.data;
  },
};

/**
 * 인증 서비스
 * Firebase ID 토큰 기반 백엔드 인증
 */
import api from './api';

export interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  profile_picture?: string;
}

export interface LoginResponse {
  success: boolean;
  user?: User;
  error?: string;
}

export const authService = {
  /**
   * Firebase ID 토큰으로 백엔드 로그인
   * @param idToken Firebase에서 받은 ID 토큰
   */
  loginWithIdToken: async (idToken: string): Promise<LoginResponse> => {
    const response = await api.post('/api/login', { idToken });
    return response.data;
  },

  // 회원가입 (필요 시 구현)
  signup: async (email, password, name) => {
    const response = await api.post('/auth/signup', { email, password, name });
    return response.data;
  },

  // 로그아웃
  logout: async () => {
    const response = await api.post('/api/logout');
    return response.data;
  },

  /**
   * 현재 로그인한 사용자 정보 조회
   */
  getCurrentUser: async (): Promise<User | null> => {
    try {
      const response = await api.get('/api/me');
      if (response.data.success) {
        return response.data.user;
      }
      return null;
    } catch {
      return null;
    }
  },

  /**
   * 인증 상태 확인
   */
  checkAuth: async (): Promise<boolean> => {
    try {
      const response = await api.get('/api/me');
      return response.data.success === true;
    } catch {
      return false;
    }
  }
};

export default authService;

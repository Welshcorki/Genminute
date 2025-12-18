import axios from 'axios';

// 백엔드 API 기본 URL (개발 환경)
// 실제 배포 시에는 환경 변수 등을 통해 동적으로 설정해야 함
const API_BASE_URL = 'http://localhost:5000'; 

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // 쿠키/세션 기반 인증을 위해 필요
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터 (에러 처리 공통화 등)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 공통 에러 처리 로직 (예: 401 Unauthorized 시 로그아웃 처리 등)
    if (error.response && error.response.status === 401) {
        // 필요 시 로그아웃 처리 또는 로그인 페이지 리다이렉트
        console.warn('Unauthorized access. Redirecting to login...');
    }
    return Promise.reject(error);
  }
);

export default api;
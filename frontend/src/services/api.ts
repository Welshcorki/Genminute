import axios from 'axios';

// API 서버 주소
// - VITE_API_BASE_URL이 있으면 그 값을 사용
// - 개발 서버(npm run dev, :5173)에서는 별도로 띄운 Flask(:5000)를 호출
// - 빌드 결과물은 Flask가 직접 서빙하므로 같은 출처(상대 경로)로 호출
//   → 접속 주소가 localhost든 127.0.0.1이든 배포 도메인이든 CORS 없이 동작
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:5000' : '');

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRedirecting = false;

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !isRedirecting) {
      isRedirecting = true;

      sessionStorage.setItem('redirect_after_login', window.location.pathname);

      window.location.href = '/login';

      setTimeout(() => { isRedirecting = false; }, 3000);
    }
    return Promise.reject(error);
  }
);

export default api;

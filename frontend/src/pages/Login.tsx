/**
 * 로그인 페이지
 * Firebase Google 인증을 통한 로그인
 */
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signInWithGoogle, isAuthenticated, isLoading: authLoading, firebaseReady } = useAuth();
  
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      const savedRedirect = sessionStorage.getItem('redirect_after_login');
      if (savedRedirect) {
        sessionStorage.removeItem('redirect_after_login');
        navigate(savedRedirect, { replace: true });
      } else {
        const from = location.state?.from?.pathname || '/';
        navigate(from, { replace: true });
      }
    }
  }, [isAuthenticated, authLoading, navigate, location]);

  const handleGoogleLogin = async () => {
    setError('');
    setIsLoading(true);

    try {
      await signInWithGoogle();
      // 로그인 성공 시 AuthContext가 상태를 업데이트하고 useEffect에서 리다이렉트 처리
    } catch (err: any) {
      console.error('Google 로그인 실패:', err);
      
      // Firebase 에러 메시지 처리
      let errorMessage = '로그인에 실패했습니다. 다시 시도해주세요.';
      
      if (err.code === 'auth/popup-closed-by-user') {
        errorMessage = '로그인 창이 닫혔습니다. 다시 시도해주세요.';
      } else if (err.code === 'auth/popup-blocked') {
        errorMessage = '팝업이 차단되었습니다. 팝업 차단을 해제해주세요.';
      } else if (err.code === 'auth/network-request-failed') {
        errorMessage = '네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 인증 로딩 중일 때
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-indigo-600 mx-auto" />
          <p className="mt-4 text-gray-600">인증 확인 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* 배경 효과 */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-teal-500/20 rounded-full blur-3xl"></div>
      </div>

      <div className="relative sm:mx-auto sm:w-full sm:max-w-md">
        {/* 로고 및 타이틀 */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <img 
              src="/logo.png" 
              alt="GenMinute Logo" 
              className="h-24 w-24 sm:h-32 sm:w-32"
            />
          </div>
          <p className="mt-2 text-slate-400">
            AI 기반 회의록 자동화 및 인사이트 분석
          </p>
        </div>
      </div>

      <div className="relative mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white/10 backdrop-blur-lg py-8 px-6 shadow-2xl rounded-2xl border border-white/20">
          {/* 에러 메시지 */}
            {error && (
            <div className="mb-6 rounded-lg bg-red-500/20 border border-red-500/30 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
                  </div>
                  <div className="ml-3">
                  <p className="text-sm text-red-200">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Google 로그인 버튼 */}
              <button
            onClick={handleGoogleLogin}
            disabled={isLoading || !firebaseReady}
            className={`w-full flex justify-center items-center py-3 px-4 rounded-xl shadow-lg text-base font-medium transition-all duration-200 ${
              isLoading || !firebaseReady
                ? 'bg-white/50 cursor-not-allowed'
                : 'bg-white hover:bg-gray-100 hover:shadow-xl hover:-translate-y-0.5'
                }`}
              >
                {isLoading ? (
              <>
                <Loader2 className="animate-spin h-5 w-5 mr-3 text-gray-600" />
                <span className="text-gray-600">로그인 중...</span>
              </>
            ) : !firebaseReady ? (
              <>
                <Loader2 className="animate-spin h-5 w-5 mr-3 text-gray-600" />
                <span className="text-gray-600">초기화 중...</span>
              </>
            ) : (
              <>
                <svg className="h-5 w-5 mr-3" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                <span className="text-gray-700">Google 계정으로 로그인</span>
              </>
            )}
              </button>

          {/* 안내 문구 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-slate-400">
              Google 계정으로 간편하게 시작하세요
            </p>
          </div>
          
          {/* 서비스 약관 */}
          <div className="mt-6 text-center">
            <p className="text-xs text-slate-500">
              로그인 시{' '}
              <a href="#" className="text-indigo-400 hover:text-indigo-300 underline">
                서비스 약관
              </a>
              {' '}및{' '}
              <a href="#" className="text-indigo-400 hover:text-indigo-300 underline">
                개인정보처리방침
              </a>
              에 동의하게 됩니다.
            </p>
           </div>
        </div>

        {/* 하단 정보 */}
        <div className="mt-8 text-center">
          <p className="text-sm text-slate-500">
            © 2025 GenMinute. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;

/**
 * 인증 컨텍스트
 * 전역 인증 상태 관리 및 Firebase 연동
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged
} from 'firebase/auth';
import type { User as FirebaseUser } from 'firebase/auth';
import { 
  ensureFirebaseInitialized, 
  getFirebaseAuth, 
  getGoogleProvider,
  isFirebaseInitialized 
} from '../config/firebase';
import api from '../services/api';

// 사용자 정보 타입
interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  profile_picture?: string;
}

// 인증 컨텍스트 타입
interface AuthContextType {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  firebaseReady: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// 기본값
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider Props
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [firebaseReady, setFirebaseReady] = useState(false);

  // Firebase 초기화 및 인증 상태 감지
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const initAuth = async () => {
      try {
        // Firebase 초기화 대기
        await ensureFirebaseInitialized();
        setFirebaseReady(true);
        
        const auth = getFirebaseAuth();
        
        // Firebase 인증 상태 변경 감지
        unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
          setFirebaseUser(fbUser);
          
          if (fbUser) {
            // Firebase 로그인 상태 -> 백엔드에서 사용자 정보 가져오기
            try {
              const response = await api.get('/api/me');
              if (response.data.success) {
                setUser(response.data.user);
              }
            } catch {
              // 백엔드 세션이 없으면 Firebase ID 토큰으로 로그인 시도
              try {
                const idToken = await fbUser.getIdToken();
                const loginResponse = await api.post('/api/login', { idToken });
                if (loginResponse.data.success) {
                  setUser(loginResponse.data.user);
                }
              } catch (loginError) {
                console.error('백엔드 로그인 실패:', loginError);
                setUser(null);
              }
            }
          } else {
            setUser(null);
          }
          
          setIsLoading(false);
        });
      } catch (error) {
        console.error('Firebase 초기화 실패:', error);
        setFirebaseReady(false);
        setIsLoading(false);
      }
    };

    initAuth();

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, []);

  // Google 로그인
  const signInWithGoogle = async () => {
    if (!isFirebaseInitialized()) {
      throw new Error('Firebase가 아직 초기화되지 않았습니다.');
    }
    
    try {
      setIsLoading(true);
      
      const auth = getFirebaseAuth();
      const provider = getGoogleProvider();
      
      // Firebase Google 로그인
      const result = await signInWithPopup(auth, provider);
      const idToken = await result.user.getIdToken();
      
      // 백엔드에 ID 토큰 전송하여 세션 생성
      const response = await api.post('/api/login', { idToken });
      
      if (response.data.success) {
        setUser(response.data.user);
      } else {
        throw new Error(response.data.error || '로그인에 실패했습니다.');
      }
    } catch (error: unknown) {
      console.error('Google 로그인 실패:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 로그아웃
  const signOut = async () => {
    try {
      setIsLoading(true);
      
      // 백엔드 세션 삭제
      await api.post('/api/logout');
      
      // Firebase 로그아웃 (Firebase가 초기화된 경우에만)
      if (isFirebaseInitialized()) {
        const auth = getFirebaseAuth();
        await firebaseSignOut(auth);
      }
      
      setUser(null);
    } catch (error) {
      console.error('로그아웃 실패:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 사용자 정보 새로고침
  const refreshUser = async () => {
    try {
      const response = await api.get('/api/me');
      if (response.data.success) {
        setUser(response.data.user);
      }
    } catch (error) {
      console.error('사용자 정보 갱신 실패:', error);
    }
  };

  const value: AuthContextType = {
    user,
    firebaseUser,
    isLoading,
    isAuthenticated: !!user,
    firebaseReady,
    signInWithGoogle,
    signOut,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// 커스텀 훅
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;

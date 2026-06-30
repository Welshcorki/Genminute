/**
 * 인증 컨텍스트
 * 전역 인증 상태 관리 및 Supabase 연동
 */
import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User as SupabaseUser, Session } from '@supabase/supabase-js';
import { supabase } from '../config/supabase';
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
  supabaseUser: SupabaseUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
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
  const [supabaseUser, setSupabaseUser] = useState<SupabaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Supabase 인증 상태 감지
  useEffect(() => {
    // 현재 세션 확인
    const initAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        
        if (session?.user) {
          setSupabaseUser(session.user);
          await syncWithBackend(session);
        }
      } catch (error) {
        console.error('인증 초기화 실패:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();

    // 인증 상태 변경 리스너
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSupabaseUser(session?.user ?? null);

        if (event === 'SIGNED_IN' && session) {
          await syncWithBackend(session);
        } else if (event === 'SIGNED_OUT') {
          setUser(null);
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // 백엔드와 세션 동기화
  const syncWithBackend = async (session: Session) => {
    try {
      // 먼저 기존 백엔드 세션 확인
      try {
        const meResponse = await api.get('/api/me');
        if (meResponse.data.success) {
          setUser(meResponse.data.user);
          return;
        }
      } catch {
        // 백엔드 세션 없음 → 로그인 시도
      }

      // Supabase access token으로 백엔드 로그인
      const accessToken = session.access_token;
      const loginResponse = await api.post('/api/login', { accessToken });
      if (loginResponse.data.success) {
        setUser(loginResponse.data.user);
      }
    } catch (error) {
      console.error('백엔드 동기화 실패:', error);
      setUser(null);
    }
  };

  // Google 로그인
  const signInWithGoogle = async () => {
    try {
      setIsLoading(true);

      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin + '/auth/callback',
        },
      });

      if (error) {
        throw error;
      }
      // OAuth 리다이렉트가 발생하므로, 이후 처리는 onAuthStateChange에서 수행
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

      // Supabase 로그아웃
      await supabase.auth.signOut();

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
    supabaseUser,
    isLoading,
    isAuthenticated: !!user,
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

/**
 * Firebase 클라이언트 설정
 * 백엔드 API에서 Firebase 설정을 동적으로 가져옵니다.
 */
import { initializeApp } from 'firebase/app';
import type { FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import type { Auth } from 'firebase/auth';
import api from '../services/api';

// Firebase 인스턴스 (초기화 후 설정됨)
let app: FirebaseApp | null = null;
let auth: Auth | null = null;
let googleProvider: GoogleAuthProvider | null = null;
let isInitialized = false;
let initializationPromise: Promise<void> | null = null;

// Firebase 설정 타입
interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
  measurementId?: string;
}

/**
 * 백엔드에서 Firebase 설정을 가져와 초기화
 */
async function initializeFirebase(): Promise<void> {
  if (isInitialized) return;
  
  try {
    // 백엔드에서 Firebase 설정 가져오기
    const response = await api.get('/api/firebase-config');
    
    if (!response.data.success) {
      throw new Error('Firebase 설정을 가져오는데 실패했습니다.');
    }
    
    const firebaseConfig: FirebaseConfig = response.data.config;
    
    // Firebase 앱 초기화
    app = initializeApp(firebaseConfig);
    
    // Firebase Auth 인스턴스
    auth = getAuth(app);
    
    // Google 로그인 Provider
    googleProvider = new GoogleAuthProvider();
    googleProvider.addScope('email');
    googleProvider.addScope('profile');
    
    isInitialized = true;
    console.log('✅ Firebase 초기화 완료');
  } catch (error) {
    console.error('❌ Firebase 초기화 실패:', error);
    throw error;
  }
}

/**
 * Firebase 초기화 보장 (싱글톤 패턴)
 * 여러 곳에서 호출해도 한 번만 초기화됨
 */
export async function ensureFirebaseInitialized(): Promise<void> {
  if (isInitialized) return;
  
  if (!initializationPromise) {
    initializationPromise = initializeFirebase();
  }
  
  return initializationPromise;
}

/**
 * Firebase Auth 인스턴스 반환
 * 초기화가 완료되어야 사용 가능
 */
export function getFirebaseAuth(): Auth {
  if (!auth) {
    throw new Error('Firebase가 초기화되지 않았습니다. ensureFirebaseInitialized()를 먼저 호출하세요.');
  }
  return auth;
}

/**
 * Google Provider 반환
 */
export function getGoogleProvider(): GoogleAuthProvider {
  if (!googleProvider) {
    throw new Error('Firebase가 초기화되지 않았습니다. ensureFirebaseInitialized()를 먼저 호출하세요.');
  }
  return googleProvider;
}

/**
 * Firebase 초기화 상태 확인
 */
export function isFirebaseInitialized(): boolean {
  return isInitialized;
}

export { app, auth, googleProvider };

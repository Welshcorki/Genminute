import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { UploadProvider } from './contexts/UploadContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import UploadStatusBar from './components/UploadStatusBar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NoteList from './pages/NoteList';
import NoteDetail from './pages/NoteDetail';
import SharedNoteList from './pages/SharedNoteList';
import Recorder from './pages/Recorder';

// 공개 접근 허용 여부 설정
// true: 비로그인 상태에서도 모든 페이지 접근 가능 (로그인 버튼만 표시)
// false: 기존 방식 (로그인 페이지가 먼저 나타남)
const ENABLE_PUBLIC_ACCESS = true;

function App() {
  return (
    <AuthProvider>
      <UploadProvider>
    <Router>
      <Routes>
            {/* 로그인 페이지 (인증 불필요) */}
        <Route path="/login" element={<Login />} />
        {/* Supabase OAuth 리다이렉트 수신 경로 */}
        <Route path="/auth/callback" element={<Login />} />
        
            {/* 조건부 라우팅: 공개 접근 허용 여부에 따라 ProtectedRoute 사용 여부 결정 */}
            {ENABLE_PUBLIC_ACCESS ? (
              // 비로그인 접근 허용 모드
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/notes" element={<NoteList />} />
                <Route path="/notes/:meetingId" element={<NoteDetail />} />
                <Route path="/shared-notes" element={<SharedNoteList />} />
                <Route path="/record" element={<Recorder />} />
              </Route>
            ) : (
              // 기존 방식 (ProtectedRoute 사용)
              <Route element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route path="/" element={<Dashboard />} />
                <Route path="/notes" element={<NoteList />} />
                <Route path="/notes/:meetingId" element={<NoteDetail />} />
                <Route path="/shared-notes" element={<SharedNoteList />} />
                <Route path="/record" element={<Recorder />} />
              </Route>
            )}
      </Routes>
          
          {/* 전역 업로드 상태 표시 바 */}
          <UploadStatusBar />
    </Router>
      </UploadProvider>
    </AuthProvider>
  );
}

export default App;

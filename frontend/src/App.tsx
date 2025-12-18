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
import Recorder from './pages/Recorder';

function App() {
  return (
    <AuthProvider>
      <UploadProvider>
    <Router>
      <Routes>
            {/* 로그인 페이지 (인증 불필요) */}
        <Route path="/login" element={<Login />} />
        
            {/* 인증이 필요한 페이지들 */}
            <Route element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
          <Route path="/" element={<Dashboard />} />
          <Route path="/notes" element={<NoteList />} />
              <Route path="/notes/:meetingId" element={<NoteDetail />} />
          <Route path="/record" element={<Recorder />} />
        </Route>
      </Routes>
          
          {/* 전역 업로드 상태 표시 바 */}
          <UploadStatusBar />
    </Router>
      </UploadProvider>
    </AuthProvider>
  );
}

export default App;

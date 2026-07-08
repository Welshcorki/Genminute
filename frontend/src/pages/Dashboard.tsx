import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mic, Upload, Clock, FileText, MoreVertical, Calendar, ChevronRight, File, LogIn } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { meetingService, type Meeting, type UserStats } from '../services/meeting';
import { UploadModal } from '../components/UploadModal';

const Dashboard = () => {
  const { user: authUser, isAuthenticated } = useAuth();
  const [recentNotes, setRecentNotes] = useState<Meeting[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      if (!isAuthenticated) {
        // 비로그인 상태에서는 데이터를 가져오지 않음
        setIsLoading(false);
        return;
      }

      try {
        const [notesData, statsData] = await Promise.all([
          meetingService.getRecentMeetings(),
          meetingService.getUserStats()
        ]);
        // 최대 5개만 표시 (백엔드에서도 제한하지만 프론트엔드에서도 추가 제한)
        setRecentNotes(notesData.slice(0, 5));
        setStats(statsData);
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated]);

  if (isLoading) {
    return <div className="p-10 text-center text-slate-500">데이터를 불러오는 중...</div>;
  }

  return (
    <div className="space-y-10">
      {/* 1. 환영 메시지 & 빠른 액션 */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-brand-950 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden border border-slate-800">
        {/* Decorative background blur */}
        <div className="absolute -top-24 -right-24 w-80 h-80 bg-brand-500/30 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-teal-500/20 rounded-full blur-3xl"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-2">
              {isAuthenticated ? (
                <>안녕하세요, <span className="text-brand-200">{authUser?.name || '사용자'}</span>님! 👋</>
              ) : (
                <>GenMinute에 오신 것을 환영합니다! 👋</>
              )}
            </h1>
            <p className="text-slate-400 text-lg leading-relaxed">
              회의, 강의, 인터뷰...<br className="md:hidden" /> 모든 대화를 인사이트로 바꿔보세요.
            </p>
          </div>
          <div className="flex gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  to="/record"
                  className="flex items-center px-6 py-3 bg-brand-600 text-white rounded-xl hover:bg-brand-500 transition-all font-bold shadow-lg hover:shadow-brand-500/20 active:scale-95"
                >
                  <Mic className="w-5 h-5 mr-2" />
                  새 기록 시작
                </Link>
                <button
                  onClick={() => setIsUploadModalOpen(true)}
                  className="flex items-center px-6 py-3 bg-white/10 text-white border border-white/10 rounded-xl hover:bg-white/20 transition-all font-medium backdrop-blur-sm"
                >
                  <Upload className="w-5 h-5 mr-2" />
                  파일 업로드
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="flex items-center px-6 py-3 bg-brand-600 text-white rounded-xl hover:bg-brand-500 transition-all font-bold shadow-lg hover:shadow-brand-500/20 active:scale-95"
              >
                <LogIn className="w-5 h-5 mr-2" />
                로그인하여 시작하기
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* 2. 통계 요약 (Stats) */}
      {isAuthenticated ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            icon={<FileText className="w-6 h-6 text-brand-600" />}
            label="이번 달 노트"
            value={stats ? `${stats.monthly_notes}개` : '0개'} 
            bgColor="bg-brand-50 border border-brand-100"
            clickable={true}
            onClick={() => navigate('/notes')}
          />
          <StatCard
            icon={<Clock className="w-6 h-6 text-teal-600" />}
            label="총 녹음 시간"
            value={stats ? formatRecordingTime(stats.total_recording_hours, stats.total_recording_minutes) : '0시간'} 
            bgColor="bg-teal-50 border border-teal-100"
          />
          <StatCard
            icon={<File className="w-6 h-6 text-rose-600" />} 
            label="최근 활동"
            value={recentNotes.length > 0 ? '기록 있음' : '기록 없음'}
            subText={recentNotes.length > 0 ? '클릭하여 최근 노트 확인' : '첫 기록을 시작해보세요'}
            bgColor="bg-rose-50 border border-rose-100"
            clickable={recentNotes.length > 0}
            onClick={() => {
              if (recentNotes.length > 0) {
                // 가장 최근 노트로 이동
                navigate(`/notes/${recentNotes[0].meeting_id}`);
              }
            }}
          />
        </div>
      ) : (
        <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center shadow-sm">
          <p className="text-slate-600 mb-4">로그인하여 통계와 노트를 확인하세요.</p>
          <Link
            to="/login"
            className="inline-flex items-center px-6 py-3 bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors font-medium"
          >
            <LogIn className="w-5 h-5 mr-2" />
            로그인하기
          </Link>
        </div>
      )}

      {/* 3. 최근 내 노트 리스트 */}
      {isAuthenticated && (
        <div>
          <div className="flex items-center justify-between mb-6 px-1">
            <h2 className="text-2xl font-bold text-slate-900">최근 내 노트</h2>
            <Link to="/notes" className="flex items-center text-sm text-slate-500 hover:text-brand-600 font-semibold transition-colors">
              전체 보기 <ChevronRight className="w-4 h-4 ml-1" />
            </Link>
          </div>

          {recentNotes.length === 0 ? (
          <div className="bg-white p-10 rounded-2xl border border-slate-200 text-center shadow-sm">
            <div className="flex justify-center mb-4">
              <div className="p-4 bg-slate-50 rounded-full">
                <FileText className="w-8 h-8 text-slate-400" />
              </div>
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">아직 저장된 노트가 없습니다</h3>
            <p className="text-slate-500 mb-6">첫 번째 회의나 강의를 기록하고 인사이트를 얻어보세요.</p>
            <Link
              to="/record"
              className="inline-flex items-center px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors font-medium text-sm shadow-md hover:shadow-lg"
            >
              <Mic className="w-4 h-4 mr-2" />
              지금 기록하기
            </Link>
          </div>
        ) : (
          <div className="grid gap-5">
            {recentNotes.map((note) => (
              <div
                key={note.meeting_id}
                onClick={() => navigate(`/notes/${note.meeting_id}`)}
                className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer group"
              >
                <div className="flex justify-between items-start">
                  <div className="space-y-3 w-full">
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-bold text-slate-900 group-hover:text-brand-600 transition-colors truncate">
                        {note.title}
                      </h3>
                      <span className="text-xs font-medium text-slate-500 flex items-center bg-slate-100 px-2.5 py-1 rounded-full shrink-0">
                        <Calendar className="w-3 h-3 mr-1.5" />
                        {note.date}
                      </span>
                    </div>
                    <p className="text-slate-600 text-sm line-clamp-2 leading-relaxed max-w-2xl">
                      {note.summary || '요약 내용이 없습니다. (자동 요약 생성 대기 중)'}
                    </p>
                    <div className="flex gap-2 pt-1">
                      {/* 태그 예시 (임시 - 추후 DB 연동 필요) */}
                      {['#자동생성', '#AI요약'].map((tag) => (
                        <span key={tag} className="text-xs font-semibold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-md">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation(); // 카드 클릭 이벤트 전파 방지
                      // 추후 더보기 메뉴 기능 추가
                    }}
                    className="text-slate-300 hover:text-slate-600 p-2 rounded-full hover:bg-slate-50 transition-colors ml-4"
                  >
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          )}
        </div>
      )}

      {/* 업로드 모달 */}
      {isAuthenticated && (
        <UploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onComplete={(meetingId) => {
            // 업로드 완료 시 노트 목록 새로고침 및 상세 페이지로 이동
            if (meetingId) {
              navigate(`/notes/${meetingId}`);
            } else {
              // meetingId가 없으면 노트 목록으로 이동
              navigate('/notes');
            }
          }}
        />
      )}
    </div>
  );
};

// 녹음 시간 포맷팅 함수
const formatRecordingTime = (hours: number, minutes: number): string => {
  if (hours > 0) {
    return `${hours}시간 ${minutes > 0 ? `${minutes}분` : ''}`;
  } else if (minutes > 0) {
    return `${minutes}분`;
  } else {
    return '0분';
  }
};

// 통계 카드 컴포넌트
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subText?: string;
  bgColor: string;
  onClick?: () => void;
  clickable?: boolean;
}

const StatCard = ({ icon, label, value, subText, bgColor, onClick, clickable }: StatCardProps) => (
  <div 
    className={`bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow flex items-center gap-5 ${clickable ? 'cursor-pointer hover:border-brand-200' : ''}`}
    onClick={onClick}
  >
    <div className={`p-4 rounded-xl ${bgColor}`}>
      {icon}
    </div>
    <div>
      <p className="text-sm font-semibold text-slate-500 mb-1">{label}</p>
      <h3 className="text-2xl font-extrabold text-slate-900">{value}</h3>
      {subText && <p className="text-xs font-medium text-rose-500 mt-1">{subText}</p>}
    </div>
  </div>
);

export default Dashboard;

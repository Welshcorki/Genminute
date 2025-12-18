/**
 * NoteDetail 페이지 - 회의록 상세 뷰어
 * 
 * 기능:
 * - 오디오/비디오 플레이어
 * - 전사 스크립트 (화자별 구분)
 * - 요약 탭
 * - 마인드맵 탭
 * - 챗봇 탭 (ChatSidebar)
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  Volume2, 
  VolumeX,
  FileText,
  Network,
  MessageCircle,
  Loader2,
  Calendar,
  Users,
  Clock,
  AlertCircle,
  Trash2,
  MoreVertical,
  Edit,
  X
} from 'lucide-react';
import { meetingService, type MeetingDetail, type TranscriptSegment } from '../services/meeting';
import SummaryView from '../components/SummaryView';
import MindmapView from '../components/MindmapView';
import MinutesView from '../components/MinutesView';
import ChatSidebar from '../components/ChatSidebar';

type TabType = 'script' | 'summary' | 'mindmap' | 'minutes' | 'chat';

const NoteDetail = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();

  // 상태
  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('script');
  
  // 편집 상태
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingDate, setIsEditingDate] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDate, setEditDate] = useState('');

  // 오디오 플레이어 상태
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [activeSegmentId, setActiveSegmentId] = useState<number | null>(null);
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  // 데이터 로드
  useEffect(() => {
    const loadMeeting = async () => {
      if (!meetingId) return;

      try {
        setIsLoading(true);
        setError(null);
        const data = await meetingService.getMeetingDetail(meetingId);
        if (data.success) {
          setMeeting(data);
        } else {
          setError('회의를 불러올 수 없습니다.');
        }
      } catch (err: any) {
        console.error('회의 로드 실패:', err);
        if (err.response?.status === 403) {
          setError('이 회의에 접근 권한이 없습니다.');
        } else if (err.response?.status === 404) {
          setError('회의를 찾을 수 없습니다.');
        } else {
          setError('회의를 불러오는 중 오류가 발생했습니다.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadMeeting();
  }, [meetingId]);

  // 오디오 시간 업데이트
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
      
      // 현재 재생 중인 세그먼트 찾기
      if (meeting?.transcript) {
        const activeSegment = meeting.transcript.find(
          seg => audio.currentTime >= seg.start_time && audio.currentTime < seg.end_time
        );
        if (activeSegment) {
          setActiveSegmentId(activeSegment.id);
        }
      }
    };

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [meeting?.transcript]);

  // 활성 세그먼트로 스크롤
  useEffect(() => {
    if (activeSegmentId && transcriptRef.current) {
      const activeElement = transcriptRef.current.querySelector(`[data-segment-id="${activeSegmentId}"]`);
      if (activeElement) {
        activeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [activeSegmentId]);

  // 재생/일시정지
  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  // 음소거
  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  // 시간 포맷팅
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 세그먼트 클릭 시 해당 시간으로 이동
  const handleSegmentClick = (segment: TranscriptSegment) => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.currentTime = segment.start_time;
    if (!isPlaying) {
      audio.play();
      setIsPlaying(true);
    }
  };

  // 회의 삭제
  const handleDelete = async () => {
    if (!meetingId || !meeting?.can_edit) return;
    
    if (!window.confirm('정말 이 회의록을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return;
    }

    try {
      await meetingService.deleteMeeting(meetingId);
      navigate('/notes');
    } catch (err) {
      console.error('삭제 실패:', err);
      alert('회의록 삭제에 실패했습니다.');
    }
  };

  // 제목 수정 시작
  const handleStartEditTitle = () => {
    if (!meeting) return;
    setEditTitle(meeting.title);
    setIsEditingTitle(true);
    setIsMenuOpen(false);
  };

  // 날짜 수정 시작
  const handleStartEditDate = () => {
    if (!meeting) return;
    // 날짜 형식 변환: "2025-12-18 14:30:00" -> "2025-12-18T14:30"
    const dateStr = meeting.meeting_date.replace(' ', 'T').slice(0, 16);
    setEditDate(dateStr);
    setIsEditingDate(true);
    setIsMenuOpen(false);
  };

  // 제목 수정 저장
  const handleSaveTitle = async () => {
    if (!meetingId || !editTitle.trim()) return;

    try {
      const result = await meetingService.updateMeetingTitle(meetingId, editTitle.trim());
      if (result.success) {
        setMeeting(prev => prev ? { ...prev, title: editTitle.trim() } : null);
        setIsEditingTitle(false);
      } else {
        alert(result.error || '제목 수정에 실패했습니다.');
      }
    } catch (err) {
      console.error('제목 수정 실패:', err);
      alert('제목 수정에 실패했습니다.');
    }
  };

  // 날짜 수정 저장
  const handleSaveDate = async () => {
    if (!meetingId || !editDate) return;

    try {
      const result = await meetingService.updateMeetingDate(meetingId, editDate);
      if (result.success) {
        // 날짜 형식 변환: "2025-12-18T14:30" -> "2025-12-18 14:30:00"
        const formattedDate = editDate.replace('T', ' ') + ':00';
        setMeeting(prev => prev ? { ...prev, meeting_date: formattedDate } : null);
        setIsEditingDate(false);
      } else {
        alert(result.error || '날짜 수정에 실패했습니다.');
      }
    } catch (err) {
      console.error('날짜 수정 실패:', err);
      alert('날짜 수정에 실패했습니다.');
    }
  };

  // 화자별 색상
  const getSpeakerColor = (speaker: string): string => {
    const colors = [
      'bg-indigo-100 text-indigo-700 border-indigo-200',
      'bg-teal-100 text-teal-700 border-teal-200',
      'bg-rose-100 text-rose-700 border-rose-200',
      'bg-amber-100 text-amber-700 border-amber-200',
      'bg-purple-100 text-purple-700 border-purple-200',
      'bg-cyan-100 text-cyan-700 border-cyan-200',
    ];
    
    if (!meeting?.participants) return colors[0];
    const index = meeting.participants.indexOf(speaker);
    return colors[index % colors.length];
  };

  // 로딩 중
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-500">회의록을 불러오는 중...</p>
      </div>
    );
  }

  // 에러
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="p-4 bg-red-50 rounded-full mb-4">
          <AlertCircle className="w-10 h-10 text-red-500" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">오류 발생</h2>
        <p className="text-slate-500 mb-6">{error}</p>
        <Link
          to="/notes"
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          노트 목록으로
        </Link>
      </div>
    );
  }

  if (!meeting) return null;

  return (
    <div className="max-w-6xl mx-auto">
      {/* 헤더 */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-slate-500 hover:text-slate-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          뒤로 가기
        </button>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            {isEditingTitle ? (
              <div className="flex items-center gap-2 mb-2">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="text-2xl font-bold text-slate-900 border border-indigo-300 rounded-lg px-3 py-1 flex-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveTitle();
                    if (e.key === 'Escape') setIsEditingTitle(false);
                  }}
                />
                <button
                  onClick={handleSaveTitle}
                  className="px-3 py-1 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
                >
                  저장
                </button>
                <button
                  onClick={() => setIsEditingTitle(false)}
                  className="px-3 py-1 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-colors text-sm"
                >
                  취소
                </button>
              </div>
            ) : (
              <h1 className="text-2xl font-bold text-slate-900 mb-2">{meeting.title}</h1>
            )}
            <div className="flex items-center gap-4 text-sm text-slate-500">
              {isEditingDate ? (
                <div className="flex items-center gap-2">
                  <input
                    type="datetime-local"
                    value={editDate}
                    onChange={(e) => setEditDate(e.target.value)}
                    className="border border-indigo-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    autoFocus
                  />
                  <button
                    onClick={handleSaveDate}
                    className="px-2 py-1 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-xs"
                  >
                    저장
                  </button>
                  <button
                    onClick={() => setIsEditingDate(false)}
                    className="px-2 py-1 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-colors text-xs"
                  >
                    취소
                  </button>
                </div>
              ) : (
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {meeting.meeting_date}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                {meeting.participants.length}명 참석
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatTime(duration)}
              </span>
            </div>
          </div>

          {meeting.can_edit && (
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <MoreVertical className="w-5 h-5" />
              </button>
              {isMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setIsMenuOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 z-20">
                    <button
                      onClick={handleStartEditTitle}
                      className="w-full flex items-center gap-2 px-4 py-2 text-left text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                      제목 수정
                    </button>
                    <button
                      onClick={handleStartEditDate}
                      className="w-full flex items-center gap-2 px-4 py-2 text-left text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <Calendar className="w-4 h-4" />
                      날짜 수정
                    </button>
                    <div className="border-t border-slate-200" />
                    <button
                      onClick={handleDelete}
                      className="w-full flex items-center gap-2 px-4 py-2 text-left text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      삭제
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 오디오 플레이어 */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 shadow-sm">
        <audio ref={audioRef} src={meeting.audio_url} preload="metadata" />
        
        <div className="flex items-center gap-4">
          {/* 재생 버튼 */}
          <button
            onClick={togglePlay}
            className="p-3 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          {/* 진행 바 */}
          <div className="flex-1">
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={(e) => {
                const newTime = parseFloat(e.target.value);
                if (audioRef.current) {
                  audioRef.current.currentTime = newTime;
                }
                setCurrentTime(newTime);
              }}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* 음소거 버튼 */}
          <button
            onClick={toggleMute}
            className="p-2 text-slate-500 hover:text-slate-700 transition-colors"
          >
            {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="flex border-b border-slate-200 mb-6">
        {[
          { id: 'script', label: '스크립트', icon: FileText },
          { id: 'summary', label: '요약', icon: FileText },
          { id: 'mindmap', label: '마인드맵', icon: Network },
          { id: 'minutes', label: '회의록', icon: FileText },
          { id: 'chat', label: '챗봇', icon: MessageCircle },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* 탭 컨텐츠 */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        {/* 스크립트 탭 */}
        {activeTab === 'script' && (
          <div ref={transcriptRef} className="p-6 max-h-[600px] overflow-y-auto">
            {meeting.transcript.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                전사 데이터가 없습니다.
              </div>
            ) : (
              <div className="space-y-4">
                {meeting.transcript.map((segment) => (
                  <div
                    key={segment.id}
                    data-segment-id={segment.id}
                    onClick={() => handleSegmentClick(segment)}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      activeSegmentId === segment.id
                        ? 'bg-indigo-50 ring-2 ring-indigo-500'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded border ${getSpeakerColor(segment.speaker_label)}`}>
                        {segment.speaker_label}
                      </span>
                      <span className="text-xs text-slate-400">
                        {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                      </span>
                    </div>
                    <p className="text-slate-700 leading-relaxed">{segment.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 요약 탭 */}
        {activeTab === 'summary' && (
          <div className="p-6">
            <SummaryView meetingId={meetingId!} />
          </div>
        )}

        {/* 마인드맵 탭 */}
        {activeTab === 'mindmap' && (
          <div className="p-6">
            <MindmapView meetingId={meetingId!} />
          </div>
        )}

        {/* 회의록 탭 */}
        {activeTab === 'minutes' && (
          <div className="p-6">
            <MinutesView meetingId={meetingId!} />
          </div>
        )}

        {/* 챗봇 탭 */}
        {activeTab === 'chat' && (
          <div className="p-0">
            <ChatSidebar meetingId={meetingId!} meetingTitle={meeting.title} />
          </div>
        )}
      </div>
    </div>
  );
};

export default NoteDetail;


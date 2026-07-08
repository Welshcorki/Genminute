/**
 * NoteDetail 페이지 - 회의록 상세 뷰어
 */
import { useState, useEffect, useRef } from 'react';
import WaveSurfer from 'wavesurfer.js';
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
  X,
  Share2,
  CheckSquare,
  Gauge,
  Repeat,
  RotateCcw
} from 'lucide-react';
import { meetingService, type MeetingDetail } from '../services/meeting';
import { SPEAKER_COLORS, getSpeakerColorByIndex } from '../config/speakers';
import SummaryView from '../components/SummaryView';
import MindmapView from '../components/MindmapView';
import MinutesView from '../components/MinutesView';
import ActionItemsView from '../components/ActionItemsView';
import ChatSidebar from '../components/ChatSidebar';
import ShareModal from '../components/ShareModal';
import SpeakerShareChart from '../components/SpeakerShareChart';
import { useAudioPlayer } from '../hooks/useAudioPlayer';
import { useTranscriptSync } from '../hooks/useTranscriptSync';

type TabType = 'script' | 'summary' | 'mindmap' | 'minutes' | 'actionItems' | 'chat';

const NoteDetail = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();

  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('script');
  
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingDate, setIsEditingDate] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDate, setEditDate] = useState('');
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  const player = useAudioPlayer(meeting?.is_video ?? false);
  const waveformRef = useRef<HTMLDivElement>(null);

  const transcriptSync = useTranscriptSync({
    transcript: meeting?.transcript,
    currentTime: player.currentTime,
    seekTo: player.seekTo,
    isPlaying: player.isPlaying,
    togglePlay: player.togglePlay,
  });

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

  // WaveSurfer
  useEffect(() => {
    if (!player.showWaveform || !waveformRef.current || !meeting || meeting.is_video) return;

    const wavesurfer = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#6366f1',
      progressColor: '#4f46e5',
      cursorColor: '#312e81',
      barWidth: 2,
      barRadius: 3,
      height: 128,
      normalize: true,
      backend: 'WebAudio',
      mediaControls: false,
    });

    wavesurfer.load(meeting.audio_url);

    const handlePlay = () => {
      if (player.audioRef.current && !player.audioRef.current.paused) {
        wavesurfer.play();
      }
    };
    const handlePause = () => wavesurfer.pause();

    const syncTime = () => {
      if (player.audioRef.current && player.duration > 0) {
        const ct = player.audioRef.current.currentTime;
        if (Math.abs(wavesurfer.getCurrentTime() - ct) > 0.1) {
          wavesurfer.seekTo(ct / player.duration);
        }
      }
    };

    // Wavesurfer version 7 "seeking" or "interaction"
    wavesurfer.on('interaction', () => {
      if (player.audioRef.current) {
        const seekTime = wavesurfer.getCurrentTime();
        transcriptSync.handleTimeSeek(seekTime);
      }
    });

    const audio = player.audioRef.current;
    if (audio) {
      audio.addEventListener('play', handlePlay);
      audio.addEventListener('pause', handlePause);
      audio.addEventListener('timeupdate', syncTime);
    }

    wavesurfer.setPlaybackRate(player.playbackRate);

    return () => {
      if (audio) {
        audio.removeEventListener('play', handlePlay);
        audio.removeEventListener('pause', handlePause);
        audio.removeEventListener('timeupdate', syncTime);
      }
      wavesurfer.destroy();
    };
  }, [player.showWaveform, meeting?.audio_url, meeting?.is_video, player.playbackRate, player.duration]);

  const handleDelete = async () => {
    if (!meetingId || !meeting?.can_edit) return;
    if (!window.confirm('정말 이 회의록을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

    try {
      await meetingService.deleteMeeting(meetingId);
      navigate('/notes');
    } catch (err) {
      console.error('삭제 실패:', err);
      alert('회의록 삭제에 실패했습니다.');
    }
  };

  const handleStartEditTitle = () => {
    if (!meeting) return;
    setEditTitle(meeting.title);
    setIsEditingTitle(true);
    setIsMenuOpen(false);
  };

  const handleStartEditDate = () => {
    if (!meeting) return;
    const dateStr = meeting.meeting_date.replace(' ', 'T').slice(0, 16);
    setEditDate(dateStr);
    setIsEditingDate(true);
    setIsMenuOpen(false);
  };

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

  const handleSaveDate = async () => {
    if (!meetingId || !editDate) return;

    try {
      const result = await meetingService.updateMeetingDate(meetingId, editDate);
      if (result.success) {
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

  const getSpeakerColor = (speaker: string): string => {
    if (!meeting?.participants) return SPEAKER_COLORS[0].chip;
    const index = meeting.participants.indexOf(speaker);
    return getSpeakerColorByIndex(index).chip;
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-10 h-10 text-brand-600 animate-spin mb-4" />
        <p className="text-slate-500">회의록을 불러오는 중...</p>
      </div>
    );
  }

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
          className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
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
                  className="text-2xl font-bold text-slate-900 border border-brand-300 rounded-lg px-3 py-1 flex-1 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveTitle();
                    if (e.key === 'Escape') setIsEditingTitle(false);
                  }}
                />
                <button
                  onClick={handleSaveTitle}
                  className="px-3 py-1 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm"
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
                    className="border border-brand-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    autoFocus
                  />
                  <button
                    onClick={handleSaveDate}
                    className="px-2 py-1 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-xs"
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
                {player.formatTime(player.duration)}
              </span>
            </div>
          </div>

          {meeting.can_edit && (
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                aria-label="더보기 메뉴"
                aria-expanded={isMenuOpen}
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
                      onClick={() => {
                        setIsShareModalOpen(true);
                        setIsMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-left text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <Share2 className="w-4 h-4" />
                      공유
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

      {/* 미디어 플레이어 */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 shadow-sm">
        {meeting.is_video ? (
          <video 
            ref={player.videoRef} 
            src={meeting.audio_url} 
            preload="metadata"
            className="w-full rounded-lg mb-4"
            style={{ maxHeight: '400px' }}
          />
        ) : (
          <audio ref={player.audioRef} src={meeting.audio_url} preload="metadata" />
        )}
        
        {!meeting.is_video && player.showWaveform && (
          <div ref={waveformRef} className="w-full h-32 mb-4 rounded-lg bg-slate-50" />
        )}
        
        <div className="flex items-center gap-4">
          <button
            onClick={player.togglePlay}
            aria-label={player.isPlaying ? '일시정지' : '재생'}
            className="p-3 bg-brand-600 text-white rounded-full hover:bg-brand-700 transition-colors"
          >
            {player.isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          <div className="flex-1">
            <div className="relative">
              <input
                type="range"
                aria-label="재생 위치"
                min={0}
                max={player.duration || 100}
                value={player.currentTime}
                onChange={(e) => transcriptSync.handleTimeSeek(parseFloat(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
              />
              {player.loopStart !== null && player.loopEnd !== null && (
                <div
                  className="absolute top-0 h-2 bg-brand-300 rounded-lg pointer-events-none"
                  style={{
                    left: `${(player.loopStart / player.duration) * 100}%`,
                    width: `${((player.loopEnd - player.loopStart) / player.duration) * 100}%`,
                  }}
                />
              )}
            </div>
            <div className="flex justify-between text-xs font-mono text-slate-500 mt-1">
              <span>{player.formatTime(player.currentTime)}</span>
              <span>{player.formatTime(player.duration)}</span>
            </div>
            {player.loopStart !== null && player.loopEnd !== null && (
              <div className="text-xs font-mono text-brand-600 mt-1">
                반복: {player.formatTime(player.loopStart)} - {player.formatTime(player.loopEnd)}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-slate-500" />
            <select
              value={player.playbackRate}
              onChange={(e) => player.setPlaybackRate(parseFloat(e.target.value))}
              className="text-sm border border-slate-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value={0.5}>0.5x</option>
              <option value={0.75}>0.75x</option>
              <option value={1.0}>1.0x</option>
              <option value={1.25}>1.25x</option>
              <option value={1.5}>1.5x</option>
              <option value={1.75}>1.75x</option>
              <option value={2.0}>2.0x</option>
            </select>
          </div>

          <div className="flex items-center gap-1 border-l border-slate-200 pl-2">
            <button
              onClick={() => player.setLoopPoint('start')}
              className={`p-2 rounded-lg transition-colors ${
                player.loopStart !== null
                  ? 'bg-brand-100 text-brand-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
              }`}
              title="반복 시작점 설정"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={() => player.setLoopPoint('end')}
              className={`p-2 rounded-lg transition-colors ${
                player.loopEnd !== null
                  ? 'bg-brand-100 text-brand-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
              }`}
              title="반복 끝점 설정"
            >
              <RotateCcw className="w-4 h-4 rotate-180" />
            </button>
            {player.loopStart !== null && player.loopEnd !== null && (
              <>
                <button
                  onClick={player.toggleLoop}
                  className={`p-2 rounded-lg transition-colors ${
                    player.isLooping
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                  }`}
                  title="구간 반복 재생"
                >
                  <Repeat className="w-4 h-4" />
                </button>
                <button
                  onClick={player.clearLoop}
                  className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  title="반복 구간 초기화"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            )}
          </div>

          <button
            onClick={player.toggleMute}
            aria-label={player.isMuted ? '음소거 해제' : '음소거'}
            className="p-2 text-slate-500 hover:text-slate-700 transition-colors"
          >
            {player.isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </button>
          
          {!meeting.is_video && (
            <button
              onClick={() => player.setShowWaveform(!player.showWaveform)}
              className={`p-2 rounded-lg transition-colors ${
                player.showWaveform
                  ? 'bg-brand-100 text-brand-600'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
              }`}
              title="파형 시각화"
            >
              <Network className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="flex border-b border-slate-200 mb-6">
        {[
          { id: 'script', label: '스크립트', icon: FileText },
          { id: 'summary', label: '요약', icon: FileText },
          { id: 'mindmap', label: '마인드맵', icon: Network },
          { id: 'minutes', label: '회의록', icon: FileText },
          { id: 'actionItems', label: 'Action Items', icon: CheckSquare },
          { id: 'chat', label: '챗봇', icon: MessageCircle },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600'
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
        {activeTab === 'script' && (
          <div ref={transcriptSync.transcriptRef} className="p-6 max-h-[600px] overflow-y-auto">
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
                    onClick={() => transcriptSync.handleSegmentClick(segment)}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      transcriptSync.activeSegmentId === segment.id
                        ? 'bg-brand-50 ring-2 ring-brand-500'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded border ${getSpeakerColor(segment.speaker_label)}`}>
                        {segment.speaker_label}
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        {player.formatTime(segment.start_time)} - {player.formatTime(segment.end_time)}
                      </span>
                    </div>
                    <p className="text-slate-700 leading-relaxed">{segment.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <SummaryView meetingId={meetingId!} />
            </div>
            <div className="lg:col-span-1">
              <SpeakerShareChart 
                speakerShare={meeting.speaker_share?.reduce((acc, curr) => ({
                  ...acc,
                  [curr.speaker_label]: curr.percentage
                }), {}) || {}} 
              />
            </div>
          </div>
        )}

        {activeTab === 'mindmap' && (
          <div className="p-6">
            <MindmapView meetingId={meetingId!} />
          </div>
        )}

        {activeTab === 'minutes' && (
          <div className="p-6">
            <MinutesView meetingId={meetingId!} />
          </div>
        )}

        {activeTab === 'actionItems' && (
          <div className="p-6">
            <ActionItemsView meetingId={meetingId!} />
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="p-0">
            <ChatSidebar meetingId={meetingId!} meetingTitle={meeting.title} />
          </div>
        )}
      </div>

      {meetingId && (
        <ShareModal
          isOpen={isShareModalOpen}
          onClose={() => setIsShareModalOpen(false)}
          meetingId={meetingId}
        />
      )}
    </div>
  );
};

export default NoteDetail;

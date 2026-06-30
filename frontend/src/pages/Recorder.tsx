/**
 * Recorder 페이지 - 실시간 오디오 녹음
 * 
 * 기능:
 * - 마이크 녹음 (대면 회의/강의)
 * - 시스템 오디오 녹화 (Zoom/화상회의)
 * - 실시간 파형 시각화
 * - 녹음 완료 후 업로드
 */
import { useState, useMemo, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mic, Monitor, Play, Pause, Square, Upload, Loader2, AlertCircle, ArrowLeft, RotateCcw, LogIn } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useRecorder, type RecordingType } from '../hooks/useRecorder';
import AudioVisualizer from '../components/AudioVisualizer';
import { useUpload } from '../contexts/UploadContext';

type PageState = 'select' | 'recording' | 'preview' | 'uploading' | 'error';

const Recorder = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { addUpload } = useUpload();
  
  // 페이지 상태
  const [pageState, setPageState] = useState<PageState>('select');
  const [title, setTitle] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // 녹음 훅
  const {
    state: recordingState,
    recordingType,
    duration,
    recordedBlob,
    analyser,
    startMicRecording,
    startSystemRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    reset,
  } = useRecorder({
    onStop: () => {
      setPageState('preview');
    },
    onError: (err) => {
      setError(err.message);
      setPageState('error');
    },
  });

  // 시간 포맷팅
  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hrs > 0) {
      return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 녹음 시작
  const handleStartRecording = async (type: RecordingType) => {
    if (!isAuthenticated) {
      setError('녹음을 시작하려면 로그인이 필요합니다.');
      return;
    }

    setError(null);
    setPageState('recording');
    
    if (type === 'mic') {
      await startMicRecording();
    } else {
      await startSystemRecording();
    }
  };

  // 녹음 취소 및 처음으로
  const handleCancel = () => {
    reset();
    setTitle('');
    setError(null);
    setPageState('select');
  };

  // 업로드 (전역 Context 사용)
  const handleUpload = async () => {
    if (!recordedBlob || !title.trim()) return;

    try {
      // Blob을 File로 변환
      const extension = recordingType === 'sys' ? 'webm' : 'webm';
      const fileName = `${title.trim().replace(/[^a-zA-Z0-9가-힣\s]/g, '')}.${extension}`;
      const file = new File([recordedBlob], fileName, { type: recordedBlob.type });

      // 전역 업로드 Context에 작업 추가 (UploadStatusBar에 자동으로 표시됨)
      const meetingId = await addUpload(
        file,
        title.trim()
      );

      // 완료 시 노트 상세 페이지로 이동
      if (meetingId) {
        navigate(`/notes/${meetingId}`);
      }
    } catch (err) {
      setError('업로드 중 오류가 발생했습니다.');
      setPageState('error');
    }
  };

  // 다시 녹음
  const handleReRecord = () => {
    reset();
    setTitle('');
    setPageState('select');
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* 헤더 */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-slate-500 hover:text-slate-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          뒤로 가기
        </button>
        <h1 className="text-3xl font-bold text-slate-900">실시간 녹음</h1>
        <p className="text-slate-500 mt-2">
          회의, 강의, 인터뷰를 실시간으로 녹음하고 AI가 자동으로 정리합니다.
        </p>
      </div>

      {/* Step 1: 녹음 타입 선택 */}
      {pageState === 'select' && (
        <div className="space-y-6">
          {!isAuthenticated && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <AlertCircle className="w-5 h-5 text-amber-600" />
                <p className="text-sm font-medium text-amber-900">로그인이 필요합니다</p>
              </div>
              <p className="text-sm text-amber-700 mb-3">
                녹음을 시작하려면 먼저 로그인해주세요.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm font-medium"
              >
                <LogIn className="w-4 h-4 mr-2" />
                로그인하기
              </Link>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 마이크 녹음 */}
            <button
              onClick={() => handleStartRecording('mic')}
              disabled={!isAuthenticated}
              className={`group p-6 bg-white border-2 rounded-2xl transition-all text-left ${
                isAuthenticated
                  ? 'border-slate-200 hover:border-indigo-500 hover:shadow-lg'
                  : 'border-slate-100 opacity-50 cursor-not-allowed'
              }`}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-indigo-50 rounded-xl group-hover:bg-indigo-100 transition-colors">
                  <Mic className="w-8 h-8 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">마이크 녹음</h3>
                  <p className="text-sm text-slate-500">대면 회의 / 강의</p>
                </div>
              </div>
              <p className="text-slate-600 text-sm leading-relaxed">
                노트북이나 스마트폰의 마이크로 주변 소리를 녹음합니다. 
                오프라인 회의나 강의에 적합합니다.
              </p>
            </button>

            {/* 시스템 오디오 녹화 */}
            <button
              onClick={() => handleStartRecording('sys')}
              disabled={!isAuthenticated}
              className={`group p-6 bg-white border-2 rounded-2xl transition-all text-left ${
                isAuthenticated
                  ? 'border-slate-200 hover:border-teal-500 hover:shadow-lg'
                  : 'border-slate-100 opacity-50 cursor-not-allowed'
              }`}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-teal-50 rounded-xl group-hover:bg-teal-100 transition-colors">
                  <Monitor className="w-8 h-8 text-teal-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">시스템 오디오</h3>
                  <p className="text-sm text-slate-500">Zoom / 화상회의</p>
                </div>
              </div>
              <p className="text-slate-600 text-sm leading-relaxed">
                컴퓨터에서 재생되는 소리를 녹화합니다. 
                Zoom, Teams, Meet 등 화상회의에 적합합니다.
              </p>
              <div className="mt-3 p-2 bg-indigo-50 border border-indigo-200 rounded-lg">
                <p className="text-xs text-indigo-800">
                  💡 화면 공유 시 <strong>"시스템 오디오 공유"</strong>를 체크해주세요
                </p>
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Step 2: 녹음 중 */}
      {pageState === 'recording' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          {/* 녹음 타입 표시 */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {recordingType === 'mic' ? (
              <>
                <Mic className="w-5 h-5 text-indigo-600" />
                <span className="text-slate-600 font-medium">마이크 녹음</span>
              </>
            ) : (
              <>
                <Monitor className="w-5 h-5 text-teal-600" />
                <span className="text-slate-600 font-medium">시스템 오디오 녹화</span>
              </>
            )}
          </div>

          {/* 타이머 */}
          <div className="text-center mb-8">
            <div className="text-6xl font-mono font-bold text-slate-900">
              {formatTime(duration)}
            </div>
            <div className={`mt-2 flex items-center justify-center gap-2 ${
              recordingState === 'recording' ? 'text-red-500' : 'text-amber-500'
            }`}>
              <span className={`w-3 h-3 rounded-full ${
                recordingState === 'recording' ? 'bg-red-500 animate-pulse' : 'bg-amber-500'
              }`} />
              <span className="font-medium">
                {recordingState === 'recording' ? '녹음 중' : '일시정지'}
              </span>
            </div>
          </div>

          {/* 파형 시각화 */}
          <div className="h-32 bg-slate-50 rounded-xl mb-8 overflow-hidden">
            <AudioVisualizer
              analyser={analyser}
              isRecording={recordingState === 'recording'}
              barColor={recordingType === 'mic' ? '#4f46e5' : '#0d9488'}
            />
          </div>

          {/* 컨트롤 버튼 */}
          <div className="flex justify-center gap-4">
            {/* 일시정지/재개 */}
            {recordingState === 'recording' ? (
              <button
                onClick={pauseRecording}
                className="p-4 bg-amber-100 text-amber-600 rounded-full hover:bg-amber-200 transition-colors"
                title="일시정지"
              >
                <Pause className="w-6 h-6" />
              </button>
            ) : recordingState === 'paused' ? (
              <button
                onClick={resumeRecording}
                className="p-4 bg-indigo-100 text-indigo-600 rounded-full hover:bg-indigo-200 transition-colors"
                title="재개"
              >
                <Play className="w-6 h-6" />
              </button>
            ) : null}

            {/* 정지 */}
            <button
              onClick={stopRecording}
              className="p-4 bg-red-100 text-red-600 rounded-full hover:bg-red-200 transition-colors"
              title="녹음 중지"
            >
              <Square className="w-6 h-6" />
            </button>

            {/* 취소 */}
            <button
              onClick={handleCancel}
              className="p-4 bg-slate-100 text-slate-600 rounded-full hover:bg-slate-200 transition-colors"
              title="취소"
            >
              <RotateCcw className="w-6 h-6" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: 미리보기 및 업로드 */}
      {pageState === 'preview' && recordedBlob && (
        <PreviewSection 
          recordedBlob={recordedBlob}
          recordingType={recordingType}
          duration={duration}
          formatTime={formatTime}
          title={title}
          setTitle={setTitle}
          handleReRecord={handleReRecord}
          handleUpload={handleUpload}
        />
      )}

      {/* Step 4: 업로드 중 */}
      {pageState === 'uploading' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-indigo-50 rounded-full">
              <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
            </div>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">분석 중</h2>
          <p className="text-slate-500 mb-4">오른쪽 하단의 업로드 상태바에서 진행 상황을 확인할 수 있습니다.</p>
          <p className="text-sm text-slate-400">
            다른 페이지로 이동해도 진행 상황을 확인할 수 있습니다.
          </p>
        </div>
      )}

      {/* Step 5: 에러 */}
      {pageState === 'error' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-red-50 rounded-full">
              <AlertCircle className="w-10 h-10 text-red-600" />
            </div>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">오류 발생</h2>
          <p className="text-red-600 mb-6">{error}</p>
          <div className="flex justify-center gap-4">
            <button
              onClick={handleCancel}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors font-medium"
            >
              처음으로
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// 미리보기 섹션 컴포넌트 (오디오 URL 메모이제이션을 위해 분리)
interface PreviewSectionProps {
  recordedBlob: Blob;
  recordingType: RecordingType | null;
  duration: number;
  formatTime: (seconds: number) => string;
  title: string;
  setTitle: (title: string) => void;
  handleReRecord: () => void;
  handleUpload: () => void;
}

const PreviewSection = ({
  recordedBlob,
  recordingType,
  duration,
  formatTime,
  title,
  setTitle,
  handleReRecord,
  handleUpload,
}: PreviewSectionProps) => {
  // 오디오 URL을 메모이제이션하여 리렌더링 시 재생성 방지
  const audioUrl = useMemo(() => {
    return URL.createObjectURL(recordedBlob);
  }, [recordedBlob]);

  // 컴포넌트 언마운트 시 URL 해제
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
      <h2 className="text-xl font-bold text-slate-900 mb-6">녹음 완료</h2>

      {/* 녹음 정보 */}
      <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl mb-6">
        <div className={`p-3 rounded-xl ${
          recordingType === 'mic' ? 'bg-indigo-100' : 'bg-teal-100'
        }`}>
          {recordingType === 'mic' ? (
            <Mic className="w-6 h-6 text-indigo-600" />
          ) : (
            <Monitor className="w-6 h-6 text-teal-600" />
          )}
        </div>
        <div>
          <p className="font-medium text-slate-900">
            {recordingType === 'mic' ? '마이크 녹음' : '시스템 오디오 녹화'}
          </p>
          <p className="text-sm text-slate-500">
            {formatTime(duration)} • {(recordedBlob.size / (1024 * 1024)).toFixed(2)} MB
          </p>
        </div>
      </div>

      {/* 오디오 플레이어 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          미리 듣기
        </label>
        <audio
          key={audioUrl} // key를 추가하여 URL이 변경될 때만 재생성
          controls
          src={audioUrl}
          className="w-full"
        />
      </div>

      {/* 제목 입력 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">
          회의 제목 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="예: 주간 업무 보고 회의"
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>

      {/* 버튼 */}
      <div className="flex gap-4">
        <button
          onClick={handleReRecord}
          className="flex-1 px-4 py-3 border border-slate-300 text-slate-600 rounded-xl hover:bg-slate-50 transition-colors font-medium"
        >
          다시 녹음
        </button>
        <button
          onClick={handleUpload}
          disabled={!title.trim()}
          className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center gap-2"
        >
          <Upload className="w-5 h-5" />
          분석 시작
        </button>
      </div>
    </div>
  );
};

export default Recorder;


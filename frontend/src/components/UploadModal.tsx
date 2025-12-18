/**
 * 파일 업로드 모달
 * - Drag & Drop 지원
 * - 파일 선택
 * - 제목/날짜 입력
 * - 전역 업로드 상태 관리 (Context 연동)
 */
import { useState, useRef, useCallback } from 'react';
import { X, Upload, FileAudio, FileVideo, AlertCircle, RotateCcw } from 'lucide-react';
import { useUpload } from '../contexts/UploadContext';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: (meetingId: string) => void;
}

type UploadStep = 'select' | 'form' | 'error';

const ALLOWED_EXTENSIONS = ['mp3', 'wav', 'm4a', 'mp4', 'webm', 'ogg'];
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

export const UploadModal = ({ isOpen, onClose, onComplete }: UploadModalProps) => {
  const [step, setStep] = useState<UploadStep>('select');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [meetingDate, setMeetingDate] = useState('');
  const [tempDate, setTempDate] = useState(''); // 임시 날짜 값
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false); // 날짜 선택기 열림 상태
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addUpload } = useUpload();

  // 파일 유효성 검사
  const validateFile = (file: File): string | null => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
      return `지원하지 않는 파일 형식입니다. (${ALLOWED_EXTENSIONS.join(', ')})`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return '파일 크기가 500MB를 초과합니다.';
    }
    return null;
  };

  // 파일 선택 처리
  const handleFileSelect = useCallback((file: File) => {
    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      setStep('error');
      return;
    }
    
    setSelectedFile(file);
    // 파일명에서 확장자 제거하여 기본 제목으로 설정
    const defaultTitle = file.name.replace(/\.[^/.]+$/, '');
    setTitle(defaultTitle);
    setStep('form');
  }, []);

  // Drag & Drop 핸들러
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // 파일 input 변경 핸들러
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  // 업로드 시작 (전역 Context로 관리)
  const handleUpload = async () => {
    if (!selectedFile || !title.trim()) return;

    // 모달 닫고 백그라운드에서 업로드 진행
    handleClose();

    // 전역 업로드 Context에 작업 추가
    const meetingId = await addUpload(
      selectedFile,
      title.trim(),
      meetingDate || undefined
    );

    // 완료 시 콜백 호출
    if (meetingId) {
      onComplete?.(meetingId);
    }
  };

  // 모달 닫기 및 초기화
  const handleClose = () => {
    setStep('select');
    setSelectedFile(null);
    setTitle('');
    setMeetingDate('');
    setErrorMessage('');
    setIsDragging(false);
    onClose();
  };

  // 다시 시도
  const handleRetry = () => {
    setStep('select');
    setSelectedFile(null);
    setTitle('');
    setMeetingDate('');
    setErrorMessage('');
  };

  // 파일 타입 아이콘
  const getFileIcon = () => {
    if (!selectedFile) return <Upload className="w-8 h-8 text-indigo-600" />;
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (['mp4', 'webm'].includes(ext || '')) {
      return <FileVideo className="w-8 h-8 text-indigo-600" />;
    }
    return <FileAudio className="w-8 h-8 text-indigo-600" />;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 배경 오버레이 */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* 모달 컨텐츠 */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 p-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-900">
            파일 업로드
          </h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Step 1: 파일 선택 */}
        {step === 'select' && (
          <>
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
                isDragging 
                  ? 'border-indigo-500 bg-indigo-50' 
                  : 'border-slate-300 hover:border-indigo-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
                onChange={handleFileInputChange}
                className="hidden"
              />
              <div className="flex justify-center mb-4">
                <div className="p-4 bg-indigo-50 rounded-full">
                  <Upload className="w-8 h-8 text-indigo-600" />
                </div>
              </div>
              <p className="text-slate-600 mb-2">
                파일을 드래그하거나 클릭하여 업로드
              </p>
              <p className="text-sm text-slate-400">
                지원 형식: MP3, WAV, M4A, MP4, WEBM (최대 500MB)
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                닫기
              </button>
            </div>
          </>
        )}

        {/* Step 2: 제목/날짜 입력 폼 */}
        {step === 'form' && selectedFile && (
          <>
            {/* 선택된 파일 정보 */}
            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg mb-6">
              <div className="p-2 bg-white rounded-lg shadow-sm">
                {getFileIcon()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-900 truncate">{selectedFile.name}</p>
                <p className="text-sm text-slate-500">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setStep('select');
                }}
                className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-slate-500" />
              </button>
            </div>

            {/* 제목 입력 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                회의 제목 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="예: 주간 업무 보고 회의"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {/* 날짜 입력 (선택) */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                회의 날짜 <span className="text-slate-400">(선택)</span>
              </label>
              
              {/* 날짜 표시 및 선택 버튼 */}
              {!isDatePickerOpen ? (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setTempDate(meetingDate);
                      setIsDatePickerOpen(true);
                    }}
                    className="flex-1 px-4 py-2 border border-slate-300 rounded-lg text-left hover:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
                  >
                    {meetingDate ? (
                      <span className="text-slate-900">
                        {(() => {
                          const date = new Date(meetingDate);
                          const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
                          const dayName = dayNames[date.getDay()];
                          return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 (${dayName}) ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
                        })()}
                      </span>
                    ) : (
                      <span className="text-slate-400">날짜를 선택하세요</span>
                    )}
                  </button>
                  {meetingDate && (
                    <button
                      type="button"
                      onClick={() => setMeetingDate('')}
                      className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                      title="날짜 삭제"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ) : (
                /* 날짜 선택기 (열린 상태) */
                <div className="border border-indigo-300 rounded-lg p-4 bg-indigo-50/30">
                  <input
                    type="datetime-local"
                    value={tempDate}
                    onChange={(e) => setTempDate(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white"
                    autoFocus
                  />
                  {tempDate && (
                    <p className="mt-2 text-sm text-slate-600">
                      {(() => {
                        const date = new Date(tempDate);
                        const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
                        const dayName = dayNames[date.getDay()];
                        return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 (${dayName}) ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
                      })()}
                    </p>
                  )}
                  <div className="flex justify-end gap-2 mt-3">
                    <button
                      type="button"
                      onClick={() => {
                        setTempDate('');
                        setIsDatePickerOpen(false);
                      }}
                      className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
                    >
                      취소
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setMeetingDate(tempDate);
                        setIsDatePickerOpen(false);
                      }}
                      className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      확인
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* 버튼 */}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setStep('select');
                }}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                뒤로
              </button>
              <button
                onClick={handleUpload}
                disabled={!title.trim()}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                분석 시작
              </button>
            </div>
          </>
        )}

        {/* 에러 */}
        {step === 'error' && (
          <div className="text-center py-8">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-red-50 rounded-full">
                <AlertCircle className="w-10 h-10 text-red-600" />
              </div>
            </div>
            <p className="text-lg font-medium text-slate-900 mb-2">
              오류가 발생했습니다
            </p>
            <p className="text-sm text-red-600 mb-6">
              {errorMessage}
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                닫기
              </button>
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                다시 시도
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadModal;

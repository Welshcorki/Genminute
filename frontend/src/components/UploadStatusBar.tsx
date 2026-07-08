/**
 * 전역 업로드 상태 표시 바
 * - 화면 하단 우측에 고정
 * - 진행 중인 업로드 목록 표시
 * - 취소/제거 기능
 * - 접기/펼치기 기능
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Loader2,
  X,
  CheckCircle,
  AlertCircle,
  ChevronUp,
  ChevronDown,
  ExternalLink,
  Trash2,
} from 'lucide-react';
import { useUpload } from '../contexts/UploadContext';
import type { UploadTask } from '../contexts/UploadContext';

// 진행 단계별 표시 정보
const STEP_INFO: Record<string, { label: string; percent: number }> = {
  upload: { label: '업로드 중', percent: 10 },
  validation: { label: '검증 중', percent: 20 },
  conversion: { label: '변환 중', percent: 30 },
  stt: { label: 'STT 변환 중', percent: 50 },
  chunking: { label: '분석 중', percent: 70 },
  mindmap: { label: '마인드맵 생성 중', percent: 90 },
  complete: { label: '완료', percent: 100 },
  error: { label: '오류', percent: 0 },
};

// 개별 업로드 항목
const UploadTaskItem = ({ task }: { task: UploadTask }) => {
  const { removeTask, cancelTask } = useUpload();
  const navigate = useNavigate();

  const stepInfo = task.progress?.step
    ? STEP_INFO[task.progress.step] || { label: '처리 중', percent: 0 }
    : { label: '준비 중', percent: 0 };

  const handleViewResult = () => {
    if (task.meetingId) {
      navigate(`/notes/${task.meetingId}`);
    }
  };

  return (
    <div className="px-4 py-3 border-b border-slate-100 last:border-b-0">
      {/* 파일명 및 액션 버튼 */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-900 truncate flex-1 pr-2">
          {task.title}
        </span>
        <div className="flex items-center gap-1">
          {task.status === 'uploading' && (
            <button
              onClick={() => cancelTask(task.id)}
              className="p-1 hover:bg-slate-100 rounded text-slate-400 hover:text-red-500 transition-colors"
              title="취소"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {task.status === 'complete' && (
            <>
              <button
                onClick={handleViewResult}
                className="p-1 hover:bg-slate-100 rounded text-brand-500 hover:text-brand-600 transition-colors"
                title="결과 보기"
              >
                <ExternalLink className="w-4 h-4" />
              </button>
              <button
                onClick={() => removeTask(task.id)}
                className="p-1 hover:bg-slate-100 rounded text-slate-400 hover:text-slate-600 transition-colors"
                title="제거"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}
          {task.status === 'error' && (
            <button
              onClick={() => removeTask(task.id)}
              className="p-1 hover:bg-slate-100 rounded text-slate-400 hover:text-slate-600 transition-colors"
              title="제거"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* 상태 표시 */}
      <div className="flex items-center gap-2">
        {task.status === 'uploading' && (
          <>
            <Loader2 className="w-3 h-3 animate-spin text-brand-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">{stepInfo.label}</span>
                <span className="text-xs font-mono text-slate-400">{stepInfo.percent}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-600 rounded-full transition-all duration-300"
                  style={{ width: `${stepInfo.percent}%` }}
                />
              </div>
            </div>
          </>
        )}
        {task.status === 'complete' && (
          <>
            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
            <span className="text-xs text-green-600">분석 완료</span>
          </>
        )}
        {task.status === 'error' && (
          <>
            <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
            <span className="text-xs text-red-600 truncate">
              {task.errorMessage || '오류 발생'}
            </span>
          </>
        )}
      </div>
    </div>
  );
};

export const UploadStatusBar = () => {
  const { activeTasks, clearCompletedTasks } = useUpload();
  const [isExpanded, setIsExpanded] = useState(true);

  // 작업이 없으면 렌더링하지 않음
  if (activeTasks.length === 0) return null;

  const uploadingCount = activeTasks.filter(t => t.status === 'uploading').length;
  const completedCount = activeTasks.filter(t => t.status === 'complete').length;
  const errorCount = activeTasks.filter(t => t.status === 'error').length;

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden">
      {/* 헤더 */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200 cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {uploadingCount > 0 && (
            <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
          )}
          <span className="font-medium text-slate-900">
            업로드 {uploadingCount > 0 ? `진행 중 (${uploadingCount})` : ''}
          </span>
          {completedCount > 0 && (
            <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
              {completedCount} 완료
            </span>
          )}
          {errorCount > 0 && (
            <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
              {errorCount} 오류
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {(completedCount > 0 || errorCount > 0) && uploadingCount === 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearCompletedTasks();
              }}
              className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-600 transition-colors"
              title="모두 지우기"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {/* 작업 목록 */}
      {isExpanded && (
        <div className="max-h-64 overflow-y-auto">
          {activeTasks.map(task => (
            <UploadTaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadStatusBar;


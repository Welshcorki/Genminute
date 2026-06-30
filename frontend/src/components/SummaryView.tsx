/**
 * SummaryView - 회의 요약 표시 컴포넌트
 * 
 * 기능:
 * - 요약 로딩 및 표시
 * - 요약이 없을 경우 생성 버튼
 * - 마크다운 렌더링
 */
import { useState, useEffect } from 'react';
import { Loader2, RefreshCw, FileText, Sparkles } from 'lucide-react';
import { summaryService } from '../services/summary';

interface SummaryViewProps {
  meetingId: string;
}

export const SummaryView = ({ meetingId }: SummaryViewProps) => {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 요약 로드
  const loadSummary = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await summaryService.getSummary(meetingId);
      if (response.success && response.summary) {
        setSummary(response.summary);
      } else {
        setSummary(null);
      }
    } catch (err) {
      console.error('요약 로드 실패:', err);
      setError('요약을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 요약 생성
  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      const response = await summaryService.generateSummary(meetingId);
      if (response.success && response.summary) {
        setSummary(response.summary);
      } else {
        setError(response.error || '요약 생성에 실패했습니다.');
      }
    } catch (err) {
      console.error('요약 생성 실패:', err);
      setError('요약 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [meetingId]);

  // 로딩 중
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-500">요약을 불러오는 중...</p>
      </div>
    );
  }

  // 에러
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="p-4 bg-red-50 rounded-full mb-4">
          <FileText className="w-8 h-8 text-red-400" />
        </div>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadSummary}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          다시 시도
        </button>
      </div>
    );
  }

  // 요약 없음
  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="p-4 bg-slate-50 rounded-full mb-4">
          <FileText className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">
          아직 요약이 없습니다
        </h3>
        <p className="text-slate-500 mb-6 text-center max-w-md">
          AI가 회의 내용을 분석하여 핵심 내용을 정리합니다.
        </p>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              생성 중...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              요약 생성하기
            </>
          )}
        </button>
      </div>
    );
  }

  // 요약 표시
  return (
    <div className="prose prose-slate max-w-none">
      {/* 재생성 버튼 */}
      <div className="flex justify-end mb-4 not-prose">
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
        >
          {isGenerating ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          다시 생성
        </button>
      </div>

      {/* 마크다운 렌더링 (간단한 구현) */}
      <div className="whitespace-pre-wrap text-slate-700 leading-relaxed">
        {summary.split('\n').map((line, index) => {
          // 제목 처리
          if (line.startsWith('### ')) {
            return (
              <h3 key={`h3-${index}`} className="text-lg font-semibold text-slate-900 mt-6 mb-3">
                {line.replace('### ', '')}
              </h3>
            );
          }
          if (line.startsWith('## ')) {
            return (
              <h2 key={`h2-${index}`} className="text-xl font-bold text-slate-900 mt-8 mb-4 border-b border-slate-200 pb-2">
                {line.replace('## ', '')}
              </h2>
            );
          }
          if (line.startsWith('# ')) {
            return (
              <h1 key={`h1-${index}`} className="text-2xl font-bold text-indigo-600 mb-6">
                {line.replace('# ', '')}
              </h1>
            );
          }
          // 리스트 처리
          if (line.startsWith('- ') || line.startsWith('* ')) {
            return (
              <ul key={`ul-${index}`} className="list-disc list-inside ml-4 mb-2">
                <li className="text-slate-700">
                  {line.replace(/^[-*] /, '')}
                </li>
              </ul>
            );
          }
          // 빈 줄
          if (line.trim() === '') {
            return <br key={`br-${index}`} />;
          }
          // 일반 텍스트
          return (
            <p key={`p-${index}`} className="mb-2">
              {line}
            </p>
          );
        })}
      </div>
    </div>
  );
};

export default SummaryView;


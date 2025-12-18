import { useState, useEffect } from 'react';
import { Loader2, AlertCircle, FileText } from 'lucide-react';
import { minutesService } from '../services/minutes';

interface MinutesViewProps {
  meetingId: string;
}

const MinutesView = ({ meetingId }: MinutesViewProps) => {
  const [minutes, setMinutes] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMinutes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await minutesService.getMinutes(meetingId);
      
      if (response.success && response.has_minutes && response.minutes) {
        setMinutes(response.minutes);
      } else {
        setMinutes(null);
      }
    } catch (err: any) {
      console.error('회의록 로드 실패:', err);
      setError('회의록을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMinutes();
  }, [meetingId]);

  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      const response = await minutesService.generateMinutes(meetingId);
      
      if (response.success && response.minutes) {
        setMinutes(response.minutes);
      } else {
        setError(response.error || '회의록 생성에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('회의록 생성 실패:', err);
      setError(err.response?.data?.error || '회의록 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-500">회의록을 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2 text-red-600 mb-4">
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">오류 발생</span>
        </div>
        <p className="text-slate-600 mb-4">{error}</p>
        <button
          onClick={loadMinutes}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (!minutes) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-slate-50 rounded-full">
              <FileText className="w-8 h-8 text-slate-400" />
            </div>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">회의록이 아직 생성되지 않았습니다</h3>
          <p className="text-slate-500 mb-6">회의록을 생성하면 회의 내용을 정리된 형식으로 볼 수 있습니다.</p>
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 inline-block animate-spin mr-2" />
                생성 중...
              </>
            ) : (
              '회의록 생성하기'
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-slate-900">회의록</h2>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-4 h-4 inline-block animate-spin mr-2" />
              재생성 중...
            </>
          ) : (
            '다시 생성'
          )}
        </button>
      </div>
      <div className="prose prose-slate max-w-none">
        <div className="whitespace-pre-wrap text-slate-700 leading-relaxed">
          {minutes.split('\n').map((line, index) => {
            // 제목 처리 (# 제목)
            if (line.startsWith('# ')) {
              return (
                <h1 key={index} className="text-2xl font-bold text-slate-900 mt-6 mb-3">
                  {line.substring(2)}
                </h1>
              );
            }
            if (line.startsWith('## ')) {
              return (
                <h2 key={index} className="text-xl font-bold text-slate-900 mt-5 mb-2 border-b border-indigo-500 pb-1">
                  {line.substring(3)}
                </h2>
              );
            }
            if (line.startsWith('### ')) {
              return (
                <h3 key={index} className="text-lg font-semibold text-slate-900 mt-4 mb-2">
                  {line.substring(4)}
                </h3>
              );
            }
            // 리스트 처리 (- 항목)
            if (line.startsWith('- ') || line.startsWith('* ')) {
              return (
                <li key={index} className="ml-4 mb-1">
                  {line.substring(2)}
                </li>
              );
            }
            // 빈 줄
            if (line.trim() === '') {
              return <br key={index} />;
            }
            // 일반 텍스트
            return (
              <p key={index} className="mb-3">
                {line}
              </p>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default MinutesView;


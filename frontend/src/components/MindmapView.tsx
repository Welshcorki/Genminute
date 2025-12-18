/**
 * MindmapView - 회의 마인드맵 표시 컴포넌트
 * 
 * 기능:
 * - 마인드맵 로딩 및 표시
 * - 마인드맵이 없을 경우 생성 버튼
 * - 계층적 트리 구조 렌더링
 */
import { useState, useEffect } from 'react';
import { Loader2, RefreshCw, Network, Sparkles, ChevronRight, ChevronDown } from 'lucide-react';
import { mindmapService, type MindmapNode } from '../services/mindmap';

interface MindmapViewProps {
  meetingId: string;
}

// 마인드맵 노드 렌더링 컴포넌트
const MindmapNodeItem = ({ node, level = 0 }: { node: MindmapNode; level?: number }) => {
  const [isExpanded, setIsExpanded] = useState(level < 2); // 2단계까지 기본 펼침
  const hasChildren = node.children && node.children.length > 0;

  // 레벨별 스타일
  const getLevelStyles = () => {
    switch (level) {
      case 0:
        return 'text-xl font-bold text-indigo-600 bg-indigo-50 px-4 py-3 rounded-xl';
      case 1:
        return 'text-lg font-semibold text-slate-900 border-l-4 border-indigo-500 pl-4 py-2';
      case 2:
        return 'text-base font-medium text-slate-700 pl-4 py-1.5';
      default:
        return 'text-sm text-slate-600 pl-4 py-1';
    }
  };

  return (
    <div className={`${level > 0 ? 'ml-4' : ''}`}>
      <div
        className={`flex items-center gap-2 ${getLevelStyles()} ${
          hasChildren ? 'cursor-pointer hover:bg-slate-50 rounded-lg transition-colors' : ''
        }`}
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {hasChildren && (
          <span className="flex-shrink-0 text-slate-400">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </span>
        )}
        {!hasChildren && level > 0 && (
          <span className="w-2 h-2 bg-slate-300 rounded-full flex-shrink-0" />
        )}
        <span>{node.title}</span>
      </div>

      {hasChildren && isExpanded && (
        <div className={`mt-2 ${level === 0 ? 'ml-2' : ''}`}>
          {node.children!.map((child, index) => (
            <MindmapNodeItem key={index} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export const MindmapView = ({ meetingId }: MindmapViewProps) => {
  const [mindmap, setMindmap] = useState<MindmapNode | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 마인드맵 로드
  const loadMindmap = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await mindmapService.getMindmap(meetingId);
      if (response.success && response.mindmap) {
        setMindmap(response.mindmap);
      } else {
        setMindmap(null);
      }
    } catch (err) {
      console.error('마인드맵 로드 실패:', err);
      setError('마인드맵을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 마인드맵 생성
  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      const response = await mindmapService.generateMindmap(meetingId);
      if (response.success && response.mindmap) {
        setMindmap(response.mindmap);
      } else {
        setError(response.error || '마인드맵 생성에 실패했습니다.');
      }
    } catch (err) {
      console.error('마인드맵 생성 실패:', err);
      setError('마인드맵 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    loadMindmap();
  }, [meetingId]);

  // 로딩 중
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-500">마인드맵을 불러오는 중...</p>
      </div>
    );
  }

  // 에러
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="p-4 bg-red-50 rounded-full mb-4">
          <Network className="w-8 h-8 text-red-400" />
        </div>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadMindmap}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          다시 시도
        </button>
      </div>
    );
  }

  // 마인드맵 없음
  if (!mindmap) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="p-4 bg-slate-50 rounded-full mb-4">
          <Network className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">
          아직 마인드맵이 없습니다
        </h3>
        <p className="text-slate-500 mb-6 text-center max-w-md">
          AI가 회의 내용을 분석하여 구조화된 마인드맵을 생성합니다.
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
              마인드맵 생성하기
            </>
          )}
        </button>
      </div>
    );
  }

  // 마인드맵 표시
  return (
    <div>
      {/* 재생성 버튼 */}
      <div className="flex justify-end mb-4">
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

      {/* 마인드맵 트리 */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <MindmapNodeItem node={mindmap} />
      </div>
    </div>
  );
};

export default MindmapView;


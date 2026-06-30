/**
 * MindmapView - 회의 마인드맵 표시 컴포넌트
 * 
 * 기능:
 * - 마인드맵 로딩 및 표시
 * - 마인드맵이 없을 경우 생성 버튼
 * - 계층적 트리 구조 렌더링
 */
import { useState, useEffect } from 'react';
import { Loader2, RefreshCw, Network, Sparkles } from 'lucide-react';
import { mindmapService, type MindmapNode } from '../services/mindmap';

import { useRef } from 'react';
import { Transformer } from 'markmap-lib';
import { Markmap } from 'markmap-view';

interface MindmapViewProps {
  meetingId: string;
}

const transformer = new Transformer();

// Helper to convert MindmapNode tree to markdown text for Markmap
const convertNodeToMarkdown = (node: MindmapNode, depth = 1): string => {
  let markdown = `${'#'.repeat(depth)} ${node.title}\n`;
  if (node.children && node.children.length > 0) {
    node.children.forEach(child => {
      markdown += convertNodeToMarkdown(child, depth + 1);
    });
  }
  return markdown;
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

  // SVG Refs
  const svgRef = useRef<SVGSVGElement>(null);
  const markmapRef = useRef<Markmap | null>(null);

  // Markmap 초기화 및 렌더링
  useEffect(() => {
    if (!svgRef.current || !mindmap) return;
    
    // Convert current structure to Markdown
    const markdownStr = convertNodeToMarkdown(mindmap);

    // Transform Markdown to Markmap Root Node
    const { root } = transformer.transform(markdownStr);

    if (markmapRef.current) {
      markmapRef.current.setData(root);
      markmapRef.current.fit();
    } else {
      markmapRef.current = Markmap.create(svgRef.current, {
        color: (node: any) => {
          // Color logic based on depth
          const depthColors = ['#4f46e5', '#14b8a6', '#f59e0b', '#f43f5e', '#a855f7'];
          return depthColors[Math.min(node.depth, depthColors.length - 1)];
        },
        paddingX: 16,
      }, root);
    }
  }, [mindmap]);

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

      {/* 마인드맵 렌더러 (SVG) */}
      <div className="bg-white rounded-xl border border-slate-200 p-2 overflow-hidden w-full h-[600px] flex items-center justify-center">
        <svg ref={svgRef} className="w-full h-full" />
      </div>
    </div>
  );
};

export default MindmapView;


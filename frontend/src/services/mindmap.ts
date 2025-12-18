/**
 * 마인드맵 서비스
 * - 회의 마인드맵 조회
 * - 마인드맵 마크다운 → 트리 구조 변환
 */
import api from './api';

export interface MindmapNode {
  title: string;
  children?: MindmapNode[];
}

export interface MindmapData {
  meeting_id: string;
  mindmap: MindmapNode;
  created_at?: string;
}

export interface MindmapResponse {
  success: boolean;
  mindmap?: MindmapNode;
  mindmap_markdown?: string;
  error?: string;
}

/**
 * 마크다운 마인드맵을 트리 구조로 변환
 * 예시 입력:
 * # 회의 제목
 * ## 주제 1
 * ### 세부 항목 1-1
 * ### 세부 항목 1-2
 * ## 주제 2
 */
const parseMarkdownToTree = (markdown: string): MindmapNode | null => {
  if (!markdown || !markdown.trim()) return null;

  const lines = markdown.split('\n').filter(line => line.trim());
  if (lines.length === 0) return null;

  const root: MindmapNode = { title: '회의', children: [] };
  const stack: { node: MindmapNode; level: number }[] = [{ node: root, level: 0 }];

  for (const line of lines) {
    const match = line.match(/^(#{1,6})\s+(.+)$/);
    if (!match) continue;

    const level = match[1].length;
    const title = match[2].trim();
    const newNode: MindmapNode = { title, children: [] };

    // 현재 레벨보다 낮거나 같은 항목을 스택에서 제거
    while (stack.length > 1 && stack[stack.length - 1].level >= level) {
      stack.pop();
    }

    // 부모 노드에 추가
    const parent = stack[stack.length - 1].node;
    if (!parent.children) parent.children = [];
    parent.children.push(newNode);

    // 스택에 추가
    stack.push({ node: newNode, level });
  }

  // root의 children이 1개면 그 자식을 반환, 아니면 root 반환
  if (root.children && root.children.length === 1) {
    return root.children[0];
  }
  return root.children && root.children.length > 0 ? root : null;
};

export const mindmapService = {
  /**
   * 회의 마인드맵 조회
   * 백엔드 API: /api/mindmap/<meeting_id>
   * 백엔드 응답: { success, has_mindmap, mindmap_content (markdown string) }
   */
  getMindmap: async (meetingId: string): Promise<MindmapResponse> => {
    try {
      const response = await api.get(`/api/mindmap/${meetingId}`);
      const data = response.data;
      
      if (data.has_mindmap && data.mindmap_content) {
        const mindmapTree = parseMarkdownToTree(data.mindmap_content);
        return {
          success: true,
          mindmap: mindmapTree || undefined,
          mindmap_markdown: data.mindmap_content
        };
      }
      
      return { success: true, mindmap: undefined };
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { success: false, error: '마인드맵이 없습니다.' };
      }
      throw error;
    }
  },

  /**
   * 마인드맵은 업로드 시 자동 생성됨 (별도 생성 API 없음)
   * 요약 재생성 시 마인드맵도 같이 재생성됨
   */
  generateMindmap: async (meetingId: string): Promise<MindmapResponse> => {
    // 요약 생성 API를 호출하면 마인드맵도 함께 생성됨
    const response = await api.post(`/api/summarize/${meetingId}`);
    if (response.data.success) {
      // 생성 후 마인드맵 다시 조회
      return await mindmapService.getMindmap(meetingId);
    }
    return { success: false, error: response.data.error || '마인드맵 생성에 실패했습니다.' };
  },
};

export default mindmapService;


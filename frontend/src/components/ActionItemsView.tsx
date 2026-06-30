import { useState, useEffect } from 'react';
import { Loader2, AlertCircle, CheckCircle2, Circle, Calendar, Sparkles } from 'lucide-react';
import { actionItemsService, type ActionItem } from '../services/actionItems';

interface ActionItemsViewProps {
  meetingId: string;
}

const ActionItemsView = ({ meetingId }: ActionItemsViewProps) => {
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadActionItems = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const items = await actionItemsService.getActionItems(meetingId);
      setActionItems(items);
    } catch (err: any) {
      console.error('Action Items 로드 실패:', err);
      setError('Action Items를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadActionItems();
  }, [meetingId]);

  const handleExtract = async () => {
    try {
      setIsExtracting(true);
      setError(null);
      const response = await actionItemsService.extractActionItems(meetingId);
      
      if (response.success) {
        // 추출 후 목록 새로고침
        await loadActionItems();
      } else {
        setError(response.error || 'Action Item 추출에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('Action Item 추출 실패:', err);
      setError(err.response?.data?.error || 'Action Item 추출 중 오류가 발생했습니다.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleToggleStatus = async (item: ActionItem) => {
    const newStatus = item.status === 'pending' ? 'done' : 'pending';
    
    try {
      const response = await actionItemsService.updateActionItemStatus(item.id, newStatus);
      
      if (response.success) {
        // 상태 업데이트 후 목록 새로고침
        await loadActionItems();
      } else {
        setError(response.error || '상태 업데이트에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('상태 업데이트 실패:', err);
      setError(err.response?.data?.error || '상태 업데이트 중 오류가 발생했습니다.');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
        <p className="text-slate-500">Action Items를 불러오는 중...</p>
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
          onClick={loadActionItems}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (actionItems.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-slate-50 rounded-full">
              <Sparkles className="w-8 h-8 text-slate-400" />
            </div>
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">Action Item이 아직 추출되지 않았습니다</h3>
          <p className="text-slate-500 mb-6">회의록에서 할 일을 자동으로 추출하여 관리할 수 있습니다.</p>
          <button
            onClick={handleExtract}
            disabled={isExtracting}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExtracting ? (
              <>
                <Loader2 className="w-4 h-4 inline-block animate-spin mr-2" />
                추출 중...
              </>
            ) : (
              'Action Item 추출하기'
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-900">Action Items</h2>
        <button
          onClick={handleExtract}
          disabled={isExtracting}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExtracting ? (
            <>
              <Loader2 className="w-4 h-4 inline-block animate-spin mr-2" />
              재추출 중...
            </>
          ) : (
            '다시 추출'
          )}
        </button>
      </div>

      <div className="space-y-4">
        {actionItems.map((item) => (
          <div
            key={item.id}
            className={`p-4 rounded-lg border-2 transition-all ${
              item.status === 'done'
                ? 'bg-slate-50 border-slate-200'
                : 'bg-white border-indigo-200 hover:border-indigo-300'
            }`}
          >
            <div className="flex items-start gap-3">
              <button
                onClick={() => handleToggleStatus(item)}
                className={`mt-1 flex-shrink-0 transition-colors ${
                  item.status === 'done'
                    ? 'text-indigo-600 hover:text-indigo-700'
                    : 'text-slate-400 hover:text-indigo-600'
                }`}
              >
                {item.status === 'done' ? (
                  <CheckCircle2 className="w-6 h-6" />
                ) : (
                  <Circle className="w-6 h-6" />
                )}
              </button>
              
              <div className="flex-1 min-w-0">
                <p
                  className={`font-medium mb-2 ${
                    item.status === 'done'
                      ? 'text-slate-500 line-through'
                      : 'text-slate-900'
                  }`}
                >
                  {item.content}
                </p>
                
                {item.due_date && (
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <Calendar className="w-4 h-4" />
                    <span>{formatDate(item.due_date)}</span>
                  </div>
                )}
                
                {item.calendar_event_id && (
                  <div className="mt-2 text-xs text-indigo-600">
                    ✓ Google Calendar에 등록됨
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActionItemsView;


import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, MessageSquare, Maximize2, Minimize2 } from 'lucide-react';
import { chatService, type ChatSource } from '../services/chat';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  timestamp: Date;
}

interface ChatSidebarProps {
  meetingId: string;
  meetingTitle?: string;
}

/**
 * NoteDetail 페이지에서 사용하는 회의별 챗봇 사이드바
 * 특정 meeting_id에 대한 질문만 처리
 */
const ChatSidebar = ({ meetingId, meetingTitle }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showExpandButton, setShowExpandButton] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 세션 스토리지 키 (회의별로 분리)
  const CHAT_HISTORY_KEY = `chat_history_${meetingId}`;

  // 페이지 로드 시 대화 내역 복원
  useEffect(() => {
    loadChatHistory();
  }, [meetingId]);

  // 메시지 추가 시 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 텍스트 영역 높이 조절
  useEffect(() => {
    if (textareaRef.current) {
      const lineHeight = 24;
      const maxHeight4Lines = lineHeight * 4 + 16;
      
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      
      setShowExpandButton(scrollHeight > maxHeight4Lines);
      
      if (isExpanded) {
        const maxHeight = lineHeight * 8 + 16;
        textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
        textareaRef.current.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
      } else {
        textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight4Lines)}px`;
        textareaRef.current.style.overflowY = scrollHeight > maxHeight4Lines ? 'auto' : 'hidden';
      }
    }
  }, [input, isExpanded]);

  // 입력이 비어지면 확장 모드 해제
  useEffect(() => {
    if (!input.trim()) {
      setIsExpanded(false);
      setShowExpandButton(false);
    }
  }, [input]);

  const loadChatHistory = () => {
    try {
      const historyJson = sessionStorage.getItem(CHAT_HISTORY_KEY);
      if (historyJson) {
        const history = JSON.parse(historyJson);
        const loadedMessages: Message[] = history.messages.map((msg: any) => ({
          id: msg.id || `msg-${Date.now()}-${Math.random()}`,
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(loadedMessages);
      }
    } catch (error) {
      console.error('챗봇 대화 내역 불러오기 오류:', error);
    }
  };

  const saveChatHistory = (messagesToSave: Message[]) => {
    try {
      const history = {
        messages: messagesToSave.map(msg => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          sources: msg.sources,
          timestamp: msg.timestamp.toISOString(),
        })),
      };
      sessionStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('메시지 저장 오류:', error);
    }
  };

  const handleSend = async () => {
    const query = input.trim();
    if (!query || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);
    saveChatHistory(newMessages);

    try {
      // 특정 meeting_id로 질문
      const response = await chatService.sendMessage(query, meetingId);

      if (response.success) {
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.answer || '',
          sources: response.sources,
          timestamp: new Date(),
        };
        const finalMessages = [...newMessages, assistantMessage];
        setMessages(finalMessages);
        saveChatHistory(finalMessages);
      } else {
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: response.error || '오류가 발생했습니다.',
          timestamp: new Date(),
        };
        const finalMessages = [...newMessages, errorMessage];
        setMessages(finalMessages);
        saveChatHistory(finalMessages);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '네트워크 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date(),
      };
      const finalMessages = [...newMessages, errorMessage];
      setMessages(finalMessages);
      saveChatHistory(finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (seconds?: number): string => {
    if (seconds === undefined) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const clearHistory = () => {
    setMessages([]);
    sessionStorage.removeItem(CHAT_HISTORY_KEY);
  };

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-white">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-brand-600" />
          <div>
            <h3 className="font-semibold text-slate-900 text-sm">AI 질문</h3>
            {meetingTitle && (
              <p className="text-xs text-slate-500 truncate max-w-[200px]">{meetingTitle}</p>
            )}
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
          >
            대화 삭제
          </button>
        )}
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p className="text-sm">이 회의 내용에 대해 질문해보세요.</p>
            <p className="text-xs text-slate-400 mt-1">예: "이 회의의 핵심 결정 사항은?"</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-white text-slate-900 border border-slate-200 shadow-sm'
              }`}
            >
              <p className="whitespace-pre-wrap text-sm">{message.content}</p>

              {/* 출처 표시 */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200">
                  <p className="text-xs font-semibold mb-2 text-slate-600">📍 출처:</p>
                  <div className="space-y-1">
                    {message.sources.map((source, index) => (
                      <div
                        key={index}
                        className="text-xs text-brand-600 flex items-center gap-1"
                      >
                        <span>{source.subtopic_title || source.title}</span>
                        {source.start_time !== undefined && (
                          <span className="text-slate-500">
                            ({formatTime(parseFloat(source.start_time))} ~ {formatTime(parseFloat(source.end_time || '0'))})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-sm">
              <Loader2 className="w-5 h-5 animate-spin text-brand-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <div className="flex gap-2 items-center">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="이 회의에 대해 질문하세요..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent pr-10"
              rows={1}
              disabled={isLoading}
            />
            {input.trim() && showExpandButton && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="absolute right-2 top-2 p-1 hover:bg-slate-100 rounded text-slate-500 hover:text-slate-700 transition-colors"
                title={isExpanded ? '축소' : '확장'}
              >
                {isExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="w-10 h-10 bg-brand-600 text-white rounded-full hover:bg-brand-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center flex-shrink-0"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatSidebar;


import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, MessageSquare, X, ChevronLeft, Maximize2, Minimize2 } from 'lucide-react';
import { chatService, type ChatSource } from '../services/chat';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  timestamp: Date;
}

const CHAT_HISTORY_KEY = 'chatbot_history';
const CHATBOT_STATE_KEY = 'chatbot_state';

interface GlobalChatSidebarProps {
  hideOnPages?: string[]; // 이 페이지들에서는 사이드바 숨김
}

const GlobalChatSidebar = ({ hideOnPages = [] }: GlobalChatSidebarProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showExpandButton, setShowExpandButton] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 현재 경로 확인
  const currentPath = window.location.pathname;
  const shouldHide = hideOnPages.some(path => currentPath.includes(path));

  // 페이지 로드 시 상태 복원
  useEffect(() => {
    if (shouldHide) {
      setIsOpen(false);
      return;
    }

    const savedState = sessionStorage.getItem(CHATBOT_STATE_KEY);
    if (savedState === 'open') {
      setIsOpen(true);
    }
    loadChatHistory();
  }, [shouldHide]);

  // 사이드바 열림/닫힘 시 상태 저장 및 레이아웃 조정
  useEffect(() => {
    if (shouldHide) return;

    sessionStorage.setItem(CHATBOT_STATE_KEY, isOpen ? 'open' : 'closed');
    
    // 메인 컨텐츠 영역 레이아웃 조정
    const mainContent = document.querySelector('main');
    if (mainContent && mainContent instanceof HTMLElement) {
      if (isOpen) {
        // 챗봇 열림: 오른쪽에 사이드바 공간 확보, 왼쪽으로 밀림
        mainContent.style.marginRight = '400px';
        mainContent.style.marginLeft = '0';
        mainContent.style.transition = 'all 0.3s ease';
      } else {
        // 챗봇 닫힘: 중앙 정렬 (기본 상태)
        mainContent.style.marginRight = 'auto';
        mainContent.style.marginLeft = 'auto';
        mainContent.style.transition = 'all 0.3s ease';
      }
    }

    return () => {
      if (mainContent && mainContent instanceof HTMLElement) {
        mainContent.style.marginRight = 'auto';
        mainContent.style.marginLeft = 'auto';
      }
    };
  }, [isOpen, shouldHide]);

  // 메시지 추가 시 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 텍스트 영역 높이 조절 (4줄 제한 또는 확장 모드)
  useEffect(() => {
    if (textareaRef.current) {
      const lineHeight = 24; // text-sm의 대략적인 line-height
      const maxHeight4Lines = lineHeight * 4 + 16; // 4줄 + padding
      
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      
      // 4줄을 넘어가는지 확인
      setShowExpandButton(scrollHeight > maxHeight4Lines);
      
      if (isExpanded) {
        // 확장 모드: 최대 8줄까지
        const maxHeight = lineHeight * 8 + 16;
        textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
        textareaRef.current.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
      } else {
        // 기본 모드: 4줄로 제한
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

  const handleSend = async () => {
    const query = input.trim();
    if (!query || isLoading) return;

    // 사용자 메시지 추가
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

    // sessionStorage에 저장
    try {
      const history = {
        messages: newMessages.map(msg => ({
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

    try {
      // meeting_id 없이 전체 회의록에서 검색
      const response = await chatService.sendMessage(query);

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
        
        // sessionStorage에 저장
        try {
          const history = {
            messages: finalMessages.map(msg => ({
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
      } else {
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: response.error || '오류가 발생했습니다.',
          timestamp: new Date(),
        };
        setMessages([...newMessages, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '네트워크 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date(),
      };
      setMessages([...newMessages, errorMessage]);
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
    if (!seconds) return '';
    const date = new Date(seconds * 1000);
    return date.toISOString().substr(14, 5);
  };

  // 숨김 페이지에서는 렌더링하지 않음
  if (shouldHide) {
    return null;
  }

  return (
    <>
      {/* 토글 탭 */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed top-1/2 right-0 -translate-y-1/2 translate-x-[35px] w-10 h-[120px] bg-gradient-to-br from-brand-600 to-brand-700 hover:translate-x-0 rounded-l-lg shadow-lg z-[999] flex flex-col items-center justify-center gap-2 text-white font-semibold transition-all duration-300 hover:shadow-xl"
          title="AI Assistant"
        >
          <ChevronLeft className="w-6 h-6" />
          <span className="writing-vertical text-xs tracking-wider">CHAT</span>
        </button>
      )}

      {/* 사이드바 */}
      <aside
        className={`fixed top-0 right-0 w-[400px] h-screen bg-white border-l border-slate-200 shadow-2xl z-[1000] flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-brand-600" />
            <h3 className="font-semibold text-slate-900">AI Assistant</h3>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-slate-200 rounded transition-colors text-slate-600 hover:text-slate-900"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
          {messages.length === 0 && (
            <div className="text-center text-slate-500 py-8">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p className="text-sm">안녕하세요! 회의 내용에 대해 무엇이든 물어보세요.</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-brand-600 text-white'
                    : 'bg-white text-slate-900 border border-slate-200'
                }`}
              >
                <p className="whitespace-pre-wrap text-sm">{message.content}</p>

                {/* 출처 표시 */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-300">
                    <p className="text-xs font-semibold mb-2 text-slate-600">출처:</p>
                    <div className="space-y-1">
                      {message.sources.map((source, index) => (
                        <div
                          key={index}
                          className="text-xs text-brand-600"
                        >
                          {source.title}
                          {source.start_time && (
                            <span className="text-slate-500 ml-1">
                              ({formatTime(parseFloat(source.start_time))})
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
              <div className="bg-white rounded-lg p-3 border border-slate-200">
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
                placeholder="메시지를 입력하세요..."
                className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent pr-10"
                rows={1}
                disabled={isLoading}
              />
              {/* 확장/축소 버튼 (오른쪽 상단) */}
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
              className="w-10 h-10 flex-shrink-0 bg-brand-600 text-white rounded-full hover:bg-brand-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default GlobalChatSidebar;


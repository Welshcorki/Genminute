import React, { useState, useRef, useEffect } from 'react';
import { X, MessageSquare, Send } from 'lucide-react';

interface AIAssistantProps {
  onClose: () => void;
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    text: string;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        text: input
    };

    setMessages(prev => [...prev, newMessage]);
    setInput('');

    // Simulate AI response
    setTimeout(() => {
        setMessages(prev => [...prev, {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            text: "죄송합니다. 현재 데모 버전에서는 실제 AI 응답이 지원되지 않습니다. 하지만 UI는 완벽하게 작동합니다!"
        }]);
    }, 1000);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="h-14 border-b border-slate-100 flex items-center justify-between px-6 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-2 text-slate-800 font-bold">
          <div className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse"></div>
          AI Assistant
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 transition-colors p-1.5 rounded-full hover:bg-slate-50"
        >
          <X size={20} />
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 opacity-60 mt-4">
            <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-sm mb-4 border border-slate-100">
                <MessageSquare size={32} strokeWidth={1.5} className="text-indigo-400" />
            </div>
            <p className="text-sm font-medium text-slate-500">무엇이든 물어보세요</p>
            <p className="text-xs text-slate-400 mt-1">회의 요약, 할 일 추출, 아이디어 제안 등</p>
          </div>
        ) : (
          <div className="space-y-6">
              {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-sm ${
                          msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-br-sm'
                            : 'bg-white border border-slate-100 text-slate-700 rounded-bl-sm'
                      }`}>
                          {msg.text}
                      </div>
                  </div>
              ))}
              <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-100">
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지 입력..."
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-4 pr-12 py-3.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-sm placeholder-slate-400 text-slate-700"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all disabled:bg-slate-200 disabled:text-slate-400 shadow-sm"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};
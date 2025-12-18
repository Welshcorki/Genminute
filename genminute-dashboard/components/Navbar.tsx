import React from 'react';
import { Home, FileText, Mic, User } from 'lucide-react';
import { Tab } from '../types';

interface NavbarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 md:px-8 flex items-center justify-between sticky top-0 z-50">
      {/* Logo Area */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 md:w-10 md:h-10 relative flex items-center justify-center">
            <div className="flex flex-col items-center">
                <span className="text-2xl">🦁</span>
                <span className="text-[0.5rem] font-bold tracking-widest text-indigo-900 uppercase -mt-1">GenMinute</span>
            </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="hidden md:flex items-center gap-1">
        <button
          onClick={() => onTabChange(Tab.HOME)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-all duration-200 ${
            activeTab === Tab.HOME
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Home size={18} />
          홈
        </button>
        <button
          onClick={() => onTabChange(Tab.MINUTES)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-all duration-200 ${
            activeTab === Tab.MINUTES
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <FileText size={18} />
          회의록
        </button>
        <button
          onClick={() => onTabChange(Tab.RECORD)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-all duration-200 ${
            activeTab === Tab.RECORD
              ? 'bg-indigo-50 text-indigo-700'
              : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Mic size={18} />
          녹음
        </button>
      </nav>

      {/* Mobile Menu Icon (Placeholder) */}
      <div className="md:hidden text-slate-500 hover:text-indigo-600 transition-colors cursor-pointer">
        <User size={24} />
      </div>
    </header>
  );
};
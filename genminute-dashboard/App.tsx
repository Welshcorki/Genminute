import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { AIAssistant } from './components/AIAssistant';
import { Tab } from './types';
import { ChevronLeft } from 'lucide-react';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>(Tab.HOME);
  const [isAssistantOpen, setIsAssistantOpen] = useState(true);

  const toggleAssistant = () => {
    setIsAssistantOpen(!isAssistantOpen);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Layout */}
      <div className="flex flex-1 relative overflow-hidden">
        {/* Main Dashboard Area */}
        <main className={`flex-1 overflow-y-auto transition-all duration-300 ${isAssistantOpen ? 'mr-0 md:mr-[400px]' : 'mr-0'}`}>
          <div className="max-w-7xl mx-auto p-4 md:p-8">
            <Dashboard />
          </div>
        </main>

        {/* Floating Toggle Button (Visible when sidebar is closed) */}
        {!isAssistantOpen && (
          <button
            onClick={toggleAssistant}
            className="fixed right-0 top-1/2 transform -translate-y-1/2 bg-indigo-600 text-white p-2 rounded-l-md shadow-lg hover:bg-indigo-700 transition-colors z-50 flex items-center gap-1 writing-vertical-lr"
            aria-label="Open AI Assistant"
            style={{ writingMode: 'vertical-rl' }}
          >
             <span className="text-sm font-medium py-2 rotate-180">AI Assistant</span>
             <ChevronLeft size={16} />
          </button>
        )}

        {/* Right Sidebar - AI Assistant */}
        <div
          className={`fixed top-[64px] right-0 bottom-0 w-full md:w-[400px] bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-40 border-l border-slate-200 ${
            isAssistantOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          <AIAssistant onClose={() => setIsAssistantOpen(false)} />
        </div>
      </div>
    </div>
  );
};

export default App;
import React from 'react';
import { Mic, Upload, FileText, Clock, File, ChevronRight } from 'lucide-react';
import { StatCard } from './StatCard';

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Banner */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 rounded-2xl p-6 md:p-10 text-white shadow-xl shadow-indigo-900/10 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold mb-2 flex items-center gap-2">
              안녕하세요, 사용자님! <span className="animate-wave">👋</span>
            </h1>
            <p className="text-slate-300 text-sm md:text-base">
              회의, 강의, 인터뷰... 모든 대화를 인사이트로 바꿔보세요.
            </p>
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <button className="flex-1 md:flex-none bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-600/20">
              <Mic size={20} />
              새 기록 시작
            </button>
            <button className="flex-1 md:flex-none bg-white/10 hover:bg-white/20 text-white border border-white/10 px-5 py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-all backdrop-blur-sm">
              <Upload size={20} />
              파일 업로드
            </button>
          </div>
        </div>
        {/* Decorative background blur */}
        <div className="absolute -top-24 -right-24 w-80 h-80 bg-indigo-500/30 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-teal-500/20 rounded-full blur-3xl"></div>
      </section>

      {/* Stats Row */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <StatCard
          icon={<FileText size={24} />}
          iconBgColor="bg-indigo-50"
          iconColor="text-indigo-600"
          title="이번 달 노트"
          value="0개"
        />
        <StatCard
          icon={<Clock size={24} />}
          iconBgColor="bg-teal-50"
          iconColor="text-teal-600"
          title="총 녹음 시간"
          value="0시간"
        />
        <StatCard
          icon={<File size={24} />}
          iconBgColor="bg-rose-50"
          iconColor="text-rose-600"
          title="최근 활동"
          value="기록 없음"
          subtext="첫 기록을 시작해보세요"
          subtextColor="text-rose-500"
        />
      </section>

      {/* Recent Notes Section */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800">최근 내 노트</h2>
          <button className="text-slate-500 text-sm flex items-center gap-1 hover:text-indigo-600 transition-colors">
            전체 보기 <ChevronRight size={16} />
          </button>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-12 flex flex-col items-center justify-center text-center h-[320px] shadow-sm">
          <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mb-4 text-slate-400">
            <FileText size={32} />
          </div>
          <h3 className="text-lg font-bold text-slate-800 mb-2">아직 저장된 노트가 없습니다</h3>
          <p className="text-slate-500 mb-8 max-w-sm">
            첫 번째 회의나 강의를 기록하고 인사이트를 얻어보세요.
          </p>
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-all shadow-md hover:shadow-lg">
            <Mic size={18} />
            지금 기록하기
          </button>
        </div>
      </section>
    </div>
  );
};
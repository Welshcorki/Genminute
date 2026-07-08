import { useMemo } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { SPEAKER_COLORS } from '../config/speakers';

ChartJS.register(ArcElement, Tooltip, Legend);

interface SpeakerShareChartProps {
  speakerShare: Record<string, number>;
  /** 참석자 목록 — 전사 스크립트의 화자 칩과 색 순서를 맞추기 위한 기준 */
  participants?: string[];
}

export default function SpeakerShareChart({ speakerShare, participants }: SpeakerShareChartProps) {
  const data = useMemo(() => {
    const labels = Object.keys(speakerShare);
    const dataPoints = Object.values(speakerShare);

    // 참석자 목록 순서를 기준으로 색을 배정해 스크립트의 화자 칩과 일치시킴
    const backgroundColors = labels.map((label, i) => {
      const index = participants ? participants.indexOf(label) : i;
      const safeIndex = index >= 0 ? index : i;
      return SPEAKER_COLORS[safeIndex % SPEAKER_COLORS.length].hex;
    });

    return {
      labels,
      datasets: [
        {
          data: dataPoints,
          backgroundColor: backgroundColors,
          borderWidth: 1,
          borderColor: '#ffffff',
          hoverOffset: 4,
        },
      ],
    };
  }, [speakerShare, participants]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          font: { family: "'Pretendard Variable', 'Pretendard', sans-serif", size: 12 },
          color: '#475569',
          usePointStyle: true,
          padding: 20
        }
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            return ` ${label}: ${value}%`;
          }
        }
      }
    },
    cutout: '70%',
    layout: {
      padding: 10
    }
  };

  const hasData = Object.keys(speakerShare).length > 0;

  return (
    <div className="flex flex-col items-center p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700 w-full mb-4 pl-2 border-l-4 border-brand-500">
        화자별 발언 비중
      </h3>
      {hasData ? (
        <div className="relative w-full h-48 flex justify-center items-center">
          <Doughnut data={data} options={options} />
        </div>
      ) : (
        <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
          비중 데이터가 없습니다
        </div>
      )}
    </div>
  );
}

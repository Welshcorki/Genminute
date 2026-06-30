import { useMemo } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface SpeakerShareChartProps {
  speakerShare: Record<string, number>;
}

// 화자별 지정 색상 매핑 (NoteDetail의 getSpeakerColor과 일치하도록 유사 톤 사용)
const SPEAKER_COLORS = [
  '#6366f1', // indigo-500
  '#14b8a6', // teal-500
  '#f43f5e', // rose-500
  '#f59e0b', // amber-500
  '#a855f7', // purple-500
  '#0ea5e9', // cyan-500
];

export default function SpeakerShareChart({ speakerShare }: SpeakerShareChartProps) {
  const data = useMemo(() => {
    const labels = Object.keys(speakerShare);
    const dataPoints = Object.values(speakerShare);
    
    // 차별화된 색상 부여를 위해 라벨 개수만큼 색상 생성
    const backgroundColors = labels.map((_, i) => SPEAKER_COLORS[i % SPEAKER_COLORS.length]);

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
  }, [speakerShare]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          font: { family: "'Inter', sans-serif", size: 12 },
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
      <h3 className="text-sm font-semibold text-slate-700 w-full mb-4 pl-2 border-l-4 border-indigo-500">
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

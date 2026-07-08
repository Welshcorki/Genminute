/**
 * WaveformMotif - 장식용 오디오 파형 스트립
 *
 * "모든 대화를 기록한다"는 제품의 재료(소리)를 시각 언어로 쓰는 시그니처 그래픽.
 * Dashboard 히어로와 Login 페이지가 같은 모티프를 공유합니다.
 * 바 높이는 고정 상수라 렌더마다 모양이 변하지 않으며, 순수 장식이므로
 * 스크린 리더에는 노출하지 않습니다(aria-hidden).
 */

// 발화 구간(높은 바 묶음)과 짧은 침묵(낮은 바)이 섞인 대화 형태의 높이 값 (0~100)
const BAR_HEIGHTS = [
  8, 14, 26, 42, 58, 66, 52, 38, 44, 60, 72, 56, 34, 18, 10, 6,
  12, 30, 54, 78, 92, 70, 48, 62, 84, 66, 40, 22, 12, 8, 16, 36,
  58, 74, 62, 46, 30, 50, 68, 88, 96, 72, 50, 32, 44, 64, 52, 28,
  14, 8, 20, 40, 60, 76, 58, 36, 24, 42, 66, 80, 60, 38, 20, 10,
];

const BAR_SLOT = 10; // viewBox 단위의 바 1개 슬롯 폭 (바 6 + 간격 4)

interface WaveformMotifProps {
  className?: string;
}

const WaveformMotif = ({ className = '' }: WaveformMotifProps) => (
  <svg
    aria-hidden="true"
    viewBox={`0 0 ${BAR_HEIGHTS.length * BAR_SLOT} 100`}
    preserveAspectRatio="none"
    className={className}
  >
    {BAR_HEIGHTS.map((height, i) => (
      <rect
        key={i}
        x={i * BAR_SLOT + 2}
        y={100 - height}
        width={BAR_SLOT - 4}
        height={height}
        rx={2}
        fill="currentColor"
      />
    ))}
  </svg>
);

export default WaveformMotif;

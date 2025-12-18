/**
 * AudioVisualizer - 오디오 파형 시각화 컴포넌트
 * 
 * AnalyserNode를 받아서 Canvas에 실시간 파형을 그립니다.
 */
import { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  analyser: AnalyserNode | null;
  isRecording: boolean;
  className?: string;
  barColor?: string;
  backgroundColor?: string;
}

export const AudioVisualizer = ({
  analyser,
  isRecording,
  className = '',
  barColor = '#4f46e5', // indigo-600
  backgroundColor = '#f8fafc', // slate-50
}: AudioVisualizerProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationIdRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Canvas 크기 설정
    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // 정적 상태 (녹음 안 함)
    const drawIdle = () => {
      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;

      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, width, height);

      // 중앙에 수평선
      ctx.strokeStyle = '#e2e8f0'; // slate-200
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
    };

    // 파형 그리기
    const draw = () => {
      if (!analyser || !isRecording) {
        drawIdle();
        return;
      }

      animationIdRef.current = requestAnimationFrame(draw);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyser.getByteTimeDomainData(dataArray);

      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;

      // 배경
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, width, height);

      // 파형
      ctx.lineWidth = 2;
      ctx.strokeStyle = barColor;
      ctx.beginPath();

      const sliceWidth = (width * 1.0) / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }

        x += sliceWidth;
      }

      ctx.lineTo(width, height / 2);
      ctx.stroke();
    };

    if (isRecording && analyser) {
      draw();
    } else {
      drawIdle();
    }

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };
  }, [analyser, isRecording, barColor, backgroundColor]);

  return (
    <canvas
      ref={canvasRef}
      className={`w-full h-full ${className}`}
      style={{ display: 'block' }}
    />
  );
};

export default AudioVisualizer;


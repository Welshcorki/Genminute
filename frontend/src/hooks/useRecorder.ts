/**
 * useRecorder - 오디오/비디오 녹음 커스텀 훅
 * 
 * 기능:
 * - 마이크 녹음 (모바일/대면 회의)
 * - 시스템 오디오 녹화 (Zoom/화상회의)
 * - 파형 시각화용 AnalyserNode 제공
 * - 타이머 기능
 */
import { useState, useRef, useCallback, useEffect } from 'react';

export type RecordingType = 'mic' | 'sys';
export type RecordingState = 'idle' | 'recording' | 'paused' | 'stopped';

interface UseRecorderOptions {
  onDataAvailable?: (data: Blob) => void;
  onStop?: (blob: Blob, type: RecordingType) => void;
  onError?: (error: Error) => void;
}

interface UseRecorderReturn {
  // 상태
  state: RecordingState;
  recordingType: RecordingType | null;
  duration: number; // 초 단위
  recordedBlob: Blob | null;
  
  // 시각화용
  analyser: AnalyserNode | null;
  
  // 액션
  startMicRecording: () => Promise<void>;
  startSystemRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  reset: () => void;
}

export const useRecorder = (options: UseRecorderOptions = {}): UseRecorderReturn => {
  const { onDataAvailable, onStop, onError } = options;

  // 상태
  const [state, setState] = useState<RecordingState>('idle');
  const [recordingType, setRecordingType] = useState<RecordingType | null>(null);
  const [duration, setDuration] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  // 타이머 시작
  const startTimer = useCallback(() => {
    startTimeRef.current = Date.now() - (duration * 1000);
    timerRef.current = window.setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      setDuration(elapsed);
    }, 100);
  }, [duration]);

  // 타이머 정지
  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // 시각화 설정
  const setupAnalyser = useCallback((stream: MediaStream) => {
    try {
      // Safari 호환성을 위한 webkitAudioContext 지원
      // @ts-ignore - webkitAudioContext는 Safari 비표준 API
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextClass();
      const source = audioContext.createMediaStreamSource(stream);
      const analyserNode = audioContext.createAnalyser();
      
      analyserNode.fftSize = 2048;
      source.connect(analyserNode);
      // 스피커로 출력하지 않음 (하울링 방지)
      
      audioContextRef.current = audioContext;
      setAnalyser(analyserNode);
    } catch (error) {
      console.error('Analyser 설정 실패:', error);
    }
  }, []);

  // 리소스 정리
  const cleanup = useCallback(() => {
    stopTimer();
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    setAnalyser(null);
  }, [stopTimer]);

  // 녹음 설정 (공통 로직)
  const setupRecorder = useCallback((stream: MediaStream, type: RecordingType) => {
    chunksRef.current = [];
    
    // MIME 타입 결정
    let mimeType: string;
    if (type === 'sys') {
      // 시스템 녹화: 비디오 + 오디오
      const videoTypes = [
        'video/webm;codecs=vp8,opus',
        'video/webm;codecs=vp9,opus',
        'video/webm'
      ];
      mimeType = videoTypes.find(t => MediaRecorder.isTypeSupported(t)) || 'video/webm';
    } else {
      // 마이크 녹음: 오디오 전용
      mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/ogg;codecs=opus';
    }

    console.log(`녹음 시작: type=${type}, mimeType=${mimeType}`);

    const mediaRecorder = new MediaRecorder(stream, { mimeType });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
        onDataAvailable?.(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mimeType });
      setRecordedBlob(blob);
      setState('stopped');
      cleanup();
      onStop?.(blob, type);
    };

    mediaRecorder.onerror = (event: any) => {
      console.error('MediaRecorder 오류:', event);
      onError?.(new Error('녹음 중 오류가 발생했습니다.'));
      cleanup();
      setState('idle');
    };

    mediaRecorderRef.current = mediaRecorder;
    streamRef.current = stream;
    
    // 시각화 설정 (오디오 트랙이 있는 경우만)
    if (stream.getAudioTracks().length > 0) {
      setupAnalyser(stream);
    }

    // 녹음 시작
    mediaRecorder.start(1000); // 1초마다 데이터 청크 생성
    setRecordingType(type);
    setState('recording');
    startTimer();
  }, [cleanup, onDataAvailable, onStop, onError, setupAnalyser, startTimer]);

  // 마이크 녹음 시작
  const startMicRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setupRecorder(stream, 'mic');
    } catch (error: any) {
      if (error.name === 'NotAllowedError') {
        onError?.(new Error('마이크 권한이 거부되었습니다. 브라우저 설정에서 마이크를 허용해주세요.'));
      } else {
        onError?.(new Error(`마이크 접근 오류: ${error.message}`));
      }
    }
  }, [setupRecorder, onError]);

  // 시스템 오디오 녹화 시작
  const startSystemRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          // @ts-ignore - cursor는 DisplayMediaStreamConstraints 전용 속성
          cursor: 'never'
        },
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false
        }
      });

      // 오디오 트랙 확인
      const audioTrack = stream.getAudioTracks()[0];
      if (!audioTrack) {
        stream.getTracks().forEach(track => track.stop());
        onError?.(new Error('시스템 오디오가 공유되지 않았습니다. "시스템 오디오 공유" 체크박스를 확인해주세요.'));
        return;
      }

      // 화면 공유 중지 시 녹음도 중지
      audioTrack.onended = () => {
        if (mediaRecorderRef.current?.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      };

      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.onended = () => {
          if (mediaRecorderRef.current?.state === 'recording') {
            mediaRecorderRef.current.stop();
          }
        };
      }

      setupRecorder(stream, 'sys');
    } catch (error: any) {
      if (error.name === 'NotAllowedError') {
        // 사용자가 취소한 경우 - 에러 표시 안 함
        return;
      }
      onError?.(new Error(`시스템 오디오 접근 오류: ${error.message}`));
    }
  }, [setupRecorder, onError]);

  // 녹음 중지
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording' || mediaRecorderRef.current?.state === 'paused') {
      mediaRecorderRef.current.stop();
      stopTimer();
    }
  }, [stopTimer]);

  // 녹음 일시정지
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.pause();
      setState('paused');
      stopTimer();
    }
  }, [stopTimer]);

  // 녹음 재개
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'paused') {
      mediaRecorderRef.current.resume();
      setState('recording');
      startTimer();
    }
  }, [startTimer]);

  // 초기화
  const reset = useCallback(() => {
    cleanup();
    setState('idle');
    setRecordingType(null);
    setDuration(0);
    setRecordedBlob(null);
    chunksRef.current = [];
    mediaRecorderRef.current = null;
  }, [cleanup]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    state,
    recordingType,
    duration,
    recordedBlob,
    analyser,
    startMicRecording,
    startSystemRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    reset,
  };
};

export default useRecorder;


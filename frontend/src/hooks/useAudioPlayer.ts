import { useState, useRef, useCallback, useEffect } from 'react';

export interface UseAudioPlayerReturn {
  audioRef: React.RefObject<HTMLAudioElement | null>;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  isMuted: boolean;
  playbackRate: number;
  loopStart: number | null;
  loopEnd: number | null;
  isLooping: boolean;
  showWaveform: boolean;
  togglePlay: () => void;
  toggleMute: () => void;
  setPlaybackRate: (rate: number) => void;
  seekTo: (time: number) => void;
  setLoopPoint: (type: 'start' | 'end') => void;
  toggleLoop: () => void;
  clearLoop: () => void;
  setShowWaveform: (show: boolean) => void;
  formatTime: (seconds: number) => string;
}

export function useAudioPlayer(isVideo: boolean): UseAudioPlayerReturn {
  const audioRef = useRef<HTMLAudioElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRateState] = useState(1.0);
  const [showWaveform, setShowWaveform] = useState(false);

  const [loopStart, setLoopStart] = useState<number | null>(null);
  const [loopEnd, setLoopEnd] = useState<number | null>(null);
  const [isLooping, setIsLooping] = useState(false);

  const getMedia = useCallback(() => {
    return isVideo ? videoRef.current : audioRef.current;
  }, [isVideo]);

  useEffect(() => {
    const media = getMedia();
    if (!media) return;

    const handleTimeUpdate = () => {
      setCurrentTime(media.currentTime);

      if (isLooping && loopStart !== null && loopEnd !== null) {
        if (media.currentTime >= loopEnd) {
          media.currentTime = loopStart;
        }
      }
    };

    const updateDuration = () => {
      if (media.duration && isFinite(media.duration) && !isNaN(media.duration) && media.duration > 0) {
        setDuration(media.duration);
      }
    };

    const handleEnded = () => {
      setIsPlaying(false);
      const finalDuration = media.duration && !isNaN(media.duration) ? media.duration : duration;
      setCurrentTime(finalDuration);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    media.addEventListener('timeupdate', handleTimeUpdate);
    media.addEventListener('loadedmetadata', updateDuration);
    media.addEventListener('durationchange', updateDuration);
    media.addEventListener('ended', handleEnded);
    media.addEventListener('play', handlePlay);
    media.addEventListener('pause', handlePause);

    media.playbackRate = playbackRate;

    return () => {
      media.removeEventListener('timeupdate', handleTimeUpdate);
      media.removeEventListener('loadedmetadata', updateDuration);
      media.removeEventListener('durationchange', updateDuration);
      media.removeEventListener('ended', handleEnded);
      media.removeEventListener('play', handlePlay);
      media.removeEventListener('pause', handlePause);
    };
  }, [getMedia, playbackRate, isLooping, loopStart, loopEnd, duration]);

  const togglePlay = useCallback(() => {
    const media = getMedia();
    if (!media) return;
    if (isPlaying) {
      media.pause();
    } else {
      media.play();
    }
  }, [getMedia, isPlaying]);

  const toggleMute = useCallback(() => {
    const media = getMedia();
    if (!media) return;
    media.muted = !isMuted;
    setIsMuted(!isMuted);
  }, [getMedia, isMuted]);

  const setPlaybackRate = useCallback((rate: number) => {
    const media = getMedia();
    if (media) {
      media.playbackRate = rate;
    }
    setPlaybackRateState(rate);
  }, [getMedia]);

  const seekTo = useCallback((time: number) => {
    const media = getMedia();
    if (!media) return;
    media.currentTime = time;
    setCurrentTime(time);
  }, [getMedia]);

  const setLoopPoint = useCallback((type: 'start' | 'end') => {
    const media = getMedia();
    if (!media) return;

    const time = media.currentTime;
    if (type === 'start') {
      setLoopStart(time);
      if (loopEnd === null || time >= loopEnd) {
        setLoopEnd(null);
      }
    } else {
      if (loopStart === null || time <= loopStart) {
        setLoopStart(null);
        setLoopEnd(null);
        setIsLooping(false);
        return;
      }
      setLoopEnd(time);
    }
  }, [getMedia, loopEnd, loopStart]);

  const toggleLoop = useCallback(() => {
    if (loopStart !== null && loopEnd !== null) {
      setIsLooping(prev => !prev);
    }
  }, [loopStart, loopEnd]);

  const clearLoop = useCallback(() => {
    setLoopStart(null);
    setLoopEnd(null);
    setIsLooping(false);
  }, []);

  const formatTime = useCallback((seconds: number): string => {
    if (!isFinite(seconds) || isNaN(seconds) || seconds < 0) {
      return '00:00';
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  return {
    audioRef,
    videoRef,
    isPlaying,
    currentTime,
    duration,
    isMuted,
    playbackRate,
    loopStart,
    loopEnd,
    isLooping,
    showWaveform,
    togglePlay,
    toggleMute,
    setPlaybackRate,
    seekTo,
    setLoopPoint,
    toggleLoop,
    clearLoop,
    setShowWaveform,
    formatTime,
  };
}

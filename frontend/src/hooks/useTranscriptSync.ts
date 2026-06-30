import { useState, useCallback, useEffect, useRef } from 'react';
import type { TranscriptSegment } from '../services/meeting';

export interface UseTranscriptSyncReturn {
  activeSegmentId: number | null;
  transcriptRef: React.RefObject<HTMLDivElement | null>;
  handleSegmentClick: (segment: TranscriptSegment) => void;
  handleTimeSeek: (newTime: number) => void;
}

interface UseTranscriptSyncOptions {
  transcript: TranscriptSegment[] | undefined;
  currentTime: number;
  seekTo: (time: number) => void;
  isPlaying: boolean;
  togglePlay: () => void;
}

export function useTranscriptSync({
  transcript,
  currentTime,
  seekTo,
  isPlaying,
  togglePlay,
}: UseTranscriptSyncOptions): UseTranscriptSyncReturn {
  const [activeSegmentId, setActiveSegmentId] = useState<number | null>(null);
  const [userSelectedSegmentId, setUserSelectedSegmentId] = useState<number | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);

  const calculateDistance = useCallback((time: number, segment: TranscriptSegment): number => {
    if (time >= segment.start_time && time < segment.end_time) return 0;
    if (time < segment.start_time) return segment.start_time - time;
    return time - segment.end_time;
  }, []);

  const findClosestSegment = useCallback((time: number): TranscriptSegment | null => {
    if (!transcript?.length) return null;
    return transcript.reduce((closest, seg) => {
      if (!closest) return seg;
      return calculateDistance(time, seg) < calculateDistance(time, closest) ? seg : closest;
    }, null as TranscriptSegment | null);
  }, [transcript, calculateDistance]);

  useEffect(() => {
    if (!transcript?.length) return;

    if (userSelectedSegmentId) {
      const selected = transcript.find(seg => seg.id === userSelectedSegmentId);
      if (selected && currentTime >= selected.start_time && currentTime < selected.end_time) {
        setActiveSegmentId(userSelectedSegmentId);
        return;
      } else {
        setUserSelectedSegmentId(null);
      }
    }

    const active = transcript.find(
      seg => currentTime >= seg.start_time && currentTime < seg.end_time
    );

    if (active) {
      setActiveSegmentId(active.id);
    } else {
      const DISTANCE_THRESHOLD = 2.0;
      const minDistance = Math.min(
        ...transcript.map(seg => calculateDistance(currentTime, seg))
      );
      if (minDistance >= DISTANCE_THRESHOLD) {
        const closest = findClosestSegment(currentTime);
        if (closest) setActiveSegmentId(closest.id);
      }
    }
  }, [transcript, currentTime, userSelectedSegmentId, calculateDistance, findClosestSegment]);

  useEffect(() => {
    if (activeSegmentId && transcriptRef.current) {
      const el = transcriptRef.current.querySelector(`[data-segment-id="${activeSegmentId}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [activeSegmentId]);

  const handleSegmentClick = useCallback((segment: TranscriptSegment) => {
    setUserSelectedSegmentId(segment.id);
    setActiveSegmentId(segment.id);
    seekTo(segment.start_time);
    if (!isPlaying) {
      togglePlay();
    }
  }, [seekTo, isPlaying, togglePlay]);

  const handleTimeSeek = useCallback((newTime: number) => {
    seekTo(newTime);
    if (!transcript?.length) return;

    const active = transcript.find(
      seg => newTime >= seg.start_time && newTime < seg.end_time
    );

    if (active) {
      setUserSelectedSegmentId(active.id);
      setActiveSegmentId(active.id);
    } else {
      const closest = findClosestSegment(newTime);
      if (closest) {
        setUserSelectedSegmentId(closest.id);
        setActiveSegmentId(closest.id);
      }
    }
  }, [seekTo, transcript, findClosestSegment]);

  return {
    activeSegmentId,
    transcriptRef,
    handleSegmentClick,
    handleTimeSeek,
  };
}

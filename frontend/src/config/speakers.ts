/**
 * 화자 색 시스템 — 단일 소스
 *
 * UI 액센트는 brand-* 1색으로 통일하지만, 화자 구분은 "누가 말했나"라는
 * 정보이므로 유일하게 다색을 허용합니다. 전사 스크립트의 화자 칩과
 * 화자별 발언 비중 차트가 같은 순서의 같은 색을 사용해야 합니다.
 */

export interface SpeakerColor {
  /** Tailwind 클래스 (화자 칩/라벨용) */
  chip: string;
  /** chart.js 등 캔버스 렌더링용 hex — chip과 같은 색 계열의 500 톤 */
  hex: string;
}

export const SPEAKER_COLORS: SpeakerColor[] = [
  { chip: 'bg-indigo-100 text-indigo-700 border-indigo-200', hex: '#6366f1' },
  { chip: 'bg-teal-100 text-teal-700 border-teal-200', hex: '#14b8a6' },
  { chip: 'bg-rose-100 text-rose-700 border-rose-200', hex: '#f43f5e' },
  { chip: 'bg-amber-100 text-amber-700 border-amber-200', hex: '#f59e0b' },
  { chip: 'bg-purple-100 text-purple-700 border-purple-200', hex: '#a855f7' },
  { chip: 'bg-cyan-100 text-cyan-700 border-cyan-200', hex: '#0ea5e9' },
];

/** 화자 인덱스(참석자 목록 순서 등)를 색으로 변환 */
export const getSpeakerColorByIndex = (index: number): SpeakerColor =>
  SPEAKER_COLORS[((index % SPEAKER_COLORS.length) + SPEAKER_COLORS.length) % SPEAKER_COLORS.length];

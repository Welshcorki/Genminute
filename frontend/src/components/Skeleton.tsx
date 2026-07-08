/**
 * Skeleton - 로딩 상태 플레이스홀더
 *
 * 텍스트 로더("불러오는 중...") 대신 실제 콘텐츠와 유사한 형태를 보여줘
 * 로딩 중 레이아웃 점프를 줄입니다.
 */

interface SkeletonProps {
  className?: string;
}

/** 기본 블록 — 크기·모양은 className으로 지정 */
export const Skeleton = ({ className = '' }: SkeletonProps) => (
  <div aria-hidden="true" className={`animate-pulse bg-slate-200/70 rounded ${className}`} />
);

/** 노트 카드 형태 (NoteList / Dashboard 최근 노트) */
export const NoteCardSkeleton = () => (
  <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
    <Skeleton className="h-5 w-24 mb-3" />
    <Skeleton className="h-6 w-2/3 mb-2" />
    <Skeleton className="h-4 w-full mb-1.5" />
    <Skeleton className="h-4 w-5/6" />
  </div>
);

export default Skeleton;

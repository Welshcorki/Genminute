import { useEffect, useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search, Calendar, Filter, FileText, LogIn, X, ArrowUp, ArrowDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { meetingService, type Meeting, type PaginatedMeetingsResponse } from '../services/meeting';

const PER_PAGE = 10;

type SortType = 'date' | 'title';
type SortDirection = 'asc' | 'desc';

const NoteList = () => {
  const { isAuthenticated } = useAuth();
  
  // 상태 관리
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  
  // 필터 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [startDateInput, setStartDateInput] = useState('');  // 입력용
  const [endDateInput, setEndDateInput] = useState('');      // 입력용
  const [startDate, setStartDate] = useState('');            // 실제 적용된 필터
  const [endDate, setEndDate] = useState('');                // 실제 적용된 필터
  const [showDateFilter, setShowDateFilter] = useState(false);
  
  // 정렬 상태
  const [sortType, setSortType] = useState<SortType>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  
  // sortBy 계산
  const sortBy = `${sortType}_${sortDirection}` as 'date_desc' | 'date_asc' | 'title_asc' | 'title_desc';
  
  // 무한 스크롤을 위한 ref
  const observerTarget = useRef<HTMLDivElement>(null);
  
  // 디바운싱: 검색어 변경 후 500ms 대기
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [searchTerm]);
  
  // 회의 목록 로드 함수
  const loadMeetings = useCallback(async (page: number, reset: boolean = false) => {
    try {
      if (reset) {
        setIsLoading(true);
      } else {
        setIsLoadingMore(true);
      }
      
      const response: PaginatedMeetingsResponse = await meetingService.getAllMeetings({
        page,
        perPage: PER_PAGE,
        search: debouncedSearchTerm || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        sortBy: sortBy,
      });
      
      if (reset) {
        setMeetings(response.meetings);
      } else {
        // 중복 제거: meeting_id 기준으로 필터링
        setMeetings(prev => {
          const existingIds = new Set(prev.map(m => m.meeting_id));
          const newMeetings = response.meetings.filter(m => !existingIds.has(m.meeting_id));
          return [...prev, ...newMeetings];
        });
      }
      
      setCurrentPage(page);
      setHasMore(page < response.pagination.total_pages);
    } catch (error) {
      console.error("회의 목록 로딩 실패:", error);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [debouncedSearchTerm, startDate, endDate, sortBy]);
  
  // 더 많은 데이터 로드
  const loadMoreMeetings = useCallback(() => {
    if (!hasMore || isLoadingMore) return;
    loadMeetings(currentPage + 1, false);
  }, [currentPage, hasMore, isLoadingMore, loadMeetings]);
  
  // 초기 데이터 로드 및 필터 변경 시 재로드
  useEffect(() => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }
    
    // 필터가 변경되면 첫 페이지부터 다시 로드
    setMeetings([]);
    setCurrentPage(1);
    setHasMore(true);
    loadMeetings(1, true);
  }, [isAuthenticated, debouncedSearchTerm, startDate, endDate, sortBy, loadMeetings]);
  
  // 무한 스크롤: 다음 페이지 로드
  useEffect(() => {
    if (!isAuthenticated || !hasMore || isLoading || isLoadingMore) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMoreMeetings();
        }
      },
      { threshold: 0.1 }
    );
    
    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }
    
    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [isAuthenticated, hasMore, isLoading, isLoadingMore, loadMoreMeetings]);
  
  // 날짜 필터 적용
  const handleApplyDateFilter = () => {
    setStartDate(startDateInput);
    setEndDate(endDateInput);
  };
  
  // 날짜 필터 초기화
  const clearDateFilter = () => {
    setStartDateInput('');
    setEndDateInput('');
    setStartDate('');
    setEndDate('');
  };
  
  // 날짜 필터가 적용되어 있는지 확인
  const hasDateFilter = startDate || endDate;
  
  // 날짜순 토글 핸들러
  const handleDateSortToggle = () => {
    if (sortType === 'date') {
      // 날짜순이 이미 선택되어 있으면 방향만 토글
      setSortDirection(prev => prev === 'desc' ? 'asc' : 'desc');
    } else {
      // 다른 정렬이 선택되어 있으면 날짜순으로 변경 (기본: 최신순)
      setSortType('date');
      setSortDirection('desc');
    }
  };
  
  // 제목순 토글 핸들러
  const handleTitleSortToggle = () => {
    if (sortType === 'title') {
      // 제목순이 이미 선택되어 있으면 방향만 토글
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      // 다른 정렬이 선택되어 있으면 제목순으로 변경 (기본: 가나다순)
      setSortType('title');
      setSortDirection('asc');
    }
  };
  
  if (isLoading && meetings.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-slate-500 animate-pulse">노트 목록을 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 헤더 및 검색 영역 */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">내 노트</h1>
          <p className="text-slate-500 mt-1">저장된 모든 회의와 기록을 관리하세요.</p>
        </div>
        
        <div className="flex gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="제목, 내용 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleDateSortToggle}
              className={`px-3 py-2 rounded-xl border transition-all text-sm font-medium flex items-center ${
                sortType === 'date'
                  ? 'bg-brand-50 border-brand-200 text-brand-700'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {sortType === 'date' 
                ? (sortDirection === 'desc' ? '최신순' : '오래된 순')
                : '날짜순'
              }
              {sortType === 'date' && (
                sortDirection === 'desc' 
                  ? <ArrowDown className="w-4 h-4 ml-1" />
                  : <ArrowUp className="w-4 h-4 ml-1" />
              )}
            </button>
            <button
              onClick={handleTitleSortToggle}
              className={`px-3 py-2 rounded-xl border transition-all text-sm font-medium flex items-center ${
                sortType === 'title'
                  ? 'bg-brand-50 border-brand-200 text-brand-700'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {sortType === 'title'
                ? (sortDirection === 'asc' ? '제목 가나다순' : '제목 역순')
                : '제목순'
              }
              {sortType === 'title' && (
                sortDirection === 'asc'
                  ? <ArrowUp className="w-4 h-4 ml-1" />
                  : <ArrowDown className="w-4 h-4 ml-1" />
              )}
            </button>
          </div>
          <button
            aria-label="날짜 필터"
            aria-expanded={showDateFilter}
            onClick={() => setShowDateFilter(!showDateFilter)}
            className={`p-2 border rounded-xl hover:bg-slate-50 transition-colors ${
              hasDateFilter 
                ? 'bg-brand-50 border-brand-200 text-brand-700' 
                : 'bg-white border-slate-200 text-slate-600'
            }`}
          >
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {/* 날짜 필터 UI */}
      {showDateFilter && (
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                시작일
              </label>
              <input
                type="date"
                value={startDateInput}
                onChange={(e) => setStartDateInput(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                종료일
              </label>
              <input
                type="date"
                value={endDateInput}
                onChange={(e) => setEndDateInput(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleApplyDateFilter}
                className="px-4 py-2 text-sm font-medium bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
              >
                필터 적용
              </button>
              {hasDateFilter && (
                <button
                  onClick={clearDateFilter}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  초기화
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 목록 영역 */}
      {!isAuthenticated ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="inline-flex p-4 bg-slate-50 rounded-full mb-4">
            <FileText className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            로그인이 필요합니다
          </h3>
          <p className="text-slate-500 mb-6">
            노트를 확인하려면 로그인해주세요.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center px-5 py-2.5 bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors font-medium"
          >
            <LogIn className="w-5 h-5 mr-2" />
            로그인하기
          </Link>
        </div>
      ) : meetings.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="inline-flex p-4 bg-slate-50 rounded-full mb-4">
            <FileText className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            {debouncedSearchTerm || hasDateFilter ? '검색 결과가 없습니다' : '아직 작성된 노트가 없습니다'}
          </h3>
          <p className="text-slate-500 mb-6">
            {debouncedSearchTerm || hasDateFilter ? '다른 검색어나 날짜 범위로 다시 시도해보세요.' : '새로운 회의나 강의를 기록해보세요.'}
          </p>
          {!debouncedSearchTerm && !hasDateFilter && (
            <Link
              to="/record"
              className="inline-flex items-center px-5 py-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors font-medium"
            >
              새 기록 시작
            </Link>
          )}
        </div>
      ) : (
        <>
          <div className="grid gap-4">
            {meetings.map((meeting) => (
              <Link
                key={meeting.meeting_id}
                to={`/notes/${meeting.meeting_id}`}
                className="group block bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-brand-200 transition-all duration-200"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
                      <Calendar className="w-3 h-3 mr-1" />
                      {meeting.date}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 group-hover:text-brand-600 transition-colors truncate mb-1">
                    {meeting.title}
                  </h3>

                  <p className="text-slate-600 text-sm line-clamp-2 leading-relaxed">
                    {meeting.summary || '아직 요약된 내용이 없습니다. 클릭하여 상세 내용을 확인하세요.'}
                  </p>
                </div>
              </Link>
            ))}
          </div>
          
          {/* 무한 스크롤 트리거 및 로딩 표시 */}
          {hasMore && (
            <div ref={observerTarget} className="py-8 text-center">
              {isLoadingMore && (
                <div className="text-slate-500 animate-pulse">더 많은 노트를 불러오는 중...</div>
              )}
            </div>
          )}
          
          {/* 모든 데이터 로드 완료 표시 */}
          {!hasMore && meetings.length > 0 && (
            <div className="py-8 text-center text-slate-400 text-sm">
              모든 노트를 불러왔습니다. (총 {meetings.length}개)
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default NoteList;

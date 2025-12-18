import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Calendar, Filter, MoreVertical, FileText } from 'lucide-react';
import { meetingService, type Meeting } from '../services/meeting';

const NoteList = () => {
  const navigate = useNavigate();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [filteredMeetings, setFilteredMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        const data = await meetingService.getAllMeetings();
        setMeetings(data);
        setFilteredMeetings(data);
      } catch (error) {
        console.error("회의 목록 로딩 실패:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMeetings();
  }, []);

  // 검색어 변경 시 필터링
  useEffect(() => {
    const term = searchTerm.toLowerCase();
    const filtered = meetings.filter(meeting => 
      meeting.title.toLowerCase().includes(term) || 
      (meeting.summary && meeting.summary.toLowerCase().includes(term))
    );
    setFilteredMeetings(filtered);
  }, [searchTerm, meetings]);

  if (isLoading) {
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
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
            />
          </div>
          <button className="p-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition-colors">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* 목록 영역 */}
      {filteredMeetings.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-3xl border border-slate-100 shadow-sm">
          <div className="inline-flex p-4 bg-slate-50 rounded-full mb-4">
            <FileText className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            {searchTerm ? '검색 결과가 없습니다' : '아직 작성된 노트가 없습니다'}
          </h3>
          <p className="text-slate-500 mb-6">
            {searchTerm ? '다른 검색어로 다시 시도해보세요.' : '새로운 회의나 강의를 기록해보세요.'}
          </p>
          {!searchTerm && (
            <Link
              to="/record"
              className="inline-flex items-center px-5 py-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors font-medium"
            >
              새 기록 시작
            </Link>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredMeetings.map((meeting) => (
            <div
              key={meeting.meeting_id}
              onClick={() => navigate(`/notes/${meeting.meeting_id}`)}
              className="group bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-200 cursor-pointer"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600">
                      <Calendar className="w-3 h-3 mr-1" />
                      {meeting.date}
                    </span>
                    {/* 오디오/비디오 타입 뱃지 (추후 데이터 연동 시 실제 값으로 대체) */}
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
                      Audio
                    </span>
                  </div>
                  
                  <div className="block group-hover:text-amber-600 transition-colors">
                    <h3 className="text-lg font-bold text-slate-900 truncate mb-1">
                      {meeting.title}
                    </h3>
                  </div>
                  
                  <p className="text-slate-600 text-sm line-clamp-2 leading-relaxed">
                    {meeting.summary || '아직 요약된 내용이 없습니다. 클릭하여 상세 내용을 확인하세요.'}
                  </p>
                  
                  <div className="flex gap-2 mt-3">
                    {/* 태그 (임시) */}
                    {['#회의', '#기획'].map((tag, i) => (
                      <span key={i} className="text-xs text-slate-400 font-medium">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation(); // 카드 클릭 이벤트 전파 방지
                      // 추후 더보기 메뉴 기능 추가
                    }}
                    className="p-2 text-slate-300 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors"
                  >
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NoteList;

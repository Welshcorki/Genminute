import { useEffect, useState } from 'react';
import { Search, Calendar, Share2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { shareService, type SharedMeeting } from '../services/share';

const SharedNoteList = () => {
  const navigate = useNavigate();
  const [meetings, setMeetings] = useState<SharedMeeting[]>([]);
  const [filteredMeetings, setFilteredMeetings] = useState<SharedMeeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchSharedMeetings = async () => {
      try {
        const data = await shareService.getSharedMeetings();
        setMeetings(data);
        setFilteredMeetings(data);
      } catch (error) {
        console.error("공유받은 노트 목록 로딩 실패:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSharedMeetings();
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
        <div className="text-slate-500 animate-pulse">공유받은 노트 목록을 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 헤더 및 검색 영역 */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">공유받은 노트</h1>
          <p className="text-slate-500 mt-1">다른 사용자가 공유한 회의와 기록을 확인하세요.</p>
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
        </div>
      </div>

      {/* 목록 영역 */}
      {filteredMeetings.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-3xl border border-slate-100 shadow-sm">
          <div className="inline-flex p-4 bg-slate-50 rounded-full mb-4">
            <Share2 className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            {searchTerm ? '검색 결과가 없습니다' : '공유받은 노트가 없습니다'}
          </h3>
          <p className="text-slate-500 mb-6">
            {searchTerm ? '다른 검색어로 다시 시도해보세요.' : '다른 사용자가 노트를 공유하면 여기에 표시됩니다.'}
          </p>
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
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                      <Share2 className="w-3 h-3 mr-1" />
                      공유받음
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
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SharedNoteList;


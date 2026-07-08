import { useState, useEffect } from 'react';
import { X, Mail, User, Trash2, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { shareService, type SharedUser } from '../services/share';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  meetingId: string;
}

const ShareModal = ({ isOpen, onClose, meetingId }: ShareModalProps) => {
  const [email, setEmail] = useState('');
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 모달이 열릴 때마다 공유 사용자 목록 로드
  useEffect(() => {
    if (isOpen && meetingId) {
      loadSharedUsers();
    }
  }, [isOpen, meetingId]);

  // 공유 사용자 목록 로드
  const loadSharedUsers = async () => {
    try {
      setIsLoadingUsers(true);
      const users = await shareService.getSharedUsers(meetingId);
      setSharedUsers(users);
    } catch (err) {
      console.error('공유 사용자 목록 로드 실패:', err);
    } finally {
      setIsLoadingUsers(false);
    }
  };

  // 공유하기
  const handleShare = async () => {
    if (!email.trim()) {
      setError('이메일을 입력해주세요.');
      return;
    }

    // 이메일 형식 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      const result = await shareService.shareMeeting(meetingId, email.trim());
      
      if (result.success) {
        setSuccess(result.message || '공유되었습니다.');
        setEmail('');
        // 공유 사용자 목록 새로고침
        await loadSharedUsers();
        // 2초 후 성공 메시지 제거
        setTimeout(() => setSuccess(null), 2000);
      } else {
        setError(result.error || result.message || '공유에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('공유 실패:', err);
      setError(err.response?.data?.error || '공유 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 공유 해제
  const handleUnshare = async (userId: number, userEmail: string) => {
    if (!window.confirm(`${userEmail}님의 공유를 해제하시겠습니까?`)) {
      return;
    }

    try {
      const result = await shareService.unshareMeeting(meetingId, userId);
      
      if (result.success) {
        // 공유 사용자 목록에서 제거
        setSharedUsers(prev => prev.filter(user => user.id !== userId));
        setSuccess('공유가 해제되었습니다.');
        setTimeout(() => setSuccess(null), 2000);
      } else {
        setError(result.error || result.message || '공유 해제에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('공유 해제 실패:', err);
      setError(err.response?.data?.error || '공유 해제 중 오류가 발생했습니다.');
    }
  };

  // Enter 키로 공유
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleShare();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 배경 오버레이 */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />
      
      {/* 모달 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 헤더 */}
          <div className="flex items-center justify-between p-6 border-b border-slate-200">
            <h2 className="text-xl font-bold text-slate-900">노트 공유</h2>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* 컨텐츠 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* 이메일 입력 */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                이메일 주소
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setError(null);
                    }}
                    onKeyDown={handleKeyDown}
                    placeholder="user@example.com"
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                </div>
                <button
                  onClick={handleShare}
                  disabled={isLoading || !email.trim()}
                  className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    '공유'
                  )}
                </button>
              </div>
            </div>

            {/* 에러/성공 메시지 */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{success}</span>
              </div>
            )}

            {/* 공유된 사용자 목록 */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-3">
                공유된 사용자 ({sharedUsers.length})
              </h3>
              {isLoadingUsers ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-brand-600 animate-spin" />
                </div>
              ) : sharedUsers.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  공유된 사용자가 없습니다.
                </div>
              ) : (
                <div className="space-y-2">
                  {sharedUsers.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {user.profile_picture ? (
                          <img
                            src={user.profile_picture}
                            alt={user.name || user.email}
                            className="w-10 h-10 rounded-full object-cover border-2 border-slate-200"
                          />
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center flex-shrink-0">
                            <User className="w-5 h-5 text-brand-600" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 truncate">
                            {user.name || user.email}
                          </p>
                          <p className="text-xs text-slate-500 truncate">
                            {user.email}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleUnshare(user.id, user.email)}
                        className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
                        title="공유 해제"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 푸터 */}
          <div className="p-6 border-t border-slate-200">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ShareModal;


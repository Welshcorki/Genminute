import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, FileText, Mic, Menu, X, LogOut, User, Share2, LogIn } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import GlobalChatSidebar from './GlobalChatSidebar';

const Layout = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut, isAuthenticated } = useAuth();

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);

  // 현재 경로가 활성화되었는지 확인하는 헬퍼 함수
  const isActive = (path: string) => location.pathname === path;

  // 로그아웃 처리
  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('로그아웃 실패:', error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20 items-center">
            {/* Logo */}
            <Link to="/" className="flex items-center" onClick={closeMenu}>
              <img src="/logo.png" alt="GenMinute Logo" className="h-16 w-auto object-contain hover:opacity-90 transition-opacity" />
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-6">
              <NavLink to="/" icon={<Home size={20} />} label="홈" active={isActive('/')} />
              <NavLink to="/notes" icon={<FileText size={20} />} label="내 노트" active={isActive('/notes')} />
              <NavLink to="/shared-notes" icon={<Share2 size={20} />} label="공유받은 노트" active={isActive('/shared-notes')} />
              <NavLink to="/record" icon={<Mic size={20} />} label="기록" active={isActive('/record')} />

              {/* User Menu / Login Button */}
              <div className="relative ml-4">
                {isAuthenticated ? (
                  <>
                    <button
                      onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                      className="flex items-center space-x-2 p-2 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      {user?.profile_picture ? (
                        <img
                          src={user.profile_picture}
                          alt={user.name || 'User'}
                          className="h-8 w-8 rounded-full object-cover border-2 border-slate-200"
                        />
                      ) : (
                        <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center">
                          <User size={18} className="text-brand-600" />
                        </div>
                      )}
                      <span className="text-sm font-medium text-slate-700 hidden lg:block">
                        {user?.name || user?.email?.split('@')[0] || '사용자'}
                      </span>
                    </button>

                    {/* Dropdown Menu */}
                    {isUserMenuOpen && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50">
                        <div className="px-4 py-2 border-b border-slate-100">
                          <p className="text-sm font-medium text-slate-900 truncate">
                            {user?.name || '사용자'}
                          </p>
                          <p className="text-xs text-slate-500 truncate">
                            {user?.email}
                          </p>
                        </div>
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                        >
                          <LogOut size={16} />
                          <span>로그아웃</span>
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <Link
                    to="/login"
                    className="flex items-center space-x-2 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors font-medium text-sm"
                  >
                    <LogIn size={18} />
                    <span className="hidden lg:inline">로그인</span>
                  </Link>
                )}
              </div>
            </nav>

            {/* Mobile Menu Button */}
            <div className="md:hidden flex items-center space-x-2">
              {/* Mobile User Avatar / Login Button */}
              {isAuthenticated ? (
                user?.profile_picture ? (
                  <img
                    src={user.profile_picture}
                    alt={user.name || 'User'}
                    className="h-8 w-8 rounded-full object-cover border-2 border-slate-200"
                  />
                ) : (
                  <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center">
                    <User size={18} className="text-brand-600" />
                  </div>
                )
              ) : (
                <Link
                  to="/login"
                  className="flex items-center space-x-1 px-3 py-1.5 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium"
                >
                  <LogIn size={16} />
                  <span>로그인</span>
                </Link>
              )}
              <button
                onClick={toggleMenu}
                className="p-2 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              >
                {isMenuOpen ? <X size={28} /> : <Menu size={28} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white shadow-lg absolute w-full">
            <div className="px-4 pt-4 pb-4 space-y-2">
              {/* User Info / Login Button */}
              {isAuthenticated ? (
                <>
                  <div className="px-4 py-3 mb-2 bg-slate-50 rounded-lg">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {user?.name || '사용자'}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {user?.email}
                    </p>
                  </div>
                  
                  <MobileNavLink to="/" icon={<Home size={20} />} label="홈" active={isActive('/')} onClick={closeMenu} />
                  <MobileNavLink to="/notes" icon={<FileText size={20} />} label="내 노트" active={isActive('/notes')} onClick={closeMenu} />
                  <MobileNavLink to="/shared-notes" icon={<Share2 size={20} />} label="공유받은 노트" active={isActive('/shared-notes')} onClick={closeMenu} />
                  <MobileNavLink to="/record" icon={<Mic size={20} />} label="기록" active={isActive('/record')} onClick={closeMenu} />
                  
                  {/* Logout Button */}
                  <button
                    onClick={() => {
                      closeMenu();
                      handleLogout();
                    }}
                    className="w-full flex items-center space-x-4 px-4 py-3 rounded-lg text-base font-semibold text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut size={20} />
                    <span>로그아웃</span>
                  </button>
                </>
              ) : (
                <>
                  <MobileNavLink to="/" icon={<Home size={20} />} label="홈" active={isActive('/')} onClick={closeMenu} />
                  <MobileNavLink to="/notes" icon={<FileText size={20} />} label="내 노트" active={isActive('/notes')} onClick={closeMenu} />
                  <MobileNavLink to="/shared-notes" icon={<Share2 size={20} />} label="공유받은 노트" active={isActive('/shared-notes')} onClick={closeMenu} />
                  <MobileNavLink to="/record" icon={<Mic size={20} />} label="기록" active={isActive('/record')} onClick={closeMenu} />
                  
                  {/* Login Button */}
                  <Link
                    to="/login"
                    onClick={closeMenu}
                    className="w-full flex items-center space-x-4 px-4 py-3 rounded-lg text-base font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-colors"
                  >
                    <LogIn size={20} />
                    <span>로그인</span>
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <Outlet />
      </main>

      {/* Click outside to close user menu */}
      {isUserMenuOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsUserMenuOpen(false)}
        />
      )}

      {/* Global Chatbot Sidebar */}
      <GlobalChatSidebar hideOnPages={['/notes/']} />
    </div>
  );
};

// Helper Components for clean code
const NavLink = ({ to, icon, label, active }: { to: string; icon: React.ReactNode; label: string; active: boolean }) => (
  <Link
    to={to}
    className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
      active
        ? 'text-slate-900 bg-gray-100 shadow-sm'
        : 'text-slate-500 hover:text-slate-900 hover:bg-gray-50'
    }`}
  >
    {icon}
    <span>{label}</span>
  </Link>
);

const MobileNavLink = ({ to, icon, label, active, onClick }: { to: string; icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) => (
  <Link
    to={to}
    onClick={onClick}
    className={`flex items-center space-x-4 px-4 py-3 rounded-lg text-base font-semibold transition-colors ${
      active
        ? 'text-slate-900 bg-gray-100'
        : 'text-slate-500 hover:text-slate-900 hover:bg-gray-50'
    }`}
  >
    {icon}
    <span>{label}</span>
  </Link>
);

export default Layout;

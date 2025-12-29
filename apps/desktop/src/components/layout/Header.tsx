/**
 * 顶部导航栏组件 - 支持字体大小调整和用户菜单
 * @author Ysf
 */
import { useState, useRef, useEffect } from 'react';
import { Bell, Search, User, Type, LogOut, Settings } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
import { useAppStore, FontSize } from '@/stores/useAppStore';
import { useAuth, useAuthStore } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

const fontSizeOptions: { value: FontSize; label: string }[] = [
  { value: 'small', label: '小' },
  { value: 'medium', label: '中' },
  { value: 'large', label: '大' },
];

export function Header() {
  const navigate = useNavigate();
  const { fontSize, setFontSize } = useAppStore();
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate({ to: '/login' });
  };

  return (
    <header className="h-14 bg-white flex items-center justify-between px-5 shadow-xs">
      <div className="flex items-center gap-2 flex-1 max-w-sm">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-lg flex-1">
          <Search className="w-4 h-4 text-slate-400" strokeWidth={1.75} />
          <input
            type="text"
            placeholder="搜索内容、草稿..."
            className="flex-1 bg-transparent border-none outline-none text-slate-700 placeholder:text-slate-400"
          />
          <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded bg-slate-100 px-1.5 font-mono text-[10px] text-slate-400">
            ⌘K
          </kbd>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {/* 字体大小切换 */}
        <div className="flex items-center gap-1 px-1 py-1 bg-slate-100 rounded-lg">
          <Type className="w-3.5 h-3.5 text-slate-400 ml-1" strokeWidth={1.75} />
          {fontSizeOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFontSize(opt.value)}
              className={cn(
                'px-2 py-1 rounded-md text-xs font-medium transition-all duration-150',
                fontSize === opt.value
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="w-px h-5 bg-slate-200 mx-1" />
        <button className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors duration-150">
          <Bell className="w-[18px] h-[18px]" strokeWidth={1.75} />
        </button>

        {/* 用户菜单 */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2 p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors duration-150"
          >
            {user?.avatar ? (
              <img src={user.avatar} alt="" className="w-7 h-7 rounded-full" />
            ) : (
              <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center">
                <User className="w-4 h-4 text-blue-600" strokeWidth={1.75} />
              </div>
            )}
          </button>

          {showMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-100 py-1 z-50">
              <div className="px-4 py-2 border-b border-slate-100">
                <p className="text-sm font-medium text-slate-800 truncate">
                  {user?.nickname || user?.username || '用户'}
                </p>
                <p className="text-xs text-slate-400 truncate">{user?.phone || user?.email}</p>
              </div>
              <button
                onClick={() => { setShowMenu(false); navigate({ to: '/settings' }); }}
                className="w-full px-4 py-2 text-left text-sm text-slate-600 hover:bg-slate-50 flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                设置
              </button>
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                退出登录
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

/**
 * 侧边栏组件 - 可折叠设计
 * @author Ysf
 * @updated 2026-01-07
 */
import { Link, useRouterState, useNavigate } from '@tanstack/react-router';
import {
  LayoutDashboard, Lightbulb, PenTool, Library, Sparkles,
  FolderOpen, Send, BarChart2, Users, Bot, Settings,
  LogOut, ChevronLeft, ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/useAppStore';
import { useAuth } from '@/hooks/useAuth';
import { useState } from 'react';
import logo from '@/assets/logo-icon.svg';

const navItems = [
  { path: '/', label: '工作台', icon: LayoutDashboard },
  { path: '/topics', label: '选题中心', icon: Lightbulb },
  { path: '/creation', label: '创作中心', icon: PenTool },
  { path: '/assets', label: '素材库', icon: Library },
  { path: '/inspiration', label: '灵感库', icon: Sparkles },
  { path: '/works', label: '作品管理', icon: FolderOpen },
  { path: '/publish', label: '发布中心', icon: Send },
  { path: '/analytics', label: '数据看板', icon: BarChart2 },
  { path: '/accounts', label: '账号管理', icon: Users },
  { path: '/agent', label: 'Agent', icon: Bot },
];

export function Sidebar() {
  const routerState = useRouterState();
  const navigate = useNavigate();
  const currentPath = routerState.location.pathname;
  const { sidebarCollapsed, toggleSidebar } = useAppStore();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate({ to: '/login' });
  };

  return (
    <aside
      className={cn(
        'glass-card flex flex-col shrink-0 h-full z-20 transition-all duration-200 ease-out relative rounded-none border-t-0 border-b-0 border-l-0',
        sidebarCollapsed ? 'w-16' : 'w-[160px]'
      )}
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-3 shrink-0 gap-2 border-b border-[rgb(var(--color-border))]">
        <img src={logo} alt="创流" className="w-8 h-8 shrink-0" />
        {!sidebarCollapsed && (
          <div className="flex flex-col overflow-hidden animate-fade-in">
            <span className="text-lg font-heading font-bold text-primary-600 dark:text-primary-400 leading-tight">
              创流
            </span>
            <span className="text-[10px] text-slate-500 truncate">
              AI超级大脑
            </span>
          </div>
        )}
      </div>

      {/* 折叠按钮 */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-[72px] w-6 h-6 bg-white dark:bg-slate-800 border border-[rgb(var(--color-border))] rounded-full flex items-center justify-center shadow-sm hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors z-30 cursor-pointer"
        title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
      >
        {sidebarCollapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
      </button>

      {/* 导航菜单 */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1 scrollbar-thin">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPath === item.path || (item.path !== '/' && currentPath.startsWith(item.path));

          return (
            <Link
              key={item.path}
              to={item.path}
              title={sidebarCollapsed ? item.label : undefined}
              className={cn(
                'flex items-center rounded-lg transition-all duration-fast cursor-pointer',
                sidebarCollapsed ? 'px-3 py-2.5 justify-center' : 'px-3 py-2',
                isActive
                  ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-slate-200'
              )}
            >
              <Icon
                className={cn('w-5 h-5 shrink-0', !sidebarCollapsed && 'mr-3')}
                strokeWidth={isActive ? 2 : 1.5}
              />
              {!sidebarCollapsed && (
                <span className="font-medium text-sm truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* 用户区域 */}
      <div className="p-2 shrink-0 border-t border-[rgb(var(--color-border))] relative">
        <div
          onClick={() => setShowUserMenu(!showUserMenu)}
          className={cn(
            'flex items-center rounded-lg cursor-pointer hover:bg-slate-100 dark:hover:bg-white/5 transition-colors',
            sidebarCollapsed ? 'p-2 justify-center' : 'px-2 py-2'
          )}
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary-500 to-cta shrink-0 flex items-center justify-center text-white text-xs font-bold shadow-sm">
            {user?.nickname?.[0] || user?.username?.[0] || 'U'}
          </div>
          {!sidebarCollapsed && (
            <div className="ml-2 overflow-hidden">
              <p className="text-sm font-medium truncate">{user?.nickname || user?.username || '未登录'}</p>
              <p className="text-xs text-slate-500 truncate">Pro Plan</p>
            </div>
          )}
        </div>

        {/* 用户菜单弹出层 */}
        {showUserMenu && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
            <div className={cn(
              'absolute bottom-full mb-2 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-[rgb(var(--color-border))] p-1 z-50 animate-slide-up',
              sidebarCollapsed ? 'left-2 w-40' : 'left-2 right-2'
            )}>
              <Link
                to="/settings"
                className="flex items-center px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 text-sm transition-colors cursor-pointer"
                onClick={() => setShowUserMenu(false)}
              >
                <Settings className="w-4 h-4 mr-2 text-slate-400" />
                设置
              </Link>
              <div className="divider my-1" />
              <button
                onClick={handleLogout}
                className="w-full flex items-center px-3 py-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 text-red-600 text-sm transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4 mr-2" />
                退出登录
              </button>
            </div>
          </>
        )}
      </div>
    </aside>
  );
}

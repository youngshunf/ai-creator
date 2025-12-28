/**
 * 侧边栏组件 - 精致版
 * @author Ysf
 */
import { Link, useRouterState } from '@tanstack/react-router';
import { Home, PenTool, Send, BarChart3, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import logoIcon from '@/assets/logo-icon.svg';

const navItems = [
  { path: '/', label: '首页', icon: Home },
  { path: '/creation', label: 'AI 创作', icon: PenTool },
  { path: '/publish', label: '发布中心', icon: Send },
  { path: '/analytics', label: '数据分析', icon: BarChart3 },
  { path: '/settings', label: '设置', icon: Settings },
];

export function Sidebar() {
  const routerState = useRouterState();
  const currentPath = routerState.location.pathname;

  return (
    <aside className="w-60 bg-white flex flex-col shadow-sm">
      <div className="h-16 px-5 flex items-center gap-3">
        <img src={logoIcon} alt="创流" className="w-8 h-8" />
        <div>
          <h1 className="text-base font-semibold text-slate-900 tracking-tight">创流</h1>
          <p className="text-xs text-slate-400">自媒体创作者的AI超级大脑</p>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPath === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'gradient-primary text-white shadow-brand'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              )}
            >
              <Icon className="w-[18px] h-[18px]" strokeWidth={isActive ? 2 : 1.75} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 bg-slate-50/50">
        <p className="text-2xs text-slate-400 font-medium">CreatorFlow v0.1.0</p>
      </div>
    </aside>
  );
}

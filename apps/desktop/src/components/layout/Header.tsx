/**
 * 顶部导航组件 - 简化设计
 * @author Ysf
 * @updated 2026-01-07
 */
import { useState, useRef, useEffect } from 'react';
import { Bell, Sun, Moon, Type } from 'lucide-react';
import { useAppStore } from '@/stores/useAppStore';
import { useRouterState } from '@tanstack/react-router';
import { ProjectSelector } from './ProjectSelector';

const PAGE_TITLES: Record<string, string> = {
  '/': '工作台',
  '/topics': '选题中心',
  '/creation': '创作中心',
  '/accounts': '账号管理',
  '/assets': '素材库',
  '/inspiration': '灵感库',
  '/works': '作品管理',
  '/analytics': '数据看板',
  '/publish': '发布中心',
  '/agent': 'Agent',
  '/settings': '设置',
};

const FONT_SIZES = [
  { label: '小', value: 14 },
  { label: '中', value: 16 },
  { label: '大', value: 18 },
  { label: '特大', value: 20 },
];

export function Header() {
  const { theme, toggleTheme, fontSize, setFontSize } = useAppStore();
  const routerState = useRouterState();
  const currentPath = routerState.location.pathname;
  const [showFontMenu, setShowFontMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const title = PAGE_TITLES[currentPath] || '创流';
  const isDark = theme === 'dark' || (theme === 'system' && typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowFontMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="h-14 flex items-center justify-between px-6 glass-card rounded-none border-t-0 border-r-0 border-l-0 relative z-[200]">
      {/* 页面标题 */}
      <h1 className="text-lg font-heading font-semibold">{title}</h1>

      {/* 操作区 */}
      <div className="flex items-center gap-3">
        <ProjectSelector />

        <div className="divider-vertical h-5" />

        {/* 字体大小 */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowFontMenu(!showFontMenu)}
            className="btn-icon"
            title="调整字体大小"
          >
            <Type className="w-5 h-5" />
          </button>
          {showFontMenu && (
            <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 py-1 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 min-w-[100px] z-[100]">
              {FONT_SIZES.map((size) => (
                <button
                  key={size.value}
                  onClick={() => { setFontSize(size.value); setShowFontMenu(false); }}
                  className={`w-full px-4 py-2 text-center text-sm hover:bg-slate-100 dark:hover:bg-slate-700 ${fontSize === size.value ? 'text-primary-600 font-medium' : ''}`}
                >
                  {size.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 主题切换 */}
        <button
          onClick={toggleTheme}
          className="btn-icon"
          title="切换主题"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* 通知 */}
        <button className="btn-icon relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-cta rounded-full" />
        </button>
      </div>
    </header>
  );
}

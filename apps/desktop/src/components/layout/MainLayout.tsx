/**
 * 主布局组件 - 响应式设计
 * @author Ysf
 * @updated 2026-01-07
 */
import { ReactNode, useEffect, useRef } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAppStore } from '@/stores/useAppStore';

interface MainLayoutProps {
  children: ReactNode;
}

const MIN_WIDTH_FOR_EXPANDED = 1024; // md 断点

export function MainLayout({ children }: MainLayoutProps) {
  const { fontSize, theme, sidebarCollapsed, setSidebarCollapsed } = useAppStore();
  const userManuallyToggled = useRef(false);

  // 同步主题和字体大小
  useEffect(() => {
    const html = document.documentElement;

    // Font Size
    html.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
    html.classList.add(`font-size-${fontSize}`);

    // Theme
    if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
  }, [fontSize, theme]);

  // 响应式侧边栏：窗口变小时自动收起，变大时不自动展开
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < MIN_WIDTH_FOR_EXPANDED && !sidebarCollapsed) {
        setSidebarCollapsed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarCollapsed, setSidebarCollapsed]);

  return (
    <div className="flex h-screen bg-[rgb(var(--color-bg))] transition-colors duration-normal">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden p-6 scrollbar-thin relative z-0">{children}</main>
      </div>
    </div>
  );
}

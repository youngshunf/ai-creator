/**
 * 主布局组件 - 支持字体大小调整
 * @author Ysf
 */
import { ReactNode, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAppStore } from '@/stores/useAppStore';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const fontSize = useAppStore((s) => s.fontSize);

  // 将字体大小类应用到 html 元素，使 rem 单位生效
  useEffect(() => {
    const html = document.documentElement;
    html.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
    html.classList.add(`font-size-${fontSize}`);
  }, [fontSize]);

  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-5">{children}</main>
      </div>
    </div>
  );
}

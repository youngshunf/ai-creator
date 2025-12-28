/**
 * 顶部导航栏组件 - 支持字体大小调整
 * @author Ysf
 */
import { Bell, Search, User, Type } from 'lucide-react';
import { useAppStore, FontSize } from '@/stores/useAppStore';
import { cn } from '@/lib/utils';

const fontSizeOptions: { value: FontSize; label: string }[] = [
  { value: 'small', label: '小' },
  { value: 'medium', label: '中' },
  { value: 'large', label: '大' },
];

export function Header() {
  const { fontSize, setFontSize } = useAppStore();

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
        <button className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors duration-150">
          <User className="w-[18px] h-[18px]" strokeWidth={1.75} />
        </button>
      </div>
    </header>
  );
}

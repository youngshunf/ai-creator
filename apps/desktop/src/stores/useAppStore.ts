/**
 * 应用全局状态管理
 * @author Ysf
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type FontSize = 'small' | 'medium' | 'large';

interface AppState {
  theme: 'light' | 'dark' | 'system';
  fontSize: FontSize;
  sidebarCollapsed: boolean;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setFontSize: (size: FontSize) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'system',
      fontSize: 'medium',
      sidebarCollapsed: false,
      setTheme: (theme) => set({ theme }),
      setFontSize: (fontSize) => set({ fontSize }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    { name: 'app-storage' }
  )
);

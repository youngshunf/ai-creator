/**
 * 发布管理 Store
 * @author Ysf
 */
import { create } from 'zustand';
import { invoke } from '@tauri-apps/api/core';
import { Platform, PlatformAccount } from './useAccountStore';

export type PublishStatus = 'pending' | 'publishing' | 'success' | 'failed';

export interface PublishTask {
  id: string;
  user_id: string;
  content_id: string;
  account_id: string;
  platform: Platform;
  status: PublishStatus;
  adapted_content: string | null;
  scheduled_at: number | null;
  published_at: number | null;
  platform_post_id: string | null;
  platform_post_url: string | null;
  error_message: string | null;
  retry_count: number;
  created_at: number;
  updated_at: number;
}

export interface PublishContent {
  title: string;
  content: string;
  images: string[];
  hashtags: string[];
}

interface PublishState {
  tasks: PublishTask[];
  loading: boolean;
  error: string | null;

  fetchTasks: (contentId: string) => Promise<void>;
  createTask: (contentId: string, accountId: string, platform: Platform, scheduledAt?: number) => Promise<PublishTask>;
  publishNow: (content: PublishContent, accounts: { id: string; platform: Platform }[]) => Promise<void>;
  retryTask: (taskId: string) => Promise<void>;
  updateTaskStatus: (taskId: string, status: PublishStatus, errorMessage?: string) => Promise<void>;
}

export const usePublishStore = create<PublishState>((set, get) => ({
  tasks: [],
  loading: false,
  error: null,

  fetchTasks: async (contentId: string) => {
    set({ loading: true, error: null });
    try {
      const tasks = await invoke<PublishTask[]>('db_list_publications', { contentId });
      set({ tasks, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  createTask: async (contentId, accountId, platform, scheduledAt) => {
    set({ loading: true, error: null });
    try {
      const userId = 'current-user'; // TODO: 从 auth store 获取
      const task = await invoke<PublishTask>('db_create_publication', {
        userId,
        data: { content_id: contentId, account_id: accountId, platform, scheduled_at: scheduledAt },
      });
      set((state) => ({ tasks: [...state.tasks, task], loading: false }));
      return task;
    } catch (e) {
      set({ error: String(e), loading: false });
      throw e;
    }
  },

  publishNow: async (content, accounts) => {
    set({ loading: true, error: null });
    try {
      // 为每个账号创建发布任务
      for (const account of accounts) {
        const task = await get().createTask('temp-content-id', account.id, account.platform);
        // 更新状态为发布中
        await get().updateTaskStatus(task.id, 'publishing');

        // TODO: 调用 sidecar 执行发布
        // 模拟发布过程
        setTimeout(async () => {
          // 模拟成功/失败
          const success = Math.random() > 0.2;
          await get().updateTaskStatus(task.id, success ? 'success' : 'failed', success ? undefined : '发布失败，请重试');
        }, 3000);
      }
      set({ loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  retryTask: async (taskId: string) => {
    await get().updateTaskStatus(taskId, 'publishing');
    // TODO: 重新执行发布
    setTimeout(async () => {
      await get().updateTaskStatus(taskId, 'success');
    }, 2000);
  },

  updateTaskStatus: async (taskId, status, errorMessage) => {
    try {
      await invoke('db_update_publication_status', { id: taskId, status, errorMessage });
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, status, error_message: errorMessage || null } : t)),
      }));
    } catch (e) {
      set({ error: String(e) });
    }
  },
}));

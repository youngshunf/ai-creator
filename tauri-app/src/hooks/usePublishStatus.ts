/**
 * 发布状态 Hook
 * @author Ysf
 */
import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export type PublishStatus = 'idle' | 'publishing' | 'success' | 'error';

export interface PublishTask {
  id: string;
  platform: string;
  status: PublishStatus;
  progress: number;
  error?: string;
  postUrl?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface UsePublishStatusReturn {
  tasks: PublishTask[];
  isPublishing: boolean;
  publish: (platforms: string[], content: any) => Promise<void>;
  cancelPublish: (taskId: string) => void;
  clearTasks: () => void;
}

export function usePublishStatus(): UsePublishStatusReturn {
  const [tasks, setTasks] = useState<PublishTask[]>([]);

  const isPublishing = tasks.some((t) => t.status === 'publishing');

  const publish = useCallback(
    async (platforms: string[], content: any) => {
      // 为每个平台创建任务
      const newTasks: PublishTask[] = platforms.map((platform) => ({
        id: `${platform}-${Date.now()}`,
        platform,
        status: 'publishing' as const,
        progress: 0,
        startedAt: new Date().toISOString(),
      }));

      setTasks((prev) => [...prev, ...newTasks]);

      // 并行发布到各平台
      await Promise.all(
        newTasks.map(async (task) => {
          try {
            // 更新进度
            setTasks((prev) =>
              prev.map((t) =>
                t.id === task.id ? { ...t, progress: 30 } : t
              )
            );

            // 调用发布 API
            const result = await invoke<{
              success: boolean;
              post_url?: string;
              error?: string;
            }>('publish_content', {
              platform: task.platform,
              content,
            });

            // 更新结果
            setTasks((prev) =>
              prev.map((t) =>
                t.id === task.id
                  ? {
                      ...t,
                      status: result.success ? 'success' : 'error',
                      progress: 100,
                      postUrl: result.post_url,
                      error: result.error,
                      completedAt: new Date().toISOString(),
                    }
                  : t
              )
            );
          } catch (err) {
            setTasks((prev) =>
              prev.map((t) =>
                t.id === task.id
                  ? {
                      ...t,
                      status: 'error',
                      progress: 100,
                      error: err instanceof Error ? err.message : '发布失败',
                      completedAt: new Date().toISOString(),
                    }
                  : t
              )
            );
          }
        })
      );
    },
    []
  );

  const cancelPublish = useCallback((taskId: string) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId && t.status === 'publishing'
          ? { ...t, status: 'error', error: '已取消' }
          : t
      )
    );
  }, []);

  const clearTasks = useCallback(() => {
    setTasks((prev) => prev.filter((t) => t.status === 'publishing'));
  }, []);

  return {
    tasks,
    isPublishing,
    publish,
    cancelPublish,
    clearTasks,
  };
}

export default usePublishStatus;

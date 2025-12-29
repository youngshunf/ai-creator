/**
 * Sidecar 初始化组件
 *
 * 在应用启动时自动初始化 Sidecar 进程。
 *
 * @author Ysf
 * @date 2025-12-28
 */

import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { appDataDir } from '@tauri-apps/api/path';

interface SidecarInitializerProps {
  children: React.ReactNode;
}

export function SidecarInitializer({ children }: SidecarInitializerProps) {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initSidecar = async () => {
      try {
        const isDev = import.meta.env.DEV;

        // 开发模式：使用硬编码的项目根目录路径
        // 生产模式：使用打包的路径
        const sidecarPath = isDev
          ? '/Users/mac/saas/ai-creator'  // 开发时的项目根目录
          : await appDataDir();

        // 初始化 Sidecar
        await invoke('init_sidecar', { sidecarPath });
        setStatus('ready');
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : String(e);
        console.error('Sidecar 初始化失败:', errorMsg);
        setError(errorMsg);
        // 开发模式下允许继续使用（Sidecar 可能未配置）
        if (import.meta.env.DEV) {
          console.warn('开发模式：跳过 Sidecar 初始化');
          setStatus('ready');
        } else {
          setStatus('error');
        }
      }
    };

    initSidecar();

    // 清理：关闭 Sidecar
    return () => {
      invoke('shutdown_sidecar').catch(console.error);
    };
  }, []);

  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
          <p className="text-muted-foreground">正在初始化...</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center max-w-md p-6">
          <div className="mb-4 text-4xl">⚠️</div>
          <h2 className="text-xl font-semibold mb-2">初始化失败</h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <p className="text-sm text-muted-foreground">
            请确保已安装 Python 环境并配置正确。
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default SidecarInitializer;

/**
 * Sidecar 通信 Hook
 *
 * 提供与 Python Sidecar 进程通信的 React Hook。
 *
 * @author Ysf
 * @date 2025-12-28
 */

import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

// 类型定义
interface AIWritingRequest {
  graph_name: string;
  inputs: Record<string, unknown>;
  user_id: string;
}

interface AIWritingResult {
  title: string;
  content: string;
  tags: string[];
}

interface AIWritingResponse {
  success: boolean;
  data?: AIWritingResult;
  error?: string;
}

interface UseSidecarReturn {
  // 状态
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;

  // 方法
  initSidecar: (sidecarPath: string) => Promise<boolean>;
  shutdownSidecar: () => Promise<boolean>;
  healthCheck: () => Promise<boolean>;
  executeGraph: (graphName: string, inputs: Record<string, unknown>, userId?: string) => Promise<AIWritingResponse>;
}

/**
 * Sidecar 通信 Hook
 */
export function useSidecar(): UseSidecarReturn {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 初始化 Sidecar
   */
  const initSidecar = useCallback(async (sidecarPath: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      await invoke('init_sidecar', { sidecarPath });
      setIsInitialized(true);
      return true;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      setError(errorMsg);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 关闭 Sidecar
   */
  const shutdownSidecar = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      await invoke('shutdown_sidecar');
      setIsInitialized(false);
      return true;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      setError(errorMsg);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 健康检查
   */
  const healthCheck = useCallback(async (): Promise<boolean> => {
    try {
      const result = await invoke<boolean>('sidecar_health_check');
      return result;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      setError(errorMsg);
      return false;
    }
  }, []);

  /**
   * 执行 Graph
   */
  const executeGraph = useCallback(async (
    graphName: string,
    inputs: Record<string, unknown>,
    userId: string = 'default_user'
  ): Promise<AIWritingResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const request: AIWritingRequest = {
        graph_name: graphName,
        inputs,
        user_id: userId,
      };

      const response = await invoke<AIWritingResponse>('execute_ai_writing', { request });

      if (!response.success && response.error) {
        setError(response.error);
      }

      return response;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : String(e);
      setError(errorMsg);
      return {
        success: false,
        error: errorMsg,
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isInitialized,
    isLoading,
    error,
    initSidecar,
    shutdownSidecar,
    healthCheck,
    executeGraph,
  };
}

export default useSidecar;

/**
 * LLM 状态 Hook
 * @author Ysf
 */
import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export interface LLMStatus {
  isConnected: boolean;
  isChecking: boolean;
  lastCheckedAt: number | null;
  error: string | null;
}

export interface ModelInfo {
  modelId: string;
  provider: string;
  displayName: string;
  maxTokens: number;
  supportsStreaming: boolean;
  supportsVision: boolean;
}

export interface UsageStats {
  totalTokens: number;
  totalCost: number;
  requestCount: number;
  period: string;
  breakdown?: {
    model: string;
    tokens: number;
    cost: number;
  }[];
}

export interface UseLLMStatusReturn {
  status: LLMStatus;
  models: ModelInfo[];
  usage: UsageStats | null;
  checkConnection: () => Promise<boolean>;
  fetchModels: () => Promise<void>;
  fetchUsage: (period?: string) => Promise<void>;
}

export function useLLMStatus(): UseLLMStatusReturn {
  const [status, setStatus] = useState<LLMStatus>({
    isConnected: false,
    isChecking: false,
    lastCheckedAt: null,
    error: null,
  });
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);

  const checkConnection = useCallback(async (): Promise<boolean> => {
    setStatus((prev) => ({ ...prev, isChecking: true, error: null }));

    try {
      const response = await invoke<{ success: boolean; error?: string }>(
        'check_llm_connection'
      );

      const isConnected = response.success;
      setStatus({
        isConnected,
        isChecking: false,
        lastCheckedAt: Date.now(),
        error: response.error || null,
      });

      return isConnected;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '连接检查失败';
      setStatus({
        isConnected: false,
        isChecking: false,
        lastCheckedAt: Date.now(),
        error: errorMessage,
      });
      return false;
    }
  }, []);

  const fetchModels = useCallback(async (): Promise<void> => {
    try {
      const response = await invoke<{
        success: boolean;
        data?: ModelInfo[];
      }>('get_available_models');

      if (response.success && response.data) {
        setModels(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  }, []);

  const fetchUsage = useCallback(async (period = 'month'): Promise<void> => {
    try {
      const response = await invoke<{
        success: boolean;
        data?: UsageStats;
      }>('get_usage_stats', { period });

      if (response.success && response.data) {
        setUsage(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch usage:', err);
    }
  }, []);

  useEffect(() => {
    checkConnection();

    const interval = setInterval(() => {
      checkConnection();
    }, 30000);

    return () => clearInterval(interval);
  }, [checkConnection]);

  return {
    status,
    models,
    usage,
    checkConnection,
    fetchModels,
    fetchUsage,
  };
}

export default useLLMStatus;

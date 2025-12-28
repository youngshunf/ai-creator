/**
 * 认证 Hook
 * @author Ysf
 */
import { useState, useCallback, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  username: string;
  email?: string;
  avatar?: string;
  subscription?: {
    plan: 'free' | 'pro' | 'enterprise';
    expiresAt?: string;
  };
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setToken: (token) => set({ token }),

      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'ai-creator-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

export function useAuth(): UseAuthReturn {
  const { user, isAuthenticated, setUser, setToken, logout: storeLogout } =
    useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(
    async (credentials: LoginCredentials): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await invoke<{
          success: boolean;
          data?: {
            user: User;
            token: string;
            llm_token: string;
          };
          error?: string;
        }>('login', { credentials });

        if (!response.success || !response.data) {
          setError(response.error || '登录失败');
          return false;
        }

        const { user, token, llm_token } = response.data;

        setUser(user);
        setToken(token);

        await invoke('save_llm_token', { token: llm_token });

        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : '登录失败，请重试';
        setError(errorMessage);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [setUser, setToken]
  );

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);

    try {
      await invoke('clear_llm_token');
      storeLogout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [storeLogout]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const response = await invoke<{
        success: boolean;
        data?: { token: string };
      }>('refresh_token');

      if (response.success && response.data) {
        setToken(response.data.token);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, [setToken]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
  };
}

export default useAuth;

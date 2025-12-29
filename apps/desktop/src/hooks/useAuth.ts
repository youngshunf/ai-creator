/**
 * 认证 Hook
 * @author Ysf
 */
import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: number;
  uuid: string;
  username: string;
  nickname: string;
  phone?: string;
  email?: string;
  avatar?: string;
  is_new_user: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  llmToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string, llmToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      llmToken: null,
      isAuthenticated: false,

      setAuth: (user, token, llmToken) =>
        set({
          user,
          token,
          llmToken,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          token: null,
          llmToken: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'ai-creator-auth',
    }
  )
);

interface LoginResponse {
  user: User;
  token: string;
  llm_token: string;
  is_new_user: boolean;
}

export function useAuth() {
  const { user, isAuthenticated, setAuth, logout: storeLogout } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 发送验证码
  const sendCode = useCallback(async (phone: string): Promise<boolean> => {
    setIsSendingCode(true);
    setError(null);
    try {
      await invoke('send_verification_code', { phone });
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return false;
    } finally {
      setIsSendingCode(false);
    }
  }, []);

  // 手机号登录
  const phoneLogin = useCallback(
    async (phone: string, code: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);
      try {
        const resp = await invoke<LoginResponse>('phone_login', { phone, code });
        setAuth(resp.user, resp.token, resp.llm_token);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [setAuth]
  );

  // 密码登录
  const passwordLogin = useCallback(
    async (username: string, password: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);
      try {
        const resp = await invoke<LoginResponse>('password_login', { username, password });
        setAuth(resp.user, resp.token, resp.llm_token);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [setAuth]
  );

  // 登出
  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await invoke('logout');
      storeLogout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [storeLogout]);

  return {
    user,
    isAuthenticated,
    isLoading,
    isSendingCode,
    error,
    sendCode,
    phoneLogin,
    passwordLogin,
    logout,
    clearError: () => setError(null),
  };
}

export default useAuth;

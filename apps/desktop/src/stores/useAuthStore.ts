/**
 * 认证状态管理
 * @author Ysf
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface User {
  id: string;
  username: string;
  nickname: string;
  phone?: string;
  email?: string;
  avatar?: string;
  is_new_user: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null; // access_token
  refreshToken: string | null; // refresh_token
  expiresAt: number | null; // access_token expire time (timestamp)
  isAuthenticated: boolean;

  // Actions
  setAuth: (
    user: User,
    token: string,
    refreshToken: string,
    expiresAt: number,
  ) => void;
  setToken: (token: string, expiresAt: number) => void;
  updateUser: (user: User) => void;
  logout: () => void;
  getToken: () => string | null;
  getRefreshToken: () => string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      expiresAt: null,
      isAuthenticated: false,

      setAuth: (user, token, refreshToken, expiresAt) =>
        set({
          user,
          token,
          refreshToken,
          expiresAt,
          isAuthenticated: true,
        }),

      setToken: (token, expiresAt) =>
        set({
          token,
          expiresAt,
        }),

      updateUser: (user) =>
        set((state) => ({
          user: { ...state.user, ...user },
        })),

      logout: () =>
        set({
          user: null,
          token: null,
          refreshToken: null,
          expiresAt: null,
          isAuthenticated: false,
        }),

      getToken: () => get().token,
      getRefreshToken: () => get().refreshToken,
    }),
    {
      name: "ai-creator-auth-storage",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

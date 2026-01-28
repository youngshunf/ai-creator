/**
 * 认证 Hook
 * @author Ysf
 */
import { useState, useCallback } from "react";
import { useAuthStore } from "@/stores/useAuthStore";
import {
  loginApi,
  logoutApi,
  sendVerificationCodeApi,
  type LoginResult,
} from "@/api/auth";

export function useAuth() {
  const {
    user,
    isAuthenticated,
    setAuth,
    logout: storeLogout,
  } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 发送验证码
  const sendCode = useCallback(async (phone: string): Promise<boolean> => {
    setIsSendingCode(true);
    setError(null);
    try {
      await sendVerificationCodeApi(phone);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return false;
    } finally {
      setIsSendingCode(false);
    }
  }, []);

  // 处理登录成功逻辑
  const handleLoginSuccess = useCallback(
    async (resp: LoginResult) => {
      // 后端目前有两种返回：
      // - /auth/login: user.{ id: number, uuid: string, ... }
      // - /auth/phone-login: user.{ uuid: string, ... }
      // 这里统一使用 uuid 作为前端 user.uuid，保证与云端 user_id 一致
      const rawUser: any = resp.user as any;
      const effectiveUserUuid: string =
        (rawUser.uuid as string) ?? String(rawUser.id ?? "");

      const normalizedUser = {
        uuid: effectiveUserUuid,
        username: rawUser.username as string,
        nickname: rawUser.nickname as string,
        phone: rawUser.phone as string | undefined,
        email: rawUser.email as string | undefined,
        avatar: rawUser.avatar as string | undefined,
        is_new_user: Boolean(rawUser.is_new_user),
      };

      const expiresAt = new Date(resp.access_token_expire_time).getTime();
      setAuth(normalizedUser, resp.access_token, resp.refresh_token, expiresAt);

      // 同步用户信息到本地 SQLite（以 UUID 作为主键）
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("sync_user_to_local", {
          user_id: effectiveUserUuid,
          email: normalizedUser.email || null,
          username: normalizedUser.username || null,
          nickname: normalizedUser.nickname || null,
          avatar: normalizedUser.avatar || null,
        });
        console.log("[Auth] User synced to local database");
      } catch (err) {
        console.warn("[Auth] Failed to sync user to local:", err);
      }

      // 同步 Token 到 Sidecar (用于 LLM 调用)
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("sync_auth_tokens", {
          request: {
            api_token: resp.llm_token || null,
            access_token: resp.access_token,
            access_token_expire_time: resp.access_token_expire_time,
            refresh_token: resp.refresh_token,
            refresh_token_expire_time: resp.refresh_token_expire_time,
          },
        });
        console.log("[Auth] Tokens synced to sidecar");
      } catch (err) {
        console.warn("[Auth] Failed to sync tokens to sidecar:", err);
      }

      // 登录后启动云端同步（项目 & 平台账号）
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("start_sync", {
          userId: effectiveUserUuid,
          token: resp.access_token,
        });
        console.log("[Auth] Background sync started");
      } catch (err) {
        console.warn("[Auth] Failed to start sync engine:", err);
      }
    },
    [setAuth],
  );

  // 手机号登录
  const phoneLogin = useCallback(
    async (phone: string, code: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);
      try {
        const resp = await loginApi({ phone, code });
        handleLoginSuccess(resp);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [handleLoginSuccess],
  );

  // 密码登录
  const passwordLogin = useCallback(
    async (username: string, password: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);
      try {
        const resp = await loginApi({ username, password });
        handleLoginSuccess(resp);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [handleLoginSuccess],
  );

  // 登出
  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await logoutApi();
      storeLogout();
    } catch (err) {
      console.error("Logout error:", err);
      // 即使 API 失败也清除本地状态
      storeLogout();
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

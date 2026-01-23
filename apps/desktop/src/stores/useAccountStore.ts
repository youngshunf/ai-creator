/**
 * 账号管理 Store
 * @author Ysf
 */
import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";
import { syncAccountToCloudApi } from "@/api/account";
import { useProjectStore } from "@/stores/useProjectStore";
import { useAuthStore } from "@/stores/useAuthStore";

export type Platform = "xiaohongshu" | "wechat" | "douyin";

export interface PlatformAccount {
  id: string;
  user_id: string;
  project_id: string;
  platform: Platform;
  account_id: string;
  account_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  session_valid: boolean;
  followers_count: number;
  following_count: number;
  posts_count: number;
  likes_count: number;
  created_at: number;
  updated_at: number;
  last_profile_sync_at: number | null;
}

export interface PlatformInfo {
  name: string;
  display_name: string;
  login_url: string;
  spec: {
    title_max_length: number;
    content_max_length: number;
    image_max_count: number;
  };
}

interface AccountState {
  accounts: PlatformAccount[];
  platforms: PlatformInfo[];
  loading: boolean;
  syncingIds: string[];
  error: string | null;

  fetchAccounts: (projectId: string, retryCount?: number) => Promise<void>;
  fetchPlatforms: () => Promise<void>;
  addAccount: (
    projectId: string,
    platform: Platform,
    accountId: string,
    accountName?: string,
    profile?: { avatar_url?: string; followers_count?: number },
  ) => Promise<PlatformAccount>;
  deleteAccount: (id: string) => Promise<void>;
  startLogin: (
    platform: Platform,
  ) => Promise<{ login_url: string; message: string }>;
  syncAccount: (id: string) => Promise<void>;
}

export const useAccountStore = create<AccountState>((set, get) => ({
  accounts: [],
  platforms: [],
  loading: false,
  syncingIds: [],
  error: null,

  fetchAccounts: async (projectId: string, retryCount = 0) => {
    set({ loading: true, error: null });
    try {
      const accounts = await invoke<PlatformAccount[]>("db_list_accounts", {
        projectId,
      });
      set({ accounts, loading: false });
    } catch (e) {
      const errorMsg = String(e);
      // 如果是数据库未初始化错误，重试（最多 10 次，每次 1 秒）
      if (
        (errorMsg.includes("数据库未初始化") ||
          errorMsg.includes("Database not initialized")) &&
        retryCount < 10
      ) {
        console.warn(
          `[AccountStore] Database not ready, retrying... (${retryCount + 1}/10)`,
        );
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return get().fetchAccounts(projectId, retryCount + 1);
      }
      set({ error: errorMsg, loading: false });
    }
  },

  fetchPlatforms: async () => {
    try {
      // 静态平台列表，后续可从 sidecar 获取
      const platforms: PlatformInfo[] = [
        {
          name: "xiaohongshu",
          display_name: "小红书",
          login_url: "https://www.xiaohongshu.com/login",
          spec: {
            title_max_length: 20,
            content_max_length: 1000,
            image_max_count: 9,
          },
        },
        {
          name: "wechat",
          display_name: "微信公众号",
          login_url: "https://mp.weixin.qq.com/",
          spec: {
            title_max_length: 64,
            content_max_length: 20000,
            image_max_count: 20,
          },
        },
        {
          name: "douyin",
          display_name: "抖音",
          login_url: "https://creator.douyin.com/",
          spec: {
            title_max_length: 55,
            content_max_length: 2200,
            image_max_count: 35,
          },
        },
      ];
      set({ platforms });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  addAccount: async (projectId, platform, accountId, accountName, profile) => {
    set({ loading: true, error: null });
    // 模拟网络延迟（可选，为了更好的 UI 体验）
    await new Promise((r) => setTimeout(r, 50));
    try {
      const authUser = useAuthStore.getState().user;
      const effectiveUserId = authUser?.id
        ? String(authUser.id)
        : "current-user";
      const account = await invoke<PlatformAccount>("db_create_account", {
        userId: effectiveUserId,
        projectId,
        platform,
        accountId,
        accountName,
      });
      const enrichedAccount = {
        ...account,
        avatar_url: profile?.avatar_url || account.avatar_url,
        followers_count: profile?.followers_count ?? account.followers_count,
      };

      // 同步到云端 (异步，不阻塞 UI)
      (async () => {
        try {
          // 使用传入的 projectId (应该是 string)
          await syncAccountToCloudApi(projectId, {
            project_id: projectId,
            platform,
            account_id: accountId,
            account_name: accountName || undefined,
            avatar_url: profile?.avatar_url || undefined,
            followers_count: profile?.followers_count,
          });
          console.log("[addAccount] 已同步到云端");
        } catch (cloudErr) {
          console.error("[addAccount] 同步到云端失败 (可能是离线):", cloudErr);
        }
      })();

      set((state) => ({
        accounts: [...state.accounts, enrichedAccount],
        loading: false,
      }));
      return enrichedAccount;
    } catch (e) {
      set({ error: String(e), loading: false });
      throw e;
    }
  },

  deleteAccount: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await invoke("db_delete_account", { id });
      set((state) => ({
        accounts: state.accounts.filter((a) => a.id !== id),
        loading: false,
      }));
    } catch (e) {
      console.error("[deleteAccount] 删除失败:", e);
      set({ error: String(e), loading: false });
    }
  },

  startLogin: async (platform: Platform) => {
    // 调用 sidecar 启动浏览器登录
    const platformInfo = get().platforms.find((p) => p.name === platform);
    return {
      login_url: platformInfo?.login_url || "",
      message: `请在浏览器中完成 ${platformInfo?.display_name || platform} 登录`,
    };
  },

  syncAccount: async (id: string) => {
    console.log("[syncAccount] 被调用, id:", id);
    const { syncingIds } = get();
    if (syncingIds.includes(id)) return;

    set({ syncingIds: [...syncingIds, id] });

    // 让浏览器有机会渲染 loading 状态
    await new Promise((resolve) => setTimeout(resolve, 50));

    try {
      const account = get().accounts.find((a) => a.id === id);
      if (!account) throw new Error("Account not found");

      console.log(
        "[syncAccount] 开始同步:",
        account.platform,
        account.account_id,
      );
      const result = await invoke<{
        success: boolean;
        profile?: Record<string, unknown>;
        error?: string;
      }>("sync_account", {
        platform: account.platform,
        accountId: account.account_id,
      });
      console.log("[syncAccount] 同步结果:", result);

      if (result.success && result.profile) {
        // 映射后端字段到前端字段（兼容 Stagehand / Playwright 两种格式）
        const profile = result.profile;

        const nickname =
          (profile.nickname as string) || account.account_name || null;
        const avatarUrl =
          (profile.avatar_url as string) || account.avatar_url || null;

        const rawFollowers =
          (profile.followers_count as number | undefined) ??
          (profile.followers as number | undefined);
        const rawFollowing =
          (profile.following_count as number | undefined) ??
          (profile.following as number | undefined);
        const rawPosts =
          (profile.posts_count as number | undefined) ??
          (profile.posts as number | undefined);
        const rawLikes =
          (profile.likes_count as number | undefined) ??
          (profile.likes as number | undefined);
        const rawFavorites =
          (profile.favorites_count as number | undefined) ??
          (profile.favorites as number | undefined) ??
          (profile.collects as number | undefined);

        const followers_count =
          typeof rawFollowers === "number"
            ? rawFollowers
            : account.followers_count;
        const following_count =
          typeof rawFollowing === "number"
            ? rawFollowing
            : account.following_count;
        const posts_count =
          typeof rawPosts === "number" ? rawPosts : account.posts_count;

        const extraStats: Record<string, unknown> = {};
        if (typeof rawLikes === "number") extraStats.likes_count = rawLikes;
        if (typeof rawFavorites === "number")
          extraStats.favorites_count = rawFavorites;
        const metadataJson =
          Object.keys(extraStats).length > 0
            ? JSON.stringify(extraStats)
            : null;

        const updatedAccount = {
          account_name: nickname,
          avatar_url: avatarUrl,
          followers_count,
          following_count,
          posts_count,
          likes_count:
            typeof rawLikes === "number" ? rawLikes : account.likes_count || 0,
        };

        // 保存到本地数据库（包括作品数和扩展统计）
        try {
          await invoke("db_update_account_profile", {
            id,
            accountName: updatedAccount.account_name,
            avatarUrl: updatedAccount.avatar_url,
            followersCount: updatedAccount.followers_count,
            followingCount: updatedAccount.following_count,
            postsCount: updatedAccount.posts_count,
            metadata: metadataJson,
          });
          console.log("[syncAccount] 已保存到本地数据库");
        } catch (dbErr) {
          console.error("[syncAccount] 保存到本地数据库失败:", dbErr);
        }

        // 同步到云端
        try {
          const currentProject = useProjectStore.getState().currentProject;
          if (currentProject?.id) {
            await syncAccountToCloudApi(currentProject.id, {
              project_id: currentProject.id,
              platform: account.platform,
              account_id: account.account_id,
              account_name: updatedAccount.account_name || undefined,
              avatar_url: updatedAccount.avatar_url || undefined,
              followers_count: updatedAccount.followers_count,
              following_count: updatedAccount.following_count,
            });
            console.log("[syncAccount] 已同步到云端");
          }
        } catch (cloudErr) {
          console.error("[syncAccount] 同步到云端失败:", cloudErr);
        }

        // 更新前端状态
        set((state) => ({
          accounts: state.accounts.map((a) =>
            a.id === id
              ? {
                  ...a,
                  ...updatedAccount,
                  last_profile_sync_at: Math.floor(Date.now() / 1000),
                }
              : a,
          ),
        }));
      }
    } catch (e) {
      console.error("[syncAccount] 同步失败:", e);
    } finally {
      set((state) => ({
        syncingIds: state.syncingIds.filter((i) => i !== id),
      }));
    }
  },
}));

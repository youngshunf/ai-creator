/**
 * 账号管理 Store
 * @author Ysf
 */
import { create } from 'zustand';
import { invoke } from '@tauri-apps/api/core';
import { syncAccountToCloudApi } from '@/api/account';
import { useProjectStore } from '@/stores/useProjectStore';

export type Platform = 'xiaohongshu' | 'wechat' | 'douyin';

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

  fetchAccounts: (projectId: string) => Promise<void>;
  fetchPlatforms: () => Promise<void>;
  addAccount: (projectId: string, platform: Platform, accountId: string, accountName?: string, profile?: { avatar_url?: string; followers_count?: number }) => Promise<PlatformAccount>;
  deleteAccount: (id: string) => Promise<void>;
  startLogin: (platform: Platform) => Promise<{ login_url: string; message: string }>;
  syncAccount: (id: string) => Promise<void>;
}

export const useAccountStore = create<AccountState>((set, get) => ({
  accounts: [],
  platforms: [],
  loading: false,
  syncingIds: [],
  error: null,

  fetchAccounts: async (projectId: string) => {
    set({ loading: true, error: null });
    try {
      const accounts = await invoke<PlatformAccount[]>('db_list_accounts', { projectId });
      set({ accounts, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  fetchPlatforms: async () => {
    try {
      // 静态平台列表，后续可从 sidecar 获取
      const platforms: PlatformInfo[] = [
        { name: 'xiaohongshu', display_name: '小红书', login_url: 'https://www.xiaohongshu.com/login', spec: { title_max_length: 20, content_max_length: 1000, image_max_count: 9 } },
        { name: 'wechat', display_name: '微信公众号', login_url: 'https://mp.weixin.qq.com/', spec: { title_max_length: 64, content_max_length: 20000, image_max_count: 20 } },
        { name: 'douyin', display_name: '抖音', login_url: 'https://creator.douyin.com/', spec: { title_max_length: 55, content_max_length: 2200, image_max_count: 35 } },
      ];
      set({ platforms });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  addAccount: async (projectId, platform, accountId, accountName, profile) => {
    set({ loading: true, error: null });
    await new Promise((r) => setTimeout(r, 50));
    try {
      const userId = 'current-user';
      const account = await invoke<PlatformAccount>('db_create_account', {
        userId,
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

      // 同步到云端
      try {
        const currentProject = useProjectStore.getState().currentProject;
        if (currentProject?.id) {
          await syncAccountToCloudApi(Number(currentProject.id), {
            project_id: Number(currentProject.id),
            platform,
            account_id: accountId,
            account_name: accountName || undefined,
            avatar_url: profile?.avatar_url || undefined,
            followers_count: profile?.followers_count,
          });
          console.log('[addAccount] 已同步到云端');
        }
      } catch (cloudErr) {
        console.error('[addAccount] 同步到云端失败:', cloudErr);
      }

      set((state) => ({ accounts: [...state.accounts, enrichedAccount], loading: false }));
      return enrichedAccount;
    } catch (e) {
      set({ error: String(e), loading: false });
      throw e;
    }
  },

  deleteAccount: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await invoke('db_delete_account', { id });
      set((state) => ({
        accounts: state.accounts.filter((a) => a.id !== id),
        loading: false,
      }));
    } catch (e) {
      console.error('[deleteAccount] 删除失败:', e);
      set({ error: String(e), loading: false });
    }
  },

  startLogin: async (platform: Platform) => {
    // TODO: 调用 sidecar 启动浏览器登录
    const platformInfo = get().platforms.find((p) => p.name === platform);
    return {
      login_url: platformInfo?.login_url || '',
      message: `请在浏览器中完成 ${platformInfo?.display_name || platform} 登录`,
    };
  },

  syncAccount: async (id: string) => {
    console.log('[syncAccount] 被调用, id:', id);
    const { syncingIds } = get();
    if (syncingIds.includes(id)) return;

    set({ syncingIds: [...syncingIds, id] });

    // 让浏览器有机会渲染 loading 状态
    await new Promise(resolve => setTimeout(resolve, 50));

    try {
      const account = get().accounts.find((a) => a.id === id);
      if (!account) throw new Error('Account not found');

      console.log('[syncAccount] 开始同步:', account.platform, account.account_id);
      const result = await invoke<{ success: boolean; profile?: Record<string, unknown>; error?: string }>('sync_account', {
        platform: account.platform,
        accountId: account.account_id,
      });
      console.log('[syncAccount] 同步结果:', result);

      if (result.success && result.profile) {
        // 映射后端字段到前端字段
        const profile = result.profile;
        const updatedAccount = {
          account_name: (profile.nickname as string) || account.account_name,
          avatar_url: (profile.avatar_url as string) || account.avatar_url,
          followers_count: (profile.followers_count as number) ?? account.followers_count,
          following_count: (profile.following_count as number) ?? account.following_count,
        };

        // 保存到本地数据库
        try {
          await invoke('db_update_account_profile', {
            id,
            accountName: updatedAccount.account_name,
            avatarUrl: updatedAccount.avatar_url,
            followersCount: updatedAccount.followers_count,
            followingCount: updatedAccount.following_count,
          });
          console.log('[syncAccount] 已保存到本地数据库');
        } catch (dbErr) {
          console.error('[syncAccount] 保存到本地数据库失败:', dbErr);
        }

        // 同步到云端
        try {
          const currentProject = useProjectStore.getState().currentProject;
          if (currentProject?.id) {
            await syncAccountToCloudApi(Number(currentProject.id), {
              project_id: Number(currentProject.id),
              platform: account.platform,
              account_id: account.account_id,
              account_name: updatedAccount.account_name || undefined,
              avatar_url: updatedAccount.avatar_url || undefined,
              followers_count: updatedAccount.followers_count,
              following_count: updatedAccount.following_count,
            });
            console.log('[syncAccount] 已同步到云端');
          }
        } catch (cloudErr) {
          console.error('[syncAccount] 同步到云端失败:', cloudErr);
        }

        // 更新前端状态
        set((state) => ({
          accounts: state.accounts.map((a) =>
            a.id === id ? {
              ...a,
              ...updatedAccount,
              last_profile_sync_at: Math.floor(Date.now() / 1000),
            } : a
          ),
        }));
      }
    } catch (e) {
      console.error('[syncAccount] 同步失败:', e);
    } finally {
      set((state) => ({
        syncingIds: state.syncingIds.filter((i) => i !== id),
      }));
    }
  },
}));

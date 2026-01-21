/**
 * 账号卡片组件
 * @author Ysf
 */
import {
  MoreHorizontal,
  RefreshCw,
  ExternalLink,
  Trash2,
  ThumbsUp,
  Users,
  Heart,
  Image as ImageIcon,
} from "lucide-react";
import { PlatformAccount } from "@/stores/useAccountStore";
import { useState, useEffect } from "react";
import { flushSync } from "react-dom";
import { invoke } from "@tauri-apps/api/core";

interface AccountCardProps {
  account: PlatformAccount;
  syncing?: boolean;
  onSync?: () => void;
  onDelete?: (id: string) => void;
}

const platformConfig: Record<
  string,
  { bg: string; text: string; name: string; url: string }
> = {
  xiaohongshu: {
    bg: "bg-red-500",
    text: "书",
    name: "小红书",
    url: "https://www.xiaohongshu.com/user/profile/",
  },
  wechat: {
    bg: "bg-green-500",
    text: "微",
    name: "微信公众号",
    url: "https://mp.weixin.qq.com/",
  },
  douyin: {
    bg: "bg-black",
    text: "抖",
    name: "抖音",
    url: "https://www.douyin.com/user/",
  },
};

export function AccountCard({
  account,
  syncing,
  onSync,
  onDelete,
}: AccountCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [localSyncing, setLocalSyncing] = useState(false);

  useEffect(() => {
    if (!syncing) setLocalSyncing(false);
  }, [syncing]);

  const isSyncing = syncing || localSyncing;
  const config = platformConfig[account.platform] || {
    bg: "bg-slate-500",
    text: "?",
    name: account.platform,
    url: "",
  };

  const formatCount = (count: number | null) => {
    if (count == null) return "-";
    if (count >= 10000) return `${(count / 10000).toFixed(1)}w`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
    return count.toString();
  };

  const formatSyncTime = (timestamp: number | null) => {
    if (!timestamp) return "从未同步";
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return "刚刚";
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString("zh-CN");
  };

  const handleVisit = async () => {
    try {
      await invoke("open_session_browser", {
        platform: account.platform,
        accountId: account.id,
      });
    } catch (e) {
      console.error("Failed to open session browser:", e);
    }
  };

  return (
    <div className="group bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm hover:shadow-md transition-all border border-slate-100 dark:border-slate-700/50 hover:border-slate-200 dark:hover:border-slate-600">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full overflow-hidden relative border border-slate-100 dark:border-slate-600 shadow-sm shrink-0">
            {account.avatar_url ? (
              <img
                src={account.avatar_url}
                alt={account.account_name || ""}
                className="w-full h-full object-cover"
              />
            ) : (
              <div
                className={`w-full h-full ${config.bg} flex items-center justify-center text-white font-bold text-sm`}
              >
                {config.text}
              </div>
            )}
          </div>
          <div className="min-w-0">
            <h3 className="font-bold text-slate-900 dark:text-white truncate text-sm">
              {account.account_name || `${config.name}账号`}
            </h3>
            <div className="flex items-center mt-0.5 space-x-2">
              <span className="text-xs text-slate-400 dark:text-slate-500 truncate">
                {config.name}
              </span>
              <div className="flex items-center">
                <span
                  className={`w-1.5 h-1.5 rounded-full mr-1 ${account.session_valid ? "bg-green-500" : "bg-yellow-500"}`}
                />
                <span
                  className={`text-[10px] ${account.session_valid ? "text-green-600 dark:text-green-400" : "text-yellow-600 dark:text-yellow-400"}`}
                >
                  {account.session_valid ? "已授权" : "需授权"}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="relative shrink-0">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-white/5 rounded-lg transition-colors"
          >
            <MoreHorizontal className="w-4 h-4" />
          </button>
          {showMenu && (
            <div className="absolute right-0 top-8 bg-white dark:bg-slate-700 rounded-lg shadow-lg border border-slate-200 dark:border-slate-600 py-1 z-10 w-24">
              <button
                onClick={() => {
                  onDelete?.(account.id);
                  setShowMenu(false);
                }}
                className="flex items-center gap-2 px-3 py-2 text-xs text-red-500 hover:bg-slate-50 dark:hover:bg-slate-600 w-full"
              >
                <Trash2 className="w-3.5 h-3.5" /> 删除
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 mb-4">
        <div className="text-center">
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mb-0.5 flex items-center justify-center gap-0.5">
            <Users className="w-3 h-3" /> 粉丝
          </div>
          <div className="font-bold text-slate-900 dark:text-white text-sm">
            {formatCount(account.followers_count)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mb-0.5 flex items-center justify-center gap-0.5">
            <ThumbsUp className="w-3 h-3" /> 点赞
          </div>
          <div className="font-bold text-slate-900 dark:text-white text-sm">
            {formatCount(account.likes_count)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mb-0.5 flex items-center justify-center gap-0.5">
            <ImageIcon className="w-3 h-3" /> 作品
          </div>
          <div className="font-bold text-slate-900 dark:text-white text-sm">
            {formatCount(account.posts_count)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-[10px] text-slate-400 dark:text-slate-500 mb-0.5 flex items-center justify-center gap-0.5">
            <Heart className="w-3 h-3" /> 关注
          </div>
          <div className="font-bold text-slate-900 dark:text-white text-sm">
            {formatCount(account.following_count)}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-slate-50 dark:border-slate-700/30">
        <span className="text-[10px] text-slate-400 dark:text-slate-500">
          {isSyncing
            ? "同步中..."
            : `同步于 ${formatSyncTime(account.last_profile_sync_at)}`}
        </span>

        <div className="flex items-center gap-2">
          {account.session_valid ? (
            <>
              <button
                onClick={handleVisit}
                className="p-1.5 text-slate-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-md transition-colors"
                title="访问主页"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  console.log("[AccountCard] 同步按钮点击");
                  flushSync(() => setLocalSyncing(true));
                  onSync?.();
                }}
                disabled={isSyncing}
                className={`p-1.5 text-slate-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-md transition-colors ${isSyncing ? "animate-spin text-primary-500" : ""}`}
                title="同步数据"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </>
          ) : (
            <button className="px-2 py-1 text-[10px] font-medium text-white bg-red-500 hover:bg-red-600 rounded transition-colors shadow-sm">
              重新授权
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

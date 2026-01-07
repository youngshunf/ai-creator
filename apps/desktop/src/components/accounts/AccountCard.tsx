/**
 * 账号卡片组件
 * @author Ysf
 */
import { MoreHorizontal, RefreshCw, ExternalLink, Trash2 } from 'lucide-react';
import { PlatformAccount } from '@/stores/useAccountStore';
import { useState, useEffect } from 'react';
import { flushSync } from 'react-dom';

interface AccountCardProps {
  account: PlatformAccount;
  syncing?: boolean;
  onSync?: () => void;
  onDelete?: (id: string) => void;
}

const platformConfig: Record<string, { bg: string; text: string; name: string }> = {
  xiaohongshu: { bg: 'bg-red-500', text: '书', name: '小红书' },
  wechat: { bg: 'bg-green-500', text: '微', name: '微信公众号' },
  douyin: { bg: 'bg-black', text: '抖', name: '抖音' },
};

export function AccountCard({ account, syncing, onSync, onDelete }: AccountCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [localSyncing, setLocalSyncing] = useState(false);

  useEffect(() => {
    if (!syncing) setLocalSyncing(false);
  }, [syncing]);

  const isSyncing = syncing || localSyncing;
  console.log('[AccountCard] render, localSyncing:', localSyncing, 'syncing:', syncing, 'isSyncing:', isSyncing);
  const config = platformConfig[account.platform] || { bg: 'bg-slate-500', text: '?', name: account.platform };

  const formatCount = (count: number | null) => {
    if (count == null) return '-';
    if (count >= 10000) return `${(count / 10000).toFixed(1)}w`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
    return count.toString();
  };

  const formatSyncTime = (timestamp: number | null) => {
    if (!timestamp) return '从未同步';
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <div className="group bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-soft hover:shadow-soft-lg transition-all border border-transparent hover:border-slate-200 dark:hover:border-slate-700">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-full overflow-hidden relative border-2 border-white dark:border-slate-600 shadow-sm">
            {account.avatar_url ? (
              <img src={account.avatar_url} alt={account.account_name || ''} className="w-full h-full object-cover" />
            ) : (
              <div className={`w-full h-full ${config.bg} flex items-center justify-center text-white font-bold`}>
                {config.text}
              </div>
            )}
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white">{account.account_name || `${config.name}账号`}</h3>
            <div className="flex items-center mt-0.5">
              <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${account.session_valid ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {account.session_valid ? '授权正常' : '需重新授权'}
              </span>
            </div>
          </div>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-white/5 rounded-lg transition-colors"
          >
            <MoreHorizontal className="w-5 h-5" />
          </button>
          {showMenu && (
            <div className="absolute right-0 top-8 bg-white dark:bg-slate-700 rounded-lg shadow-lg border border-slate-200 dark:border-slate-600 py-1 z-10">
              <button
                onClick={() => { onDelete?.(account.id); setShowMenu(false); }}
                className="flex items-center gap-2 px-4 py-2 text-sm text-red-500 hover:bg-slate-50 dark:hover:bg-slate-600 w-full"
              >
                <Trash2 className="w-4 h-4" /> 删除
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-white/5">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">粉丝</div>
          <div className="font-bold text-slate-900 dark:text-white">{formatCount(account.followers_count)}</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-white/5">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">关注</div>
          <div className="font-bold text-slate-900 dark:text-white">{formatCount(account.following_count)}</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-slate-50 dark:bg-white/5">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">作品</div>
          <div className="font-bold text-slate-900 dark:text-white">{formatCount(account.posts_count)}</div>
        </div>
      </div>

      <div className="text-xs text-slate-400 dark:text-slate-500 mb-3 flex justify-between">
        <span>添加于 {new Date(account.created_at * 1000).toLocaleDateString('zh-CN')}</span>
        <span>同步于 {formatSyncTime(account.last_profile_sync_at)}</span>
      </div>

      <div className="flex items-center gap-2 pt-4 border-t border-slate-100 dark:border-slate-700/50">
        {account.session_valid ? (
          <>
            <button
              onClick={() => { console.log('[AccountCard] 同步按钮点击'); flushSync(() => setLocalSyncing(true)); onSync?.(); }}
              disabled={isSyncing}
              className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} /> {isSyncing ? '同步中...' : '同步'}
            </button>
            <button className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition-colors">
              <ExternalLink className="w-4 h-4 mr-2" /> 访问
            </button>
          </>
        ) : (
          <button className="flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors shadow-lg shadow-red-500/20">
            重新授权
          </button>
        )}
      </div>
    </div>
  );
}

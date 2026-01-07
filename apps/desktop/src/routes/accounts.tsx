/**
 * 账号管理页面路由
 * @author Ysf
 */
import { createFileRoute } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { useAccountStore, Platform } from '@/stores/useAccountStore';
import { useProjectStore } from '@/stores/useProjectStore';
import { AccountCard } from '@/components/accounts/AccountCard';
import { AddAccountDialog } from '@/components/accounts/AddAccountDialog';

export const Route = createFileRoute('/accounts')({
  component: AccountsPage,
});

function AccountsPage() {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const { accounts, platforms, loading, syncingIds, fetchAccounts, fetchPlatforms, deleteAccount, syncAccount } = useAccountStore();
  const { currentProject } = useProjectStore();
  const currentProjectId = currentProject?.id;

  useEffect(() => {
    fetchPlatforms();
    if (currentProjectId) {
      fetchAccounts(String(currentProjectId));
    }
  }, [currentProjectId, fetchAccounts, fetchPlatforms]);

  // 按平台分组账号
  const groupedAccounts = accounts.reduce((acc, account) => {
    if (!acc[account.platform]) acc[account.platform] = [];
    acc[account.platform].push(account);
    return acc;
  }, {} as Record<string, typeof accounts>);

  const platformConfig: Record<string, { bg: string; text: string; name: string }> = {
    xiaohongshu: { bg: 'bg-red-500', text: '书', name: '小红书' },
    wechat: { bg: 'bg-green-500', text: '微', name: '微信公众号' },
    douyin: { bg: 'bg-black', text: '抖', name: '抖音' },
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">平台账号管理</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">管理你的自媒体平台账号授权与同步设置</p>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-primary-600/20"
        >
          <Plus className="w-5 h-5 mr-2" />
          添加账号
        </button>
      </div>

      {/* 账号列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-500">加载中...</div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-slate-500 dark:text-slate-400 mb-4">还没有绑定任何账号</p>
          <button
            onClick={() => setShowAddDialog(true)}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium"
          >
            添加第一个账号
          </button>
        </div>
      ) : (
        Object.entries(groupedAccounts).map(([platform, platformAccounts]) => {
          const config = platformConfig[platform] || { bg: 'bg-slate-500', text: '?', name: platform };
          return (
            <section key={platform}>
              <div className="flex items-center space-x-3 mb-4">
                <div className={`w-8 h-8 rounded-full ${config.bg} flex items-center justify-center font-bold text-white text-xs shadow-md`}>
                  {config.text}
                </div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">{config.name}</h2>
                <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-white/10 text-xs font-medium text-slate-500 dark:text-slate-400">
                  {platformAccounts.length}个账号
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {platformAccounts.map((account) => (
                  <AccountCard
                    key={account.id}
                    account={account}
                    syncing={syncingIds.includes(account.id)}
                    onSync={() => syncAccount(account.id)}
                    onDelete={(id) => deleteAccount(id)}
                  />
                ))}
              </div>
            </section>
          );
        })
      )}

      {/* 添加账号对话框 */}
      <AddAccountDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        projectId={currentProjectId ? String(currentProjectId) : ''}
      />
    </div>
  );
}

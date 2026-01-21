/**
 * 账号管理页面路由
 * @author Ysf
 */
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { Plus, FolderPlus, AlertCircle } from 'lucide-react';
import { useAccountStore, Platform } from '@/stores/useAccountStore';
import { useProjectStore } from '@/stores/useProjectStore';
import { AccountCard } from '@/components/accounts/AccountCard';
import { AddAccountDialog } from '@/components/accounts/AddAccountDialog';

export const Route = createFileRoute('/accounts')({
  component: AccountsPage,
});

function AccountsPage() {
  const navigate = useNavigate();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showNoProjectWarning, setShowNoProjectWarning] = useState(false);
  const { accounts, platforms, loading, syncingIds, fetchAccounts, fetchPlatforms, deleteAccount, syncAccount } = useAccountStore();
  const { currentProject, projects, fetchProjects, isLoading: projectsLoading } = useProjectStore();
  const currentProjectId = currentProject?.id;

  // 检查是否有可用项目
  const hasProject = !!currentProject && !!currentProjectId;

  // 处理添加账号点击
  const handleAddAccountClick = () => {
    if (!hasProject) {
      setShowNoProjectWarning(true);
      return;
    }
    setShowAddDialog(true);
  };

  useEffect(() => {
    fetchPlatforms();
    fetchProjects();
  }, [fetchPlatforms, fetchProjects]);

  useEffect(() => {
    if (currentProjectId) {
      fetchAccounts(String(currentProjectId));
    }
  }, [currentProjectId, fetchAccounts]);

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
      {/* 无项目警告提示 */}
      {showNoProjectWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowNoProjectWarning(false)} />
          <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">请先创建项目</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">添加账号前需要先创建一个项目</p>
              </div>
            </div>
            <p className="text-slate-600 dark:text-slate-300 mb-6">
              项目是组织账号和内容的基础单元。创建项目后，您可以在项目下添加多个平台账号进行统一管理。
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowNoProjectWarning(false)}
                className="flex-1 px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => {
                  setShowNoProjectWarning(false);
                  navigate({ to: '/project/create' });
                }}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors"
              >
                <FolderPlus className="w-4 h-4" />
                创建项目
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">平台账号管理</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {hasProject 
              ? `当前项目：${currentProject.name}` 
              : '管理你的自媒体平台账号授权与同步设置'}
          </p>
        </div>
        <button
          onClick={handleAddAccountClick}
          className="flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-primary-600/20"
        >
          <Plus className="w-5 h-5 mr-2" />
          添加账号
        </button>
      </div>

      {/* 无项目空状态 */}
      {!hasProject && !projectsLoading && (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
            <FolderPlus className="w-10 h-10 text-slate-400" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">请先创建项目</h3>
          <p className="text-slate-500 dark:text-slate-400 mb-6 max-w-md mx-auto">
            项目是管理账号的基础。创建项目后，您可以在项目下添加多个平台账号，实现内容的统一管理和发布。
          </p>
          <button
            onClick={() => navigate({ to: '/project/create' })}
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-primary-600/20"
          >
            <FolderPlus className="w-5 h-5" />
            创建第一个项目
          </button>
        </div>
      )}

      {/* 账号列表 - 只在有项目时显示 */}
      {hasProject && (loading ? (
        <div className="text-center py-12 text-slate-500">加载中...</div>
      ) : accounts.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-slate-500 dark:text-slate-400 mb-4">当前项目还没有绑定任何账号</p>
          <button
            onClick={handleAddAccountClick}
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
      ))}

      {/* 添加账号对话框 */}
      <AddAccountDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        projectId={currentProjectId ? String(currentProjectId) : ''}
      />
    </div>
  );
}

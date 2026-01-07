/**
 * 发布中心主组件
 * @author Ysf
 */
import { useState, useEffect } from 'react';
import { Send, Clock, History } from 'lucide-react';
import { PlatformCard, PlatformInfo } from './PlatformCard';
import { ContentAdapter } from './ContentAdapter';
import { PreviewPanel } from './PreviewPanel';
import { ScheduleForm } from './ScheduleForm';
import { PublishQueue } from './PublishQueue';
import { useDraftStore } from '@/stores/useDraftStore';
import { useAccountStore } from '@/stores/useAccountStore';
import { usePublishStore } from '@/stores/usePublishStore';
import { useProjectStore } from '@/stores/useProjectStore';
import { cn } from '@/lib/utils';

// 平台图标和颜色映射
const PLATFORM_META: Record<string, { icon: string; color: string }> = {
  xiaohongshu: { icon: '📕', color: '#FF2442' },
  wechat: { icon: '💬', color: '#07C160' },
  douyin: { icon: '🎵', color: '#000000' },
};

type TabType = 'publish' | 'schedule' | 'history';

export function PublishCenter() {
  const [activeTab, setActiveTab] = useState<TabType>('publish');
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);

  const { getCurrentDraft } = useDraftStore();
  const { accounts, fetchAccounts, startLogin } = useAccountStore();
  const { tasks, loading: publishing, publishNow, retryTask } = usePublishStore();
  const { currentProject } = useProjectStore();
  const currentDraft = getCurrentDraft();

  useEffect(() => {
    if (currentProject?.id) {
      fetchAccounts(String(currentProject.id));
    }
  }, [currentProject?.id, fetchAccounts]);

  // 转换账号为平台卡片格式
  const platforms: PlatformInfo[] = accounts.map((acc) => ({
    id: acc.id,
    name: acc.account_name || acc.platform,
    icon: PLATFORM_META[acc.platform]?.icon || '📱',
    color: PLATFORM_META[acc.platform]?.color || '#666',
    connected: acc.session_valid,
  }));

  const handlePlatformSelect = (accountId: string) => {
    setSelectedAccountIds((prev) =>
      prev.includes(accountId)
        ? prev.filter((id) => id !== accountId)
        : [...prev, accountId]
    );
  };

  const handleConnect = async (accountId: string) => {
    const account = accounts.find((a) => a.id === accountId);
    if (account) {
      await startLogin(account.platform);
    }
  };

  const handlePublish = async () => {
    if (selectedAccountIds.length === 0 || !currentDraft) return;
    const selectedAccounts = accounts
      .filter((a) => selectedAccountIds.includes(a.id))
      .map((a) => ({ id: a.id, platform: a.platform }));
    await publishNow(
      { title: currentDraft.title, content: currentDraft.content, images: [], hashtags: [] },
      selectedAccounts
    );
  };

  const tabs = [
    { id: 'publish' as const, label: '立即发布', icon: Send },
    { id: 'schedule' as const, label: '定时发布', icon: Clock },
    { id: 'history' as const, label: '发布历史', icon: History },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* 标签栏 */}
      <div className="flex items-center gap-1 p-4 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
              activeTab === tab.id
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-accent'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'publish' && (
          <div className="grid grid-cols-2 gap-6">
            {/* 左侧：平台选择和内容适配 */}
            <div className="space-y-6">
              {/* 平台选择 */}
              <div>
                <h3 className="text-lg font-semibold mb-4">选择发布平台</h3>
                <div className="grid grid-cols-2 gap-3">
                  {platforms.length > 0 ? (
                    platforms.map((platform) => (
                      <PlatformCard
                        key={platform.id}
                        platform={platform}
                        selected={selectedAccountIds.includes(platform.id)}
                        onSelect={handlePlatformSelect}
                        onConnect={handleConnect}
                      />
                    ))
                  ) : (
                    <p className="col-span-2 text-muted-foreground text-center py-4">
                      暂无绑定账号，请先在账号管理中添加
                    </p>
                  )}
                </div>
              </div>

              {/* 内容适配 */}
              {selectedAccountIds.length > 0 && currentDraft && (
                <ContentAdapter
                  content={{
                    title: currentDraft.title,
                    content: currentDraft.content,
                    images: [],
                  }}
                  platforms={selectedAccountIds}
                />
              )}

              {/* 发布按钮 */}
              <button
                type="button"
                onClick={handlePublish}
                disabled={selectedAccountIds.length === 0 || !currentDraft || publishing}
                className={cn(
                  'w-full py-3 rounded-lg font-medium transition-colors',
                  'bg-primary text-primary-foreground',
                  'hover:bg-primary/90',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {publishing
                  ? '发布中...'
                  : `发布到 ${selectedAccountIds.length} 个平台`}
              </button>
            </div>

            {/* 右侧：预览 */}
            <div>
              <h3 className="text-lg font-semibold mb-4">内容预览</h3>
              {currentDraft ? (
                <PreviewPanel
                  content={{
                    title: currentDraft.title,
                    content: currentDraft.content,
                    images: [],
                  }}
                  platform={accounts.find((a) => selectedAccountIds.includes(a.id))?.platform || 'xiaohongshu'}
                />
              ) : (
                <div className="p-8 text-center text-muted-foreground border rounded-lg">
                  <p>请先在创作页面编写内容</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'schedule' && (
          <ScheduleForm
            platforms={selectedAccountIds}
            onSchedule={(time) => console.log('Schedule:', time)}
          />
        )}

        {activeTab === 'history' && (
          <PublishQueue tasks={tasks} />
        )}
      </div>
    </div>
  );
}

export default PublishCenter;

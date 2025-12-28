/**
 * 发布中心主组件
 * @author Ysf
 */
import { useState } from 'react';
import { Send, Clock, History, Settings } from 'lucide-react';
import { PlatformCard, PlatformInfo } from './PlatformCard';
import { ContentAdapter } from './ContentAdapter';
import { PreviewPanel } from './PreviewPanel';
import { ScheduleForm } from './ScheduleForm';
import { useDraftStore } from '@/stores/useDraftStore';
import { cn } from '@/lib/utils';

// 支持的平台列表
const PLATFORMS: PlatformInfo[] = [
  {
    id: 'xiaohongshu',
    name: '小红书',
    icon: '📕',
    color: '#FF2442',
    connected: false,
  },
  {
    id: 'wechat_mp',
    name: '微信公众号',
    icon: '💬',
    color: '#07C160',
    connected: false,
  },
  {
    id: 'weibo',
    name: '微博',
    icon: '🔴',
    color: '#E6162D',
    connected: false,
  },
];

type TabType = 'publish' | 'schedule' | 'history';

export function PublishCenter() {
  const [activeTab, setActiveTab] = useState<TabType>('publish');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [platforms, setPlatforms] = useState<PlatformInfo[]>(PLATFORMS);
  const [isPublishing, setIsPublishing] = useState(false);

  const { getCurrentDraft } = useDraftStore();
  const currentDraft = getCurrentDraft();

  const handlePlatformSelect = (platformId: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platformId)
        ? prev.filter((id) => id !== platformId)
        : [...prev, platformId]
    );
  };

  const handleConnect = (platformId: string) => {
    // TODO: 实现平台绑定流程
    console.log('Connect platform:', platformId);
  };

  const handlePublish = async () => {
    if (selectedPlatforms.length === 0 || !currentDraft) return;

    setIsPublishing(true);
    try {
      // TODO: 调用发布 API
      console.log('Publishing to:', selectedPlatforms);
    } finally {
      setIsPublishing(false);
    }
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
                  {platforms.map((platform) => (
                    <PlatformCard
                      key={platform.id}
                      platform={platform}
                      selected={selectedPlatforms.includes(platform.id)}
                      onSelect={handlePlatformSelect}
                      onConnect={handleConnect}
                    />
                  ))}
                </div>
              </div>

              {/* 内容适配 */}
              {selectedPlatforms.length > 0 && currentDraft && (
                <ContentAdapter
                  content={{
                    title: currentDraft.title,
                    content: currentDraft.content,
                    images: [],
                  }}
                  platforms={selectedPlatforms}
                />
              )}

              {/* 发布按钮 */}
              <button
                type="button"
                onClick={handlePublish}
                disabled={
                  selectedPlatforms.length === 0 || !currentDraft || isPublishing
                }
                className={cn(
                  'w-full py-3 rounded-lg font-medium transition-colors',
                  'bg-primary text-primary-foreground',
                  'hover:bg-primary/90',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {isPublishing
                  ? '发布中...'
                  : `发布到 ${selectedPlatforms.length} 个平台`}
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
                  platform={selectedPlatforms[0] || 'xiaohongshu'}
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
            platforms={selectedPlatforms}
            onSchedule={(time) => console.log('Schedule:', time)}
          />
        )}

        {activeTab === 'history' && (
          <div className="text-center text-muted-foreground py-12">
            <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无发布历史</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PublishCenter;

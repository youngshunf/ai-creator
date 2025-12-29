/**
 * 设置页面
 * @author Ysf
 */
import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import {
  Settings,
  Key,
  Sparkles,
  Bell,
  Palette,
  Database,
  Shield,
  HelpCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ModelSelector } from '@/components/settings/ModelSelector';
import { UsageStatsPanel as UsageStats } from '@/components/settings/UsageStats';
import { CredentialManager } from '@/components/settings/CredentialManager';

export const Route = createFileRoute('/settings/')({
  component: SettingsPage,
});

type SettingsTab = 'credentials' | 'llm' | 'notifications' | 'appearance' | 'storage' | 'about';

const TABS: { id: SettingsTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'credentials', label: '平台凭证', icon: Key },
  { id: 'llm', label: 'AI 模型', icon: Sparkles },
  { id: 'notifications', label: '通知设置', icon: Bell },
  { id: 'appearance', label: '外观主题', icon: Palette },
  { id: 'storage', label: '数据存储', icon: Database },
  { id: 'about', label: '关于', icon: HelpCircle },
];

function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('credentials');
  const [selectedModel, setSelectedModel] = useState<string>('claude-3-5-sonnet');
  const [notifications, setNotifications] = useState({
    publishSuccess: true,
    publishFailed: true,
    scheduleReminder: true,
    systemUpdates: false,
  });
  const [appearance, setAppearance] = useState({
    theme: 'system' as 'light' | 'dark' | 'system',
    fontSize: 'medium' as 'small' | 'medium' | 'large',
  });

  return (
    <div className="flex h-full">
      {/* 侧边导航 */}
      <div className="w-56 border-r bg-muted/30 p-4">
        <div className="flex items-center gap-2 mb-6 px-2">
          <Settings className="w-5 h-5 text-primary" />
          <h2 className="font-semibold">设置</h2>
        </div>
        <nav className="space-y-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent text-muted-foreground hover:text-foreground'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl mx-auto">
          {activeTab === 'credentials' && <CredentialManager />}

          {activeTab === 'llm' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">AI 模型设置</h3>
                  <p className="text-sm text-muted-foreground">
                    选择默认使用的 AI 模型
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    默认模型
                  </label>
                  <ModelSelector
                    value={selectedModel}
                    onChange={setSelectedModel}
                  />
                </div>

                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium mb-3">用量统计</h4>
                  <UsageStats />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Bell className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">通知设置</h3>
                  <p className="text-sm text-muted-foreground">
                    管理应用通知偏好
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {[
                  { key: 'publishSuccess', label: '发布成功通知', desc: '内容发布成功时通知' },
                  { key: 'publishFailed', label: '发布失败通知', desc: '内容发布失败时通知' },
                  { key: 'scheduleReminder', label: '定时发布提醒', desc: '定时发布前 5 分钟提醒' },
                  { key: 'systemUpdates', label: '系统更新通知', desc: '有新版本时通知' },
                ].map((item) => (
                  <div
                    key={item.key}
                    className="flex items-center justify-between p-4 rounded-xl border"
                  >
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                    <button
                      onClick={() =>
                        setNotifications((prev) => ({
                          ...prev,
                          [item.key]: !prev[item.key as keyof typeof prev],
                        }))
                      }
                      className={cn(
                        'w-12 h-7 rounded-full transition-colors relative',
                        notifications[item.key as keyof typeof notifications]
                          ? 'bg-primary'
                          : 'bg-muted'
                      )}
                    >
                      <span
                        className={cn(
                          'absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-transform',
                          notifications[item.key as keyof typeof notifications]
                            ? 'translate-x-6'
                            : 'translate-x-1'
                        )}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Palette className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">外观主题</h3>
                  <p className="text-sm text-muted-foreground">
                    自定义应用外观
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-3 block">主题模式</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { value: 'light', label: '浅色' },
                      { value: 'dark', label: '深色' },
                      { value: 'system', label: '跟随系统' },
                    ].map((theme) => (
                      <button
                        key={theme.value}
                        onClick={() =>
                          setAppearance((prev) => ({
                            ...prev,
                            theme: theme.value as typeof prev.theme,
                          }))
                        }
                        className={cn(
                          'p-4 rounded-xl border-2 transition-all',
                          appearance.theme === theme.value
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        {theme.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-3 block">字体大小</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { value: 'small', label: '小' },
                      { value: 'medium', label: '中' },
                      { value: 'large', label: '大' },
                    ].map((size) => (
                      <button
                        key={size.value}
                        onClick={() =>
                          setAppearance((prev) => ({
                            ...prev,
                            fontSize: size.value as typeof prev.fontSize,
                          }))
                        }
                        className={cn(
                          'p-4 rounded-xl border-2 transition-all',
                          appearance.fontSize === size.value
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                      >
                        {size.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'storage' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Database className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">数据存储</h3>
                  <p className="text-sm text-muted-foreground">
                    管理本地数据和缓存
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-xl border">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium">草稿数据</span>
                    <span className="text-sm text-muted-foreground">12.5 MB</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-1/4 rounded-full" />
                  </div>
                </div>

                <div className="p-4 rounded-xl border">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium">缓存数据</span>
                    <span className="text-sm text-muted-foreground">45.2 MB</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500 w-1/2 rounded-full" />
                  </div>
                </div>

                <div className="flex gap-3">
                  <button className="flex-1 py-3 px-4 rounded-xl border hover:bg-accent transition-colors">
                    清除缓存
                  </button>
                  <button className="flex-1 py-3 px-4 rounded-xl border hover:bg-accent transition-colors text-red-500">
                    重置所有数据
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'about' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <HelpCircle className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">关于创流</h3>
                  <p className="text-sm text-muted-foreground">
                    版本信息和帮助
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-6 rounded-xl border text-center">
                  <h2 className="text-2xl font-bold gradient-text mb-2">创流</h2>
                  <p className="text-muted-foreground mb-4">
                    自媒体创作者的 AI 超级大脑
                  </p>
                  <p className="text-sm">版本 1.0.0</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <button className="p-4 rounded-xl border hover:bg-accent transition-colors text-left">
                    <p className="font-medium">使用文档</p>
                    <p className="text-sm text-muted-foreground">查看帮助文档</p>
                  </button>
                  <button className="p-4 rounded-xl border hover:bg-accent transition-colors text-left">
                    <p className="font-medium">检查更新</p>
                    <p className="text-sm text-muted-foreground">当前已是最新版本</p>
                  </button>
                  <button className="p-4 rounded-xl border hover:bg-accent transition-colors text-left">
                    <p className="font-medium">反馈问题</p>
                    <p className="text-sm text-muted-foreground">报告 Bug 或建议</p>
                  </button>
                  <button className="p-4 rounded-xl border hover:bg-accent transition-colors text-left">
                    <p className="font-medium">开源许可</p>
                    <p className="text-sm text-muted-foreground">MIT License</p>
                  </button>
                </div>

                <div className="p-4 rounded-xl bg-muted/50 text-center text-sm text-muted-foreground">
                  <p>© 2025 创流 (CreatorFlow)</p>
                  <p>Made with ❤️ by @Ysf</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

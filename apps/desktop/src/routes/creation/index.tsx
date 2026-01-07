/**
 * 创作页面路由 - Tech Startup + SaaS 风格
 * @author Ysf
 * @updated 2026-01-07
 */
import { createFileRoute } from '@tanstack/react-router';
import { useState, useCallback, useEffect } from 'react';
import { PanelRightClose, PanelRightOpen, Cloud, CloudOff, ChevronRight, Bot, Sparkles } from 'lucide-react';
import { marked } from 'marked';
import { TipTapEditor } from '@/components/editor/TipTapEditor';
import { AIWritingPanel } from '@/components/editor/AIWritingPanel';
import { AssetPanel } from '@/components/creation/AssetPanel';
import { useDraftStore } from '@/stores/useDraftStore';
import { useAutoSave, formatLastSaved } from '@/hooks/useAutoSave';
import { cn } from '@/lib/utils';

export const Route = createFileRoute('/creation/')({
  component: CreationPage,
});

function CreationPage() {
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [activeTab, setActiveTab] = useState<'article' | 'image' | 'video'>('article');
  const [rightPanelTab, setRightPanelTab] = useState<'ai' | 'assets'>('ai');
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');

  const {
    currentDraftId,
    getCurrentDraft,
    createDraft,
    updateDraft,
    setCurrentDraft,
  } = useDraftStore();

  const { isSaving, lastSavedAt, saveNow } = useAutoSave({
    draftId: currentDraftId,
    content,
    title,
    delay: 2000,
    enabled: !!currentDraftId,
  });

  useEffect(() => {
    const draft = getCurrentDraft();
    if (draft) {
      setContent(draft.content);
      setTitle(draft.title);
    } else {
      if (!currentDraftId) {
        const id = createDraft({
          title: '未命名草稿',
          content: '',
          tags: [],
          isAutoSaved: false,
        });
        setCurrentDraft(id);
      }
    }
  }, []);

  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
  }, []);

  const handleTitleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setTitle(e.target.value);
    },
    []
  );

  const handleAIGenerated = useCallback(
    (generatedTitle: string, generatedContent: string, tags: string[]) => {
      setTitle(generatedTitle);
      const htmlContent = marked.parse(generatedContent, { async: false }) as string;
      setContent(htmlContent);

      if (currentDraftId) {
        updateDraft(currentDraftId, {
          title: generatedTitle,
          content: htmlContent,
          tags,
        });
      }
    },
    [currentDraftId, updateDraft]
  );

  const handleAssetInsert = useCallback((type: 'image' | 'text', assetContent: string) => {
    let newContent = content;
    if (type === 'image') {
      newContent += `\n\n![Image](${assetContent})\n`;
    } else {
      newContent += `\n\n${assetContent}\n`;
    }
    setContent(newContent);
  }, [content]);

  return (
    <div className="flex flex-col h-[calc(100%+48px)] -m-6">
      {/* 顶部工具栏 - 无边距铺满 */}
      <div className="h-12 flex items-center justify-between px-4 glass-card rounded-none border-x-0 border-t-0 shrink-0 z-20">
        <div className="flex items-center gap-4">
          {/* Tab 切换 */}
          <div className="flex p-0.5 bg-slate-100 dark:bg-slate-800 rounded-lg">
            {[
              { key: 'article', label: '文章创作' },
              { key: 'image', label: '图片创作' },
              { key: 'video', label: '视频创作' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as typeof activeTab)}
                className={cn(
                  'px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-fast',
                  activeTab === tab.key
                    ? 'bg-white dark:bg-slate-700 text-primary-600 dark:text-primary-400 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* 保存状态 */}
          <div className="flex items-center gap-2 text-sm text-slate-500">
            {isSaving ? (
              <>
                <Cloud className="w-4 h-4 animate-pulse text-primary-500" />
                <span>保存中...</span>
              </>
            ) : lastSavedAt ? (
              <>
                <Cloud className="w-4 h-4 text-success" />
                <span>已保存 {formatLastSaved(lastSavedAt)}</span>
              </>
            ) : (
              <>
                <CloudOff className="w-4 h-4" />
                <span>未保存</span>
              </>
            )}
          </div>

          <button onClick={saveNow} disabled={isSaving} className="btn-secondary text-sm py-1.5">
            保存草稿
          </button>

          <button className="btn-primary flex items-center text-sm py-1.5">
            去发布
            <ChevronRight className="w-4 h-4 ml-1" />
          </button>

          <div className="divider-vertical h-6 mx-1" />

          <button
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="btn-icon"
            title={showRightPanel ? '隐藏面板' : '显示面板'}
          >
            {showRightPanel ? <PanelRightClose className="w-5 h-5" /> : <PanelRightOpen className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* 工作区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧大纲 - 缩窄宽度 */}
        <aside className="w-48 hidden lg:flex flex-col shrink-0 border-r border-[rgb(var(--color-border))] bg-slate-50/50 dark:bg-slate-900/30">
          <div className="p-3 border-b border-[rgb(var(--color-border))]">
            <h3 className="font-heading font-semibold text-xs text-slate-500 uppercase tracking-wider">大纲</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
            <button className="w-full text-left px-3 py-2 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 text-sm font-medium border-l-2 border-primary-500">
              1. 引言
            </button>
            <button className="w-full text-left px-3 py-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5 text-sm border-l-2 border-transparent hover:border-slate-300">
              2. 浅色系搭配
            </button>
            <button className="w-full text-left px-3 py-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5 text-sm border-l-2 border-transparent hover:border-slate-300">
              3. 材质选择
            </button>
          </div>
        </aside>

        {/* 中间编辑区 - 最小宽度 */}
        <main className="flex-1 min-w-[500px] bg-white dark:bg-slate-900 overflow-hidden">
          <div className="h-full">
            <input
              type="text"
              value={title}
              onChange={handleTitleChange}
              placeholder="输入标题..."
              className="w-full bg-transparent text-3xl font-heading font-bold px-6 pt-6 pb-4 border-none focus:ring-0 focus:outline-none placeholder-slate-300 dark:placeholder-slate-600"
            />
            <div className="h-[calc(100%-80px)]">
              <TipTapEditor
                content={content}
                onChange={handleContentChange}
                placeholder="开始创作你的内容..."
                showToolbar={true}
                showCharacterCount={true}
                showAIAssist={false}
                className="h-full"
              />
            </div>
          </div>
        </main>

        {/* 右侧 AI 面板 */}
        {showRightPanel && (
          <aside className="w-80 flex flex-col shrink-0 border-l border-[rgb(var(--color-border))] bg-slate-50/50 dark:bg-slate-900/50">
            {/* Tab 切换 */}
            <div className="p-2 border-b border-[rgb(var(--color-border))]">
              <div className="flex p-0.5 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <button
                  onClick={() => setRightPanelTab('ai')}
                  className={cn(
                    'flex-1 py-1.5 text-xs font-medium rounded-md transition-all flex items-center justify-center gap-1',
                    rightPanelTab === 'ai'
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  )}
                >
                  <Bot className="w-3.5 h-3.5" />
                  AI 助手
                </button>
                <button
                  onClick={() => setRightPanelTab('assets')}
                  className={cn(
                    'flex-1 py-1.5 text-xs font-medium rounded-md transition-all flex items-center justify-center gap-1',
                    rightPanelTab === 'assets'
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  )}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  素材灵感
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-thin">
              {rightPanelTab === 'ai' ? (
                <AIWritingPanel onGenerated={handleAIGenerated} />
              ) : (
                <AssetPanel onInsert={handleAssetInsert} />
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

export default CreationPage;

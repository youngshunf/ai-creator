/**
 * 创作页面路由
 * @author Ysf
 */
import { createFileRoute } from '@tanstack/react-router';
import { useState, useCallback, useEffect } from 'react';
import { PanelLeftClose, PanelLeft, Save, Cloud, CloudOff } from 'lucide-react';
import { TipTapEditor } from '@/components/editor/TipTapEditor';
import { AIWritingPanel } from '@/components/editor/AIWritingPanel';
import { useDraftStore } from '@/stores/useDraftStore';
import { useAutoSave, formatLastSaved } from '@/hooks/useAutoSave';
import { cn } from '@/lib/utils';

export const Route = createFileRoute('/creation/')({
  component: CreationPage,
});

function CreationPage() {
  const [showAIPanel, setShowAIPanel] = useState(true);
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

  // 初始化或加载草稿
  useEffect(() => {
    const draft = getCurrentDraft();
    if (draft) {
      setContent(draft.content);
      setTitle(draft.title);
    } else {
      // 创建新草稿
      const id = createDraft({
        title: '未命名草稿',
        content: '',
        tags: [],
        isAutoSaved: false,
      });
      setCurrentDraft(id);
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
      setContent(generatedContent);

      if (currentDraftId) {
        updateDraft(currentDraftId, {
          title: generatedTitle,
          content: generatedContent,
          tags,
        });
      }
    },
    [currentDraftId, updateDraft]
  );

  return (
    <div className="flex h-full">
      {/* AI 写作面板 */}
      <div
        className={cn(
          'border-r bg-muted/30 transition-all duration-300 overflow-hidden',
          showAIPanel ? 'w-[400px]' : 'w-0'
        )}
      >
        {showAIPanel && (
          <div className="h-full overflow-auto">
            <AIWritingPanel onGenerated={handleAIGenerated} />
          </div>
        )}
      </div>

      {/* 主编辑区 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 顶部工具栏 */}
        <div className="flex items-center justify-between px-4 py-2 border-b bg-background">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowAIPanel(!showAIPanel)}
              className="p-2 rounded hover:bg-accent transition-colors"
              title={showAIPanel ? '隐藏 AI 面板' : '显示 AI 面板'}
            >
              {showAIPanel ? (
                <PanelLeftClose className="w-4 h-4" />
              ) : (
                <PanelLeft className="w-4 h-4" />
              )}
            </button>

            <input
              type="text"
              value={title}
              onChange={handleTitleChange}
              placeholder="输入标题..."
              className="text-lg font-medium bg-transparent border-none focus:outline-none focus:ring-0 w-[300px]"
            />
          </div>

          <div className="flex items-center gap-3">
            {/* 保存状态 */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {isSaving ? (
                <>
                  <Cloud className="w-4 h-4 animate-pulse" />
                  <span>保存中...</span>
                </>
              ) : lastSavedAt ? (
                <>
                  <Cloud className="w-4 h-4 text-green-500" />
                  <span>{formatLastSaved(lastSavedAt)}</span>
                </>
              ) : (
                <>
                  <CloudOff className="w-4 h-4" />
                  <span>未保存</span>
                </>
              )}
            </div>

            <button
              type="button"
              onClick={saveNow}
              disabled={isSaving}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border hover:bg-accent transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>保存</span>
            </button>
          </div>
        </div>

        {/* 编辑器 */}
        <div className="flex-1 overflow-hidden">
          <TipTapEditor
            content={content}
            onChange={handleContentChange}
            placeholder="开始创作你的内容..."
            showToolbar={true}
            showCharacterCount={true}
            showAIAssist={true}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
}

export default CreationPage;

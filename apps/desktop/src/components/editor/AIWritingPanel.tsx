/**
 * AI 写作面板组件
 * @author Ysf
 */
import { useState } from 'react';
import { Loader2, Sparkles, X, Plus, RefreshCw } from 'lucide-react';
import { StyleSelector } from './StyleSelector';
import { useAIWriter, AIWriterOptions } from '@/hooks/useAIWriter';
import { WritingStyle } from '@/config/writingStyles';
import { cn } from '@/lib/utils';

interface AIWritingPanelProps {
  onGenerated?: (title: string, content: string, tags: string[]) => void;
  className?: string;
}

export function AIWritingPanel({ onGenerated, className }: AIWritingPanelProps) {
  const [topic, setTopic] = useState('');
  const [selectedStyle, setSelectedStyle] = useState<WritingStyle | null>(null);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [additionalPrompt, setAdditionalPrompt] = useState('');

  const { isGenerating, progress, error, result, generate, cancel, reset } =
    useAIWriter();

  const handleAddKeyword = () => {
    const trimmed = keywordInput.trim();
    if (trimmed && !keywords.includes(trimmed) && keywords.length < 10) {
      setKeywords([...keywords, trimmed]);
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setKeywords(keywords.filter((k) => k !== keyword));
  };

  const handleKeywordKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  const handleGenerate = async () => {
    if (!selectedStyle) return;

    const options: AIWriterOptions = {
      topic,
      styleId: selectedStyle.id,
      platform: selectedStyle.platform[0],
      keywords,
      additionalPrompt: additionalPrompt || undefined,
    };

    const result = await generate(options);

    if (result) {
      onGenerated?.(result.title, result.content, result.tags);
    }
  };

  const handleReset = () => {
    reset();
    setTopic('');
    setSelectedStyle(null);
    setKeywords([]);
    setAdditionalPrompt('');
  };

  return (
    <div className={cn('flex flex-col gap-4 p-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          AI 智能创作
        </h3>
        {(result || error) && (
          <button
            type="button"
            onClick={handleReset}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
          >
            <RefreshCw className="w-4 h-4" />
            重新开始
          </button>
        )}
      </div>

      {/* 主题输入 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">创作主题</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="输入你想创作的主题，如：秋季护肤攻略"
          className="w-full px-4 py-3 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={isGenerating}
        />
      </div>

      {/* 风格选择 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">写作风格</label>
        <StyleSelector
          value={selectedStyle?.id}
          onChange={setSelectedStyle}
        />
      </div>

      {/* 关键词 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">关键词（可选）</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={handleKeywordKeyDown}
            placeholder="输入关键词后按回车添加"
            className="flex-1 px-4 py-2 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={isGenerating}
          />
          <button
            type="button"
            onClick={handleAddKeyword}
            disabled={isGenerating || !keywordInput.trim()}
            className="px-3 py-2 rounded-lg border hover:bg-accent disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        {keywords.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {keywords.map((keyword) => (
              <span
                key={keyword}
                className="inline-flex items-center gap-1 px-2 py-1 bg-secondary rounded-md text-sm"
              >
                {keyword}
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(keyword)}
                  className="hover:text-destructive"
                  disabled={isGenerating}
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 额外要求 */}
      <div className="space-y-2">
        <label className="text-sm font-medium">额外要求（可选）</label>
        <textarea
          value={additionalPrompt}
          onChange={(e) => setAdditionalPrompt(e.target.value)}
          placeholder="输入其他创作要求，如：字数控制在500字以内"
          rows={2}
          className="w-full px-4 py-3 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-none"
          disabled={isGenerating}
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      {/* 生成进度 */}
      {isGenerating && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">正在生成...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 生成按钮 */}
      <div className="flex gap-2">
        {isGenerating ? (
          <button
            type="button"
            onClick={cancel}
            className="flex-1 py-3 rounded-lg border hover:bg-accent transition-colors"
          >
            取消生成
          </button>
        ) : (
          <button
            type="button"
            onClick={handleGenerate}
            disabled={!topic.trim() || !selectedStyle}
            className={cn(
              'flex-1 py-3 rounded-lg font-medium transition-colors',
              'bg-primary text-primary-foreground hover:bg-primary/90',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'flex items-center justify-center gap-2'
            )}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                开始创作
              </>
            )}
          </button>
        )}
      </div>

      {/* 生成结果预览 */}
      {result && (
        <div className="mt-4 p-4 rounded-lg border bg-muted/50 space-y-3">
          <h4 className="font-medium">生成结果预览</h4>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-muted-foreground">标题：</span>
              <span className="font-medium">{result.title}</span>
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">标签：</span>
              {result.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block px-2 py-0.5 bg-secondary rounded text-xs ml-1"
                >
                  #{tag}
                </span>
              ))}
            </div>
            <div className="text-sm text-muted-foreground line-clamp-3">
              {result.content.slice(0, 200)}...
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIWritingPanel;

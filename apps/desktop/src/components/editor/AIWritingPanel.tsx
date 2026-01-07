/**
 * AI 写作面板组件 - Tech Startup + SaaS 风格
 * @author Ysf
 * @updated 2026-01-07
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
    <div className={cn('flex flex-col gap-5 p-4', className)}>
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-heading font-semibold flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-cta flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          AI 智能创作
        </h3>
        {(result || error) && (
          <button
            type="button"
            onClick={handleReset}
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            重新开始
          </button>
        )}
      </div>

      {/* 主题输入 */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-600 dark:text-slate-400">创作主题</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="如：秋季护肤攻略"
          className="w-full px-3 py-2.5 rounded-lg bg-white dark:bg-slate-800 border border-[rgb(var(--color-border))] text-sm placeholder-slate-400 focus:outline-none focus:border-transparent focus:shadow-[0_0_0_2px_rgb(37,99,235),0_0_0_4px_rgba(37,99,235,0.15)] transition-all"
          disabled={isGenerating}
        />
      </div>

      {/* 风格选择 */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-600 dark:text-slate-400">写作风格</label>
        <StyleSelector
          value={selectedStyle?.id}
          onChange={setSelectedStyle}
        />
      </div>

      {/* 关键词 */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-600 dark:text-slate-400">关键词（可选）</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={handleKeywordKeyDown}
            placeholder="按回车添加"
            className="flex-1 px-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-[rgb(var(--color-border))] text-sm placeholder-slate-400 focus:outline-none focus:border-transparent focus:shadow-[0_0_0_2px_rgb(37,99,235),0_0_0_4px_rgba(37,99,235,0.15)] transition-all"
            disabled={isGenerating}
          />
          <button
            type="button"
            onClick={handleAddKeyword}
            disabled={isGenerating || !keywordInput.trim()}
            className="px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 border border-[rgb(var(--color-border))] hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        {keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {keywords.map((keyword) => (
              <span
                key={keyword}
                className="inline-flex items-center gap-1 px-2 py-1 bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded-md text-xs font-medium"
              >
                {keyword}
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(keyword)}
                  className="hover:text-primary-800 dark:hover:text-primary-300 transition-colors"
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
        <label className="text-xs font-medium text-slate-600 dark:text-slate-400">额外要求（可选）</label>
        <textarea
          value={additionalPrompt}
          onChange={(e) => setAdditionalPrompt(e.target.value)}
          placeholder="如：字数控制在500字以内"
          rows={2}
          className="w-full px-3 py-2.5 rounded-lg bg-white dark:bg-slate-800 border border-[rgb(var(--color-border))] text-sm placeholder-slate-400 focus:outline-none focus:border-transparent focus:shadow-[0_0_0_2px_rgb(37,99,235),0_0_0_4px_rgba(37,99,235,0.15)] transition-all resize-none"
          disabled={isGenerating}
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
          {error}
        </div>
      )}

      {/* 生成进度 */}
      {isGenerating && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500">正在生成...</span>
            <span className="text-primary-600 font-medium">{progress}%</span>
          </div>
          <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-cta rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 生成按钮 */}
      <div className="flex gap-2 pt-2">
        {isGenerating ? (
          <button
            type="button"
            onClick={cancel}
            className="flex-1 py-2.5 rounded-lg border border-[rgb(var(--color-border))] text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            取消生成
          </button>
        ) : (
          <button
            type="button"
            onClick={handleGenerate}
            disabled={!topic.trim() || !selectedStyle}
            className={cn(
              'flex-1 py-2.5 rounded-lg font-medium text-sm transition-all',
              'bg-gradient-to-r from-primary-500 to-primary-600 text-white',
              'hover:from-primary-600 hover:to-primary-700 hover:shadow-lg hover:shadow-primary-500/25',
              'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none',
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
        <div className="mt-2 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-[rgb(var(--color-border))] space-y-3">
          <h4 className="font-medium text-sm flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-success" />
            生成完成
          </h4>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-slate-500 text-xs">标题：</span>
              <span className="font-medium ml-1">{result.title}</span>
            </div>
            <div className="text-sm flex flex-wrap items-center gap-1">
              <span className="text-slate-500 text-xs">标签：</span>
              {result.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-xs"
                >
                  #{tag}
                </span>
              ))}
            </div>
            <div className="text-xs text-slate-500 line-clamp-3 leading-relaxed">
              {result.content.slice(0, 200)}...
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIWritingPanel;

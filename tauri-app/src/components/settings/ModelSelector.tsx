/**
 * 模型选择器组件
 * @author Ysf
 */
import { useState, useEffect } from 'react';
import { Check, ChevronDown, Sparkles } from 'lucide-react';
import { useLLMStatus, ModelInfo } from '@/hooks/useLLMStatus';
import { cn } from '@/lib/utils';

interface ModelSelectorProps {
  value?: string;
  onChange?: (modelId: string) => void;
  className?: string;
}

export function ModelSelector({ value, onChange, className }: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { models, fetchModels } = useLLMStatus();

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const selectedModel = models.find((m) => m.modelId === value);

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      anthropic: 'text-orange-500',
      openai: 'text-green-500',
      google: 'text-blue-500',
      alibaba: 'text-purple-500',
      deepseek: 'text-cyan-500',
    };
    return colors[provider] || 'text-muted-foreground';
  };

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full flex items-center justify-between px-4 py-3 rounded-lg border bg-background',
          'hover:bg-accent transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-ring'
        )}
      >
        <div className="flex items-center gap-3">
          <Sparkles className="w-4 h-4 text-primary" />
          {selectedModel ? (
            <div className="text-left">
              <div className="font-medium">{selectedModel.displayName}</div>
              <div
                className={cn(
                  'text-xs',
                  getProviderColor(selectedModel.provider)
                )}
              >
                {selectedModel.provider}
              </div>
            </div>
          ) : (
            <span className="text-muted-foreground">选择模型</span>
          )}
        </div>
        <ChevronDown
          className={cn(
            'w-4 h-4 text-muted-foreground transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-2 py-2 bg-popover border rounded-lg shadow-lg max-h-[300px] overflow-auto">
            {models.length === 0 ? (
              <div className="px-4 py-3 text-sm text-muted-foreground">
                暂无可用模型
              </div>
            ) : (
              models.map((model) => (
                <button
                  key={model.modelId}
                  type="button"
                  onClick={() => {
                    onChange?.(model.modelId);
                    setIsOpen(false);
                  }}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 hover:bg-accent transition-colors',
                    value === model.modelId && 'bg-accent'
                  )}
                >
                  <div className="flex-1 text-left">
                    <div className="font-medium">{model.displayName}</div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className={getProviderColor(model.provider)}>
                        {model.provider}
                      </span>
                      <span>·</span>
                      <span>最大 {model.maxTokens} tokens</span>
                      {model.supportsVision && (
                        <>
                          <span>·</span>
                          <span>支持图像</span>
                        </>
                      )}
                    </div>
                  </div>
                  {value === model.modelId && (
                    <Check className="w-4 h-4 text-primary" />
                  )}
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default ModelSelector;

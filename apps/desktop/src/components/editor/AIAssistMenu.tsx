/**
 * AI 辅助菜单组件 - 选中文本后显示
 * @author Ysf
 */
import { Editor } from '@tiptap/react';
import {
  Wand2,
  RefreshCw,
  Expand,
  Shrink,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface AIAssistMenuProps {
  editor: Editor;
  onAction?: (action: AIAction, selectedText: string) => Promise<string>;
}

export type AIAction =
  | 'continue'
  | 'rewrite'
  | 'expand'
  | 'shorten'
  | 'polish';

interface ActionItem {
  id: AIAction;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const actions: ActionItem[] = [
  {
    id: 'continue',
    label: '续写',
    icon: <ArrowRight className="w-4 h-4" />,
    description: '基于上下文继续生成',
  },
  {
    id: 'rewrite',
    label: '改写',
    icon: <RefreshCw className="w-4 h-4" />,
    description: '换种表达方式',
  },
  {
    id: 'expand',
    label: '扩写',
    icon: <Expand className="w-4 h-4" />,
    description: '丰富内容细节',
  },
  {
    id: 'shorten',
    label: '缩写',
    icon: <Shrink className="w-4 h-4" />,
    description: '精简内容',
  },
  {
    id: 'polish',
    label: '润色',
    icon: <Sparkles className="w-4 h-4" />,
    description: '优化语言表达',
  },
];

export function AIAssistMenu({ editor, onAction }: AIAssistMenuProps) {
  const [loading, setLoading] = useState<AIAction | null>(null);

  const handleAction = async (action: AIAction) => {
    if (!onAction) return;

    const { from, to } = editor.state.selection;
    const selectedText = editor.state.doc.textBetween(from, to, ' ');

    if (!selectedText.trim()) return;

    setLoading(action);

    try {
      const result = await onAction(action, selectedText);

      if (result) {
        editor.chain().focus().deleteSelection().insertContent(result).run();
      }
    } catch (error) {
      console.error('AI action failed:', error);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="flex items-center gap-1 p-1 bg-popover border rounded-lg shadow-lg">
      <div className="flex items-center gap-1 px-2 text-xs text-muted-foreground border-r">
        <Wand2 className="w-3 h-3" />
        <span>AI</span>
      </div>

      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          onClick={() => handleAction(action.id)}
          disabled={loading !== null}
          title={action.description}
          className={cn(
            'flex items-center gap-1.5 px-2 py-1.5 rounded text-sm',
            'hover:bg-accent transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            loading === action.id && 'animate-pulse'
          )}
        >
          {action.icon}
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}

export default AIAssistMenu;

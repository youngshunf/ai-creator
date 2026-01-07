/**
 * 选题推荐组件
 * @author Ysf
 */
import { useState } from 'react';
import { Sparkles, Loader2, RefreshCw, Check } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';

interface TopicSuggestionProps {
  onSelect: (topic: string) => void;
}

interface Topic {
  title: string;
  reason: string;
  hot: boolean;
}

export function TopicSuggestion({ onSelect }: TopicSuggestionProps) {
  const [keyword, setKeyword] = useState('');
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!keyword.trim()) return;
    setLoading(true);
    setTopics([]);

    try {
      const result = await invoke<{ success: boolean; outputs: { topics: Topic[] }; error?: string }>('execute_graph', {
        graphName: 'topic-suggestion',
        inputs: { keyword: keyword.trim(), count: 5 },
      });

      if (result.success && result.outputs?.topics) {
        setTopics(result.outputs.topics);
      } else {
        console.error('生成选题失败:', result.error);
      }
    } catch (e) {
      console.error('生成选题失败:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (topic: Topic) => {
    setSelectedTopic(topic.title);
    onSelect(topic.title);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
          placeholder="输入关键词或领域..."
          className="flex-1 px-3 py-2 text-sm border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={handleGenerate}
          disabled={loading || !keyword.trim()}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          生成选题
        </button>
      </div>

      {topics.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">推荐选题</span>
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="text-xs text-primary-500 hover:text-primary-600 flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" /> 换一批
            </button>
          </div>
          {topics.map((topic, index) => (
            <button
              key={index}
              onClick={() => handleSelect(topic)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                selectedTopic === topic.title
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10'
                  : 'border-slate-200 dark:border-slate-700 hover:border-primary-300 dark:hover:border-primary-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900 dark:text-white text-sm">{topic.title}</span>
                    {topic.hot && (
                      <span className="px-1.5 py-0.5 text-xs bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 rounded">热门</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{topic.reason}</p>
                </div>
                {selectedTopic === topic.title && <Check className="w-5 h-5 text-primary-500 shrink-0" />}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

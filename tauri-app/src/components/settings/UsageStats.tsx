/**
 * 用量统计组件
 * @author Ysf
 */
import { useEffect, useState } from 'react';
import { BarChart3, Coins, Zap, RefreshCw } from 'lucide-react';
import { useLLMStatus, UsageStats } from '@/hooks/useLLMStatus';
import { cn } from '@/lib/utils';

interface UsageStatsProps {
  className?: string;
}

type Period = 'day' | 'week' | 'month';

export function UsageStatsPanel({ className }: UsageStatsProps) {
  const [period, setPeriod] = useState<Period>('month');
  const { usage, fetchUsage } = useLLMStatus();

  useEffect(() => {
    fetchUsage(period);
  }, [period, fetchUsage]);

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(2)}`;
  };

  const periodLabels: Record<Period, string> = {
    day: '今日',
    week: '本周',
    month: '本月',
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          用量统计
        </h3>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border overflow-hidden">
            {(['day', 'week', 'month'] as Period[]).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPeriod(p)}
                className={cn(
                  'px-3 py-1 text-sm transition-colors',
                  period === p
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                )}
              >
                {periodLabels[p]}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => fetchUsage(period)}
            className="p-2 rounded hover:bg-accent transition-colors"
            title="刷新"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {usage ? (
        <>
          {/* 统计卡片 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border bg-card">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <Zap className="w-4 h-4" />
                <span className="text-sm">Token 用量</span>
              </div>
              <div className="text-2xl font-bold">
                {formatNumber(usage.totalTokens)}
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-card">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <Coins className="w-4 h-4" />
                <span className="text-sm">费用</span>
              </div>
              <div className="text-2xl font-bold">
                {formatCost(usage.totalCost)}
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-card">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm">请求次数</span>
              </div>
              <div className="text-2xl font-bold">
                {formatNumber(usage.requestCount)}
              </div>
            </div>
          </div>

          {/* 模型分布 */}
          {usage.breakdown && usage.breakdown.length > 0 && (
            <div className="p-4 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-3">模型用量分布</h4>
              <div className="space-y-3">
                {usage.breakdown.map((item) => {
                  const percentage =
                    (item.tokens / usage.totalTokens) * 100 || 0;
                  return (
                    <div key={item.model}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span>{item.model}</span>
                        <span className="text-muted-foreground">
                          {formatNumber(item.tokens)} tokens
                        </span>
                      </div>
                      <div className="h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="p-8 text-center text-muted-foreground">
          <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>暂无用量数据</p>
        </div>
      )}
    </div>
  );
}

export default UsageStatsPanel;

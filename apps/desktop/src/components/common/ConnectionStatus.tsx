/**
 * 连接状态指示器组件
 * @author Ysf
 */
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useLLMStatus } from '@/hooks/useLLMStatus';
import { cn } from '@/lib/utils';

interface ConnectionStatusProps {
  className?: string;
  showLabel?: boolean;
}

export function ConnectionStatus({
  className,
  showLabel = true,
}: ConnectionStatusProps) {
  const { status, checkConnection } = useLLMStatus();

  const handleClick = () => {
    if (!status.isChecking) {
      checkConnection();
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={status.isChecking}
      className={cn(
        'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors',
        'hover:bg-accent disabled:cursor-not-allowed',
        className
      )}
      title={
        status.isChecking
          ? '检查中...'
          : status.isConnected
            ? '已连接到 AI 服务'
            : '未连接到 AI 服务，点击重试'
      }
    >
      {status.isChecking ? (
        <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
      ) : status.isConnected ? (
        <Wifi className="w-4 h-4 text-green-500" />
      ) : (
        <WifiOff className="w-4 h-4 text-destructive" />
      )}

      {showLabel && (
        <span
          className={cn(
            'text-sm',
            status.isConnected ? 'text-green-500' : 'text-destructive'
          )}
        >
          {status.isChecking
            ? '检查中'
            : status.isConnected
              ? '已连接'
              : '未连接'}
        </span>
      )}
    </button>
  );
}

export default ConnectionStatus;

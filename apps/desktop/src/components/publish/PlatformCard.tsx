/**
 * 平台卡片组件
 * @author Ysf
 */
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface PlatformInfo {
  id: string;
  name: string;
  icon: string;
  color: string;
  connected: boolean;
  accountName?: string;
}

interface PlatformCardProps {
  platform: PlatformInfo;
  selected: boolean;
  onSelect: (id: string) => void;
  onConnect?: (id: string) => void;
}

export function PlatformCard({
  platform,
  selected,
  onSelect,
  onConnect,
}: PlatformCardProps) {
  const handleClick = () => {
    if (platform.connected) {
      onSelect(platform.id);
    } else {
      onConnect?.(platform.id);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        'relative p-4 rounded-lg border-2 transition-all text-left',
        'hover:shadow-md',
        selected && platform.connected
          ? 'border-primary bg-primary/5'
          : 'border-border hover:border-primary/50',
        !platform.connected && 'opacity-60'
      )}
    >
      {selected && platform.connected && (
        <div className="absolute top-2 right-2">
          <Check className="w-5 h-5 text-primary" />
        </div>
      )}

      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{platform.icon}</span>
        <span className="font-medium">{platform.name}</span>
      </div>

      {platform.connected ? (
        <p className="text-sm text-muted-foreground truncate">
          {platform.accountName || '已连接'}
        </p>
      ) : (
        <p className="text-sm text-primary">点击绑定账号</p>
      )}
    </button>
  );
}

export default PlatformCard;

/**
 * 写作风格选择器组件
 * @author Ysf
 */
import { useState } from 'react';
import { Check, ChevronDown } from 'lucide-react';
import { writingStyles, WritingStyle } from '@/config/writingStyles';
import { cn } from '@/lib/utils';

interface StyleSelectorProps {
  value?: string;
  onChange?: (style: WritingStyle) => void;
  platform?: string;
  className?: string;
}

export function StyleSelector({
  value,
  onChange,
  platform,
  className,
}: StyleSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const filteredStyles = platform
    ? writingStyles.filter((s) => s.platform.includes(platform))
    : writingStyles;

  const selectedStyle = writingStyles.find((s) => s.id === value);

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
          {selectedStyle ? (
            <>
              <span className="text-xl">{selectedStyle.icon}</span>
              <div className="text-left">
                <div className="font-medium">{selectedStyle.name}</div>
                <div className="text-xs text-muted-foreground">
                  {selectedStyle.description}
                </div>
              </div>
            </>
          ) : (
            <span className="text-muted-foreground">选择写作风格</span>
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
          <div className="absolute z-20 w-full mt-2 py-2 bg-white border rounded-lg shadow-lg max-h-[400px] overflow-auto">
            {filteredStyles.map((style) => (
              <button
                key={style.id}
                type="button"
                onClick={() => {
                  onChange?.(style);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 hover:bg-accent transition-colors',
                  value === style.id && 'bg-accent'
                )}
              >
                <span className="text-xl">{style.icon}</span>
                <div className="flex-1 text-left">
                  <div className="font-medium">{style.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {style.description}
                  </div>
                  <div className="flex gap-1 mt-1">
                    {style.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-1.5 py-0.5 bg-secondary rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                {value === style.id && (
                  <Check className="w-4 h-4 text-primary" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

interface StyleCardProps {
  style: WritingStyle;
  selected?: boolean;
  onClick?: () => void;
}

export function StyleCard({ style, selected, onClick }: StyleCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex flex-col items-center gap-2 p-4 rounded-lg border transition-all',
        'hover:border-primary hover:shadow-sm',
        selected && 'border-primary bg-primary/5 shadow-sm'
      )}
    >
      <span className="text-3xl">{style.icon}</span>
      <span className="font-medium text-sm">{style.name}</span>
    </button>
  );
}

interface StyleGridProps {
  value?: string;
  onChange?: (style: WritingStyle) => void;
  platform?: string;
  className?: string;
}

export function StyleGrid({
  value,
  onChange,
  platform,
  className,
}: StyleGridProps) {
  const filteredStyles = platform
    ? writingStyles.filter((s) => s.platform.includes(platform))
    : writingStyles;

  return (
    <div
      className={cn(
        'grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3',
        className
      )}
    >
      {filteredStyles.map((style) => (
        <StyleCard
          key={style.id}
          style={style}
          selected={value === style.id}
          onClick={() => onChange?.(style)}
        />
      ))}
    </div>
  );
}

export default StyleSelector;

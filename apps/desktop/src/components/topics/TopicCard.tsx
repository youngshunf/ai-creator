import { Lightbulb, Lock, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

export type TopicCardVariant = "public" | "private";

export interface TopicCardProps {
  variant: TopicCardVariant;
  title: string;
  potentialScore?: number | null;
  heatIndex?: number | null;
  keywords?: string[] | null;
  trendHint?: string | null;
  onClick?: () => void;
}

export function TopicCard({
  variant,
  title,
  potentialScore,
  heatIndex,
  keywords,
  trendHint,
  onClick,
}: TopicCardProps) {
  const Icon = variant === "private" ? Lock : Lightbulb;
  const chips = (keywords ?? []).filter(Boolean).slice(0, 4);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick?.();
      }}
      className={cn(
        "glass-card group p-4 transition-all duration-200 cursor-pointer",
        "hover:shadow-[var(--shadow-glass)] hover:-translate-y-0.5",
        "focus:outline-none focus:ring-2 focus:ring-primary/30",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "w-8 h-8 rounded-xl flex items-center justify-center shrink-0",
                variant === "private"
                  ? "bg-slate-900/5 dark:bg-white/10"
                  : "bg-primary/10",
              )}
            >
              <Icon
                className={cn(
                  "w-4 h-4",
                  variant === "private"
                    ? "text-slate-600 dark:text-slate-300"
                    : "text-primary",
                )}
              />
            </div>
            <span
              className={cn(
                "text-xs font-medium px-2 py-0.5 rounded-full border",
                variant === "private"
                  ? "bg-white/60 dark:bg-slate-900/30 border-[rgb(var(--color-border))] text-slate-600 dark:text-slate-300"
                  : "bg-primary/5 border-primary/20 text-primary-600 dark:text-primary-400",
              )}
            >
              {variant === "private" ? "私有" : "公共"}
            </span>
          </div>
          <h3 className="mt-2 font-semibold text-base leading-snug text-slate-900 dark:text-slate-100 line-clamp-2">
            {title}
          </h3>
        </div>

        <div className="shrink-0 text-right">
          <div className="text-xs text-muted-foreground">潜力</div>
          <div className="text-sm font-semibold tabular-nums">
            {typeof potentialScore === "number"
              ? potentialScore.toFixed(1)
              : "--"}
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <TrendingUp className="w-4 h-4" />
          <span className="tabular-nums">
            热度 {typeof heatIndex === "number" ? heatIndex.toFixed(1) : "--"}
          </span>
        </div>
        {trendHint && (
          <div className="text-xs text-muted-foreground truncate max-w-[55%]">
            {trendHint}
          </div>
        )}
      </div>

      {chips.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {chips.map((k) => (
            <span
              key={k}
              className="px-2 py-0.5 text-xs rounded-full bg-slate-100/70 dark:bg-slate-800/70 text-slate-600 dark:text-slate-300"
            >
              {k}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

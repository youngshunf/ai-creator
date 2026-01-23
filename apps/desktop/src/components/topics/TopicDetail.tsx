import {
  ArrowLeft,
  Flame,
  ShieldAlert,
  Sparkles,
  Target,
  Tags,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface TopicDetailData {
  title: string;
  potential_score?: number | null;
  heat_index?: number | null;
  reason?: string | null;
  keywords?: string[] | null;
  platform_heat?: Record<string, unknown> | null;
  creative_angles?: string[] | null;
  content_outline?: unknown | null;
  material_clues?: unknown | null;
  risk_notes?: string[] | null;
  heat_sources?: unknown | null;
  trend?: unknown | null;
  industry_tags?: string[] | null;
  target_audience?: unknown | null;
  format_suggestions?: string[] | null;
  source_info?: Record<string, unknown> | null;
  created_at?: string | null;
  created_time?: string | null;
}

export interface TopicDetailProps {
  variant: "public" | "private";
  data: TopicDetailData;
  onBack?: () => void;
}

function toTextList(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.map((v) => String(v)).filter(Boolean);
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => `${k}: ${String(v)}`)
      .filter(Boolean);
  }
  return [String(value)];
}

function toKeyValuePairs(value: unknown): { key: string; value: string }[] {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([k, v]) => ({ key: k, value: String(v) }))
    .filter((x) => x.key);
}

export function TopicDetail({ variant, data, onBack }: TopicDetailProps) {
  const chips = (data.keywords ?? []).filter(Boolean).slice(0, 12);
  const platformPairs = toKeyValuePairs(data.platform_heat);
  const audienceList = toTextList(data.target_audience).slice(0, 12);

  const created = data.created_time ?? data.created_at ?? null;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <button
            onClick={onBack}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-2 rounded-lg border bg-white/60 dark:bg-slate-900/30",
              "hover:bg-white/80 dark:hover:bg-slate-900/40 transition-colors cursor-pointer",
            )}
          >
            <ArrowLeft className="w-4 h-4" />
            返回
          </button>

          <h1 className="mt-4 text-2xl font-heading font-bold leading-tight line-clamp-2">
            {data.title}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "text-xs font-medium px-2 py-0.5 rounded-full border",
                variant === "private"
                  ? "bg-white/60 dark:bg-slate-900/30 border-[rgb(var(--color-border))] text-slate-600 dark:text-slate-300"
                  : "bg-primary/5 border-primary/20 text-primary-600 dark:text-primary-400",
              )}
            >
              {variant === "private" ? "私有选题" : "公共选题"}
            </span>
            {created && (
              <span className="text-xs text-muted-foreground">
                创建于 {new Date(created).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        <div className="glass-card p-4 w-[240px] shrink-0 hidden md:block">
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              潜力分
            </div>
            <div className="text-lg font-bold tabular-nums">
              {typeof data.potential_score === "number"
                ? data.potential_score.toFixed(1)
                : "--"}
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <Flame className="w-4 h-4" />
              热度
            </div>
            <div className="text-lg font-bold tabular-nums">
              {typeof data.heat_index === "number"
                ? data.heat_index.toFixed(1)
                : "--"}
            </div>
          </div>
          <div className="mt-3 text-xs text-muted-foreground">
            {data.reason ? data.reason.slice(0, 64) : "—"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-4 space-y-4">
          <div className="glass-card p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Tags className="w-4 h-4 text-primary" />
              关键词
            </div>
            {chips.length === 0 ? (
              <div className="text-sm text-muted-foreground mt-3">暂无</div>
            ) : (
              <div className="mt-3 flex flex-wrap gap-2">
                {chips.map((k) => (
                  <span
                    key={k}
                    className="px-2.5 py-1 text-xs rounded-full bg-slate-100/70 dark:bg-slate-800/70 text-slate-700 dark:text-slate-200"
                  >
                    {k}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="glass-card p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Target className="w-4 h-4 text-primary" />
              目标人群
            </div>
            {audienceList.length === 0 ? (
              <div className="text-sm text-muted-foreground mt-3">暂无</div>
            ) : (
              <ul className="mt-3 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                {audienceList.map((x, idx) => (
                  <li key={`${x}_${idx}`} className="flex gap-2">
                    <span className="text-muted-foreground">•</span>
                    <span className="flex-1">{x}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="glass-card p-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="w-4 h-4 text-primary" />
              平台热度
            </div>
            {platformPairs.length === 0 ? (
              <div className="text-sm text-muted-foreground mt-3">暂无</div>
            ) : (
              <div className="mt-3 space-y-2">
                {platformPairs.slice(0, 10).map((p) => (
                  <div
                    key={p.key}
                    className="flex items-center justify-between gap-3"
                  >
                    <div className="text-sm text-slate-700 dark:text-slate-200 truncate">
                      {p.key}
                    </div>
                    <div className="text-xs text-muted-foreground truncate max-w-[60%]">
                      {p.value}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-8 space-y-4">
          <div className="glass-card p-5">
            <div className="text-sm font-semibold">推荐理由</div>
            <div className="mt-2 text-sm text-slate-700 dark:text-slate-200 whitespace-pre-wrap">
              {data.reason || "暂无"}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-card p-5">
              <div className="text-sm font-semibold">创作角度</div>
              <div className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                {(data.creative_angles ?? []).length === 0 ? (
                  <div className="text-muted-foreground">暂无</div>
                ) : (
                  (data.creative_angles ?? []).slice(0, 12).map((x, idx) => (
                    <div key={`${x}_${idx}`} className="flex gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span className="flex-1">{x}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="glass-card p-5">
              <div className="text-sm font-semibold">形式建议</div>
              <div className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-200">
                {(data.format_suggestions ?? []).length === 0 ? (
                  <div className="text-muted-foreground">暂无</div>
                ) : (
                  (data.format_suggestions ?? []).slice(0, 12).map((x, idx) => (
                    <div key={`${x}_${idx}`} className="flex gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span className="flex-1">{x}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="glass-card p-5">
            <div className="text-sm font-semibold">内容大纲</div>
            <div className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-200">
              {toTextList(data.content_outline).length === 0 ? (
                <div className="text-muted-foreground">暂无</div>
              ) : (
                toTextList(data.content_outline)
                  .slice(0, 30)
                  .map((x, idx) => (
                    <div key={`${x}_${idx}`} className="flex gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span className="flex-1">{x}</span>
                    </div>
                  ))
              )}
            </div>
          </div>

          <div className="glass-card p-5">
            <div className="text-sm font-semibold">素材线索</div>
            <div className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-200">
              {toTextList(data.material_clues).length === 0 ? (
                <div className="text-muted-foreground">暂无</div>
              ) : (
                toTextList(data.material_clues)
                  .slice(0, 30)
                  .map((x, idx) => (
                    <div key={`${x}_${idx}`} className="flex gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span className="flex-1">{x}</span>
                    </div>
                  ))
              )}
            </div>
          </div>

          <div className="glass-card p-5 border border-amber-200/60 bg-amber-50/40 dark:bg-amber-900/10">
            <div className="flex items-center gap-2 text-sm font-semibold text-amber-800 dark:text-amber-200">
              <ShieldAlert className="w-4 h-4" />
              风险提示
            </div>
            <div className="mt-2 space-y-1 text-sm text-amber-900/90 dark:text-amber-100/90">
              {(data.risk_notes ?? []).length === 0 ? (
                <div className="text-amber-800/70 dark:text-amber-200/70">
                  暂无
                </div>
              ) : (
                (data.risk_notes ?? []).slice(0, 12).map((x, idx) => (
                  <div key={`${x}_${idx}`} className="flex gap-2">
                    <span className="text-amber-700/70 dark:text-amber-200/70">
                      •
                    </span>
                    <span className="flex-1">{x}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

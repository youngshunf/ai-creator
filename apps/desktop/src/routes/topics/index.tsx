import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw, Search, SlidersHorizontal, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/common/Toast";
import { useProjectStore } from "@/stores/useProjectStore";
import {
  getIndustriesApi,
  getSysTopicRecommendationsApi,
  type IndustryNode,
  type SysTopic,
} from "@/api/topic";
import { getProjectTopicsApi, type ProjectTopic } from "@/api/projectTopic";
import { TopicCard } from "@/components/topics/TopicCard";
import { GenerateTopicsDialog } from "@/components/topics/GenerateTopicsDialog";

export const Route = createFileRoute("/topics/")({
  component: TopicsCenterPage,
});

type TabKey = "public" | "private";

function TopicsCenterPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { currentProject } = useProjectStore();
  const queryClient = useQueryClient();

  const [tab, setTab] = useState<TabKey>("public");
  const [keyword, setKeyword] = useState("");
  const [industryId, setIndustryId] = useState<number | "all">("all");
  const [privateStatus, setPrivateStatus] = useState<number | "all">("all");
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);

  const industriesQuery = useQuery({
    queryKey: ["topicIndustries"],
    queryFn: () => getIndustriesApi(),
    enabled: tab === "public",
  });

  const sysTopicsQuery = useQuery({
    queryKey: ["sysTopicRecommendations", industryId],
    queryFn: () =>
      getSysTopicRecommendationsApi({
        industry_id: industryId === "all" ? undefined : industryId,
        limit: 50,
      }),
    enabled: tab === "public",
  });

  const projectTopicsQuery = useQuery({
    queryKey: ["projectTopics", currentProject?.id],
    queryFn: () => getProjectTopicsApi(currentProject?.id as string),
    enabled: tab === "private" && !!currentProject?.id,
  });

  const flatIndustries = useMemo(() => {
    const result: { id: number; name: string }[] = [];
    const walk = (nodes: IndustryNode[], depth: number) => {
      for (const n of nodes) {
        result.push({
          id: n.id,
          name: `${"—".repeat(Math.min(depth, 4))}${depth > 0 ? " " : ""}${n.name}`,
        });
        if (n.children?.length) walk(n.children, depth + 1);
      }
    };
    if (industriesQuery.data) walk(industriesQuery.data, 0);
    return result;
  }, [industriesQuery.data]);

  const sysTopics = useMemo(() => {
    const list: SysTopic[] = sysTopicsQuery.data ?? [];
    const kw = keyword.trim().toLowerCase();
    if (!kw) return list;
    return list.filter((t) => {
      const titleHit = t.title.toLowerCase().includes(kw);
      const keywordHit = (t.keywords ?? []).some((k) =>
        String(k).toLowerCase().includes(kw),
      );
      return titleHit || keywordHit;
    });
  }, [sysTopicsQuery.data, keyword]);

  const projectTopics = useMemo(() => {
    const list: ProjectTopic[] = projectTopicsQuery.data ?? [];
    const kw = keyword.trim().toLowerCase();
    return list
      .filter((t) =>
        privateStatus === "all" ? true : t.status === privateStatus,
      )
      .filter((t) => {
        if (!kw) return true;
        const titleHit = t.title.toLowerCase().includes(kw);
        const keywordHit = (t.keywords ?? []).some((k) =>
          String(k).toLowerCase().includes(kw),
        );
        return titleHit || keywordHit;
      });
  }, [projectTopicsQuery.data, privateStatus, keyword]);

  const isLoading =
    tab === "public" ? sysTopicsQuery.isLoading : projectTopicsQuery.isLoading;
  const isError =
    tab === "public" ? sysTopicsQuery.isError : projectTopicsQuery.isError;
  const error =
    tab === "public" ? sysTopicsQuery.error : projectTopicsQuery.error;

  const handleRefresh = async () => {
    try {
      if (tab === "public") {
        await Promise.all([
          industriesQuery.refetch(),
          sysTopicsQuery.refetch(),
        ]);
      } else {
        await projectTopicsQuery.refetch();
      }
      toast.success("已刷新", "选题列表已更新");
    } catch (e) {
      toast.error("刷新失败", String(e));
    }
  };

  const headerHint =
    tab === "public"
      ? "从云端推荐库获取热点选题，支持行业筛选与关键词检索"
      : "项目私有选题库，可同步云端并支持一键生成";

  const listEmpty =
    tab === "public" ? sysTopics.length === 0 : projectTopics.length === 0;

  const showCloudIdHint = tab === "private" && !currentProject?.id;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold">选题中心</h1>
          <p className="text-sm text-muted-foreground mt-1">{headerHint}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className={cn(
              "px-3 py-2 rounded-lg border bg-white/60 dark:bg-slate-900/30",
              "hover:bg-white/80 dark:hover:bg-slate-900/40 transition-colors flex items-center gap-2 cursor-pointer",
            )}
          >
            <RefreshCcw className="w-4 h-4" />
            <span className="text-sm font-medium">刷新</span>
          </button>

          {tab === "private" && (
            <button
              onClick={() => {
                if (!currentProject) {
                  toast.warning("无法生成", "请先选择一个项目");
                  return;
                }
                setShowGenerateDialog(true);
              }}
              className={cn(
                "btn-primary flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer",
              )}
            >
              <Sparkles className="w-4 h-4" />
              生成选题
            </button>
          )}
        </div>
      </div>

      <div className="glass-card p-2 flex items-center justify-between gap-3">
        <div className="flex p-0.5 bg-slate-100/80 dark:bg-slate-800 rounded-lg">
          {[
            { key: "public" as const, label: "公共选题" },
            { key: "private" as const, label: "私有选题" },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all duration-150 cursor-pointer",
                tab === t.key
                  ? "bg-white dark:bg-slate-700 text-primary-600 dark:text-primary-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 flex-1 justify-end">
          <div className="relative w-[320px] max-w-full">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="搜索标题/关键词..."
              className={cn(
                "w-full pl-9 pr-3 py-2 rounded-lg border bg-white/70 dark:bg-slate-900/30",
                "text-sm outline-none focus:ring-2 focus:ring-primary/30",
              )}
            />
          </div>

          {tab === "public" && (
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-muted-foreground" />
              <select
                value={industryId}
                onChange={(e) =>
                  setIndustryId(
                    e.target.value === "all" ? "all" : Number(e.target.value),
                  )
                }
                className={cn(
                  "px-3 py-2 rounded-lg border bg-white/70 dark:bg-slate-900/30 text-sm cursor-pointer",
                  "outline-none focus:ring-2 focus:ring-primary/30",
                )}
              >
                <option value="all">全部行业</option>
                {flatIndustries.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {tab === "private" && (
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-muted-foreground" />
              <select
                value={privateStatus}
                onChange={(e) =>
                  setPrivateStatus(
                    e.target.value === "all" ? "all" : Number(e.target.value),
                  )
                }
                className={cn(
                  "px-3 py-2 rounded-lg border bg-white/70 dark:bg-slate-900/30 text-sm cursor-pointer",
                  "outline-none focus:ring-2 focus:ring-primary/30",
                )}
              >
                <option value="all">全部状态</option>
                <option value={0}>待选</option>
                <option value={1}>已采纳</option>
                <option value={2}>已忽略</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {showCloudIdHint && (
        <div className="glass-card p-4 border border-amber-200/60 bg-amber-50/40 dark:bg-amber-900/10">
          <div className="text-sm text-amber-800 dark:text-amber-200 font-medium">
            当前项目尚未同步到云端
          </div>
          <div className="text-xs text-amber-700/90 dark:text-amber-200/80 mt-1">
            请先在「设置-数据同步」执行一次同步，或等待自动同步完成后再查看私有选题。
          </div>
        </div>
      )}

      {isError && (
        <div className="glass-card p-4 border border-red-200/60 bg-red-50/40 dark:bg-red-900/10">
          <div className="text-sm font-medium text-red-700 dark:text-red-200">
            加载失败
          </div>
          <div className="text-xs text-red-700/80 dark:text-red-200/80 mt-1">
            {String(error)}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {isLoading &&
          Array.from({ length: 9 }).map((_, idx) => (
            <div key={idx} className="glass-card p-4 animate-pulse h-[132px]" />
          ))}

        {!isLoading &&
          tab === "public" &&
          sysTopics.map((t) => (
            <TopicCard
              key={t.id}
              variant="public"
              title={t.title}
              potentialScore={t.potential_score}
              heatIndex={t.heat_index}
              keywords={t.keywords}
              trendHint={
                typeof t.trend === "object" &&
                t.trend &&
                !Array.isArray(t.trend)
                  ? (t.trend as any).summary
                  : null
              }
              onClick={() => navigate({ to: `/topics/public/${String(t.id)}` })}
            />
          ))}

        {!isLoading &&
          tab === "private" &&
          projectTopics.map((t) => (
            <TopicCard
              key={t.id}
              variant="private"
              title={t.title}
              potentialScore={t.potential_score}
              heatIndex={t.heat_index}
              keywords={t.keywords}
              onClick={() =>
                navigate({ to: `/topics/private/${encodeURIComponent(t.id)}` })
              }
            />
          ))}
      </div>

      {!isLoading && listEmpty && !isError && (
        <div className="glass-card p-10 text-center">
          <div className="text-sm font-medium">暂无选题</div>
          <div className="text-xs text-muted-foreground mt-1">
            {tab === "public"
              ? "试试切换行业或调整关键词"
              : "可以先生成一批项目私有选题，或等待同步拉取"}
          </div>
        </div>
      )}

      <GenerateTopicsDialog
        open={showGenerateDialog}
        projectId={currentProject?.id ?? ""}
        onClose={() => setShowGenerateDialog(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["projectTopics"] });
        }}
      />
    </div>
  );
}

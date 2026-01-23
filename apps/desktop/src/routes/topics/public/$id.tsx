import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { getSysTopicRecommendationsApi, type SysTopic } from "@/api/topic";
import { TopicDetail } from "@/components/topics/TopicDetail";
import { useToast } from "@/components/common/Toast";

export const Route = createFileRoute("/topics/public/$id")({
  component: PublicTopicDetailPage,
});

function PublicTopicDetailPage() {
  const { id } = Route.useParams();
  const topicId = Number(id);
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  const cached = useMemo(() => {
    const hits = queryClient.getQueriesData<SysTopic[]>({
      queryKey: ["sysTopicRecommendations"],
    });
    for (const [, data] of hits) {
      const found = (data ?? []).find((t) => t.id === topicId);
      if (found) return found;
    }
    return undefined;
  }, [queryClient, topicId]);

  const query = useQuery({
    queryKey: ["sysTopicDetail", topicId],
    enabled: Number.isFinite(topicId) && topicId > 0,
    initialData: cached,
    queryFn: async () => {
      const list = await getSysTopicRecommendationsApi({ limit: 200 });
      const found = list.find((t) => t.id === topicId);
      if (!found) throw new Error("选题不存在或已被移除");
      return found;
    },
  });

  if (query.isLoading) {
    return <div className="glass-card p-6 animate-pulse h-[240px]" />;
  }

  if (query.isError || !query.data) {
    return (
      <div className="glass-card p-6">
        <div className="text-sm font-medium">加载失败</div>
        <div className="text-xs text-muted-foreground mt-1">
          {String(query.error)}
        </div>
        <button
          onClick={() => {
            toast.info("返回列表");
            navigate({ to: "/topics" });
          }}
          className="btn-primary mt-4"
        >
          返回
        </button>
      </div>
    );
  }

  return (
    <TopicDetail
      variant="public"
      data={query.data}
      onBack={() => navigate({ to: "/topics" })}
    />
  );
}

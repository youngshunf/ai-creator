import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getProjectTopicsApi, type ProjectTopic } from "@/api/projectTopic";
import { TopicDetail } from "@/components/topics/TopicDetail";
import { useProjectStore } from "@/stores/useProjectStore";

export const Route = createFileRoute("/topics/private/$uuid")({
  component: PrivateTopicDetailPage,
});

function PrivateTopicDetailPage() {
  const { uuid } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { currentProject } = useProjectStore();
  const projectId = currentProject?.id || null;

  const cached = useMemo(() => {
    if (!projectId) return undefined;
    const list = queryClient.getQueryData<ProjectTopic[]>([
      "projectTopics",
      projectId,
    ]);
    return list?.find((t) => t.id === uuid);
  }, [queryClient, projectId, uuid]);

  const query = useQuery({
    queryKey: ["projectTopicDetail", projectId, uuid],
    enabled: !!projectId && !!uuid,
    initialData: cached,
    queryFn: async () => {
      const list = await getProjectTopicsApi(projectId as string);
      const found = list.find((t) => t.id === uuid);
      if (!found) throw new Error("选题不存在或未同步到云端");
      return found;
    },
  });

  if (!projectId) {
    return (
      <div className="glass-card p-6">
        <div className="text-sm font-medium">当前项目尚未同步到云端</div>
        <div className="text-xs text-muted-foreground mt-1">
          请先完成一次数据同步后再查看私有选题详情。
        </div>
        <button
          onClick={() => navigate({ to: "/topics" })}
          className="btn-primary mt-4"
        >
          返回
        </button>
      </div>
    );
  }

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
          onClick={() => navigate({ to: "/topics" })}
          className="btn-primary mt-4"
        >
          返回
        </button>
      </div>
    );
  }

  return (
    <TopicDetail
      variant="private"
      data={query.data}
      onBack={() => navigate({ to: "/topics" })}
    />
  );
}

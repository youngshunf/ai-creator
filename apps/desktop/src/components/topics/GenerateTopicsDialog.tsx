import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Loader2, Sparkles, X } from "lucide-react";
import { useToast } from "@/components/common/Toast";
import { useAuthStore } from "@/stores/useAuthStore";
import { cn } from "@/lib/utils";

interface GenerateTopicsDialogProps {
  open: boolean;
  projectId: string;
  onClose: () => void;
  onSuccess?: (count: number) => void;
}

export function GenerateTopicsDialog({
  open,
  projectId,
  onClose,
  onSuccess,
}: GenerateTopicsDialogProps) {
  const toast = useToast();
  const { user, token } = useAuthStore();

  const [baseUrl, setBaseUrl] = useState("");
  const [endpointPath, setEndpointPath] = useState("/api/hot-topics");
  const [payloadMode, setPayloadMode] = useState("trendradar");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const storageKey = useMemo(() => "topic_center.trendradar_base_url", []);

  useEffect(() => {
    if (!open) return;
    const saved = localStorage.getItem(storageKey);
    if (saved) setBaseUrl(saved);
  }, [open, storageKey]);

  if (!open) return null;

  const handleGenerate = async () => {
    const trimmed = baseUrl.trim();
    if (!projectId || !projectId.trim()) {
      toast.warning("无法生成", "请先选择一个项目");
      return;
    }
    if (!trimmed) {
      toast.warning("缺少配置", "TrendRadar Base URL 不能为空");
      return;
    }

    setIsLoading(true);
    try {
      localStorage.setItem(storageKey, trimmed);

      const result = await invoke<any[]>("generate_project_topics", {
        projectId,
        trendradarBaseUrl: trimmed,
        trendradarEndpointPath: endpointPath?.trim()
          ? endpointPath.trim()
          : null,
        trendradarPayloadMode: payloadMode?.trim() ? payloadMode.trim() : null,
      });

      const count = Array.isArray(result) ? result.length : 0;
      toast.success("生成成功", `已生成 ${count} 条私有选题`);
      onSuccess?.(count);

      if (user?.uuid && token) {
        invoke("start_sync", { userId: String(user.uuid), token }).catch(
          () => {},
        );
      }

      onClose();
    } catch (e) {
      toast.error("生成失败", String(e));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-lg glass-card p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">生成私有选题</h2>
            <p className="text-sm text-muted-foreground">
              基于当前项目关键词，从热点数据源生成一批可用选题
            </p>
          </div>
        </div>

        <div className="mt-5 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">TrendRadar Base URL</label>
            <input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="例如：https://your-trendradar.example.com"
              className={cn(
                "w-full px-3 py-2 rounded-lg border bg-white/70 dark:bg-slate-900/30 text-sm",
                "outline-none focus:ring-2 focus:ring-primary/30",
              )}
            />
          </div>

          <button
            onClick={() => setShowAdvanced((v) => !v)}
            className="text-sm text-primary-600 dark:text-primary-400 hover:underline cursor-pointer"
          >
            {showAdvanced ? "收起高级选项" : "展开高级选项"}
          </button>

          {showAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Endpoint Path</label>
                <input
                  value={endpointPath}
                  onChange={(e) => setEndpointPath(e.target.value)}
                  className={cn(
                    "w-full px-3 py-2 rounded-lg border bg-white/70 dark:bg-slate-900/30 text-sm",
                    "outline-none focus:ring-2 focus:ring-primary/30",
                  )}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Payload Mode</label>
                <input
                  value={payloadMode}
                  onChange={(e) => setPayloadMode(e.target.value)}
                  className={cn(
                    "w-full px-3 py-2 rounded-lg border bg-white/70 dark:bg-slate-900/30 text-sm",
                    "outline-none focus:ring-2 focus:ring-primary/30",
                  )}
                />
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            disabled={isLoading}
            className={cn(
              "px-4 py-2 rounded-lg border bg-white/60 dark:bg-slate-900/30 text-sm font-medium cursor-pointer",
              isLoading && "opacity-70 cursor-not-allowed",
            )}
          >
            取消
          </button>
          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className={cn(
              "btn-primary px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 cursor-pointer",
              isLoading && "opacity-70 cursor-not-allowed",
            )}
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            生成并同步
          </button>
        </div>
      </div>
    </div>
  );
}

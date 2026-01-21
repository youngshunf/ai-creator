/**
 * 添加账号对话框组件
 * @author Ysf
 */
import { useState, useRef } from "react";
import { X, Loader2, AlertTriangle } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import {
  useAccountStore,
  Platform,
  PlatformInfo,
} from "@/stores/useAccountStore";

interface AddAccountDialogProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  onSuccess?: () => void;
}

/**
 * 校验 projectId 是否有效
 */
function isValidProjectId(projectId: string | undefined | null): boolean {
  return !!projectId && projectId.trim().length > 0;
}

export function AddAccountDialog({
  open,
  onClose,
  projectId,
  onSuccess,
}: AddAccountDialogProps) {
  const { platforms, addAccount, syncAccount } = useAccountStore();
  const [step, setStep] = useState<"select" | "login">("select");
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformInfo | null>(
    null,
  );
  const [loginStatus, setLoginStatus] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const accountIdRef = useRef<string>("");

  // 校验项目 ID
  const hasValidProject = isValidProjectId(projectId);

  if (!open) return null;

  // 如果没有有效的 projectId，显示警告
  if (!hasValidProject) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />
        <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md p-6">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="text-center py-4">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-amber-600 dark:text-amber-400" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              无法添加账号
            </h2>
            <p className="text-slate-600 dark:text-slate-300 mb-4">
              请先创建或选择一个项目，然后再添加账号。
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              项目是组织账号和内容的基础单元。
            </p>
          </div>

          <button
            onClick={onClose}
            className="w-full mt-4 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors"
          >
            我知道了
          </button>
        </div>
      </div>
    );
  }

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const handleSelectPlatform = async (platform: PlatformInfo) => {
    // 先更新 UI 状态
    setSelectedPlatform(platform);
    setStep("login");
    setIsLoading(true);
    setLoginStatus("正在打开登录页面...");

    // 等待 UI 渲染完成后再打开浏览器，避免 UI 阻塞
    await new Promise((resolve) => setTimeout(resolve, 100));

    try {
      // 调用 Tauri command 启动浏览器登录
      console.log("[LOGIN] 调用 start_platform_login:", platform.name);
      const result = await invoke<{
        status: string;
        account_id: string;
        message: string;
      }>("start_platform_login", {
        platform: platform.name,
      });
      console.log("[LOGIN] start_platform_login 返回:", result);

      if (result.status === "error") {
        setIsLoading(false);
        setLoginStatus(`启动失败: ${result.message}`);
        return;
      }

      // 保存 account_id 用于后续轮询
      accountIdRef.current = result.account_id;
      console.log("[LOGIN] 保存 account_id:", accountIdRef.current);
      setLoginStatus("请在浏览器中完成登录...");

      // 轮询检查登录状态
      pollingRef.current = setInterval(async () => {
        console.log(
          "[LOGIN] 轮询检查登录状态, platform:",
          platform.name,
          "accountId:",
          accountIdRef.current,
        );
        try {
          const status = await invoke<{
            status: string;
            logged_in: boolean;
            account_id?: string;
            account_name?: string;
            avatar_url?: string;
            followers_count?: number;
            message?: string;
          }>("check_platform_login_status", {
            platform: platform.name,
            accountId: accountIdRef.current,
          });
          console.log("[LOGIN] check_platform_login_status 返回:", status);

          if (status.status === "success" && status.logged_in) {
            stopPolling();
            const accountName = status.account_name || "未知账号";
            setLoginStatus("正在保存账号...");

            // 1. 先保存账号基本信息
            const newAccount = await addAccount(
              projectId,
              platform.name as Platform,
              status.account_id || accountIdRef.current,
              accountName,
              {
                avatar_url: status.avatar_url,
                followers_count: status.followers_count,
              },
            );

            // 2. 关闭登录浏览器（登录成功后不再需要）
            setLoginStatus("正在关闭登录窗口...");
            try {
              await invoke("close_login_browser", {
                platform: platform.name,
                accountId: accountIdRef.current,
              });
              console.log("[LOGIN] 登录浏览器已关闭");
            } catch (closeErr) {
              console.warn("[LOGIN] 关闭登录浏览器失败:", closeErr);
            }

            // 3. 后台静默同步账号资料（不阻塞 UI）
            setLoginStatus("账号添加成功！");
            // 异步同步，不等待结果
            syncAccount(newAccount.id)
              .then(() => {
                console.log("[LOGIN] 账号资料同步完成");
                // 刷新列表
                onSuccess?.();
              })
              .catch((syncErr) => {
                console.warn("[LOGIN] 同步账号资料失败:", syncErr);
                onSuccess?.(); // 即使同步失败也刷新，显示基本信息
              });

            setIsLoading(false);
            setTimeout(() => handleClose(), 800);
          } else if (status.status === "error") {
            stopPolling();
            setIsLoading(false);
            console.error("[LOGIN] 登录检查返回错误:", status.message);
            setLoginStatus(`登录失败: ${status.message || "未知错误"}`);
          }
          // status === 'pending' 继续轮询
        } catch (e) {
          console.error("[LOGIN] 轮询异常:", e);
          stopPolling();
          setIsLoading(false);
          setLoginStatus(`检查状态失败: ${e}`);
        }
      }, 2000);
    } catch (e) {
      console.error("[LOGIN] 启动登录异常:", e);
      setIsLoading(false);
      setLoginStatus(`登录失败: ${e}`);
    }
  };

  const handleClose = () => {
    stopPolling();
    accountIdRef.current = "";
    setStep("select");
    setSelectedPlatform(null);
    setLoginStatus("");
    setIsLoading(false);
    onClose();
  };

  const platformIcons: Record<string, { bg: string; text: string }> = {
    xiaohongshu: { bg: "bg-red-500", text: "书" },
    wechat: { bg: "bg-green-500", text: "微" },
    douyin: { bg: "bg-black", text: "抖" },
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />
      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md p-6">
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">
          {step === "select"
            ? "选择平台"
            : `登录 ${selectedPlatform?.display_name}`}
        </h2>

        {step === "select" ? (
          <div className="space-y-3">
            {platforms.map((platform) => {
              const icon = platformIcons[platform.name] || {
                bg: "bg-slate-500",
                text: "?",
              };
              return (
                <button
                  key={platform.name}
                  onClick={() => handleSelectPlatform(platform)}
                  className="w-full flex items-center gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-primary-500 dark:hover:border-primary-500 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                >
                  <div
                    className={`w-10 h-10 rounded-full ${icon.bg} flex items-center justify-center text-white font-bold text-sm`}
                  >
                    {icon.text}
                  </div>
                  <div className="text-left">
                    <div className="font-medium text-slate-900 dark:text-white">
                      {platform.display_name}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      标题 {platform.spec.title_max_length} 字 · 正文{" "}
                      {platform.spec.content_max_length} 字 ·{" "}
                      {platform.spec.image_max_count} 张图
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            {isLoading ? (
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-500 mb-4" />
            ) : (
              <div
                className={`w-16 h-16 rounded-full ${platformIcons[selectedPlatform?.name || ""]?.bg || "bg-slate-500"} flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4`}
              >
                {platformIcons[selectedPlatform?.name || ""]?.text || "?"}
              </div>
            )}
            <p className="text-slate-600 dark:text-slate-300">{loginStatus}</p>
            <button
              onClick={() => setStep("select")}
              className="mt-4 text-sm text-primary-500 hover:text-primary-600"
            >
              返回选择平台
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

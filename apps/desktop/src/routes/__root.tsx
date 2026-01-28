/**
 * 根路由布局 - 带认证保护
 * @author Ysf
 */
import {
  createRootRoute,
  Outlet,
  useNavigate,
  useLocation,
} from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";
import { useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { MainLayout } from "@/components/layout/MainLayout";
import { useAuthStore } from "@/stores/useAuthStore";

function RootComponent() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, token } = useAuthStore();

  useEffect(() => {
    // 未登录且不在登录页，跳转到登录页
    if (!isAuthenticated && location.pathname !== "/login") {
      navigate({ to: "/login" });
    }
  }, [isAuthenticated, location.pathname, navigate]);

  useEffect(() => {
    // 监听后台同步错误事件
    const unlistenPromise = listen<string>("sync-error", (event) => {
      console.error("[Sync] Received sync-error event:", event.payload);
      const errStr = String(event.payload);
      if (errStr.includes("401") || errStr.includes("Token 已过期")) {
        console.log("[Sync] Token expired, logging out...");
        useAuthStore.getState().logout();
        navigate({ to: "/login" });
      }
    });

    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  }, [navigate]);

  useEffect(() => {
    // 自动同步逻辑
    if (isAuthenticated && user?.uuid && token) {
      console.log("[AutoSync] Starting auto-sync...");
      // 调用 Rust 后端命令 start_sync
      invoke("start_sync", { userId: String(user.uuid), token: token })
        .then(() => console.log("[AutoSync] Sync started successfully"))
        .catch((e) => {
          console.error("[AutoSync] Failed to start sync:", e);
          const errStr = String(e);
          if (errStr.includes("401") || errStr.includes("Token 已过期")) {
            useAuthStore.getState().logout();
            navigate({ to: "/login" });
          }
        });
    }
  }, [isAuthenticated, user?.uuid, token]);

  // 登录页不使用主布局
  if (location.pathname === "/login") {
    return (
      <>
        <Outlet />
        {import.meta.env.DEV && <TanStackRouterDevtools />}
      </>
    );
  }

  return (
    <MainLayout>
      <Outlet />
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </MainLayout>
  );
}

export const Route = createRootRoute({
  component: RootComponent,
});

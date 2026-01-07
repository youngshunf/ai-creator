/**
 * 根路由布局 - 带认证保护
 * @author Ysf
 */
import { createRootRoute, Outlet, useNavigate, useLocation } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';
import { useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { useAuthStore } from '@/stores/useAuthStore';

function RootComponent() {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    // 未登录且不在登录页，跳转到登录页
    if (!isAuthenticated && location.pathname !== '/login') {
      navigate({ to: '/login' });
    }
  }, [isAuthenticated, location.pathname, navigate]);

  // 登录页不使用主布局
  if (location.pathname === '/login') {
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

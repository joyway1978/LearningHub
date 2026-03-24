'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

// 公开路由配置
const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
];

// 只读页面（不需要登录但可以访问）
const READONLY_ROUTES = [
  '/',
];

interface ProtectedRouteProps {
  children: React.ReactNode;
  // 允许自定义公开路由
  customPublicRoutes?: string[];
  // 是否需要登录（默认为true）
  requireAuth?: boolean;
}

export function ProtectedRoute({
  children,
  customPublicRoutes = [],
  requireAuth = true,
}: ProtectedRouteProps) {
  const { isLoggedIn, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isReady, setIsReady] = useState(false);

  // 合并公开路由
  const allPublicRoutes = [...PUBLIC_ROUTES, ...READONLY_ROUTES, ...customPublicRoutes];

  // 检查当前路由是否为公开路由
  const isPublicRoute = allPublicRoutes.some((route) => {
    if (route === pathname) return true;
    // 支持通配符匹配，如 /materials/*
    if (route.endsWith('/*')) {
      const baseRoute = route.slice(0, -2);
      return pathname.startsWith(baseRoute);
    }
    return false;
  });

  // 检查是否需要重定向
  const shouldRedirect = requireAuth && !isPublicRoute && !isLoggedIn;

  useEffect(() => {
    // 等待认证状态加载完成
    if (isLoading) return;

    // 如果需要登录但未登录，重定向到登录页
    if (shouldRedirect) {
      const currentUrl = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : '');
      const loginUrl = `/login?redirect=${encodeURIComponent(currentUrl)}`;
      router.push(loginUrl);
      return;
    }

    // 如果已登录但访问登录/注册页，重定向到首页
    if (isLoggedIn && (pathname === '/login' || pathname === '/register')) {
      const redirect = searchParams.get('redirect');
      router.push(redirect || '/');
      return;
    }

    setIsReady(true);
  }, [isLoading, isLoggedIn, pathname, searchParams, router, shouldRedirect]);

  // 加载中显示加载动画
  if (isLoading || (!isReady && shouldRedirect)) {
    return (
      <div className="min-h-screen bg-[#fafaf9] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#1a1a2e]"></div>
          <p className="mt-4 text-sm text-[#78716c]">加载中...</p>
        </div>
      </div>
    );
  }

  // 需要登录但未登录，不渲染内容（正在重定向）
  if (shouldRedirect) {
    return null;
  }

  return <>{children}</>;
}

// 高阶组件版本，用于包装单个页面
export function withProtectedRoute<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options?: {
    requireAuth?: boolean;
    publicRoutes?: string[];
  }
): React.FC<P> {
  return function WithProtectedRouteComponent(props: P) {
    return (
      <ProtectedRoute
        requireAuth={options?.requireAuth ?? true}
        customPublicRoutes={options?.publicRoutes}
      >
        <WrappedComponent {...props} />
      </ProtectedRoute>
    );
  };
}

// 检查路由是否为公开路由的辅助函数
export function isPublicRoute(pathname: string, customRoutes: string[] = []): boolean {
  const allPublicRoutes = [...PUBLIC_ROUTES, ...READONLY_ROUTES, ...customRoutes];

  return allPublicRoutes.some((route) => {
    if (route === pathname) return true;
    if (route.endsWith('/*')) {
      const baseRoute = route.slice(0, -2);
      return pathname.startsWith(baseRoute);
    }
    return false;
  });
}

// 获取重定向URL的辅助函数
export function getRedirectUrl(
  pathname: string,
  searchParams: URLSearchParams
): string {
  const currentUrl = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : '');
  return `/login?redirect=${encodeURIComponent(currentUrl)}`;
}

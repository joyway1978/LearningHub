'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { User, TokenResponse, UserLoginRequest, UserRegisterRequest } from '@/types';
import { api } from '@/lib/api';
import {
  getToken,
  setToken,
  setRefreshToken,
  removeToken,
  isAuthenticated,
} from '@/lib/auth';
import { logAuth } from '@/lib/logger';

// Context类型定义
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isLoggedIn: boolean;
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (data: UserRegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
}

// 创建Context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider Props
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // 获取当前用户信息
  const fetchCurrentUser = useCallback(async () => {
    try {
      const userData = await api.get<User>('/auth/me');
      setUser(userData);
      setIsLoggedIn(true);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      setUser(null);
      setIsLoggedIn(false);
      removeToken();
    }
  }, []);

  // 初始化时检查登录状态
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      try {
        if (isAuthenticated()) {
          await fetchCurrentUser();
        } else {
          setUser(null);
          setIsLoggedIn(false);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [fetchCurrentUser]);

  // 登录
  const login = async (credentials: UserLoginRequest) => {
    setIsLoading(true);
    logAuth('login', undefined, { email: credentials.email, source: 'auth_context', rememberMe: credentials.rememberMe });

    try {
      const response = await api.post<TokenResponse>('/auth/login', credentials);

      // 根据"记住我"选项选择存储方式
      const rememberMe = credentials.rememberMe ?? true;
      setToken(response.access_token, rememberMe);
      logAuth('login', undefined, { email: credentials.email, source: 'auth_context', step: 'token_saved', storage: rememberMe ? 'localStorage' : 'sessionStorage' });

      if (response.refresh_token) {
        setRefreshToken(response.refresh_token, rememberMe);
      }

      await fetchCurrentUser();
      logAuth('login', undefined, { email: credentials.email, source: 'auth_context', step: 'user_fetched', isLoggedIn: true });
    } catch (error) {
      logAuth('login', undefined, {
        email: credentials.email,
        source: 'auth_context',
        step: 'error',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 注册
  const register = async (data: UserRegisterRequest) => {
    setIsLoading(true);
    logAuth('register', undefined, { email: data.email, source: 'auth_context' });

    try {
      const response = await api.post<TokenResponse>('/auth/register', data);

      logAuth('register', undefined, {
        email: data.email,
        source: 'auth_context',
        step: 'api_response_received',
        hasAccessToken: !!response.access_token,
        hasRefreshToken: !!response.refresh_token
      });

      setToken(response.access_token);
      logAuth('register', undefined, { email: data.email, source: 'auth_context', step: 'token_saved' });

      if (response.refresh_token) {
        setRefreshToken(response.refresh_token);
        logAuth('register', undefined, { email: data.email, source: 'auth_context', step: 'refresh_token_saved' });
      }

      await fetchCurrentUser();
      logAuth('register', undefined, { email: data.email, source: 'auth_context', step: 'user_fetched', isLoggedIn: true });
    } catch (error) {
      logAuth('register', undefined, {
        email: data.email,
        source: 'auth_context',
        step: 'error',
        error: error instanceof Error ? error.message : String(error)
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 登出
  const logout = useCallback(() => {
    // 可选：调用后端登出接口使token失效
    api.post('/auth/logout').catch(console.error);

    removeToken();
    setUser(null);
    setIsLoggedIn(false);
  }, []);

  // 刷新用户信息
  const refreshUser = useCallback(async () => {
    if (isAuthenticated()) {
      await fetchCurrentUser();
    }
  }, [fetchCurrentUser]);

  // 更新本地用户信息
  const updateUser = useCallback((userData: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...userData } : null));
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isLoggedIn,
    login,
    register,
    logout,
    refreshUser,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// 自定义Hook
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// 高阶组件：需要登录才能访问
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> {
  return function WithAuthComponent(props: P) {
    const { isLoggedIn, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (!isLoggedIn) {
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}

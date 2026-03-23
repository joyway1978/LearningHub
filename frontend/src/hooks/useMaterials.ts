'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import { Material, PaginatedResponse, MaterialType } from '@/types';

type SortByType = 'created_at' | 'view_count' | 'like_count' | 'download_count';
type SortOrderType = 'asc' | 'desc';

interface UseMaterialsOptions {
  initialPage?: number;
  initialPageSize?: number;
  initialSortBy?: SortByType;
  initialSortOrder?: SortOrderType;
  initialType?: MaterialType | '';
  initialSearch?: string;
}

interface UseMaterialsReturn {
  materials: Material[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
  isLoading: boolean;
  error: string | null;
  sortBy: SortByType;
  sortOrder: SortOrderType;
  type: MaterialType | '';
  search: string;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setSortBy: (sortBy: SortByType) => void;
  setSortOrder: (order: SortOrderType) => void;
  setType: (type: MaterialType | '') => void;
  setSearch: (search: string) => void;
  refresh: () => void;
}

const DEFAULT_PAGE_SIZE = 12;

export function useMaterials(options: UseMaterialsOptions = {}): UseMaterialsReturn {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // 从URL参数初始化状态
  const [page, setPageState] = useState<number>(() => {
    const urlPage = searchParams.get('page');
    return urlPage ? parseInt(urlPage, 10) : (options.initialPage || 1);
  });

  const [pageSize, setPageSizeState] = useState<number>(options.initialPageSize || DEFAULT_PAGE_SIZE);

  const [sortBy, setSortByState] = useState<SortByType>(() => {
    const urlSortBy = searchParams.get('sort_by');
    const validSortBy: SortByType[] = ['created_at', 'view_count', 'like_count', 'download_count'];
    if (urlSortBy && validSortBy.includes(urlSortBy as SortByType)) {
      return urlSortBy as SortByType;
    }
    return options.initialSortBy || 'created_at';
  });

  const [sortOrder, setSortOrderState] = useState<SortOrderType>(() => {
    const urlSortOrder = searchParams.get('sort_order');
    if (urlSortOrder === 'asc' || urlSortOrder === 'desc') {
      return urlSortOrder;
    }
    return options.initialSortOrder || 'desc';
  });

  const [type, setTypeState] = useState<MaterialType | ''>(() => {
    const urlType = searchParams.get('type');
    const validTypes: (MaterialType | '')[] = ['', 'pdf', 'video'];
    if (urlType && validTypes.includes(urlType as MaterialType)) {
      return urlType as MaterialType;
    }
    return options.initialType || '';
  });

  const [search, setSearchState] = useState<string>(() => {
    return searchParams.get('search') || options.initialSearch || '';
  });

  // 数据状态
  const [materials, setMaterials] = useState<Material[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 用于防止重复请求的ref
  const abortControllerRef = useRef<AbortController | null>(null);
  const isFirstRender = useRef<boolean>(true);

  // 更新URL参数
  const updateURLParams = useCallback((
    newPage: number,
    newSortBy: string,
    newSortOrder: string,
    newType: string,
    newSearch: string
  ) => {
    const params = new URLSearchParams();

    if (newPage > 1) params.set('page', newPage.toString());
    if (newSortBy !== 'created_at') params.set('sort_by', newSortBy);
    if (newSortOrder !== 'desc') params.set('sort_order', newSortOrder);
    if (newType) params.set('type', newType);
    if (newSearch) params.set('search', newSearch);

    const newURL = params.toString() ? `${pathname}?${params.toString()}` : pathname;
    router.replace(newURL, { scroll: false });
  }, [pathname, router]);

  // 获取数据
  const fetchMaterials = useCallback(async () => {
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.set('page', page.toString());
      params.set('page_size', pageSize.toString());
      params.set('sort_by', sortBy);
      params.set('sort_order', sortOrder);
      if (type) params.set('type', type);
      if (search) params.set('search', search);

      const response = await api.get<PaginatedResponse<Material>>(
        `/api/v1/materials?${params.toString()}`
      );

      setMaterials(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
      setHasNext(response.has_next);
      setHasPrev(response.has_prev);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      setError(err instanceof Error ? err.message : '获取课件列表失败');
      setMaterials([]);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, sortBy, sortOrder, type, search]);

  // 首次加载和参数变化时获取数据
  useEffect(() => {
    fetchMaterials();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchMaterials]);

  // 同步状态到URL（非首次渲染）
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    updateURLParams(page, sortBy, sortOrder, type, search);
  }, [page, sortBy, sortOrder, type, search, updateURLParams]);

  // 设置方法
  const setPage = useCallback((newPage: number) => {
    setPageState(Math.max(1, newPage));
  }, []);

  const setPageSize = useCallback((newSize: number) => {
    setPageSizeState(newSize);
    setPageState(1); // 重置到第一页
  }, []);

  const setSortBy = useCallback((newSortBy: SortByType) => {
    setSortByState(newSortBy);
    setPageState(1); // 重置到第一页
  }, []);

  const setSortOrder = useCallback((newOrder: SortOrderType) => {
    setSortOrderState(newOrder);
    setPageState(1); // 重置到第一页
  }, []);

  const setType = useCallback((newType: MaterialType | '') => {
    setTypeState(newType);
    setPageState(1); // 重置到第一页
  }, []);

  const setSearch = useCallback((newSearch: string) => {
    setSearchState(newSearch);
    setPageState(1); // 重置到第一页
  }, []);

  const refresh = useCallback(() => {
    fetchMaterials();
  }, [fetchMaterials]);

  return {
    materials,
    total,
    page,
    pageSize,
    totalPages,
    hasNext,
    hasPrev,
    isLoading,
    error,
    sortBy,
    sortOrder,
    type,
    search,
    setPage,
    setPageSize,
    setSortBy,
    setSortOrder,
    setType,
    setSearch,
    refresh,
  };
}

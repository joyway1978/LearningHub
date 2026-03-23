'use client';

import { MaterialCard } from '@/components/MaterialCard';
import { SearchBar } from '@/components/SearchBar';
import { MaterialFilters } from '@/components/MaterialFilters';
import { Pagination } from '@/components/Pagination';
import { useMaterials } from '@/hooks/useMaterials';
import { FileText, Loader2 } from 'lucide-react';

export function MaterialsListClient() {
  const {
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
    setSortBy,
    setSortOrder,
    setType,
    setSearch,
  } = useMaterials({
    initialPageSize: 12,
  });

  return (
    <>
      {/* 搜索和筛选区域 */}
      <div className="bg-white rounded-lg border border-stone-200 p-4 mb-6">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          {/* 搜索栏 */}
          <SearchBar
            value={search}
            onSearch={setSearch}
            placeholder="搜索课件标题..."
          />

          {/* 筛选排序 */}
          <MaterialFilters
            type={type}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onTypeChange={setType}
            onSortChange={setSortBy}
            onOrderChange={setSortOrder}
          />
        </div>
      </div>

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-amber-500 animate-spin mb-4" />
          <p className="text-stone-500">加载中...</p>
        </div>
      )}

      {/* 错误状态 */}
      {!isLoading && error && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-stone-800 mb-2">加载失败</h3>
          <p className="text-stone-500 text-center max-w-md">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-amber-500 text-white rounded-md hover:bg-amber-600 transition-colors"
          >
            重试
          </button>
        </div>
      )}

      {/* 空状态 */}
      {!isLoading && !error && materials.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-20 h-20 bg-stone-100 rounded-full flex items-center justify-center mb-4">
            <FileText className="w-10 h-10 text-stone-300" />
          </div>
          <h3 className="text-lg font-medium text-stone-800 mb-2">
            {search ? '未找到匹配的课件' : '暂无课件'}
          </h3>
          <p className="text-stone-500 text-center max-w-md">
            {search
              ? `没有找到与 "${search}" 相关的课件，请尝试其他关键词`
              : '还没有人上传课件，成为第一个分享者吧！'}
          </p>
          {search && (
            <button
              onClick={() => setSearch('')}
              className="mt-4 px-4 py-2 bg-amber-500 text-white rounded-md hover:bg-amber-600 transition-colors"
            >
              清除搜索
            </button>
          )}
        </div>
      )}

      {/* 课件网格 */}
      {!isLoading && !error && materials.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {materials.map((material) => (
              <MaterialCard key={material.id} material={material} />
            ))}
          </div>

          {/* 分页 */}
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            hasNext={hasNext}
            hasPrev={hasPrev}
            onPageChange={setPage}
            total={total}
            pageSize={pageSize}
          />
        </>
      )}
    </>
  );
}

'use client';

import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
  total?: number;
  pageSize?: number;
}

export function Pagination({
  currentPage,
  totalPages,
  hasNext,
  hasPrev,
  onPageChange,
  total,
  pageSize,
}: PaginationProps) {
  // 生成页码数组
  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      // 如果总页数较少，显示所有页码
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 显示部分页码，使用省略号
      if (currentPage <= 3) {
        // 当前页靠近开头
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        // 当前页靠近结尾
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // 当前页在中间
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4">
      {/* 统计信息 */}
      {total !== undefined && pageSize !== undefined && (
        <div className="text-sm text-stone-500">
          显示 <span className="font-medium">{Math.min((currentPage - 1) * pageSize + 1, total)}</span> 到{' '}
          <span className="font-medium">{Math.min(currentPage * pageSize, total)}</span> 条，共{' '}
          <span className="font-medium">{total}</span> 条
        </div>
      )}

      {/* 分页导航 */}
      <nav className="flex items-center gap-1" aria-label="分页">
        {/* 上一页按钮 */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPrev}
          className={`inline-flex items-center justify-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            hasPrev
              ? 'text-stone-700 bg-white border border-stone-200 hover:bg-stone-50'
              : 'text-stone-300 bg-stone-50 border border-stone-200 cursor-not-allowed'
          }`}
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          <span className="hidden sm:inline">上一页</span>
        </button>

        {/* 页码按钮 */}
        <div className="hidden sm:flex items-center gap-1">
          {getPageNumbers().map((page, index) => (
            <React.Fragment key={index}>
              {page === '...' ? (
                <span className="px-3 py-2 text-stone-400">...</span>
              ) : (
                <button
                  onClick={() => onPageChange(page as number)}
                  className={`inline-flex items-center justify-center min-w-[2.5rem] px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === page
                      ? 'bg-amber-500 text-white'
                      : 'text-stone-700 bg-white border border-stone-200 hover:bg-stone-50'
                  }`}
                >
                  {page}
                </button>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* 移动端页码显示 */}
        <div className="sm:hidden px-3 py-2 text-sm text-stone-600">
          {currentPage} / {totalPages}
        </div>

        {/* 下一页按钮 */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNext}
          className={`inline-flex items-center justify-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            hasNext
              ? 'text-stone-700 bg-white border border-stone-200 hover:bg-stone-50'
              : 'text-stone-300 bg-stone-50 border border-stone-200 cursor-not-allowed'
          }`}
        >
          <span className="hidden sm:inline">下一页</span>
          <ChevronRight className="w-4 h-4 ml-1" />
        </button>
      </nav>
    </div>
  );
}

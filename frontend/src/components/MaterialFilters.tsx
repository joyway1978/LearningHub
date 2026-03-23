'use client';

import React from 'react';
import { MaterialType } from '@/types';
import { Clock, TrendingUp, ThumbsUp, FileText, Video, LayoutGrid } from 'lucide-react';

type SortByType = 'created_at' | 'view_count' | 'like_count' | 'download_count';
type SortOrderType = 'asc' | 'desc';

interface MaterialFiltersProps {
  type: MaterialType | '';
  sortBy: SortByType;
  sortOrder: SortOrderType;
  onTypeChange: (type: MaterialType | '') => void;
  onSortChange: (sortBy: SortByType) => void;
  onOrderChange: (order: SortOrderType) => void;
}

type SortOption = {
  value: SortByType;
  label: string;
  icon: React.ReactNode;
};

const sortOptions: SortOption[] = [
  { value: 'created_at', label: '最新', icon: <Clock className="w-4 h-4" /> },
  { value: 'view_count', label: '最热', icon: <TrendingUp className="w-4 h-4" /> },
  { value: 'like_count', label: '最多点赞', icon: <ThumbsUp className="w-4 h-4" /> },
];

type TypeOption = {
  value: MaterialType | '';
  label: string;
  icon: React.ReactNode;
};

const typeOptions: TypeOption[] = [
  { value: '', label: '全部', icon: <LayoutGrid className="w-4 h-4" /> },
  { value: 'video', label: '视频', icon: <Video className="w-4 h-4" /> },
  { value: 'pdf', label: 'PDF', icon: <FileText className="w-4 h-4" /> },
];

export function MaterialFilters({
  type,
  sortBy,
  sortOrder,
  onTypeChange,
  onSortChange,
  onOrderChange,
}: MaterialFiltersProps) {
  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
      {/* 类型筛选 */}
      <div className="flex flex-wrap gap-2">
        {typeOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => onTypeChange(option.value)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              type === option.value
                ? 'bg-amber-500 text-white'
                : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-50'
            }`}
          >
            {option.icon}
            {option.label}
          </button>
        ))}
      </div>

      {/* 排序控件 */}
      <div className="flex items-center gap-2">
        {/* 排序选项 */}
        <div className="flex bg-white rounded-md border border-stone-200 p-0.5">
          {sortOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => onSortChange(option.value)}
              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                sortBy === option.value
                  ? 'bg-amber-100 text-amber-700'
                  : 'text-stone-600 hover:bg-stone-50'
              }`}
            >
              {option.icon}
              <span className="hidden sm:inline">{option.label}</span>
            </button>
          ))}
        </div>

        {/* 排序方向 */}
        <button
          onClick={() => onOrderChange(sortOrder === 'asc' ? 'desc' : 'asc')}
          className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-stone-200 bg-white text-stone-600 hover:bg-stone-50 transition-colors"
          title={sortOrder === 'asc' ? '升序' : '降序'}
        >
          {sortOrder === 'asc' ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}

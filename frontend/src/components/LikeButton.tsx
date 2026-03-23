'use client';

import React from 'react';
import { Heart } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LikeButtonProps {
  isLiked: boolean;
  likeCount: number;
  isLoading?: boolean;
  onToggle: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showCount?: boolean;
}

export function LikeButton({
  isLiked,
  likeCount,
  isLoading = false,
  onToggle,
  className,
  size = 'md',
  showCount = true,
}: LikeButtonProps) {
  // 尺寸配置
  const sizeConfig = {
    sm: {
      button: 'px-3 py-1.5 gap-1.5',
      icon: 'w-4 h-4',
      text: 'text-sm',
    },
    md: {
      button: 'px-4 py-2 gap-2',
      icon: 'w-5 h-5',
      text: 'text-base',
    },
    lg: {
      button: 'px-6 py-3 gap-2.5',
      icon: 'w-6 h-6',
      text: 'text-lg',
    },
  };

  const config = sizeConfig[size];

  return (
    <button
      onClick={onToggle}
      disabled={isLoading}
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        isLiked
          ? 'bg-amber-500 text-white hover:bg-amber-600 shadow-sm'
          : 'bg-amber-100 text-amber-700 hover:bg-amber-200',
        config.button,
        className
      )}
      aria-label={isLiked ? '取消点赞' : '点赞'}
      aria-pressed={isLiked}
    >
      {/* 心形图标 */}
      <Heart
        className={cn(
          config.icon,
          'transition-transform duration-200',
          isLiked ? 'fill-current scale-110' : 'scale-100',
          isLoading && 'animate-pulse'
        )}
      />

      {/* 点赞数 */}
      {showCount && (
        <span className={config.text}>
          {isLoading ? '...' : likeCount.toLocaleString()}
        </span>
      )}

      {/* 文字标签（可选） */}
      {!showCount && (
        <span className={config.text}>
          {isLiked ? '已点赞' : '点赞'}
        </span>
      )}
    </button>
  );
}

// 简化版点赞按钮（仅图标）
interface LikeButtonIconOnlyProps {
  isLiked: boolean;
  isLoading?: boolean;
  onToggle: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LikeButtonIconOnly({
  isLiked,
  isLoading = false,
  onToggle,
  className,
  size = 'md',
}: LikeButtonIconOnlyProps) {
  const sizeConfig = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
  };

  const iconSizeConfig = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <button
      onClick={onToggle}
      disabled={isLoading}
      className={cn(
        'inline-flex items-center justify-center rounded-full transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        isLiked
          ? 'bg-amber-500 text-white hover:bg-amber-600'
          : 'bg-stone-100 text-stone-500 hover:bg-amber-100 hover:text-amber-600',
        sizeConfig[size],
        className
      )}
      aria-label={isLiked ? '取消点赞' : '点赞'}
      aria-pressed={isLiked}
    >
      <Heart
        className={cn(
          iconSizeConfig[size],
          'transition-transform duration-200',
          isLiked && 'fill-current'
        )}
      />
    </button>
  );
}

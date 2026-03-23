'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Loader2, Maximize, Minimize, Download, ExternalLink } from 'lucide-react';
import { logMedia } from '@/lib/logger';

interface PDFViewerProps {
  src: string;
  title?: string;
  className?: string;
  onError?: (error: Error) => void;
}

export function PDFViewer({
  src,
  title,
  className,
  onError,
}: PDFViewerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadProgress, setLoadProgress] = useState(0);
  const objectRef = useRef<HTMLObjectElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const loadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const materialId = useRef<number | null>(null);

  // 从URL中提取materialId用于日志
  useEffect(() => {
    try {
      const match = src.match(/\/materials\/(\d+)\/stream/);
      if (match) {
        materialId.current = parseInt(match[1], 10);
      }
    } catch {
      // Ignore parsing errors
    }
  }, [src]);

  // 模拟加载进度
  const startProgressSimulation = useCallback(() => {
    setLoadProgress(0);
    progressIntervalRef.current = setInterval(() => {
      setLoadProgress((prev) => {
        if (prev >= 90) return prev; // 停在90%，等真正加载完成到100%
        return prev + Math.random() * 15;
      });
    }, 200);
  }, []);

  const stopProgressSimulation = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    setLoadProgress(100);
  }, []);

  // 处理加载完成
  const handleLoad = useCallback(() => {
    stopProgressSimulation();
    setIsLoading(false);
    logMedia('play', materialId.current || 0, 'pdf', {
      status: 'loaded',
      title: title || 'unknown',
      src: src.substring(0, 100), // 截断URL避免日志过长
    });
  }, [stopProgressSimulation, title, src]);

  // 处理加载错误
  const handleError = useCallback(() => {
    stopProgressSimulation();
    setIsLoading(false);
    const errorMsg = 'PDF加载失败';
    setError(errorMsg);
    logMedia('error', materialId.current || 0, 'pdf', {
      error: errorMsg,
      title: title || 'unknown',
      src: src.substring(0, 100),
    });
    onError?.(new Error(errorMsg));
  }, [onError, stopProgressSimulation, title, src]);

  // 切换全屏
  const toggleFullscreen = useCallback(async () => {
    if (!containerRef.current) return;

    try {
      if (!isFullscreen) {
        if (containerRef.current.requestFullscreen) {
          await containerRef.current.requestFullscreen();
          logMedia('play', materialId.current || 0, 'pdf', {
            action: 'fullscreen_enter',
            title: title || 'unknown',
          });
        }
      } else {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
          logMedia('play', materialId.current || 0, 'pdf', {
            action: 'fullscreen_exit',
            title: title || 'unknown',
          });
        }
      }
    } catch (err) {
      console.error('全屏切换失败:', err);
    }
  }, [isFullscreen, title]);

  // 监听全屏状态变化
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (loadTimeoutRef.current) {
        clearTimeout(loadTimeoutRef.current);
      }
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  // 初始化PDF加载
  useEffect(() => {
    logMedia('play', materialId.current || 0, 'pdf', {
      action: 'init',
      title: title || 'unknown',
      src: src.substring(0, 100),
    });

    setIsLoading(true);
    setError(null);
    startProgressSimulation();

    // 设置加载超时检测（10秒）
    loadTimeoutRef.current = setTimeout(() => {
      if (isLoading) {
        // 如果10秒后还在加载，可能是iframe onLoad没触发，强制结束加载状态
        stopProgressSimulation();
        setIsLoading(false);
        logMedia('play', materialId.current || 0, 'pdf', {
          action: 'load_timeout',
          title: title || 'unknown',
          message: 'PDF load timeout - forcing display',
        });
      }
    }, 10000);

    return () => {
      if (loadTimeoutRef.current) {
        clearTimeout(loadTimeoutRef.current);
      }
    };
  }, [src, title, isLoading, startProgressSimulation, stopProgressSimulation]);

  // 在新标签页打开PDF
  const openInNewTab = useCallback(() => {
    logMedia('play', materialId.current || 0, 'pdf', {
      action: 'open_new_tab',
      title: title || 'unknown',
    });
    window.open(src, '_blank');
  }, [src, title]);

  // 下载PDF
  const downloadPDF = useCallback(() => {
    logMedia('play', materialId.current || 0, 'pdf', {
      action: 'download',
      title: title || 'unknown',
    });
    const link = document.createElement('a');
    link.href = src;
    link.download = title ? `${title}.pdf` : 'document.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [src, title]);

  // 重试加载
  const handleRetry = useCallback(() => {
    setError(null);
    setIsLoading(true);
    setLoadProgress(0);
    logMedia('play', materialId.current || 0, 'pdf', {
      action: 'retry',
      title: title || 'unknown',
    });
    // 强制重新加载object
    if (objectRef.current) {
      objectRef.current.data = src;
    }
  }, [src, title]);

  if (error) {
    return (
      <div
        className={cn(
          'relative w-full aspect-[4/3] bg-stone-100 rounded-md flex items-center justify-center border border-stone-200',
          className
        )}
      >
        <div className="text-center px-4">
          <p className="text-stone-600 mb-3">PDF加载失败</p>
          <p className="text-stone-400 text-sm mb-4">{error}</p>
          <div className="flex gap-2 justify-center">
            <button
              onClick={handleRetry}
              className="px-3 py-1.5 bg-stone-200 hover:bg-stone-300 rounded text-stone-700 text-sm transition-colors"
            >
              刷新重试
            </button>
            <button
              onClick={openInNewTab}
              className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded text-sm transition-colors"
            >
              新标签页打开
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative w-full bg-stone-100 rounded-md overflow-hidden border border-stone-200 flex flex-col',
        isFullscreen ? 'fixed inset-0 z-50 rounded-none' : '',
        className
      )}
    >
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-stone-200">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-stone-700 font-medium text-sm truncate">
            {title || 'PDF文档'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* 下载按钮 */}
          <button
            onClick={downloadPDF}
            className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
            aria-label="下载PDF"
            title="下载"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* 新标签页打开 */}
          <button
            onClick={openInNewTab}
            className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
            aria-label="在新标签页打开"
            title="新标签页打开"
          >
            <ExternalLink className="w-4 h-4" />
          </button>

          {/* 全屏按钮 */}
          <button
            onClick={toggleFullscreen}
            className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
            aria-label={isFullscreen ? '退出全屏' : '全屏'}
            title={isFullscreen ? '退出全屏' : '全屏'}
          >
            {isFullscreen ? (
              <Minimize className="w-4 h-4" />
            ) : (
              <Maximize className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* PDF内容区域 */}
      <div className="relative flex-1 min-h-[400px]">
        {/* 加载状态 */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-stone-50 z-10">
            <div className="text-center w-64">
              <Loader2 className="w-10 h-10 text-amber-500 animate-spin mx-auto mb-3" />
              <p className="text-stone-400 text-sm mb-2">加载PDF中...</p>
              {/* 进度条 */}
              <div className="w-full bg-stone-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(loadProgress, 100)}%` }}
                />
              </div>
              <p className="text-stone-400 text-xs mt-1">{Math.round(loadProgress)}%</p>
            </div>
          </div>
        )}

        {/* 使用object标签替代iframe，对PDF更可靠 */}
        <object
          ref={objectRef}
          data={src}
          type="application/pdf"
          className="w-full h-full min-h-[400px] border-0"
          onLoad={handleLoad}
          onError={handleError}
          title={title || 'PDF预览'}
        >
          {/* 备用内容：当浏览器不支持PDF时显示 */}
          <div className="flex items-center justify-center h-full bg-stone-50">
            <div className="text-center px-4">
              <p className="text-stone-600 mb-3">无法在此浏览器中预览PDF</p>
              <div className="flex gap-2 justify-center">
                <button
                  onClick={openInNewTab}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded text-sm transition-colors"
                >
                  在新标签页打开
                </button>
                <button
                  onClick={downloadPDF}
                  className="px-4 py-2 bg-stone-200 hover:bg-stone-300 text-stone-700 rounded text-sm transition-colors"
                >
                  下载PDF
                </button>
              </div>
            </div>
          </div>
        </object>
      </div>
    </div>
  );
}

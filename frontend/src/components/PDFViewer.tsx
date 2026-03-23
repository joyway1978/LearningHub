'use client';

import React, { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Loader2, Maximize, Minimize, Download, ExternalLink } from 'lucide-react';

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
  const iframeRef = React.useRef<HTMLIFrameElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // 处理加载完成
  const handleLoad = useCallback(() => {
    setIsLoading(false);
  }, []);

  // 处理加载错误
  const handleError = useCallback(() => {
    setIsLoading(false);
    const errorMsg = 'PDF加载失败';
    setError(errorMsg);
    onError?.(new Error(errorMsg));
  }, [onError]);

  // 切换全屏
  const toggleFullscreen = useCallback(async () => {
    if (!containerRef.current) return;

    try {
      if (!isFullscreen) {
        if (containerRef.current.requestFullscreen) {
          await containerRef.current.requestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        }
      }
    } catch (err) {
      console.error('全屏切换失败:', err);
    }
  }, [isFullscreen]);

  // 监听全屏状态变化
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // 在新标签页打开PDF
  const openInNewTab = useCallback(() => {
    window.open(src, '_blank');
  }, [src]);

  // 下载PDF
  const downloadPDF = useCallback(() => {
    const link = document.createElement('a');
    link.href = src;
    link.download = title ? `${title}.pdf` : 'document.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => window.location.reload()}
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
            <div className="text-center">
              <Loader2 className="w-10 h-10 text-amber-500 animate-spin mx-auto mb-2" />
              <p className="text-stone-400 text-sm">加载PDF中...</p>
            </div>
          </div>
        )}

        {/* iframe嵌入PDF */}
        <iframe
          ref={iframeRef}
          src={src}
          className="w-full h-full min-h-[400px] border-0"
          onLoad={handleLoad}
          onError={handleError}
          title={title || 'PDF预览'}
        />
      </div>
    </div>
  );
}

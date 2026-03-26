'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Loader2, Maximize, Minimize, Download, ExternalLink, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, FileText } from 'lucide-react';
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
  const [isConverting, setIsConverting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pdfDocRef = useRef<any>(null);
  const renderTaskRef = useRef<any>(null);
  const [pageNum, setPageNum] = useState(1);
  const [numPages, setNumPages] = useState(0);
  const [scale, setScale] = useState(1.0);
  const materialId = useRef<number | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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

  // 清理重试定时器
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  // 加载 PDF.js 和文档
  useEffect(() => {
    let isCancelled = false;

    const loadPdfJsAndDoc = async () => {
      try {
        // 加载 CSS
        if (!document.getElementById('pdfjs-css')) {
          const link = document.createElement('link');
          link.id = 'pdfjs-css';
          link.rel = 'stylesheet';
          link.href = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.css';
          document.head.appendChild(link);
        }

        // 加载 JS
        if (!(window as any).pdfjsLib) {
          await new Promise<void>((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Failed to load PDF.js'));
            document.body.appendChild(script);
          });

          // 设置 worker
          const pdfjsLib = (window as any).pdfjsLib;
          pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }

        if (isCancelled) return;

        // 现在加载 PDF 文档
        await loadPDFDocument();
      } catch (err) {
        console.error('PDF.js load error:', err);
        if (!isCancelled) {
          setError('PDF 组件加载失败');
          setIsLoading(false);
        }
      }
    };

    const loadPDFDocument = async () => {
      const pdfjsLib = (window as any).pdfjsLib;
      if (!pdfjsLib) return;

      setIsLoading(true);
      setError(null);

      try {
        logMedia('play', materialId.current || 0, 'pdf', {
          action: 'init',
          title: title || 'unknown',
          src: src.substring(0, 100),
        });

        // 加载 PDF
        const loadingTask = pdfjsLib.getDocument({
          url: src,
          withCredentials: false,
        });

        // 监听进度
        loadingTask.onProgress = (progress: { loaded: number; total: number }) => {
          if (progress.total > 0 && !isCancelled) {
            const percent = (progress.loaded / progress.total) * 100;
            setLoadProgress(Math.min(percent, 90));
          }
        };

        const pdf = await loadingTask.promise;
        if (isCancelled) return;

        pdfDocRef.current = pdf;
        setNumPages(pdf.numPages);
        setLoadProgress(100);
        setIsLoading(false);

        logMedia('play', materialId.current || 0, 'pdf', {
          status: 'loaded',
          pages: pdf.numPages,
          title: title || 'unknown',
        });

        // 渲染第一页
        renderPage(1, pdf);
      } catch (err: any) {
        console.error('PDF load error:', err);
        if (isCancelled) return;

        // Check if it's a 503 error (PDF converting)
        if (err?.status === 503 || err?.message?.includes('503') || err?.name === 'ResponseException') {
          setIsConverting(true);
          setError(null);
          setIsLoading(false);

          logMedia('play', materialId.current || 0, 'pdf', {
            status: 'converting',
            retry: retryCount,
            title: title || 'unknown',
          });

          // Auto-retry after 3 seconds (max 20 retries = 60 seconds)
          if (retryCount < 20) {
            retryTimeoutRef.current = setTimeout(() => {
              setRetryCount(prev => prev + 1);
              setIsConverting(false);
              setIsLoading(true);
              loadPdfJsAndDoc();
            }, 3000);
          } else {
            setIsConverting(false);
            setError('PDF转换超时，请刷新页面重试');
            onError?.(err as Error);
          }
          return;
        }

        setError('PDF 加载失败');
        setIsLoading(false);
        onError?.(err as Error);

        logMedia('error', materialId.current || 0, 'pdf', {
          error: String(err),
          title: title || 'unknown',
        });
      }
    };

    loadPdfJsAndDoc();

    return () => {
      isCancelled = true;
      // 取消正在进行的渲染
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
      }
      // 销毁 PDF 文档
      if (pdfDocRef.current) {
        pdfDocRef.current.destroy();
        pdfDocRef.current = null;
      }
    };
  }, [src, title, onError]);

  // 渲染页面
  const renderPage = useCallback(async (num: number, pdfDoc: any = null) => {
    const pdf = pdfDoc || pdfDocRef.current;
    const canvas = canvasRef.current;

    if (!pdf || !canvas) return;

    try {
      // 取消之前的渲染任务
      if (renderTaskRef.current) {
        await renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }

      const page = await pdf.getPage(num);

      const context = canvas.getContext('2d');
      if (!context) return;

      // 计算视口
      const container = containerRef.current;
      const containerWidth = container ? container.clientWidth - 40 : 800;
      const viewport = page.getViewport({ scale: 1 });
      const autoScale = containerWidth / viewport.width;
      const finalScale = Math.max(scale, autoScale * 0.9);

      const scaledViewport = page.getViewport({ scale: finalScale });

      // 设置 canvas 尺寸
      canvas.height = scaledViewport.height;
      canvas.width = scaledViewport.width;

      // 清空画布
      context.clearRect(0, 0, canvas.width, canvas.height);

      // 渲染
      const renderContext = {
        canvasContext: context,
        viewport: scaledViewport,
      };

      const task = page.render(renderContext);
      renderTaskRef.current = task;

      await task.promise;
      renderTaskRef.current = null;

      setPageNum(num);
    } catch (err: any) {
      if (err?.name !== 'RenderingCancelledException') {
        console.error('Render error:', err);
      }
    }
  }, [scale]);

  // 当 scale 改变时重新渲染当前页
  useEffect(() => {
    if (pdfDocRef.current && pageNum > 0 && !isLoading) {
      renderPage(pageNum);
    }
  }, [scale, pageNum, isLoading, renderPage]);

  // 页面导航
  const goToPrevPage = useCallback(() => {
    if (pageNum <= 1) return;
    renderPage(pageNum - 1);
  }, [pageNum, renderPage]);

  const goToNextPage = useCallback(() => {
    if (pageNum >= numPages) return;
    renderPage(pageNum + 1);
  }, [pageNum, numPages, renderPage]);

  // 缩放
  const zoomIn = useCallback(() => {
    setScale(prev => Math.min(prev + 0.2, 3.0));
  }, []);

  const zoomOut = useCallback(() => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  }, []);

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
    setRetryCount(0);
    setError(null);
    setIsConverting(false);
    setIsLoading(true);
    window.location.reload();
  }, []);

  // 正在转换中状态
  if (isConverting) {
    return (
      <div
        className={cn(
          'relative w-full aspect-[4/3] bg-stone-100 rounded-md flex items-center justify-center border border-stone-200',
          className
        )}
      >
        <div className="text-center px-4">
          <FileText className="w-12 h-12 text-amber-500 mx-auto mb-4 animate-pulse" />
          <p className="text-stone-700 mb-2 font-medium">正在转换为 PDF...</p>
          <p className="text-stone-400 text-sm mb-4">首次加载需要几秒钟，请稍候</p>
          <div className="flex items-center justify-center gap-2 text-stone-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">重试次数: {retryCount}/20</span>
          </div>
          <p className="text-stone-400 text-xs mt-4">
            如果长时间未加载，请
            <button
              onClick={handleRetry}
              className="text-amber-600 hover:text-amber-700 underline ml-1"
            >
              刷新页面
            </button>
          </p>
        </div>
      </div>
    );
  }

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
      style={{ minHeight: '500px' }}
    >
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-stone-200">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-stone-700 font-medium text-sm truncate">
            {title || 'PDF文档'}
          </span>
          {numPages > 0 && (
            <span className="text-stone-400 text-sm">
              ({pageNum} / {numPages} 页)
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {/* 页面导航 */}
          <div className="flex items-center gap-1 mr-2">
            <button
              onClick={goToPrevPage}
              disabled={pageNum <= 1}
              className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="上一页"
              title="上一页"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={goToNextPage}
              disabled={pageNum >= numPages}
              className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="下一页"
              title="下一页"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="w-px h-5 bg-stone-200 mx-1" />

          {/* 缩放控制 */}
          <div className="flex items-center gap-1 mr-2">
            <button
              onClick={zoomOut}
              className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
              aria-label="缩小"
              title="缩小"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-stone-500 text-xs min-w-[40px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="p-1.5 text-stone-500 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
              aria-label="放大"
              title="放大"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>

          <div className="w-px h-5 bg-stone-200 mx-1" />

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

      {/* PDF 内容区域 */}
      <div className="relative flex-1 overflow-auto bg-stone-100 p-4">
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

        {/* PDF 画布 */}
        <div className="flex justify-center min-h-full">
          <canvas
            ref={canvasRef}
            className="shadow-lg bg-white"
            style={{ display: isLoading ? 'none' : 'block' }}
          />
        </div>
      </div>
    </div>
  );
}

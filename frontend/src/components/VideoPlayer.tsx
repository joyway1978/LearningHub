'use client';

import React, { useState, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Loader2, Maximize, Minimize, Volume2, VolumeX, Play, Pause } from 'lucide-react';

interface VideoPlayerProps {
  src: string;
  poster?: string;
  title?: string;
  className?: string;
  onError?: (error: Error) => void;
}

export function VideoPlayer({
  src,
  poster,
  title,
  className,
  onError,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 处理视频加载完成
  const handleLoadedData = useCallback(() => {
    setIsLoading(false);
  }, []);

  // 处理视频加载错误
  const handleError = useCallback(() => {
    setIsLoading(false);
    const errorMsg = '视频加载失败';
    setError(errorMsg);
    onError?.(new Error(errorMsg));
  }, [onError]);

  // 切换播放/暂停
  const togglePlay = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play().catch((err) => {
          console.error('播放失败:', err);
        });
      }
    }
  }, [isPlaying]);

  // 监听播放状态变化
  const handlePlay = useCallback(() => setIsPlaying(true), []);
  const handlePause = useCallback(() => setIsPlaying(false), []);

  // 切换静音
  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

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

  // 键盘快捷键
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case ' ':
        case 'k':
          e.preventDefault();
          togglePlay();
          break;
        case 'f':
          e.preventDefault();
          toggleFullscreen();
          break;
        case 'm':
          e.preventDefault();
          toggleMute();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlay, toggleFullscreen, toggleMute]);

  if (error) {
    return (
      <div
        className={cn(
          'relative w-full aspect-video bg-stone-900 rounded-md flex items-center justify-center',
          className
        )}
      >
        <div className="text-center">
          <p className="text-stone-400 mb-2">视频加载失败</p>
          <button
            onClick={() => window.location.reload()}
            className="text-amber-500 hover:text-amber-400 text-sm"
          >
            刷新重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative w-full bg-[#0c0a09] rounded-md overflow-hidden group',
        className
      )}
    >
      {/* 视频元素 */}
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="w-full h-full object-contain"
        onLoadedData={handleLoadedData}
        onError={handleError}
        onPlay={handlePlay}
        onPause={handlePause}
        preload="metadata"
        controls={false}
        playsInline
      >
        您的浏览器不支持视频播放
      </video>

      {/* 加载状态 */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-900">
          <div className="text-center">
            <Loader2 className="w-10 h-10 text-amber-500 animate-spin mx-auto mb-2" />
            <p className="text-stone-400 text-sm">加载中...</p>
          </div>
        </div>
      )}

      {/* 自定义控制栏 */}
      {!isLoading && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-4 py-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex items-center justify-between">
            {/* 左侧控制 */}
            <div className="flex items-center gap-3">
              {/* 播放/暂停按钮 */}
              <button
                onClick={togglePlay}
                className="text-white hover:text-amber-400 transition-colors"
                aria-label={isPlaying ? '暂停' : '播放'}
              >
                {isPlaying ? (
                  <Pause className="w-6 h-6" />
                ) : (
                  <Play className="w-6 h-6" />
                )}
              </button>

              {/* 音量控制 */}
              <button
                onClick={toggleMute}
                className="text-white hover:text-amber-400 transition-colors"
                aria-label={isMuted ? '取消静音' : '静音'}
              >
                {isMuted ? (
                  <VolumeX className="w-5 h-5" />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </button>

              {/* 标题 */}
              {title && (
                <span className="text-white text-sm truncate max-w-[200px] hidden sm:block">
                  {title}
                </span>
              )}
            </div>

            {/* 右侧控制 */}
            <div className="flex items-center gap-3">
              {/* 全屏按钮 */}
              <button
                onClick={toggleFullscreen}
                className="text-white hover:text-amber-400 transition-colors"
                aria-label={isFullscreen ? '退出全屏' : '全屏'}
              >
                {isFullscreen ? (
                  <Minimize className="w-5 h-5" />
                ) : (
                  <Maximize className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 点击播放遮罩（暂停时显示） */}
      {!isLoading && !isPlaying && (
        <div
          onClick={togglePlay}
          className="absolute inset-0 flex items-center justify-center cursor-pointer bg-black/20 hover:bg-black/30 transition-colors"
        >
          <div className="w-16 h-16 rounded-full bg-amber-500/90 flex items-center justify-center hover:bg-amber-500 transition-colors">
            <Play className="w-8 h-8 text-white ml-1" />
          </div>
        </div>
      )}
    </div>
  );
}

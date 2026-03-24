'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';

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
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [codecError, setCodecError] = useState<string | null>(null);
  const playerRef = useRef<any>(null);
  const isInitializedRef = useRef(false);
  const hasLoadedMetadataRef = useRef(false);
  const canPlayRef = useRef(false);

  const addLog = useCallback((msg: string) => {
    console.log(`[VideoPlayer] ${msg}`);
    setLogs(prev => [...prev.slice(-9), `${new Date().toLocaleTimeString()}: ${msg}`]);
  }, []);

  // Load Video.js CSS
  useEffect(() => {
    if (document.getElementById('videojs-css')) return;

    addLog('Loading Video.js CSS...');
    const link = document.createElement('link');
    link.id = 'videojs-css';
    link.rel = 'stylesheet';
    link.href = 'https://vjs.zencdn.net/8.6.1/video-js.css';
    link.crossOrigin = 'anonymous';
    link.onload = () => addLog('Video.js CSS loaded');
    link.onerror = () => addLog('Video.js CSS failed');
    document.head.appendChild(link);
  }, [addLog]);

  // Initialize Video.js
  useEffect(() => {
    addLog(`Video src: ${src.substring(0, 50)}...`);

    const initVideoJs = async () => {
      try {
        // Wait for video.js to be available
        let attempts = 0;
        while (!(window as any).videojs && attempts < 50) {
          await new Promise(resolve => setTimeout(resolve, 100));
          attempts++;
        }

        if (!(window as any).videojs) {
          addLog('Video.js not available after timeout');
          setError('播放器加载超时');
          return;
        }

        if (!videoRef.current) {
          addLog('Video element not available');
          return;
        }

        // Avoid double initialization
        if (isInitializedRef.current) {
          addLog('Already initialized, skipping');
          return;
        }

        addLog('Initializing Video.js...');
        const videojs = (window as any).videojs;

        // Destroy existing player
        if (playerRef.current) {
          try {
            playerRef.current.dispose();
          } catch (e) {
            // Ignore dispose errors
          }
          addLog('Disposed previous player');
        }

        // Small delay to ensure DOM is ready
        await new Promise(resolve => setTimeout(resolve, 50));

        playerRef.current = videojs(videoRef.current, {
          controls: true,
          autoplay: false,
          preload: 'metadata',
          fluid: true,
          responsive: true,
          aspectRatio: '16:9',
          playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
          controlBar: {
            children: [
              'playToggle',
              'volumePanel',
              'currentTimeDisplay',
              'timeDivider',
              'durationDisplay',
              'progressControl',
              'playbackRateMenuButton',
              'fullscreenToggle',
            ],
          },
          html5: {
            vhs: {
              overrideNative: true,
              limitRenditionByPlayerDimensions: true,
              useDevicePixelRatio: true,
            },
          },
        }, function onPlayerReady() {
          addLog('Video.js ready');
          setIsReady(true);
        });

        isInitializedRef.current = true;

        // Set source
        playerRef.current.src({
          src: src,
          type: 'video/mp4',
        });

        if (poster) {
          playerRef.current.poster(poster);
        }

        // Event listeners
        playerRef.current.on('error', (e: any) => {
          const errorCode = playerRef.current?.error()?.code;
          const errorMessage = playerRef.current?.error()?.message;
          addLog(`Video.js error: ${errorCode} - ${errorMessage}`);
          setError('视频播放失败');
          onError?.(new Error(`Video.js error: ${errorMessage}`));
        });

        playerRef.current.on('canplay', () => {
          addLog('Video can play');
        });

        playerRef.current.on('waiting', () => {
          addLog('Video waiting (buffering)');
        });

        playerRef.current.on('stalled', () => {
          addLog('Video stalled');
        });

        playerRef.current.on('loadstart', () => {
          addLog('Video load start');
        });

        playerRef.current.on('loadeddata', () => {
          addLog('Video loaded data');
        });

        playerRef.current.on('loadedmetadata', () => {
          addLog('Video loaded metadata');
          hasLoadedMetadataRef.current = true;

          // Check if video can actually play after metadata is loaded
          setTimeout(() => {
            if (hasLoadedMetadataRef.current && !canPlayRef.current) {
              // Likely a codec issue (e.g., H.265/HEVC not supported in Chrome)
              const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
              if (isChrome) {
                setCodecError('此视频编码格式不受 Chrome 浏览器支持。请使用 Safari 浏览器播放，或联系管理员转换视频格式。');
              }
            }
          }, 2000);
        });

        // Detect codec support
        playerRef.current.on('canplay', () => {
          addLog('Video can play');
          canPlayRef.current = true;
        });

      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        addLog(`Exception: ${msg}`);
        setError('播放器加载失败');
      }
    };

    // Load Video.js JS if not already loaded
    if (!(window as any).videojs) {
      addLog('Loading Video.js JS...');
      const script = document.createElement('script');
      script.src = 'https://vjs.zencdn.net/8.6.1/video.min.js';
      script.async = true;
      script.crossOrigin = 'anonymous';
      script.onload = () => {
        addLog('Video.js JS loaded');
        initVideoJs();
      };
      script.onerror = () => {
        addLog('Video.js JS failed');
        setError('播放器脚本加载失败');
      };
      document.body.appendChild(script);
    } else {
      addLog('Video.js already exists');
      initVideoJs();
    }

    return () => {
      if (playerRef.current) {
        try {
          playerRef.current.dispose();
        } catch (e) {
          // Ignore dispose errors
        }
        addLog('Cleanup: disposed player');
      }
      isInitializedRef.current = false;
    };
  }, [src, onError, addLog]);

  // Update video source when it changes
  useEffect(() => {
    if (!playerRef.current || !src) return;

    addLog(`Updating source to: ${src.substring(0, 50)}...`);

    try {
      playerRef.current.src({
        src: src,
        type: 'video/mp4',
      });
      addLog('Source updated');
    } catch (e) {
      addLog(`Failed to update source: ${e}`);
    }
  }, [src, addLog]);

  if (error || codecError) {
    return (
      <div
        className={cn(
          'relative w-full aspect-video bg-stone-900 rounded-md flex flex-col items-center justify-center gap-2',
          className
        )}
      >
        {codecError ? (
          <>
            <p className="text-amber-400 font-medium text-center px-4">{codecError}</p>
            <p className="text-stone-500 text-sm">建议使用 Safari 浏览器播放此视频</p>
            <a
              href={src}
              download
              className="text-stone-300 hover:text-white text-sm underline mt-1"
            >
              下载视频到本地播放
            </a>
          </>
        ) : (
          <p className="text-stone-400">{error}</p>
        )}
        <button
          onClick={() => window.location.reload()}
          className="text-amber-500 hover:text-amber-400 text-sm mt-2"
        >
          刷新重试
        </button>
        <div className="text-xs text-stone-600 max-w-md max-h-32 overflow-auto bg-stone-800 p-2 rounded mt-2">
          {logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative w-full rounded-md overflow-hidden',
        className
      )}
      style={{ aspectRatio: '16/9' }}
    >
      <video
        ref={videoRef}
        poster={poster}
        className="video-js vjs-big-play-centered vjs-theme-city"
        playsInline
        preload="metadata"
      >
        <source src={src} type="video/mp4" />
        您的浏览器不支持视频播放
      </video>

      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-900 z-10">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-stone-400 text-sm">加载播放器...</p>
          </div>
        </div>
      )}
    </div>
  );
}

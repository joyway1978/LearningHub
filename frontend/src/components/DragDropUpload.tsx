'use client';

import React, { useCallback, useState, useRef } from 'react';
import { cn, formatFileSize } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// 支持的文件类型（与后端转码支持的格式保持一致）
const ALLOWED_VIDEO_TYPES = [
  'video/mp4',        // .mp4
  'video/webm',       // .webm
  'video/quicktime',  // .mov
  'video/x-msvideo',  // .avi
  'video/x-matroska', // .mkv
  'video/mpeg',       // .mpg, .mpeg
  'video/3gpp',       // .3gp
];
const ALLOWED_PDF_TYPES = ['application/pdf'];
const ALLOWED_OFFICE_TYPES = [
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  // .docx
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',        // .xlsx
];
const ALLOWED_TYPES = [...ALLOWED_VIDEO_TYPES, ...ALLOWED_PDF_TYPES, ...ALLOWED_OFFICE_TYPES];

// 文件大小限制（字节）
const MAX_VIDEO_SIZE = 500 * 1024 * 1024; // 500MB
const MAX_PDF_SIZE = 50 * 1024 * 1024; // 50MB
const MAX_OFFICE_SIZE = 50 * 1024 * 1024; // 50MB (same as PDF)

// 文件类型显示名称
const FILE_TYPE_LABELS: Record<string, string> = {
  'video/mp4': 'MP4视频',
  'video/webm': 'WebM视频',
  'video/quicktime': 'MOV视频',
  'video/x-msvideo': 'AVI视频',
  'video/x-matroska': 'MKV视频',
  'video/mpeg': 'MPEG视频',
  'video/3gpp': '3GP视频',
  'application/pdf': 'PDF文档',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPT演示文稿',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word文档',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel表格',
};

// 错误类型
export type UploadError =
  | 'FILE_TOO_LARGE'
  | 'INVALID_TYPE'
  | 'NO_FILE'
  | null;

interface DragDropUploadProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
  error?: UploadError;
  errorMessage?: string;
  className?: string;
}

export function DragDropUpload({
  onFileSelect,
  selectedFile,
  error,
  errorMessage,
  className,
}: DragDropUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // 验证文件
  const validateFile = (file: File): { valid: boolean; error: UploadError; message: string } => {
    // 检查文件类型
    if (!ALLOWED_TYPES.includes(file.type)) {
      return {
        valid: false,
        error: 'INVALID_TYPE',
        message: '不支持的文件格式。支持的视频格式：MP4、WebM、MOV、AVI、MKV、MPEG；支持 PDF 文件；支持 Office 文件（PPTX、DOCX、XLSX）。视频将自动转码为浏览器兼容格式。',
      };
    }

    // 检查文件大小
    if (ALLOWED_VIDEO_TYPES.includes(file.type) && file.size > MAX_VIDEO_SIZE) {
      return {
        valid: false,
        error: 'FILE_TOO_LARGE',
        message: `视频文件过大。最大支持 ${formatFileSize(MAX_VIDEO_SIZE)}。`,
      };
    }

    if (ALLOWED_PDF_TYPES.includes(file.type) && file.size > MAX_PDF_SIZE) {
      return {
        valid: false,
        error: 'FILE_TOO_LARGE',
        message: `PDF文件过大。最大支持 ${formatFileSize(MAX_PDF_SIZE)}。`,
      };
    }

    if (ALLOWED_OFFICE_TYPES.includes(file.type) && file.size > MAX_OFFICE_SIZE) {
      return {
        valid: false,
        error: 'FILE_TOO_LARGE',
        message: `Office文件过大。最大支持 ${formatFileSize(MAX_OFFICE_SIZE)}。`,
      };
    }

    return { valid: true, error: null, message: '' };
  };

  // 处理文件选择
  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) {
        onFileSelect(null);
        return;
      }

      const validation = validateFile(file);
      if (validation.valid) {
        onFileSelect(file);
      } else {
        onFileSelect(null);
        // 触发错误回调可以通过其他方式处理
        if (validation.error) {
          // 这里可以通过事件或回调通知父组件
          console.error(validation.message);
        }
      }
    },
    [onFileSelect]
  );

  // 拖拽事件处理
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  // 点击选择文件
  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  // 文件输入变化
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  // 取消选择
  const handleClear = useCallback(() => {
    onFileSelect(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }, [onFileSelect]);

  // 获取文件图标
  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('video')) {
      return (
        <svg
          className="w-12 h-12 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
      );
    }
    if (mimeType === 'application/vnd.openxmlformats-officedocument.presentationml.presentation') {
      // PPT - Orange
      return (
        <svg
          className="w-12 h-12 text-orange-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
      );
    }
    if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
      // Word - Blue
      return (
        <svg
          className="w-12 h-12 text-blue-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
      );
    }
    if (mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
      // Excel - Green
      return (
        <svg
          className="w-12 h-12 text-green-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
      );
    }
    return (
      <svg
        className="w-12 h-12 text-red-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
    );
  };

  return (
    <div className={cn('w-full', className)}>
      {/* 上传区域 */}
      {!selectedFile ? (
        <div
          onClick={handleClick}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className={cn(
            'relative cursor-pointer rounded-md border-2 border-dashed p-12 transition-all duration-200',
            'border-border hover:border-primary',
            isDragging && 'border-primary bg-background',
            error && 'border-red-500 hover:border-red-500'
          )}
        >
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".mp4,.webm,.pdf,.pptx,.docx,.xlsx,video/mp4,video/webm,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={handleInputChange}
          />

          <div className="flex flex-col items-center justify-center text-center">
            {/* 上传图标 */}
            <div className="mb-4">
              <svg
                className={cn(
                  'mx-auto h-12 w-12 transition-colors duration-200',
                  isDragging ? 'text-primary' : 'text-text-muted'
                )}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            {/* 提示文字 */}
            <p className="mb-2 text-sm font-medium text-text-primary">
              <span className="text-primary hover:text-primary-hover">
                点击上传
              </span>{' '}
              或拖拽文件到此处
            </p>
            <p className="text-xs text-text-muted">
              支持 MP4、WebM 视频（最大 500MB）、PDF（最大 50MB）或 Office文件（最大 50MB）
            </p>
          </div>
        </div>
      ) : (
        /* 已选择文件显示 */
        <div className="rounded-md border border-border bg-surface p-6">
          <div className="flex items-start gap-4">
            {/* 文件图标 */}
            <div className="flex-shrink-0">{getFileIcon(selectedFile.type)}</div>

            {/* 文件信息 */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-text-secondary mt-1">
                {FILE_TYPE_LABELS[selectedFile.type] || selectedFile.type} ·{' '}
                {formatFileSize(selectedFile.size)}
              </p>
            </div>

            {/* 删除按钮 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="flex-shrink-0 text-text-muted hover:text-red-500"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </Button>
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && errorMessage && (
        <p className="mt-2 text-sm text-red-500">{errorMessage}</p>
      )}
    </div>
  );
}

// 导出验证函数和常量供外部使用
export { ALLOWED_TYPES, ALLOWED_VIDEO_TYPES, ALLOWED_PDF_TYPES, ALLOWED_OFFICE_TYPES, MAX_VIDEO_SIZE, MAX_PDF_SIZE, MAX_OFFICE_SIZE };
export { validateFile as validateUploadFile } from './DragDropUpload';

// 验证文件函数（用于外部调用）
export function validateFile(file: File): { valid: boolean; error: UploadError; message: string } {
  // 检查文件类型
  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: 'INVALID_TYPE',
      message: '不支持的文件格式。请上传 MP4、WebM 视频、PDF 文件或 Office 文件（PPTX、DOCX、XLSX）。',
    };
  }

  // 检查文件大小
  if (ALLOWED_VIDEO_TYPES.includes(file.type) && file.size > MAX_VIDEO_SIZE) {
    return {
      valid: false,
      error: 'FILE_TOO_LARGE',
      message: `视频文件过大。最大支持 ${formatFileSize(MAX_VIDEO_SIZE)}。`,
    };
  }

  if (ALLOWED_PDF_TYPES.includes(file.type) && file.size > MAX_PDF_SIZE) {
    return {
      valid: false,
      error: 'FILE_TOO_LARGE',
      message: `PDF文件过大。最大支持 ${formatFileSize(MAX_PDF_SIZE)}。`,
    };
  }

  if (ALLOWED_OFFICE_TYPES.includes(file.type) && file.size > MAX_OFFICE_SIZE) {
    return {
      valid: false,
      error: 'FILE_TOO_LARGE',
      message: `Office文件过大。最大支持 ${formatFileSize(MAX_OFFICE_SIZE)}。`,
    };
  }

  return { valid: true, error: null, message: '' };
}

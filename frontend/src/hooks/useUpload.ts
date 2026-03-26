'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { uploadFile } from '@/lib/api';
import { Material, MaterialStatus } from '@/types';
import { formatFileSize } from '@/lib/utils';

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
const MAX_OFFICE_SIZE = 50 * 1024 * 1024; // 50MB

// 上传状态类型
export type UploadStatus =
  | 'idle'
  | 'validating'
  | 'uploading'
  | 'processing'
  | 'success'
  | 'error';

// 错误类型
export type UploadErrorType =
  | 'FILE_TOO_LARGE'
  | 'INVALID_TYPE'
  | 'NO_FILE'
  | 'NO_TITLE'
  | 'UPLOAD_FAILED'
  | null;

// 上传错误对象
export interface UploadError {
  type: UploadErrorType;
  message: string;
}

// 上传Hook返回类型
export interface UseUploadReturn {
  // 状态
  file: File | null;
  title: string;
  description: string;
  uploadProgress: number;
  uploadStatus: UploadStatus;
  error: UploadError | null;
  uploadedMaterial: Material | null;

  // 操作
  setFile: (file: File | null) => void;
  setTitle: (title: string) => void;
  setDescription: (description: string) => void;
  validateAndSetFile: (file: File | null) => boolean;
  upload: () => Promise<boolean>;
  reset: () => void;

  // 验证函数
  validateFile: (file: File) => { valid: boolean; error: UploadError | null };
  validateForm: () => { valid: boolean; error: UploadError | null };
}

// 文件验证函数
function validateFileInternal(file: File): { valid: boolean; error: UploadError | null } {
  // 检查文件类型
  if (!ALLOWED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: {
        type: 'INVALID_TYPE',
        message: '不支持的文件格式。支持的视频格式：MP4、WebM、MOV、AVI、MKV、MPEG；支持 PDF 文件；支持 Office 文件（PPT、Word、Excel）。视频将自动转码为浏览器兼容格式，Office 文件将转换为 PDF 显示。',
      },
    };
  }

  // 检查文件大小
  if (ALLOWED_VIDEO_TYPES.includes(file.type) && file.size > MAX_VIDEO_SIZE) {
    return {
      valid: false,
      error: {
        type: 'FILE_TOO_LARGE',
        message: `视频文件过大。最大支持 ${formatFileSize(MAX_VIDEO_SIZE)}。`,
      },
    };
  }

  if (ALLOWED_PDF_TYPES.includes(file.type) && file.size > MAX_PDF_SIZE) {
    return {
      valid: false,
      error: {
        type: 'FILE_TOO_LARGE',
        message: `PDF文件过大。最大支持 ${formatFileSize(MAX_PDF_SIZE)}。`,
      },
    };
  }

  if (ALLOWED_OFFICE_TYPES.includes(file.type) && file.size > MAX_OFFICE_SIZE) {
    return {
      valid: false,
      error: {
        type: 'FILE_TOO_LARGE',
        message: `Office文件过大。最大支持 ${formatFileSize(MAX_OFFICE_SIZE)}。`,
      },
    };
  }

  return { valid: true, error: null };
}

export function useUpload(): UseUploadReturn {
  const router = useRouter();

  // 状态
  const [file, setFileState] = useState<File | null>(null);
  const [title, setTitleState] = useState('');
  const [description, setDescriptionState] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [error, setError] = useState<UploadError | null>(null);
  const [uploadedMaterial, setUploadedMaterial] = useState<Material | null>(null);

  // 使用 ref 防止重复上传
  const isUploadingRef = useRef(false);

  // 设置文件
  const setFile = useCallback((newFile: File | null) => {
    setFileState(newFile);
    if (newFile) {
      setError(null);
    }
  }, []);

  // 设置标题
  const setTitle = useCallback((newTitle: string) => {
    setTitleState(newTitle);
    if (newTitle.trim()) {
      setError((prev) => (prev?.type === 'NO_TITLE' ? null : prev));
    }
  }, []);

  // 设置描述
  const setDescription = useCallback((newDescription: string) => {
    setDescriptionState(newDescription);
  }, []);

  // 验证文件
  const validateFile = useCallback((fileToValidate: File): { valid: boolean; error: UploadError | null } => {
    return validateFileInternal(fileToValidate);
  }, []);

  // 验证并设置文件
  const validateAndSetFile = useCallback(
    (newFile: File | null): boolean => {
      if (!newFile) {
        setFile(null);
        return true;
      }

      const validation = validateFile(newFile);
      if (validation.valid) {
        setFile(newFile);
        setError(null);
        return true;
      } else {
        setFile(null);
        setError(validation.error);
        return false;
      }
    },
    [setFile, validateFile]
  );

  // 验证表单
  const validateForm = useCallback((): { valid: boolean; error: UploadError | null } => {
    // 检查文件
    if (!file) {
      return {
        valid: false,
        error: {
          type: 'NO_FILE',
          message: '请选择要上传的文件。',
        },
      };
    }

    // 再次验证文件
    const fileValidation = validateFile(file);
    if (!fileValidation.valid) {
      return fileValidation;
    }

    // 检查标题
    if (!title.trim()) {
      return {
        valid: false,
        error: {
          type: 'NO_TITLE',
          message: '请输入课件标题。',
        },
      };
    }

    return { valid: true, error: null };
  }, [file, title, validateFile]);

  // 上传文件
  const upload = useCallback(async (): Promise<boolean> => {
    // 防止重复上传
    if (isUploadingRef.current) {
      return false;
    }

    // 验证表单
    const formValidation = validateForm();
    if (!formValidation.valid) {
      setError(formValidation.error);
      return false;
    }

    if (!file) {
      setError({
        type: 'NO_FILE',
        message: '请选择要上传的文件。',
      });
      return false;
    }

    isUploadingRef.current = true;
    setUploadStatus('uploading');
    setUploadProgress(0);
    setError(null);

    try {
      // 创建 FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title.trim());
      if (description.trim()) {
        formData.append('description', description.trim());
      }

      // 上传文件
      const response = await uploadFile<Material>(
        '/upload',
        formData,
        (progress) => {
          setUploadProgress(progress);
        }
      );

      setUploadedMaterial(response);

      // 检查状态
      if (response.status === 'active' || response.status === 'hidden') {
        setUploadStatus('success');
        // 上传成功，跳转到详情页
        router.push(`/materials/${response.id}`);
        return true;
      } else if (response.status === 'processing') {
        setUploadStatus('processing');
        // 缩略图生成中，也跳转到详情页
        router.push(`/materials/${response.id}`);
        return true;
      } else {
        setUploadStatus('error');
        setError({
          type: 'UPLOAD_FAILED',
          message: '上传处理失败，请稍后重试。',
        });
        return false;
      }
    } catch (err) {
      setUploadStatus('error');
      let errorMessage = '上传失败，请稍后重试。';

      if (err instanceof Error) {
        errorMessage = err.message;
      }

      // 处理特定的错误类型
      if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        errorMessage = '登录已过期，请重新登录。';
      } else if (errorMessage.includes('413') || errorMessage.includes('Payload Too Large')) {
        errorMessage = '文件过大，请检查文件大小限制。';
      } else if (errorMessage.includes('415') || errorMessage.includes('Unsupported Media Type')) {
        errorMessage = '不支持的文件格式。';
      }

      setError({
        type: 'UPLOAD_FAILED',
        message: errorMessage,
      });
      return false;
    } finally {
      isUploadingRef.current = false;
    }
  }, [file, title, description, validateForm, router]);

  // 重置状态
  const reset = useCallback(() => {
    setFileState(null);
    setTitleState('');
    setDescriptionState('');
    setUploadProgress(0);
    setUploadStatus('idle');
    setError(null);
    setUploadedMaterial(null);
    isUploadingRef.current = false;
  }, []);

  return {
    // 状态
    file,
    title,
    description,
    uploadProgress,
    uploadStatus,
    error,
    uploadedMaterial,

    // 操作
    setFile,
    setTitle,
    setDescription,
    validateAndSetFile,
    upload,
    reset,

    // 验证函数
    validateFile,
    validateForm,
  };
}

// 导出常量
export {
  ALLOWED_TYPES,
  ALLOWED_VIDEO_TYPES,
  ALLOWED_PDF_TYPES,
  ALLOWED_OFFICE_TYPES,
  MAX_VIDEO_SIZE,
  MAX_PDF_SIZE,
  MAX_OFFICE_SIZE,
};

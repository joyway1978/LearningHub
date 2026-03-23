# API 文档

本文档详细说明 AI Learning Platform 的所有 API 端点。

## 目录

- [基础信息](#基础信息)
- [认证方式](#认证方式)
- [错误处理](#错误处理)
- [认证模块](#认证模块)
- [课件模块](#课件模块)
- [上传模块](#上传模块)
- [管理员模块](#管理员模块)

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **API版本**: v1
- **内容类型**: `application/json`

### 健康检查

```http
GET /health
```

**响应示例**:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### 数据库健康检查

```http
GET /api/v1/health/db
```

**响应示例**:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

## 认证方式

API 使用 JWT (JSON Web Token) 进行认证。

### 获取 Token

1. 调用登录接口获取 `access_token`
2. 在后续请求的 Header 中添加: `Authorization: Bearer <token>`

### Token 有效期

- **Access Token**: 默认30分钟 (可通过 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置)
- **Refresh Token**: 7天

### 刷新 Token

当 Access Token 过期时，使用 Refresh Token 获取新的 Token：

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

## 错误处理

所有错误响应都遵循统一的格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

### 错误码列表

| HTTP状态码 | 错误码 | 描述 |
|-----------|--------|------|
| 400 | `EMAIL_ALREADY_EXISTS` | 邮箱已被注册 |
| 400 | `INVALID_TYPE` | 无效的课件类型 |
| 400 | `VALIDATION_ERROR` | 请求参数验证失败 |
| 400 | `ALREADY_DELETED` | 课件已被删除 |
| 400 | `INVALID_STATUS` | 无效的课件状态 |
| 401 | `UNAUTHORIZED` | 未认证或Token无效 |
| 401 | `INVALID_TOKEN` | Token无效或已过期 |
| 401 | `USER_NOT_FOUND` | 用户不存在 |
| 403 | `FORBIDDEN` | 无权限访问 |
| 403 | `INACTIVE_USER` | 用户账号已禁用 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 404 | `JOB_NOT_FOUND` | 定时任务不存在 |
| 413 | `FILE_TOO_LARGE` | 文件过大 |
| 415 | `UNSUPPORTED_FILE_TYPE` | 不支持的文件类型 |
| 422 | `VALIDATION_ERROR` | 请求格式错误 |
| 429 | `RATE_LIMIT_EXCEEDED` | 请求过于频繁 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |
| 500 | `UPLOAD_FAILED` | 文件上传失败 |
| 500 | `CLEANUP_FAILED` | 清理任务失败 |
| 503 | `DATABASE_ERROR` | 数据库连接失败 |

## 认证模块

### 用户注册

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "用户名",
  "password": "your-password"
}
```

**请求参数**:

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| email | string | 是 | 用户邮箱，需唯一 |
| name | string | 是 | 用户名，1-100字符 |
| password | string | 是 | 密码，至少8字符 |

**成功响应** (201 Created):

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "用户名",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2024-01-15T08:30:00"
}
```

**错误响应**:

- `400 EMAIL_ALREADY_EXISTS`: 邮箱已被注册

### 用户登录

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**请求参数**:

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| email | string | 是 | 用户邮箱 |
| password | string | 是 | 用户密码 |

**成功响应** (200 OK):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "用户名",
    "avatar_url": null,
    "is_active": true,
    "created_at": "2024-01-15T08:30:00"
  }
}
```

**错误响应**:

- `401 UNAUTHORIZED`: 邮箱或密码错误

### 获取当前用户信息

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**成功响应** (200 OK):

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "用户名",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2024-01-15T08:30:00"
}
```

### 刷新 Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**成功响应** (200 OK):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 用户登出

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

**成功响应** (200 OK):

```json
{
  "message": "Successfully logged out",
  "detail": "Please discard your tokens on the client side"
}
```

## 课件模块

### 获取课件列表

```http
GET /api/v1/materials?page=1&page_size=20&sort_by=created_at&sort_order=desc&material_type=video
```

**查询参数**:

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码，从1开始 |
| page_size | integer | 否 | 20 | 每页数量，最大100 |
| sort_by | string | 否 | created_at | 排序字段: created_at, view_count, like_count |
| sort_order | string | 否 | desc | 排序方向: asc, desc |
| material_type | string | 否 | - | 筛选类型: video, pdf |

**成功响应** (200 OK):

```json
{
  "items": [
    {
      "id": 1,
      "title": "课件标题",
      "description": "课件描述",
      "type": "video",
      "file_path": "materials/1/20240115_083000_video.mp4",
      "file_size": 10485760,
      "file_format": "mp4",
      "thumbnail_path": "thumbnails/1/1.jpg",
      "uploader_id": 1,
      "uploader_name": "用户名",
      "uploader_avatar": null,
      "view_count": 100,
      "like_count": 50,
      "status": "active",
      "created_at": "2024-01-15T08:30:00",
      "updated_at": "2024-01-15T08:30:00",
      "is_liked": false
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 获取课件详情

```http
GET /api/v1/materials/{material_id}
Authorization: Bearer <token> (可选)
```

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| material_id | integer | 课件ID |

**成功响应** (200 OK):

```json
{
  "id": 1,
  "title": "课件标题",
  "description": "课件描述",
  "type": "video",
  "file_path": "materials/1/20240115_083000_video.mp4",
  "file_size": 10485760,
  "file_format": "mp4",
  "thumbnail_path": "thumbnails/1/1.jpg",
  "uploader_id": 1,
  "uploader_name": "用户名",
  "uploader_avatar": null,
  "view_count": 100,
  "like_count": 50,
  "status": "active",
  "created_at": "2024-01-15T08:30:00",
  "updated_at": "2024-01-15T08:30:00",
  "is_liked": false,
  "related_materials": [
    {
      "id": 2,
      "title": "相关课件",
      "type": "video",
      "thumbnail_path": "thumbnails/1/2.jpg",
      "view_count": 80,
      "like_count": 30
    }
  ]
}
```

**错误响应**:

- `404 NOT_FOUND`: 课件不存在或已删除

### 删除课件

```http
DELETE /api/v1/materials/{material_id}
Authorization: Bearer <token>
```

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| material_id | integer | 课件ID |

**成功响应** (204 No Content)

**错误响应**:

- `403 FORBIDDEN`: 只能删除自己上传的课件
- `404 NOT_FOUND`: 课件不存在
- `400 ALREADY_DELETED`: 课件已被删除

### 点赞/取消点赞

```http
POST /api/v1/materials/{material_id}/like
Authorization: Bearer <token>
```

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| material_id | integer | 课件ID |

**成功响应** (200 OK):

```json
{
  "is_liked": true,
  "like_count": 51
}
```

**说明**:
- 如果用户已点赞，调用此接口会取消点赞
- 如果用户未点赞，调用此接口会添加点赞

**错误响应**:

- `404 NOT_FOUND`: 课件不存在
- `400 INVALID_STATUS`: 无法对隐藏课件点赞

## 上传模块

### 上传文件

```http
POST /api/v1/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="video.mp4"
Content-Type: video/mp4

<文件内容>
------WebKitFormBoundary
Content-Disposition: form-data; name="title"

课件标题
------WebKitFormBoundary
Content-Disposition: form-data; name="description"

课件描述
------WebKitFormBoundary--
```

**请求参数**:

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| file | file | 是 | 上传的文件 |
| title | string | 是 | 课件标题，1-255字符 |
| description | string | 否 | 课件描述 |

**文件限制**:

| 类型 | 格式 | 最大大小 |
|------|------|---------|
| 视频 | mp4, webm | 500MB |
| PDF | pdf | 50MB |

**成功响应** (201 Created):

```json
{
  "id": 1,
  "title": "课件标题",
  "description": "课件描述",
  "type": "video",
  "file_path": "materials/1/20240115_083000_video.mp4",
  "file_size": 10485760,
  "file_format": "mp4",
  "thumbnail_path": null,
  "uploader_id": 1,
  "view_count": 0,
  "like_count": 0,
  "status": "active",
  "created_at": "2024-01-15T08:30:00",
  "updated_at": "2024-01-15T08:30:00"
}
```

**错误响应**:

- `413 FILE_TOO_LARGE`: 文件超过大小限制
- `415 UNSUPPORTED_FILE_TYPE`: 不支持的文件类型
- `500 UPLOAD_FAILED`: 上传失败

### 查询上传状态

```http
GET /api/v1/upload/status/{material_id}
Authorization: Bearer <token>
```

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| material_id | integer | 课件ID |

**成功响应** (200 OK):

```json
{
  "material_id": 1,
  "status": "active",
  "progress": 100,
  "message": "Upload complete and ready",
  "thumbnail_path": "thumbnails/1/1.jpg",
  "has_thumbnail": true
}
```

**状态说明**:

| 状态 | 进度 | 说明 |
|------|------|------|
| processing | 50 | 文件上传中 |
| active | 100 | 上传完成，可用 |
| hidden | 100 | 已隐藏/删除 |

### 查询缩略图状态

```http
GET /api/v1/upload/thumbnail-status/{material_id}
Authorization: Bearer <token>
```

**成功响应** (200 OK):

```json
{
  "material_id": 1,
  "thumbnail_status": "completed",
  "thumbnail_path": "thumbnails/1/1.jpg",
  "has_thumbnail": true
}
```

**缩略图状态**:

| 状态 | 说明 |
|------|------|
| pending | 等待生成 |
| completed | 生成完成 |
| failed | 生成失败(使用占位图) |

### 删除上传的课件

```http
DELETE /api/v1/upload/{material_id}
Authorization: Bearer <token>
```

**说明**: 此接口会彻底删除课件文件和数据库记录(软删除)。

## 管理员模块

**注意**: 以下接口需要管理员权限。

### 手动触发清理任务

```http
POST /api/v1/admin/cleanup
Content-Type: application/json
Authorization: Bearer <token>

{
  "cleanup_processing": true,
  "cleanup_orphans": true,
  "max_age_minutes": 30
}
```

**请求参数**:

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| cleanup_processing | boolean | 否 | true | 清理过期的processing记录 |
| cleanup_orphans | boolean | 否 | true | 清理孤儿文件 |
| max_age_minutes | integer | 否 | 30 | processing记录最大保留时间 |

**成功响应** (200 OK):

```json
{
  "success": true,
  "cleaned_records": 5,
  "cleaned_files": 3,
  "duration_seconds": 2.5,
  "errors": []
}
```

### 获取调度器状态

```http
GET /api/v1/admin/scheduler/status
Authorization: Bearer <token>
```

**成功响应** (200 OK):

```json
{
  "running": true,
  "jobs": [
    {
      "id": "cleanup_job",
      "name": "cleanup_stale_records",
      "next_run_time": "2024-01-15T09:00:00"
    }
  ]
}
```

### 暂停定时任务

```http
POST /api/v1/admin/scheduler/jobs/{job_id}/pause
Authorization: Bearer <token>
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "message": "Job cleanup_job paused successfully",
  "job_id": "cleanup_job"
}
```

### 恢复定时任务

```http
POST /api/v1/admin/scheduler/jobs/{job_id}/resume
Authorization: Bearer <token>
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "message": "Job cleanup_job resumed successfully",
  "job_id": "cleanup_job"
}
```

## 数据模型

### User (用户)

```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "用户名",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_active": true,
  "created_at": "2024-01-15T08:30:00"
}
```

### Material (课件)

```json
{
  "id": 1,
  "title": "课件标题",
  "description": "课件描述",
  "type": "video",
  "file_path": "materials/1/20240115_083000_video.mp4",
  "file_size": 10485760,
  "file_format": "mp4",
  "thumbnail_path": "thumbnails/1/1.jpg",
  "uploader_id": 1,
  "view_count": 100,
  "like_count": 50,
  "status": "active",
  "created_at": "2024-01-15T08:30:00",
  "updated_at": "2024-01-15T08:30:00"
}
```

**状态枚举**:
- `processing`: 处理中
- `active`: 可用
- `hidden`: 已隐藏/删除

**类型枚举**:
- `video`: 视频
- `pdf`: PDF文档

## 分页说明

列表接口都支持分页，响应包含以下分页信息：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**计算总页数**: `total_pages = ceil(total / page_size)`

## 速率限制

API 默认没有启用速率限制。如需启用，可以在 Nginx 或应用层配置。

## 文件访问

上传的文件通过 MinIO 提供访问，URL 格式：

```
http://localhost:9000/materials/{file_path}
```

生产环境建议配置 CDN 或反向代理。

---

**文档版本**: 1.0.0
**最后更新**: 2024-01-15

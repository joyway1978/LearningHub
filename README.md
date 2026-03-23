# AI Learning Platform - AI教学展示平台

一个功能完整的AI教学展示平台，支持视频和PDF课件的浏览、上传、点赞和分享。

## 功能特性

- **用户认证系统**: 注册、登录、JWT Token认证
- **课件管理**: 支持视频(mp4, webm)和PDF文件的上传和展示
- **浏览功能**: 课件列表、详情查看、缩略图展示
- **互动功能**: 点赞、浏览量统计(10分钟内重复浏览去重)
- **后台管理**: 定时清理任务、系统监控
- **响应式设计**: 支持桌面和移动设备

## 技术栈

### 前端
- **Next.js 14** - React框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Axios** - HTTP客户端

### 后端
- **FastAPI** - Python异步Web框架
- **SQLAlchemy 2.0** - ORM数据库操作
- **MySQL 8.0** - 关系型数据库
- **MinIO** - 对象存储服务
- **JWT** - 用户认证
- **APScheduler** - 定时任务调度

### 部署
- **Docker** - 容器化部署
- **Docker Compose** - 多服务编排

## 快速开始

### 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Git

### 安装步骤

1. **克隆仓库**

```bash
git clone <repository-url>
cd learn_ai_hub
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的参数
```

3. **启动服务**

```bash
docker-compose up -d
```

4. **访问应用**

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- MinIO控制台: http://localhost:9001

### 使用 Makefile (可选)

```bash
# 启动所有服务
make up

# 停止所有服务
make down

# 查看日志
make logs

# 运行测试
make test

# 数据库迁移
make migrate
```

## 使用说明

### 用户注册和登录

1. 访问 http://localhost:3000/register 注册账号
2. 使用注册的邮箱和密码登录
3. 登录后会自动跳转到课件列表页

### 上传课件

1. 点击"上传课件"按钮
2. 选择文件(支持视频和PDF)
3. 填写标题和描述
4. 等待上传完成

### 浏览课件

1. 在课件列表页浏览所有课件
2. 点击课件卡片查看详情
3. 支持按类型筛选和排序

### 点赞功能

1. 在课件详情页点击点赞按钮
2. 再次点击取消点赞
3. 点赞数会实时更新

## 项目结构

```
learn_ai_hub/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── core/              # 核心模块
│   │   │   ├── security.py    # JWT认证
│   │   │   ├── storage.py     # MinIO存储
│   │   │   ├── tasks.py       # 异步任务
│   │   │   └── scheduler.py   # 定时任务
│   │   ├── crud/              # 数据库操作
│   │   ├── dependencies/      # 依赖注入
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API路由
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   └── main.py            # 应用入口
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # 测试文件
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # 前端服务
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   │   ├── login/         # 登录页
│   │   │   ├── register/      # 注册页
│   │   │   ├── materials/     # 课件列表
│   │   │   ├── upload/        # 上传页
│   │   │   └── material/      # 课件详情
│   │   ├── components/        # 组件
│   │   ├── hooks/             # 自定义Hooks
│   │   ├── lib/               # 工具函数
│   │   └── types/             # TypeScript类型
│   ├── public/                # 静态资源
│   ├── Dockerfile
│   └── package.json
├── docs/                       # 文档
│   ├── API.md                 # API文档
│   ├── DEPLOYMENT.md          # 部署指南
│   ├── DESIGN.md              # 设计文档
│   └── TEST_PLAN.md           # 测试计划
├── docker-compose.yml          # Docker编排配置
├── .env.example               # 环境变量模板
├── .gitignore
├── Makefile                   # 常用命令
└── README.md                  # 项目说明
```

## API文档

详细的API文档请查看 [docs/API.md](docs/API.md)

主要API端点:

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/me` | GET | 获取当前用户信息 |
| `/api/v1/materials` | GET | 获取课件列表 |
| `/api/v1/materials/{id}` | GET | 获取课件详情 |
| `/api/v1/materials/{id}` | DELETE | 删除课件 |
| `/api/v1/materials/{id}/like` | POST | 点赞/取消点赞 |
| `/api/v1/upload` | POST | 上传文件 |
| `/api/v1/upload/status/{id}` | GET | 查询上传状态 |
| `/api/v1/admin/cleanup` | POST | 手动清理(管理员) |

## 部署指南

生产环境部署请参考 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 测试

### 后端测试

```bash
cd backend
pytest --cov=app tests/
```

### 前端测试

```bash
cd frontend
npm test
```

## 环境变量

### 数据库配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MYSQL_ROOT_PASSWORD | MySQL root密码 | rootpassword |
| MYSQL_DATABASE | 数据库名 | ai_learning |
| MYSQL_USER | 数据库用户 | app_user |
| MYSQL_PASSWORD | 数据库密码 | app_password |

### MinIO配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| MINIO_ROOT_USER | MinIO用户名 | minioadmin |
| MINIO_ROOT_PASSWORD | MinIO密码 | minioadmin |
| MINIO_BUCKET_NAME | 存储桶名 | materials |

### 后端配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SECRET_KEY | JWT密钥 | your-secret-key-change-in-production |
| ALGORITHM | JWT算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token过期时间(分钟) | 30 |
| ALLOWED_ORIGINS | 允许的跨域来源 | http://localhost:3000 |

### 前端配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| NEXT_PUBLIC_API_URL | API地址 | http://localhost:8000 |
| API_URL | 服务端API地址 | http://backend:8000 |

## 开发指南

### 本地开发

1. **启动数据库和存储服务**

```bash
docker-compose up -d mysql minio
```

2. **启动后端开发服务器**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **启动前端开发服务器**

```bash
cd frontend
npm install
npm run dev
```

### 数据库迁移

```bash
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**注意**: 生产环境部署前，请务必修改默认的密码和密钥配置。

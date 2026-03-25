# AI Learning Platform - AI教学展示平台

[![GitHub](https://img.shields.io/badge/GitHub-joyway1978%2Flearning_hub-blue)](https://github.com/joyway1978/learning_hub)

一个功能完整的AI教学展示平台，支持视频和PDF课件的浏览、上传、点赞和分享。采用 Brutally Minimal 设计风格，界面简洁高效。

## 📸 界面预览

### 首页 - 课件列表
![首页](https://raw.githubusercontent.com/joyway1978/learning_hub/main/screenshots/homepage.png)

### 移动端适配
![移动端首页](https://raw.githubusercontent.com/joyway1978/learning_hub/main/screenshots/mobile-homepage.png)

### 搜索功能
![搜索](https://raw.githubusercontent.com/joyway1978/learning_hub/main/screenshots/search.png)

### 分类筛选
![PDF筛选](https://raw.githubusercontent.com/joyway1978/learning_hub/main/screenshots/filter-pdf.png)

### 上传课件
![上传页面](https://raw.githubusercontent.com/joyway1978/learning_hub/main/screenshots/upload-page.png)

### 登录页面
![登录页面](https://raw.githubusercontent.com/joyway1978/learning_hub/main/screenshots/login-page.png)

## ✨ 功能特性

- **用户认证系统**: 注册、登录、JWT Token认证、Token自动刷新
- **课件管理**: 支持视频(mp4, webm, mov, avi, mkv)和PDF文件的上传和展示
- **智能处理**: 自动生成视频首帧和PDF首页缩略图
- **浏览功能**: 课件列表、详情查看、缩略图展示、分页加载
- **搜索筛选**: 支持按标题搜索、按类型筛选(PDF/视频)、多种排序(最新/最热/最多点赞)
- **互动功能**: 点赞、浏览量统计(10分钟内重复浏览去重)
- **响应式设计**: 完美支持桌面和移动设备
- **启动脚本**: 一键启动/停止前后端服务，支持自定义端口

## 🛠️ 技术栈

### 前端
- **Next.js 14** - React框架，App Router
- **TypeScript** - 类型安全
- **Tailwind CSS** - 原子化CSS框架
- **Axios** - HTTP客户端
- **Jest** + **React Testing Library** - 单元测试

### 后端
- **FastAPI** - Python异步Web框架
- **SQLAlchemy 2.0** - ORM数据库操作
- **MySQL 8.0** - 关系型数据库
- **MinIO** - 对象存储服务
- **JWT** - 用户认证
- **APScheduler** - 定时任务调度
- **Pytest** - 单元测试

### 部署
- **Docker** - 容器化部署
- **Docker Compose** - 多服务编排

## 🚀 快速开始

### 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Git
- Node.js >= 18 (本地开发)
- Python >= 3.9 (本地开发)

### 方式一：Docker部署（推荐）

1. **克隆仓库**

```bash
git clone git@github.com:joyway1978/learning_hub.git
cd learning_hub
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

### 方式二：使用启动脚本（本地开发）

我们提供了一个便捷的启动脚本 `start.sh`，支持灵活的服务管理：

```bash
# 启动前后端服务（默认端口：前端3000，后端8000）
./start.sh

# 只启动前端
./start.sh start -f

# 只启动后端
./start.sh start -b

# 指定端口启动
./start.sh start --frontend-port 3001 --backend-port 8001

# 停止服务
./start.sh stop

# 重启服务
./start.sh restart

# 查看服务状态
./start.sh status
```

### 使用 Makefile

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

## 📖 使用说明

### 用户注册和登录

1. 访问 http://localhost:3000/register 注册账号
2. 使用注册的邮箱和密码登录
3. 登录后会自动跳转到课件列表页

### 上传课件

1. 点击"上传课件"按钮进入上传页面
2. 拖拽或点击选择文件（支持视频和PDF）
3. 填写课件标题和描述（描述可选，最多500字）
4. 点击"上传课件"按钮
5. 等待上传完成，系统会自动生成缩略图

### 浏览课件

1. 在课件列表页浏览所有课件
2. 使用搜索框按标题搜索课件
3. 使用筛选按钮按类型筛选（全部/视频/PDF）
4. 使用排序按钮切换排序方式（最新/最热/最多点赞）
5. 点击课件卡片查看详情

### 点赞功能

1. 在课件详情页点击点赞按钮
2. 再次点击取消点赞
3. 点赞数会实时更新

## 📁 项目结构

```
learn_ai_hub/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── core/              # 核心模块
│   │   │   ├── security.py    # JWT认证
│   │   │   ├── storage.py     # MinIO存储
│   │   │   ├── scheduler.py   # 定时任务
│   │   │   └── cleanup.py     # 清理任务
│   │   ├── crud/              # 数据库操作
│   │   ├── dependencies/      # 依赖注入
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API路由
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── file_validation.py
│   │   │   ├── thumbnail_service.py
│   │   │   └── view_service.py
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
│   │   │   ├── upload/        # 上传页
│   │   │   ├── materials/     # 课件列表
│   │   │   └── profile/       # 用户资料
│   │   ├── components/        # React组件
│   │   │   ├── ui/            # UI基础组件
│   │   │   ├── MaterialCard.tsx
│   │   │   ├── MaterialFilters.tsx
│   │   │   ├── LikeButton.tsx
│   │   │   └── VideoPlayer.tsx
│   │   ├── hooks/             # 自定义Hooks
│   │   │   ├── useMaterials.ts
│   │   │   ├── useMaterialDetail.ts
│   │   │   └── useUpload.ts
│   │   ├── lib/               # 工具函数
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   └── utils.ts
│   │   └── types/             # TypeScript类型
│   ├── public/images/         # 静态图片资源
│   ├── tests/                 # 测试文件
│   ├── Dockerfile
│   └── package.json
├── docs/                       # 文档
│   ├── API.md                 # API文档
│   ├── DEPLOYMENT.md          # 部署指南
│   ├── DESIGN.md              # 设计文档
│   ├── DESIGN_SYSTEM.md       # 设计系统
│   └── TEST_PLAN.md           # 测试计划
├── screenshots/               # 项目截图
├── docker-compose.yml         # Docker编排配置
├── start.sh                   # 启动脚本
├── .env.example               # 环境变量模板
├── .gitignore
├── Makefile                   # 常用命令
└── README.md                  # 项目说明
```

## 🔌 API文档

详细的API文档请查看 [docs/API.md](docs/API.md)

主要API端点:

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/refresh` | POST | 刷新Token |
| `/api/v1/auth/me` | GET | 获取当前用户信息 |
| `/api/v1/materials` | GET | 获取课件列表 |
| `/api/v1/materials/{id}` | GET | 获取课件详情 |
| `/api/v1/materials/{id}` | PUT | 更新课件 |
| `/api/v1/materials/{id}` | DELETE | 删除课件 |
| `/api/v1/materials/{id}/like` | POST | 点赞/取消点赞 |
| `/api/v1/materials/{id}/view` | POST | 记录浏览 |
| `/api/v1/upload` | POST | 上传文件 |
| `/api/v1/upload/status/{id}` | GET | 查询上传状态 |

## 🧪 测试

### 后端测试

```bash
cd backend
pytest --cov=app tests/
```

测试覆盖:
- 用户认证（注册、登录、Token刷新）
- 课件管理（CRUD操作）
- 点赞功能
- 文件上传

### 前端测试

```bash
cd frontend
npm test
```

测试覆盖:
- UI组件（Button、Input）
- 业务组件（MaterialCard、LikeButton）
- 自定义Hooks（useMaterials、useUpload、useMaterialDetail）
- 工具函数（api、auth、utils）

## 🔧 环境变量

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
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh Token过期时间(天) | 7 |
| ALLOWED_ORIGINS | 允许的跨域来源 | http://localhost:3000 |

### 前端配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| NEXT_PUBLIC_API_URL | API地址 | http://localhost:8000 |
| API_URL | 服务端API地址 | http://backend:8000 |

## 📝 开发指南

### 本地开发

1. **启动数据库和存储服务**

```bash
docker-compose up -d mysql minio
```

2. **启动后端开发服务器**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
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

## 🚀 部署指南

生产环境部署请参考 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### 快速部署步骤

1. 配置生产环境变量
2. 使用 Docker Compose 启动服务
3. 配置反向代理（Nginx/Caddy）
4. 配置 SSL 证书
5. 完成！

## 🐛 最近更新

### v1.1.0 (2024-03)
- ✅ 添加启动脚本 `start.sh`，支持灵活的服务管理
- ✅ 添加全面的前端测试套件（Hooks、组件、工具函数）
- ✅ 修复图片资源 404 错误，添加默认占位图
- ✅ 优化 UI 组件，添加 Button 类型属性

### v1.0.0 (2024-03)
- ✅ 用户注册、登录、JWT认证
- ✅ 课件上传（视频/PDF）
- ✅ 课件浏览、搜索、筛选、排序
- ✅ 点赞功能
- ✅ 响应式设计
- ✅ Docker 部署支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📞 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

**GitHub仓库**: https://github.com/joyway1978/learning_hub

---

**注意**: 生产环境部署前，请务必修改默认的密码和密钥配置。

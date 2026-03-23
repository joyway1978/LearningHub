# CLAUDE.md

## 项目概览

**AI教学展示平台** — 公司内部AI学习资料分享平台

- 技术栈: Next.js 14 + Tailwind CSS + FastAPI + MySQL + MinIO
- 分支: master
- 文档位置: `/docs/`

## 设计系统

**重要**: 所有视觉和UI决策必须遵循设计系统。

设计系统文档: [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md)

### 关键设计决策

- **美学**: Brutally Minimal（极致极简）— 类似 Notion/Dropbox Paper
- **主色**: 深靛蓝 `#1a1a2e`
- **强调色**: 暖琥珀 `#f59e0b`（用于点赞按钮）
- **字体**: Inter (正文) + JetBrains Mono (代码/数据)
- **间距**: 8px 基础单位

### 开发前必读

1. 阅读 [`docs/DESIGN.md`](./docs/DESIGN.md) — 产品需求和架构设计
2. 阅读 [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md) — 视觉设计规范
3. 查看 [`docs/DESIGN_PREVIEW.html`](./docs/DESIGN_PREVIEW.html) — 设计效果预览
4. 阅读 [`docs/TEST_PLAN.md`](./docs/TEST_PLAN.md) — 测试计划

### 设计原则

- **内容优先**: 界面不抢夺内容注意力
- **效率至上**: 信息架构清晰，支持快速发现
- **反馈即时**: 点赞、浏览统计实时可见
- **克制装饰**: 用排版和色彩层级传达信息

## 开发规范

### 代码组织

```
learn_ai_hub/
├── docker-compose.yml
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── routers/      # API 路由
│   │   ├── services/     # 业务逻辑
│   │   └── tasks/        # 异步任务
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Next.js 前端
│   ├── app/              # App Router
│   ├── components/       # React 组件
│   └── lib/              # 工具函数
└── docs/                 # 文档
    ├── DESIGN.md
    ├── DESIGN_SYSTEM.md
    ├── DESIGN_PREVIEW.html
    └── TEST_PLAN.md
```

### 测试要求

- 单元测试: 后端服务层、工具函数
- 集成测试: API 路由、数据库操作
- E2E 测试: 关键路径（登录→上传→浏览→点赞）

## 审查流程

- `/office-hours` — 产品设计讨论
- `/plan-eng-review` — 工程审查（必需）
- `/design-consultation` — 设计系统（已完成）
- `/ship` — 部署前最终检查

## 注意事项

- 所有 UI 代码必须符合 `DESIGN_SYSTEM.md` 规范
- 不符合设计系统的代码会被标记
- 如有设计疑问，参考设计预览文件或咨询设计文档

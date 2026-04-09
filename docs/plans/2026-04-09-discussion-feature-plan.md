# 讨论功能实施计划

**日期**: 2026-04-09
**分支**: main
**状态**: 已批准（/autoplan 审查完成）

## 问题陈述

当前平台用户只能被动浏览和点赞课件，缺乏轻量化的互动方式来表达反馈（如"有帮助"、"困惑"、"有启发"）。需要一个低摩擦的反馈机制来衡量内容质量和员工参与度的初步信号。

## 目标

为课件详情页添加轻量级反馈功能，先从 Reactions 开始验证参与度：
- 用户对课件快速表达情绪反馈（👍 👎 ❓ 💡）
- 每种反应的数量统计
- 简单的文字评论作为第二阶段（在 Reactions 验证通过后）
- 用户可以看到自己的反应历史

## 前提假设

1. 用户已登录才能点反应
2. 员工更愿意点击表情而不是写文字
3. 反应数据能帮助识别内容质量问题
4. 反应功能实施快速，可快速上线验证

## 范围

### 范围内（MVP - Reactions 优先）
- Reaction 数据模型（MaterialReaction）
- Reaction API（添加/取消反应）
- Reaction 组件（表情选择器、统计展示）
- 用户反应状态持久化
- 反应数据统计（每种反应的数量）

### 范围外（Phase 2，验证后实施）
- ~~嵌套评论回复~~ → 推迟到验证后
- ~~@提及功能~~ → 推迟到验证后
- ~~评论通知中心~~ → 推迟到验证后
- ~~内容审核工作流~~ → 避免 Reactions 的审核问题
- ~~富文本编辑器~~ → 始终范围外
- ~~图片/附件评论~~ → 始终范围外

### 暂缓（因缺少前提条件）
- 文字评论（需要 username 字段、审核机制）
- @提及功能（需要用户搜索基础设施）
- 通知系统（需要批量策略）

## 技术方案

### 数据模型

```python
class MaterialReaction(Base):
    """课件反应表 - MVP 简化版"""
    id: int PK
    material_id: int FK → materials
    user_id: int FK → users
    reaction_type: str  # Enum: 'thumbs_up', 'thumbs_down', 'question', 'insight'
    created_at: datetime
    updated_at: datetime  # 用于切换反应类型

    __table_args__ = (
        UniqueConstraint('material_id', 'user_id', name='uq_material_user_reaction'),
    )

# Phase 2: 文字评论（验证后实施）
# class Comment(Base): ...
# class CommentMention(Base): ...
```

#### 实现细节

**错误处理**:
| 错误场景 | HTTP 状态 | 错误信息 |
|----------|-----------|----------|
| 无效 reaction_type | 400 | `"reaction_type must be one of: thumbs_up, thumbs_down, question, insight"` |
| 未登录 | 401 | `"Authentication required"` |
| 课件不存在 | 404 | `"Material not found"` |
| 重复反应（并发） | 409 | `"Reaction already exists"`（客户端应刷新状态）|

**安全考虑**:
- 使用数据库事务确保切换反应的原子性
- 验证 reaction_type 在允许列表中（防止存储无效值）
- 添加速率限制：10次/分钟/IP
- 防止用户为其他用户添加反应（严格 user_id 隔离）

**性能优化**:
- 反应统计使用计数器缓存（与 like_count 类似）
- 查询使用 `(material_id, user_id)` 复合索引
- 切换反应时先 DELETE 再 INSERT 确保原子性

### API设计

```
# MVP - Reactions
POST   /materials/{id}/reactions          添加/更新反应（toggle）
DELETE /materials/{id}/reactions          取消反应
GET    /materials/{id}/reactions          获取反应统计
GET    /materials/{id}/reactions/me       获取当前用户的反应状态

# Phase 2（验证后实施）
# POST   /materials/{id}/comments
# GET    /materials/{id}/comments
# ... 等等
```

### 前端组件

```
ReactionSection (课件详情页底部，点赞按钮下方)
├── ReactionBar (反应选择器) - 水平排列，gap: 12px
│   ├── ReactionButton (👍 有用) - tooltip: "有帮助"
│   ├── ReactionButton (👎 没帮助) - tooltip: "没帮助"
│   ├── ReactionButton (❓ 有疑问) - tooltip: "有疑问"
│   └── ReactionButton (💡 有启发) - tooltip: "有启发"
├── ReactionStats (反应统计展示)
│   └── 每种反应的计数（tabular-nums 对齐）
└── UserReactionState（当前用户反应状态）

# Phase 2: 文字评论（验证后实施）
# CommentSection
# └── ...
```

#### 设计规范

**ReactionButton 样式**:
- 尺寸: 40px x 40px（移动端 44px）
- 边框: 1px solid `#e7e5e4`
- 圆角: 4px（符合设计系统克制原则）
- 字体大小: 20px

**状态规范**:
| 状态 | 样式 |
|------|------|
| 默认 | 灰色边框 `#e7e5e4`，emoji 灰度 filter: grayscale(100%) |
| 悬停 | 边框 `#d6d3d1`，emoji 彩色，cursor: pointer |
| 已选中 | 边框 `#1a1a2e`，背景 `#f5f5f4`，emoji 彩色 |
| 加载中 | opacity: 0.6，cursor: not-allowed |
| 错误 | 边框 `#ef4444`，tooltip 显示错误信息 |
| 未登录 | 点击触发登录弹窗 |

**交互细节**:
- 点击后即时本地状态更新（乐观更新）
- API 失败时回滚状态，显示 toast 错误
- 切换反应类型时自动取消之前的反应
- 键盘导航: Tab 切换焦点，Enter/Space 选择
- ARIA: `aria-pressed` 表示选中状态

**位置**:
- 位于课件详情页信息面板底部
- 在点赞按钮下方，水平排列
- 与点赞按钮间距: 16px

**Tooltip**:
- 延迟显示: 300ms
- 位置: 按钮上方居中
- 样式: 深色背景，白色文字，8px 圆角

## 任务清单

### 任务1: 数据库设计和迁移
- [ ] 创建 MaterialReaction 模型（MVP）
- [ ] 添加唯一约束 (material_id, user_id)
- [ ] 生成 Alembic 迁移脚本
- [ ] 执行数据库迁移

### 任务2: Reaction API 实现（MVP）
- [ ] POST /materials/{id}/reactions 接口（toggle）
- [ ] DELETE /materials/{id}/reactions 接口
- [ ] GET /materials/{id}/reactions 接口（统计）
- [ ] GET /materials/{id}/reactions/me 接口（当前用户状态）
- [ ] 反应类型枚举定义

### 任务3: 前端 Reaction 组件（MVP）
- [ ] ReactionButton 组件（单个表情按钮）
- [ ] ReactionBar 组件（表情选择器）
- [ ] ReactionStats 组件（统计展示）
- [ ] ReactionSection 容器组件
- [ ] 集成到课件详情页

### 任务4: 测试（MVP）
- [ ] Reaction API 单元测试
- [ ] 反应切换逻辑测试
- [ ] 未授权访问拒绝测试
- [ ] 无效 reaction_type 输入测试
- [ ] 并发切换反应测试
- [ ] 前端组件测试
- [ ] E2E 测试：添加/取消/切换反应流程

### Phase 2（Reactions 验证通过后实施）
- [ ] 创建 Comment 模型
- [ ] 创建 Comment 相关 API
- [ ] 创建用户名/username 字段（前提条件）
- [ ] 内容审核机制
- [ ] 通知系统（批量策略）
- [ ] 评论前端组件

## 验收标准

### MVP（Reactions）
- [ ] 用户可以对课件点反应（4种表情）
- [ ] 用户可以取消自己的反应
- [ ] 每种反应的计数准确显示
- [ ] 用户可以看到自己对当前课件的反应状态
- [ ] 反应状态在页面刷新后保持
- [ ] 未登录用户不能点反应（401）

### Phase 2（验证后）
- ~~[ ] 用户可以发表评论~~ → 推迟
- ~~[ ] 评论嵌套回复~~ → 推迟
- ~~[ ] @提及功能~~ → 推迟
- ~~[ ] 通知系统~~ → 推迟

## 风险（MVP 调整）

| 风险 | 缓解措施 |
|------|----------|
| Reactions 数据不足以验证需求 | 4周后评估，如参与度<5%则放弃 Phase 2 |
| 表情含义不明确 | 添加 tooltip 说明 |
| 反应类型不足 | Phase 2 可根据反馈添加更多选项 |

## 估计工作量（MVP 调整后）

| 任务 | 估计时间 |
|------|----------|
| 数据库设计 | 1h |
| Reaction API | 3h |
| 前端组件 | 4h |
| 测试 | 2h |
| **总计** | **~10h** |

### 与完整评论方案对比

| 方案 | 时间 | 复杂度 | 风险 |
|------|------|--------|------|
| Reactions MVP | ~10h | 低 | 低（无审核问题） |
| 完整评论系统 | ~28h | 高 | 高（审核、通知、username 字段） |
| **节省** | **~18h** | — | — |

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | CLEAR (via /autoplan) | Reactions MVP approved, 完整评论推迟 |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR (via /autoplan) | 架构合理，测试清单已补充 |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | CLEAR (via /autoplan) | 7/10 → 8/10，设计规范已添加 |
| DX Review | `/plan-devex-review` | Developer experience gaps | 1 | CLEAR (via /autoplan) | 8/10，API 设计合理 |

**CROSS-MODEL**: CEO 和 Eng Review 均建议简化验证优先，共识达成。

**UNRESOLVED**: 0

**VERDICT**: CEO + ENG + DESIGN + DX CLEARED — 准备实施。运行 `/ship` 当准备创建 PR。

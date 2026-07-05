# Prompt Lab — Day5 多技术栈 AI 加速 Web 应用

同一个 AI 提示词实验管理工具，用三种完全不同的技术栈实现。使用 Claude Code 辅助开发。

## 三个版本

| 版本 | 技术栈 | 端口 | 文件夹 |
|------|--------|------|--------|
| **MERN** | MongoDB + Express + React + Node.js | 3000 / 5173 | `mern-version/` |
| **Django** | Django 6.0 + Django Templates + SQLite | 8000 | `django-version/` |
| **Spring Boot + Vue** | Spring Boot 3.5 + Vue 3 + H2 | 8080 / 5173 | `springboot-vue-version/` |

## 应用概念

**Prompt Lab** — AI 提示词实验日志。帮助开发者记录、迭代、比较 AI 提示词在不同模型上的表现。

核心功能：
- 管理提示词（创建、查看、编辑、删除）
- 用标签对提示词分类
- 记录每次运行（模型、Token 消耗、响应耗时），支持多次叠加
- 评分和版本追踪

## 数据模型

```
Tag { title, notes }
    ↕ M:N
Prompt { title, content, notes, tags[], runs[], version, rating }
    ↕ 1:N
Run { model, tokens, responseTime }
```

## 每个版本的详细说明

各版本 README 包含完整的前置条件、安装步骤、运行说明和 API 文档。

- [MERN 版本 README](mern-version/README.md)
- [Django 版本 README](django-version/README.md)
- [Spring Boot + Vue 版本 README](springboot-vue-version/README.md)

## 统一 API 格式

三个版本共享相同的 JSON API 契约：

```json
// 成功
{ "success": true, "data": { ... } }
// 失败
{ "success": false, "error": "具体错误描述" }
```

### API 端点

```
GET    /api/tags           — 标签列表
POST   /api/tags           — 创建标签
GET    /api/tags/:id       — 标签详情
PUT    /api/tags/:id       — 更新标签
DELETE /api/tags/:id       — 删除标签

GET    /api/prompts        — 提示词列表
POST   /api/prompts        — 创建提示词
GET    /api/prompts/:id    — 提示词详情
PUT    /api/prompts/:id    — 更新提示词
DELETE /api/prompts/:id    — 删除提示词
```

## 项目结构

```
mission5/
├── README.md                    ← 你在这里
├── .claude/
│   └── settings.local.json      ← Claude Code 权限配置
├── mern-version/                ← 版本 1：JS 全栈
│   ├── server.js
│   ├── models/ routes/ middleware/
│   ├── seed.js
│   └── client/                  ← React SPA
├── django-version/              ← 版本 2：Python 全栈（非 JS）
│   ├── manage.py
│   ├── core/                    ← Django 项目配置
│   ├── prompts/                 ← Django App（models/views/templates）
│   └── seed.py
└── springboot-vue-version/      ← 版本 3：Java 后端 + Vue 前端
    ├── backend/                 ← Spring Boot
    │   ├── pom.xml
    │   └── src/main/java/com/mission5/notes/
    └── frontend/                ← Vue 3 SPA
```

## AI 编码工具

本项目所有代码使用 **Claude Code**（DeepSeek v4-pro）辅助生成。

开发流程遵循 Vibe Coding 标准化工作流：
1. 先规划数据模型和 API 契约
2. 后端先行，curl 验证 CRUD 全通
3. 前端跟进，页面逐个构建

## Skills

开发过程中安装并使用了以下 Agent Skills：

| Skill | 用途 |
|-------|------|
| vercel-react-best-practices | React 性能优化规则 |
| web-design-guidelines |  Web 界面设计规范 |
| frontend-design | 视觉设计方向指导 |
| vercel-composition-patterns | React 组合模式 |
| tailwind-design-system | Tailwind 设计令牌系统 |
| tailwindcss-advanced-layouts | CSS Grid/Flexbox 布局 |
| modern-web-guidance | 现代 Web API 最佳实践 |
| django-patterns | Django 开发模式 |

## 许可

MIT

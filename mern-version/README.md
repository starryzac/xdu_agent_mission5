# Prompt Lab — MERN 版本

MongoDB + Express + React + Node.js 全栈实现，AI 提示词实验管理工具。

## 前置条件

- Node.js >= 18
- MongoDB（本地或 [MongoDB Atlas](https://cloud.mongodb.com) 免费云）

## 安装

```bash
cd mern-version

# 安装后端依赖
npm install

# 安装前端依赖
cd client && npm install && cd ..
```

## 配置

创建 `.env` 文件（参考项目内已有 `.env`）：

```
PORT=3000
MONGODB_URI=mongodb://localhost:27017/prompt-lab
```

如果使用 MongoDB Atlas，将 `MONGODB_URI` 替换为 Atlas 连接字符串。

## 运行

### 开发模式（前后端分离，推荐）

```bash
# 终端 1：启动后端（端口 3000，文件改动自动重启）
npm run dev

# 终端 2：启动前端（端口 5173，热更新 + API 自动代理到 3000）
npm run dev:client
```

浏览器打开 **http://localhost:5173**

### 生产模式（单端口）

```bash
npm run build && npm start
```

浏览器打开 **http://localhost:3000**

## 种子数据

```bash
node seed.js
```

预填 6 个标签 + 6 个提示词（含 16 条运行记录），覆盖代码生成、文案润色、翻译、知识问答、角色扮演、数据分析等场景。

## 数据模型

| 实体 | 字段 | 说明 |
|------|------|------|
| **Tag** | `title`, `notes`, timestamps | 标签/组别，与 Prompt 多对多关联 |
| **Prompt** | `title`, `content`, `notes`, `tags[]`, `runs[]`, `version`, `rating`, timestamps | 核心实体 |
| **Run** | `model`, `tokens`, `responseTime`, createdAt | 运行记录（一个 Prompt 可叠加多次） |

## API 端点

所有 API 返回统一格式：`{ success: bool, data?: any, error?: string }`

### Tags

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tags` | 获取所有标签（按更新时间倒序） |
| GET | `/api/tags/:id` | 获取单个标签 |
| POST | `/api/tags` | 创建标签 |
| PUT | `/api/tags/:id` | 更新标签 |
| DELETE | `/api/tags/:id` | 删除标签 |

### Prompts

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/prompts` | 获取所有提示词（含标签和运行记录） |
| GET | `/api/prompts/:id` | 获取单个提示词 |
| POST | `/api/prompts` | 创建提示词（含 tags 关联和 runs 数组） |
| PUT | `/api/prompts/:id` | 更新提示词（支持部分更新） |
| DELETE | `/api/prompts/:id` | 删除提示词 |

## 前端页面

| 路由 | 页面 | 功能 |
|------|------|------|
| `/prompts` | 提示词列表 | 卡片网格、空状态提示、排序 |
| `/prompts/new` | 新建提示词 | 表单 + 标签多选 + 内联创建标签 |
| `/prompts/:id` | 提示词详情 | 只读展示 + 运行记录表 + 添加/删除 run |
| `/prompts/:id/edit` | 编辑提示词 | 预填表单 |
| `/tags` | 标签列表 | 内联创建 + 内联编辑 + 删除 |
| `/tags/:id` | 标签详情 | notes 编辑 + 关联提示词列表 |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Express 5 + Mongoose 9 |
| 数据库 | MongoDB |
| 前端 | React 19 + Vite 8 |
| 样式 | Tailwind CSS v4 |
| 路由 | react-router-dom v6 |

## 已知问题

- MongoDB 需要单独安装或使用 Atlas 云服务
- 前端开发端口 5173 可能与 Vite 默认冲突（如同时跑另一个 Vite 项目）
- Express 5 不支持 `app.get('*')` 通配符，SPA fallback 使用 middleware 方式

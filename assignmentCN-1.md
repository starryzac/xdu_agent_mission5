# Day5 – 多技术栈 AI 加速 Web 应用构建


## 作业概述
使用 3 种不同的技术栈构建同一个功能性的 Web 应用。使用 AI 编码工具（例如 Claude Code、Codex、Trae 等）来辅助开发。至少一个版本必须在前端或后端使用非 JavaScript 语言（例如 Django、Ruby on Rails等）。

你可以复用前几周的应用（"开发者控制中心"），也可以创建自己选择的新应用，只要满足[最低功能范围](#最低功能范围)即可。应用应是端到端可用的（前端 + 后端 + 持久化存储，如适用），并展示一套连贯的功能特性。

## 前置检查（⚠️ 务必先执行，避免踩坑）

```bash
# ① 检查磁盘空间（三个全栈项目 + 依赖 ≈ 3~8 GB）
df -h ~

# ② 确认 Node.js 版本（≥ 18，三个版本都用到）
node --version

# ③ 确认包管理器可用
npm --version
# 推荐配置国内镜像（加速）：
npm config set registry https://registry.npmmirror.com

# ④ 如果用 Python 技术栈（Django / Flask / FastAPI）
python3 --version          # ≥ 3.10
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# ⑤ 如果用 Ruby 技术栈（Rails）
ruby --version             # ≥ 3.0
gem sources --add https://gems.ruby-china.com --remove https://rubygems.org/

# ⑥ 如果用 Go 技术栈（Gin）
go version                 # ≥ 1.20
go env -w GOPROXY=https://goproxy.cn,direct
```

> ⚠️ **三个版本意味着三套依赖**。每个版本放在独立文件夹中，`node_modules/` / `.venv/` 各自隔离，避免跨版本依赖冲突。

---

## 最低功能范围

### 1. CRUD 操作（创建、读取、更新、删除）

这是核心要求，必须完整实现 5 个 API 端点/操作：

| 操作 | HTTP 方法 | 端点示例 | 必须行为 |
|------|-----------|----------|----------|
| **列表** | `GET` | `/api/notes` | 返回所有资源列表，支持排序（如按创建时间倒序） |
| **详情** | `GET` | `/api/notes/:id` | 返回单条资源；不存在的 ID 返回 `{ success: false, error: "未找到" }` |
| **创建** | `POST` | `/api/notes` | 接收 JSON body，校验通过后写入数据库，返回新创建的完整对象 |
| **更新** | `PUT/PATCH` | `/api/notes/:id` | 接收 JSON body，部分或全部更新字段，返回更新后的对象 |
| **删除** | `DELETE` | `/api/notes/:id` | 删除指定资源，返回成功确认；不存在的 ID 返回错误 |

**验证标准**：使用 `curl` 或 Postman 逐条测试这 5 个端点，都能正确返回预期数据并写入/读取数据库。

### 2. 数据模型要求

以"笔记应用"为例，数据模型至少包含：

```
Note {
  id: 主键（自增整数或 UUID）
  title: 字符串（必填，不能为空，不能全空格，最长 100 字符）
  content: 字符串（必填，不能为空）
  createdAt: 时间戳（自动生成）
  updatedAt: 时间戳（更新时自动刷新）
}
```

**强制要求**：
- 至少 1 个必填字段（不能全为空或仅空格）
- 至少 1 个自动时间戳字段
- id 字段必须由数据库/后端自动生成

### 3. 持久化存储

| 存储方式 | 适用场景 | 要求 |
|----------|----------|------|
| **数据库**（SQLite/MongoDB/PostgreSQL） | 所有版本 | 重启应用后数据不丢失 |
| **文件存储**（JSON 文件） | 仅限极简版本 | 不推荐，仅作为实验性栈的备选 |

**明确要求**：
- 使用数据库（SQLite 推荐，零配置）
- 数据库文件放在项目目录内（如 `data/app.db`）
- `.gitignore` 中排除数据库文件
- 首次启动自动创建表结构（migration 或 auto-sync）

### 4. 验证和错误处理

#### 输入验证（后端必须实现）

| 验证项 | 规则 | 错误响应示例 |
|--------|------|-------------|
| title 为空 | `""` 或 `"   "` 均拒绝 | `{ success: false, error: "标题不能为空" }` |
| title 过长 | 超过 100 字符 | `{ success: false, error: "标题不能超过100个字符" }` |
| content 为空 | `""` 拒绝 | `{ success: false, error: "内容不能为空" }` |
| 资源不存在 | GET/PUT/DELETE 不存在的 id | `{ success: false, error: "笔记不存在" }` |
| 请求体格式错误 | POST/PUT 发送非 JSON | `{ success: false, error: "请求格式错误" }` |

#### 错误处理（必须实现）
- 所有 API 端点包裹在 `try/catch` 中（或框架级统一异常处理）
- 后端崩溃不会导致进程退出（至少捕获未处理异常）
- 统一响应格式：`{ success: bool, data?: any, error?: string }`
- 前端对 API 调用失败有用户可见的错误提示（非静默失败，非白屏）

### 5. 用户界面要求

**前端页面数量**：至少 3 个可交互的页面/视图

| 页面 | 功能 | 包含元素 |
|------|------|----------|
| **列表页** | 展示所有资源 | 列表/卡片展示、排序（最新在前）、空状态提示（"暂无数据"） |
| **创建/编辑页** | 表单提交 | 输入框、提交按钮、前端验证（空值提示）、成功/失败反馈 |
| **详情页** | 查看单条 | 显示所有字段、提供编辑和删除入口 |

**UI 可用性底线**：
- 页面能完成完整的 CRUD 操作闭环（创建 → 列表看到 → 点击编辑 → 更新 → 列表刷新 → 删除）
- 不能仅靠手动改 URL 或 `curl` 才能完成操作
- 不要求美观，但要求功能完整可操作
- 不要求响应式设计

### 6. 运行说明文档

每个版本的 README.md 必须包含：

```markdown
# [项目名称] - [技术栈]

## 前置条件
- Node.js >= 18 / Python >= 3.10 / 等

## 安装
```bash
cd versionX-xxx
npm install          # 或 pip install -r requirements.txt
```

## 配置
创建 `.env` 文件，参考 `.env.example`：
```
PORT=3000
DATABASE_URL=xxx
```

## 运行
```bash
# 启动后端
npm start            # 或 python app.py

# 启动前端（如适用）
cd client && npm run dev
```

访问 http://localhost:3000

## 已知问题
- [列出所有已知 bug 或未完成功能]
- [记录 AI 生成后的手动修复]
```

### 7. 统一 API 响应格式（强制）

所有版本的所有 API 端点必须返回：

```json
// 成功
{ "success": true, "data": { ... } }

// 列表成功
{ "success": true, "data": [ ... ] }

// 删除成功
{ "success": true, "data": { "message": "删除成功" } }

// 失败
{ "success": false, "error": "具体错误描述" }
```

### 8. 功能完整性自检清单

在提交前，逐项确认：

```
□ 列表 API：GET /api/xxx 返回数据，无数据时返回空数组 []
□ 详情 API：GET /api/xxx/:id 返回单条，不存在的 id 返回错误
□ 创建 API：POST /api/xxx 接收 JSON，空 title 被拒绝，成功后返回新对象
□ 更新 API：PUT /api/xxx/:id 能部分更新，不存在的 id 返回错误
□ 删除 API：DELETE /api/xxx/:id 能删除，不存在的 id 返回错误
□ 数据持久化：重启后端后，之前创建的数据仍在
□ 后端验证：空 title、空 content 在服务端被拦截
□ 前端验证：表单提交前检查必填项不为空
□ 前端错误提示：API 调用失败时用户能看到错误信息
□ 统一响应格式：所有端点返回 { success, data/error }
□ .env 配置：端口、数据库路径等通过 .env 管理
□ README.md：含前置条件、安装、配置、运行步骤
□ .gitignore：排除 node_modules、.venv、数据库文件、.env
```

## 技术栈要求
构建同一应用的 3 个独立版本，每个版本使用不同的技术栈。

### 推荐技术栈（按上手难度排序）

**JS 全栈（推荐作为版本 1）**：

| 栈 | 前端 | 后端 | 数据库 | 适合 |
|----|------|------|--------|------|
| **MERN** | React | Express | MongoDB | 最经典、教程最多 |
| **MEVN** | Vue | Express | MongoDB | Vue 更轻量，适合小项目 |
| **Next.js 全栈** | React (SSR) | API Routes | Prisma + SQLite | 一个项目搞定前后端 |

**非 JS 后端 + JS 前端（推荐作为版本 2，满足非 JS 要求）**：

| 栈 | 后端 | 前端 | 数据库 | 适合 |
|----|------|------|--------|------|
| **Django + 模板** | Django | Django 模板 | SQLite | 全栈 Python，无需写 JS |
| **Django + React** | Django REST | React | SQLite/PostgreSQL | Python 后端 + 现代前端 |
| **FastAPI + Vue** | FastAPI | Vue | SQLite | Python 异步、性能好、AI 生成质量高 |
| **Flask + Vanilla JS** | Flask | 原生 HTML/JS | SQLite | 极简，适合理解全栈原理 |
| **Gin + React** | Gin (Go) | React | SQLite | Go 性能好、部署简单、AI 生成质量不错 |
| **Rails 全栈** | Rails | ERB/Turbo | SQLite | Ruby 全栈，约定优于配置 |

**实验性栈（推荐作为版本 3，尝试不同 AI 工具）**：

| 栈 | 说明 |
|----|------|
| Express + Vanilla JS | 不用前端框架，手写原生 JS |
| Spring Boot + Vue | Java 后端（AI 对 Java 支持良好） |
| Laravel + React | PHP 后端（适合有 PHP 基础的学生） |

> ⚠️ **非 JS 语言指 Python / Ruby / Go / Java / PHP 等**。TypeScript、Deno、Bun 不算（它们属于 JS 生态）。非 JS 必须在后端（Django/Flask/FastAPI/Rails/Gin），前端可以仍是 JS。
>
> 💡 **给国内学生的建议**：优先选 Django 或 FastAPI 作为非 JS 版本——国内教程多、社区活跃、AI 对 Python 的代码生成质量最高。Ruby/Rails 和 Go/Gin 的网络资源偏少，如果卡住不容易搜到中文答案。


## 预估耗时

| 阶段 | 预估耗时 | 关键产出 |
|------|----------|----------|
| 应用设计（数据模型、路由规划） | 1~2 小时 | 实体关系草图、API 端点列表 |
| 技术栈 1（你最熟悉的主力栈） | 3~5 小时 | 完整可运行的版本 |
| 技术栈 2（非 JS 版本） | 4~6 小时 | 含非 JS 后端/前端的可运行版本 |
| 技术栈 3（实验性栈） | 3~5 小时 | 尝试不同 AI 工具或不同框架 |
| writeup.md + 各版 README | 2~3 小时 | 完整交付文档 |
| **合计** | **13~21 小时** | |

> 不要把三个版本放在同一天搞——AI 工具会有上下文混淆，你也容易疲劳。

## Checkpoint 里程碑

在投入大量时间前，先用这些小目标确认方向正确：

| # | 验证点 | 判定标准 |
|---|--------|----------|
| 🔴 1 | **一个版本的 CRUD 已跑通** | `curl` 或浏览器能完成创建→读取→更新→删除全流程，数据持久化到数据库 |
| 🔴 2 | **三个版本的 scaffold 已生成** | 三个文件夹各能启动（哪怕只是一个 Hello World 页面或 `/api/health`） |
| 🔴 3 | **非 JS 版本可运行** | 非 JS 后端能接受 API 请求并返回 JSON |
| 🔴 4 | **文档齐全** | 每个版本有 README、writeup.md 填写完整 |

> ⚠️ **Checkpoint 1 是最关键的一道坎**。如果主力栈都跑不通 CRUD，先停下来调试，不要急着开另外两个版本。


使用 AI 编码工具辅助构建。学生可自行选择以下工具之一（或类似工具）：
- **Claude Code** — Anthropic 推出的命令行 AI 编码助手
- **Codex** — OpenAI 推出的 AI 编码代理
- **Trae** — 字节跳动推出的 AI 编程助手
- 其他 AI 编码工具（例如 Cursor、GitHub Copilot、Windsurf 等）

也欢迎在其他版本中尝试不同的 AI 编码工具。


## 了解 AI 编码工具
AI 编码工具是辅助开发者编写、调试和优化代码的智能助手。它们可以通过自然语言描述理解开发者的意图，帮助快速生成代码、重构项目、修复 bug 以及搭建完整的功能模块。与传统的应用生成平台不同，这些工具更侧重于与开发者协作编码，而非一键生成整个应用。

### 工具选择建议：
1. 选择一个你感兴趣或想深入学习的 AI 编码工具。
2. 注册并熟悉该工具的基本使用方法。
3. 利用该工具辅助完成至少一个版本的应用开发。
4. 在实验报告中记录你使用的工具及其体验。


## AI 编码工具使用提示

### 提示（Prompt）范例

AI 工具的好坏很大程度上取决于你的提示质量。以下是推荐的提示结构和具体范例：

**推荐的提示结构**：
```
角色：你是一个资深 [技术栈] 开发者。
任务：构建一个 [应用名称] 的应用。
数据库：[数据库类型]
数据模型：
  - [实体名] { 字段1: 类型, 字段2: 类型, ... }
API 端点：
  - GET /api/xxx — 功能描述
  - POST /api/xxx — 功能描述
前端页面：
  - 页面1：功能描述
  - 页面2：功能描述
约束：
  - 使用 .env 管理配置
  - 每个 API 返回格式：{ success: bool, data?: any, error?: string }
  - [其他要求]
```

**具体范例（以「笔记管理」应用为例）**：

> ```
> 角色：你是一个资深 MERN（MongoDB + Express + React）全栈开发者。
> 任务：构建一个「笔记管理」Web 应用。
> 
> ## 数据模型
> Note {
>   title: String (必填, 最长 100 字),
>   content: String (必填),
>   tags: [String] (可选),
>   createdAt: Date (自动)
> }
> 
> ## 后端 API（Express + Mongoose）
> - GET    /api/notes          — 获取所有笔记（支持 ?tag=xxx 筛选）
> - GET    /api/notes/:id      — 获取单篇笔记
> - POST   /api/notes          — 创建笔记
> - PUT    /api/notes/:id      — 更新笔记
> - DELETE /api/notes/:id      — 删除笔记
> 
> 所有 API 返回格式：{ success: bool, data?: any, error?: string }
> 使用 .env 存放 MongoDB 连接字符串和端口号。
> 
> ## 前端（React）
> - 首页：笔记列表，按时间倒序，支持标签筛选
> - 详情页：查看/编辑/删除单篇笔记
> - 新建页：表单创建笔记
> 
> 请先生成后端代码，确认无误后再生成前端。
> ```

**迭代流程**：
1. 第一轮：让 AI 生成**数据模型 + 后端 API**
2. 启动后端，用 `curl` 或 Postman 验证 CRUD 都通
3. 第二轮：让 AI 生成**前端页面**（基于已确认的 API）
4. 第三轮：补充**样式、错误处理、边界情况**

### ⚠️ AI 生成代码的常见问题

AI 不是万能的——以下问题在实际作业中高频出现，请逐项检查：

| 常见问题 | 表现 | 如何修复 |
|----------|------|----------|
| **过时的 API 语法** | `mongoose.connect()` 报弃用警告；React Router v5 语法在 v6 中报错 | 检查 `package.json` 中的版本号，让 AI "用最新版本的 API 重写" |
| **硬编码配置** | 数据库连接字符串写死在代码里 | 手动提取到 `.env`，在提示中明确要求"使用 .env 管理所有配置" |
| **缺少 CORS 配置** | 前端 `fetch` 报 `Access-Control-Allow-Origin` 错误 | 检查后端是否使用了 `cors` 中间件（Express）或 `django-cors-headers`（Django） |
| **端口冲突** | 三个版本默认都用 3000 | 手动修改端口：版本1=3000, 版本2=3001, 版本3=8000 |
| **import 路径错误** | AI 生成的相对导入路径与项目结构不匹配 | 逐文件核对，必要时手动修正 |
| **AI 丢失上下文** | 生成到一半，AI "忘记"了之前定义的数据模型，开始编造字段 | 对话太长时开新会话，把数据模型作为第一句话重新贴入 |
| **凭空编造 API** | AI 引用了不存在的 npm 包或框架 API | 如果 `npm install` 找不到该包，问 AI "用标准库或其他主流包替代" |
| **验证和错误处理缺失** | 空 title 也能提交、后端 crash 后前端白屏 | 在提示中明确要求"所有端点入参校验 + try/catch 错误处理" |
| **依赖版本冲突** | `npm install` 报 `peer dependency` 错误 | 加 `--legacy-peer-deps` 或让 AI 降低某些包的版本 |

> 💡 **经验法则**：AI 约能生成 70%~80% 的代码，剩下的 20% 需要你来调试、修复和微调。这是正常的，也是学习过程。

## 交付物
1) **三个**项目文件夹（每个版本一个），放在 `day5/` 文件夹内，每个文件夹包含：
   - 源代码
   - `README.md`，包含前置条件、安装/设置说明、运行说明以及环境配置
   - 关于偏差、已知问题以及生成后的任何手动修复的备注
   - git 记录（git commit）
2) 填写完整的 `writeup.md` 文件：
   - 应用概念，
   - 开发中的心得、经验、难点、问题。
   - 3 个应用描述（每个版本一个）

## 评分标准（100 分）
- 应用概念满足最低功能范围（10 分）
- 三个不同的技术栈（10 分）
- 使用 AI 编码工具的心得经验（10 分）
- 至少一个版本使用非 JS 语言（10 分）
- 应用的三个版本（每个 **20 分**）：
   - 源代码提供在 `day5/` 的文件夹中（5 分）
   - README.md：前置条件、安装/设置说明、运行说明以及环境配置（5 分）
   - 应用功能（5 分）
   - 在 `writeup.md` 中详细描述完整版本（5 分）

---

# 附加作业：构建 Day5 评分 Skill

## 作业概述

构建一个 Claude Code **Skill**（或 slash command），用于自动检查 `day5/` 目录下的**交付物和三版应用程序**，按照 Day5 评分标准输出一份**评价报告**，报告中逐项给出评价和说明，最后输出**总分**。

> 这是一个"元作业"——用 AI 工具构建一个评分工具，来评估你用 AI 工具完成的作业。

Skill 需要检查两个层面：
- **交付物层面**：文件结构、README、writeupCN 文档、git 记录
- **应用程序层面**：每个版本的实际代码质量，包括数据模型、CRUD 实现、API 设计、验证与错误处理、UI 可用性等

## 最低要求

1. Skill 能够被 Claude Code 加载并运行
2. 对 day5 交付物**和三版应用代码**进行结构化检查，输出评价报告
3. 报告包含以下维度的逐项评价：

### 整体评分（40 分）
| 评分项 | 分值 | Skill 检查内容 |
|--------|------|---------------|
| 应用概念与最低功能范围 | 10 | writeupCN 中是否描述应用概念；三版应用代码中是否实现了完整 CRUD |
| 三个不同技术栈 | 10 | 扫描各版本 `package.json`/`requirements.txt`/`Gemfile` 等依赖文件，确认技术栈互不相同 |
| AI 编码工具心得 | 10 | writeupCN 中是否填写了心得、经验、难点 |
| 至少一个非 JS 版本 | 10 | 检查是否有 Python/Ruby/Go/Java/PHP 后端的版本 |

### 各版本应用评分（每版本 20 分 × 3 = 60 分）
| 评分项 | 分值 | Skill 检查内容 |
|--------|------|---------------|
| 源代码完整性 | 5 | 项目文件夹存在且有源代码文件，`package.json` 等配置文件齐全 |
| README 文档 | 5 | 是否含前置条件、安装/设置说明、运行说明、环境配置 |
| 应用功能 | 5 | **深入检查应用代码**：数据模型定义、CRUD 路由/端点、输入验证、错误处理、前后端对接 |
| writeup 描述 | 5 | writeupCN 中该版本的描述是否完整（技术栈、AI 工具、存储方案、遇到的问题） |

4. 报告末尾给出**总分**（满分 100 分），每项评分附简要理由

## 应用程序检查要点（示例）

Skill 应至少对每个版本进行以下代码层面的检查：

- **数据模型**：是否有明确的 schema/model 定义（Mongoose Schema / Django Model / SQLAlchemy Model 等）
- **CRUD 完整性**：是否实现了创建、读取（列表+详情）、更新、删除操作（检查路由文件或控制器中是否有对应的 HTTP 方法）
- **输入验证**：是否对必填字段进行了校验（如空 title 拒绝、字段长度限制）
- **错误处理**：API 是否有 try/catch 或统一的错误响应格式
- **前后端对接**：前端是否有对应的 API 调用代码（fetch/axios），能否与后端 API 匹配

## 自由发挥维度（学生自行选择）

| 维度 | 选项 |
|------|------|
| **粒度** | 单个综合 skill 一次性评分；或多个 skill 组合（如 `/check-files` + `/check-code` + `/grade-all`） |
| **代码检查深度** | 静态分析（检查文件存在、依赖文件、代码模式匹配 CRUD 端点）；或深度验证（实际 `npm install` + `npm start` 运行项目，用 `curl` 测试 API） |
| **代码质量检查** | 是否检查代码风格（ESLint/Prettier 配置）、TypeScript 类型安全、安全漏洞（`npm audit`） |
| **Skill 高级特性** | 可选用 hooks、subagents、MCP 工具、自定义 prompt 等扩展 skill 能力 |
| **报告格式** | 终端纯文本输出；或生成 Markdown/HTML 报告文件 |

## 交付物

在 `day5/` 下创建 `grader-skill/` 文件夹，包含：

```
grader-skill/
├── skill.md              # Skill 定义文件（Claude Code skill 入口）
├── DESIGN.md             # 设计文档：skill 架构、评分逻辑、检查维度说明
├── USAGE.md              # 使用说明：如何安装、加载、运行该 skill
└── sample-report.md      # 示例评价报告（对你的 day5 作业实际运行一次的输出）
```

### 各文件说明

**skill.md** — Skill 定义文件，包含：
- Skill 名称和描述
- 触发方式（slash command 名称）
- 评分逻辑和检查步骤
- 输出报告格式定义

**DESIGN.md** — 设计文档，包含：
- 为什么要这样设计这个 skill
- 评分逻辑的技术方案（如何检查每个评分维度，**包括如何分析应用代码**）
- 代码检查策略：如何扫描数据模型、CRUD 端点、验证逻辑、错误处理等
- 如果使用了 hooks/subagents/MCP 等高级特性，说明选型理由
- 已知局限性和改进方向

**USAGE.md** — 使用说明，包含：
- 安装前置条件
- 如何加载 skill 到 Claude Code
- 如何运行（命令示例）
- 如何解读报告输出

**sample-report.md** — 对你的 day5 作业实际运行一次 skill，将输出保存为此文件。

## 评分标准（附加作业 20 分）

- Skill 可正常加载运行（5 分）
- 评分维度覆盖完整（5 分）
- 评价报告结构清晰、评价有依据（5 分）
- 设计文档和使用说明完整（5 分）

## 提示

- 让 AI 帮你生成 skill 的初版，然后迭代优化评分逻辑
- 可以先做静态检查版本跑通流程，再考虑加入深度验证
- 在 sample-report.md 中诚实记录 skill 发现的真实问题
- 如果 skill 发现自己的作业存在问题，这正是"元"的价值所在——评分工具本身也在帮你改进

# Prompt Lab — Spring Boot + Vue 版本

Spring Boot 3.5 (Java) + Vue 3 全栈实现，AI 提示词实验管理工具。

## 前置条件

- Java >= 21
- Node.js >= 18
- Maven（项目内置 Maven Wrapper，无需手动安装）

## 安装

```bash
cd springboot-vue-version

# 后端：Maven 依赖自动下载
cd backend
./mvnw dependency:resolve    # Windows 用 mvnw.cmd

# 前端
cd ../frontend
npm install
```

## 配置

无需额外配置。后端使用 H2 文件数据库（`backend/data/prompt-lab.mv.db`），首次启动自动创建表结构并填充种子数据。

## 运行

### 开发模式

```bash
# 终端 1：启动后端（端口 8080）
cd backend
./mvnw spring-boot:run

# 终端 2：启动前端（端口 5173，API 自动代理到 8080）
cd frontend
npm run dev
```

浏览器打开 **http://localhost:5173**

### 生产模式

```bash
cd backend && ./mvnw package -DskipTests
java -jar target/notes-0.0.1-SNAPSHOT.jar
# 然后将 frontend/dist 部署到任意静态服务器
```

## 种子数据

应用首次启动时自动执行 `DataSeeder`，预填 6 个标签 + 6 个提示词（含 16 条运行记录）。若数据库中已有数据则跳过。

## 数据模型

| 实体 | 字段 | 说明 |
|------|------|------|
| **Tag** | `id`, `title`, `notes`, `createdAt`, `updatedAt` | 标签，与 Prompt 多对多关联 |
| **Prompt** | `id`, `title`, `content`, `notes`, `tags` (M:N), `runs` (1:N), `version`, `rating`, timestamps | 核心实体 |
| **Run** | `id`, `prompt` (FK), `model`, `tokens`, `responseTime`, `createdAt` | 运行记录 |

## API 端点

所有 API 返回统一格式：`{ success: bool, data?: any, error?: string }`

### Tags

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/tags` | 获取所有标签（按更新时间倒序） |
| GET | `/api/tags/{id}` | 获取单个标签 |
| POST | `/api/tags` | 创建标签 |
| PUT | `/api/tags/{id}` | 更新标签（支持部分更新） |
| DELETE | `/api/tags/{id}` | 删除标签 |

### Prompts

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/prompts` | 获取所有提示词（含标签和运行记录） |
| GET | `/api/prompts/{id}` | 获取单个提示词 |
| POST | `/api/prompts` | 创建提示词（含 tags 关联和 runs 数组） |
| PUT | `/api/prompts/{id}` | 更新提示词（支持部分更新 + runs 替换） |
| DELETE | `/api/prompts/{id}` | 删除提示词 |

## 前端页面

| 路由 | 页面 | 功能 |
|------|------|------|
| `/prompts` | 提示词列表 | 卡片网格、空状态、排序 |
| `/prompts/new` | 新建提示词 | 表单 + 标签多选 + 内联创建标签 |
| `/prompts/:id` | 提示词详情 | 只读展示 + 运行记录表 + 添加/删除 run |
| `/prompts/:id/edit` | 编辑提示词 | 预填表单 |
| `/tags` | 标签列表 | 内联创建 + 编辑 + 删除 |
| `/tags/:id` | 标签详情 | notes 编辑 + 关联提示词列表 |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Spring Boot 3.5 (Java 21) |
| 数据库 | H2 (文件模式) |
| ORM | Spring Data JPA / Hibernate |
| 前端 | Vue 3 + Vite 8 |
| 样式 | Tailwind CSS v4 |
| 路由 | Vue Router 4 |

## H2 控制台

开发时可访问 **http://localhost:8080/h2-console** 查看数据库：

- JDBC URL: `jdbc:h2:file:./data/prompt-lab`
- 用户名: `sa`
- 密码: (空)

## 已知问题

- H2 文件数据库路径相对于项目根目录，Maven 运行时的 working directory 可能影响数据库文件位置
- Spring Boot 默认 Jackson 序列化 `null` 字段（已在 `ApiResponse` 上加 `@JsonInclude(NON_NULL)` 修复）
- PUT 请求中 `tags` 的 `List<Integer>` 需转换为 `Long` 类型（已在 Controller 中处理）

# Day5 实验报告 — Prompt Lab 多技术栈 Web 应用

> 基于 `Day5_实验报告模板.md` 填写，所有 TODO 已替换为实际内容。
>
> GitHub 仓库：[https://github.com/starryzac/xdu_agent_mission5](https://github.com/starryzac/xdu_agent_mission5)

## 提交详情

姓名：**Chen TianHao** \
SUNet ID：**starryzac** \
引用来源：Claude Code (DeepSeek v4-pro) + Vercel Agent Skills + Anthropic Frontend Design Skill \
完成此作业大约花费了我 **25** 小时。

---

## 应用概念

**Prompt Lab** — AI 提示词实验日志。一个面向 AI 开发者的提示词管理工具，帮助记录、迭代、比较提示词在不同大语言模型上的表现。

核心功能：
- 管理提示词（创建、查看、编辑、删除）
- 用标签对提示词按场景分类（代码生成、文案润色、翻译等）
- 记录每次运行实验——哪个模型、消耗多少 Token、响应耗时——同一提示词可叠加多次运行记录
- 评分（1-5 星）和版本号追踪迭代过程

数据模型设计为双实体多对多：`Tag`（标签/组别）与 `Prompt`（提示词）通过 M:N 关联，`Run`（运行记录）作为 `Prompt` 的 1:N 子实体。这一设计比作业最低要求的单实体笔记应用更丰富，更能体现实体关系建模能力。

---

## 版本 #1 描述

```
应用详情：
===============
文件夹名称：mern-version
AI 编码工具：Claude Code
技术栈：MongoDB + Express 5 + React 19 + Node.js
持久化存储：MongoDB（本地实例，数据目录在 data/db/）
使用的框架/库：Mongoose 9、Vite 8、Tailwind CSS v4、react-router-dom v6

反思总结：
===============
a. 遇到的问题以及如何解决：

1. Express 5 通配符路由变更：Express 5 废弃了 app.get('*') 语法，改用
   path-to-regexp 7.x。SPA fallback 改用 middleware 方式判断 req.path 实现。

2. MongoDB 未安装：通过 winget 安装 MongoDB 8.3 Community Server，MSI 安装
   自动注册为 Windows 服务，无需手动 mongod 启动。

3. Mongoose 9.x 与 Express 5 的兼容性：两者各自独立，无直接冲突。Mongoose
   Schema 的 validate 选项与 Express 错误处理中间件配合良好。

b. 提示词使用：

使用结构化分层提示策略——先让 AI 生成数据模型（Mongoose Schema），用 curl 逐
个测试所有 CRUD 端点通过后，再让 AI 生成前端页面。关键提示结构包括：明确数
据模型字段约束、要求统一 {success, data, error} 响应格式、指定 Express 错误
处理中间件捕获 ValidationError 和 CastError。

c. 首次运行时间和功能开发时间指标：

后端 API（模型 + 路由 + 验证 + 错误处理）：~1 小时
前端页面（6 页 + Tailwind 主题 + React Router）：~2 小时
调试与修复（Express 5 兼容性 + SPA fallback）：~0.5 小时
```

---

## 版本 #2 描述

```
应用详情：
===============
文件夹名称：django-version
AI 编码工具：Claude Code
技术栈：Django 6.0 + Django Templates + SQLite
持久化存储：SQLite（db.sqlite3，项目目录内）
使用的框架/库：Django 6.0.6、Tailwind CSS CDN、django-patterns Agent Skill

反思总结：
===============
a. 遇到的问题以及如何解决：

1. Django 6.0 是最新版本（2026年7月）：文档较少，但 API 与 5.x 基本兼容。
   django-admin startproject 生成的 settings.py 结构略有变化。

2. Django ModelForm 不支持真正的部分更新：PUT 请求只传 title 时，form.is_valid()
   会因 content/notes 为空而失败。放弃 ModelForm 做 PUT，改为手动 setattr 后
   调用 full_clean() + save()。

3. JSON API 的 CSRF 保护：Django 默认对所有 POST/PUT/DELETE 要求 CSRF Token。
   API 端点需要 @csrf_exempt 装饰器豁免。在 views.py 中四个 API 函数各加一个。

4. Windows curl 发送中文 JSON 编码问题：Git Bash 下 curl 将中文按 GBK 编码，
   Django 期望 UTF-8，导致 UnicodeDecodeError。浏览器访问不受影响。

5. 模板中评分星级显示：Django 模板不支持 range()，用 if/elif 逐级判断每颗星。

b. 提示词使用：

先验证 Django 和 venv 正常工作，然后一次性生成 models.py（三个 Entity）、
forms.py（TagForm/PromptForm/RunForm）、views.py（模板视图 + JSON API）、
urls.py（18 条路由）、所有模板（base.html + 9 个子页面），最后 seed.py 填充
数据。生成过程中使用了 django-patterns Agent Skill 作为参考。

c. 首次运行时间和功能开发时间指标：

数据模型 + 表单 + 视图 + URL：~1 小时
Django 模板（server-rendered HTML）：~1.5 小时
调试（CSRF + 部分更新 + 编码问题）：~0.5 小时
```

---

## 版本 #3 描述

```
应用详情：
===============
文件夹名称：springboot-vue-version
AI 编码工具：Claude Code
技术栈：Spring Boot 3.5 + Vue 3 + H2 数据库
持久化存储：H2 文件数据库（backend/data/prompt-lab.mv.db）
使用的框架/库：Spring Data JPA、Hibernate、Jakarta Validation、Vue Router 4、
               Tailwind CSS v4、Vite 8

反思总结：
===============
a. 遇到的问题以及如何解决：

1. Jackson 反序列化类型转换：JSON 中的数字（如 tags: [1, 2]）被 Jackson 解析
   为 Integer，但 JPA Repository 的 findById() 期望 Long。在 PromptController
   中用 List<Number> 接收后手动调用 n.longValue() 转换。

2. H2 数据库文件路径：application.properties 中 jdbc:h2:file:./data/prompt-lab，
   ./ 相对于 Maven 运行时的 working directory。开发时需确保从 backend/ 目录
   运行 mvnw。

3. Jackson 序列化 null 字段：默认 Java 会把 null 字段也输出到 JSON（如
   "error": null），在 ApiResponse 类上加 @JsonInclude(NON_NULL) 解决。

4. Spring Boot 启动速度：首次 mvn spring-boot:run 需下载所有 Maven 依赖，
   耗时 3-5 分钟。后续启动依赖缓存后 10 秒内完成。

5. DataSeeder 作为 CommandLineRunner：在应用启动时自动检测数据库是否为空，
   为空则填充种子数据（6 tags + 6 prompts + 16 runs）。

b. 提示词使用：

先生成 Entity 层（JPA 注解 + Jakarta Validation），编译通过后生成 Repository
和 Controller，最后写 DataSeeder 和 CORS 配置。Vue 前端参照已有 React 版本的
组件结构，用 Vue 3 Composition API 重写。关键提示：明确要求 Controller 返回
统一 ApiResponse<T> 格式，require 字段使用 @NotBlank + @Size 验证。

c. 首次运行时间和功能开发时间指标：

后端 Entity + Repository + Controller + Config：~1.5 小时
Vue 前端（Vue Router + 6 页 + Tailwind）：~1.5 小时
调试（类型转换 + CORS + 编译错误）：~0.5 小时
```

---

# 编程心得

## Vibe Coding 的心得、经验、难点、问题

### 标准化工作流的重要性

严格按照 PPT 中"Vibe Coding 标准化工作流"六阶段执行——先定义数据模型和 API 契约，后端先行 curl 验证，前端跟进——是最有效的开发策略。三次版本都遵循了同样的流程，每次跑通 CRUD 的时间逐渐缩短（第一次 ~1.5h，第三次 ~1h）。

### 上下文管理是关键

AI 编码工具在处理大型多文件项目时容易"丢失上下文"——忘记之前定义的数据模型字段、开始编造不存在的 API。教训是：每次开新会话时第一句话就贴入数据模型定义和 API 端点列表，让 AI 重新建立上下文。

### 统一 API 契约的价值

三个版本共享同一套 `{success, data, error}` 响应格式和同样的端点路径，这意味着前端可以几乎不变地复用到不同后端。MERN 的 React 前端直接通过 Vite proxy 连 Django 和 Spring Boot 也能工作，这验证了"契约先行"的设计理念。

### 开发过程中使用的高阶技巧

| 技巧 | 应用场景 | 证明 |
|------|----------|------|
| **Agent Skills** | 安装 vercel-react-best-practices、web-design-guidelines、frontend-design、tailwind-design-system 等 8 个 skills，用于指导 React 性能优化、UI 设计规范、Tailwind 设计令牌系统 | 见 `mern-version/.agents/skills/` |
| **权限配置文件** | 通过 `.claude/settings.local.json` 预先授权所有安全操作（npm/pip/maven/curl/git 等），开发全程无需手动确认 | 见 `.claude/settings.local.json` |
| **结构化 Prompt** | 每次生成前明确：角色、任务、数据模型、API 端点、约束、响应格式 | 见各版本 models/ 和 routes/ 代码一致性 |
| **种子数据脚本** | 每个版本都有 seed.js/seed.py/DataSeeder.java，确保启动即有可演示数据 | 见各版本 seed 文件 |
| **分步验证策略** | 后端写完立即 curl 测试所有 CRUD + 验证场景，全部通过后再写前端 | curl 测试命令见会话记录 |

### AI 生成代码的常见问题及应对

1. **过时的 API**：Express 5 的 `app.get('*')` 已不支持，AI 仍然生成；手动改为 middleware fallback
2. **硬编码配置**：AI 初始生成会写死 localhost:27017；通过 .env 和 .env.example 管理
3. **import 路径错误**：Django 的 `from .models import Run` 遗漏；编译错误快速定位修复
4. **类型不匹配**：Java 中 Jackson Integer → JPA Long 转换；手动处理
5. **CSRF 遗漏**：Django API 端点需要 `@csrf_exempt`；逐个添加
6. **编码问题**：Windows GBK vs UTF-8 在 curl 测试中出现；实际浏览器访问正常

### 三个技术栈的对比感受

| 维度 | MERN | Django | Spring Boot + Vue |
|------|------|--------|-------------------|
| 开发速度 | 最快 | 快 | 中 |
| AI 代码质量 | 最高（JS 训练数据最丰富） | 高（Python 训练数据丰富） | 中（Java 代码更冗长，AI 有时混淆注解） |
| 类型安全 | 弱（JS 无类型） | 弱（Python 无类型） | 强（Java 静态类型） |
| 配置复杂度 | 低 | 极低 | 中（Maven + application.properties） |
| 启动速度 | 即时 | 即时 | 慢（首次 3-5 分钟） |
| 适合场景 | 快速原型、全栈 JS 团队 | 快速开发、Python 生态集成 | 企业级、大型项目 |

三个版本验证了同一个结论：**AI 编码工具对动态语言（JS/Python）的生成质量明显高于静态语言（Java），但静态语言的类型系统在编译阶段就能捕获更多错误，减少了运行时调试时间。**

---

*报告基于实际开发过程记录，所有代码均已推送到 GitHub。*

# Day5 Grader Skill 设计说明

## 设计目标

本 Skill 面向任意 Day5“三技术栈 Web 应用”提交物，不绑定 Prompt Lab、固定目录名或单一框架。设计优先级依次是：评分可信、证据可追溯、运行安全、跨平台可迁移、报告简明。

旧评分器的主要问题是把全项目关键词命中直接当作功能证明。同一个 `seed.js`、README 或全局 writeup 可以同时满足模型、验证、错误处理和三个版本描述；HTTP smoke 结果也不参与计分。因此即使应用未构建、未启动、测试为空，仍可能得到 100 分。

新版采用三层结构：

1. `SKILL.md`：Claude Code 入口，只保留调用流程、安全边界和结果解释。
2. `scripts/grade_day5.py`：稳定 CLI 入口；实现位于 `scripts/day5_grader/` 模块包。
3. `sample-report.md`：对当前作业的真实输出，展示双分数、风险、动态矩阵和证据。

## 模块边界

| 模块 | 职责 |
|---|---|
| `discovery` | 输入解析、文档识别、候选项目发现、技术栈和文件角色分类 |
| `remote` | GitHub 链接提取、去重、分支/子目录解析、受控浅克隆和来源元数据 |
| `analysis` | 框架级静态分析、双分数计算、Finding 和工程质量检查 |
| `runtime` | 临时副本、依赖准备、构建/测试/启动、HTTP CRUD、负向校验和进程清理 |
| `reporting` | 结论先行的 Markdown 报告、证据索引和风险排序 |
| `engine` / `cli` | 流程编排、参数兼容、JSON 输出、CI gate 和失败报告 |

Python 核心只使用标准库。Playwright 是可选增强，不存在时不会阻断静态或 HTTP 评分。

## 证据模型

每条证据记录：

- 规则 ID、版本和评分项
- 文件、行号以及 GitHub 固定 commit URL
- 期望行为和观察结果
- `document/static/dynamic` 证据等级
- `PASS/FAIL_PROJECT/BLOCKED_ENV/NOT_RUN/NOT_APPLICABLE`
- 置信度

关键约束：

- 模型证据只能来自 model/schema/entity 文件。
- CRUD 必须在同一核心资源中确认五类操作，不能从多个无关文件拼词。
- 服务端验证必须同时具备约束和实际触发链路。
- 前端证据必须包含交互视图以及与后端路由可对应的调用或模板表单。
- writeup 按 Markdown 标题切分并映射到单个版本，禁止全局段落重复计分。
- 负向模式可以推翻表面正向证据，例如 `@Valid @RequestBody Map`、Django API 直接 `get_object_or_404`、业务错误仅返回 `ApiResponse.error` 但仍为 HTTP 200。

## Day5 计分模型

课程 rubric 保持 100 分，不增加隐藏评分项。

### 整体 40 分

| 项目 | 满分 | 暂定证据 | 确认证据 |
|---|---:|---|---|
| 应用概念与最低范围 | 10 | 概念文档 4 分 + 静态功能潜力 6 分 | 文档 4 分 + 三版 CRUD/持久化各 2 分 |
| 三种不同技术栈 | 10 | 依赖清单和框架签名 | 同静态 |
| AI 编码心得 | 10 | 工具、提示策略、AI 失误、人工修复、对比反思 | 同静态 |
| 至少一个非 JS 后端 | 10 | Python/Java/Go/Ruby/PHP/C# 后端证据 | 同静态 |

### 每版 20 分

| 项目 | 满分 | 静态确认上限 | 动态部分 |
|---|---:|---:|---:|
| 源代码完整性 | 5 | 4 | 构建/启动可复现 1 |
| README | 5 | 4 | 文档命令可执行 1 |
| 应用功能 | 5 | 2 | 行为验证 3 |
| 独立 writeup 描述 | 5 | 5 | 0 |

静态模式的证据确认分最高为 79。只有三版构建、启动和必需行为均被验证，确认分才可能达到 100。

### 功能 5 分

| 子项 | 满分 | 静态 | 动态 |
|---|---:|---:|---:|
| 数据模型 | 1.0 | 0.6 | 重启持久化 0.4 |
| CRUD | 1.5 | 0.5 | 五步行为测试 1.0 |
| 输入验证 | 0.8 | 0.3 | 空白、超长请求 0.5 |
| 错误与响应契约 | 0.8 | 0.3 | 非法 JSON、404、存活性 0.5 |
| 前后端对接 | 0.9 | 0.3 | 构建、API 契约及可选浏览器检查 0.6 |

测试、CI、依赖锁定、安全、可观测性和部署说明不改变课程分数，但会进入独立工程就绪结论：

- `READY`：三版核心动态验证通过，无 Blocker/High，测试和复现链路完整。
- `CONDITIONAL`：课程核心通过，但仍有中等工程风险。
- `NOT_READY`：构建、启动、核心 CRUD/契约失败，或存在 Blocker/High。
- `NOT_VERIFIED`：只运行静态模式，或关键动态测试未执行。

## GitHub 回退

本地候选项目为零时，评分器从提交 Markdown 中提取标准链接、自动链接和裸 URL。仅接受 `https://github.com/<owner>/<repo>` 及其 `tree/blob` 形式；拒绝 SSH、任意主机、Issue、Release、Action、Raw 和图片链接。

选择顺序为：显式 `--repo-url`、带“仓库/源码/repository”上下文的链接、其他合法仓库链接。同仓库去重，最多三个不同仓库；超过上限且无法唯一选择时登记 `AMBIGUOUS_SOURCE`。

克隆策略：

- `--filter=blob:none --depth=50 --single-branch`
- `GIT_TERMINAL_PROMPT=0`、`GIT_LFS_SKIP_SMUDGE=1`
- 不初始化 submodule，不执行仓库脚本，不读取 `.env`
- 默认 120 秒、10,000 文件、250 MB 上限
- 报告记录仓库、ref、commit、获取时间和可见历史深度

GitHub 回退始终静态。仓库不可访问时仍生成报告，文档项可以评分，代码项保持未验证。

代码来源同时保留标准状态和来源结果码：`LOCAL_WORKTREE_CLEAN`、`LOCAL_WORKTREE_DIRTY`、`LOCAL_NO_GIT`、`REMOTE_SNAPSHOT`、`AMBIGUOUS_SOURCE`、`SOURCE_UNAVAILABLE` 或 `BLOCKED_ENV`。本地来源若工作区非洁净，commit 只标记仓库基线，报告不会把它描述成当前文件的确定性快照。

## 动态验证

动态模式只在显式 `--mode dynamic` 时运行。依赖下载还需要 `--allow-install`。

评分器把每版复制到临时目录，排除 `.git`、`.env*`、数据库、密钥文件、符号链接、依赖和构建产物。它优先使用锁文件安装依赖，使用随机空闲端口和临时 SQLite/H2 数据，删除环境中的常见密钥变量，并在超时或完成后回收整个进程树。

执行阶段包括：依赖安装、测试、lint、build、迁移、启动/readiness、列表、创建、详情、更新、空白、超长、非法 JSON、404、进程存活、重启持久化和删除清理。

MongoDB 项目不会使用提交者 `.env` 或真实数据库。除非配置安全测试 MongoDB，运行态会标记为 `BLOCKED_ENV`。外部 URL 默认只读；完整 CRUD 需要 `--allow-data-write`。

## 报告结构

报告参考微软 Engineering Fundamentals Playbook 的[自动化测试](https://microsoft.github.io/code-with-engineering-playbook/automated-testing/)和[测试计划](https://microsoft.github.io/code-with-engineering-playbook/automated-testing/test-planning/)，以及 Google 的[代码评审实践](https://google.github.io/eng-practices/review/)和[端到端测试建议](https://testing.googleblog.com/2016/09/testing-on-toilet-what-makes-good-end.html)。本报告借鉴其 Build/Test/Start、正反场景、明确预期、事实证据和少量关键 E2E 原则，但不宣称是任何公司的官方模板。

固定顺序：执行摘要、范围与环境、代码来源、双分数总览、关键风险、各版评分、动态测试矩阵、优先行动项、证据索引、限制与判读。

Finding 使用稳定的 `D5-001` 编号和 `Blocker/High/Medium/Low` 分级，并包含期望、实际、影响、修复建议、复现方式和最多三条直接证据。报告展开全部有效 Finding，通过项保持紧凑；未实际计时的运行项使用 `-`，不输出伪造的 `0 ms`。

可选 JSON 使用 `schema_version: 2.0`，保留双分数、来源结果码、固定 commit、环境、每版评分项、运行矩阵、Finding 和限制字段，适合 CI 或后续汇总。

## 已知限制

- 非常规框架可能需要 `grader-config.json` 覆盖资源路径和启动命令。
- 静态 JS/Java 分析是受作用域约束的模式分析，不是完整编译器 AST。
- 通用浏览器自动化无法可靠猜测所有自定义控件；不确定时标记未验证。
- Native 动态执行不能提供容器级网络隔离，因此只应对用户明确信任的本地提交启用。

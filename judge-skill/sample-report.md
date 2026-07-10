# Day5 工程评测报告

## 执行摘要

- **证据确认分：85.35 / 100**
- 静态暂定分：97.32 / 100
- 工程就绪结论：`NOT_READY`
- 评测模式：`dynamic`
- 代码来源：local
- 识别版本：3 / 3
- 风险概况：Blocker 0，High 7，Medium 4，Low 2

> 证据确认分是本报告主分。静态暂定分表示代码和文档看起来可能达到的分数，不等同于运行通过。

## 范围与环境

- 提交物：`F:\学校活动\双创周\mission5`
- 生成时间：2026-07-10T23:44:51+08:00
- 文档：`陈天昊-24189100259-day5.md`, `README.md`
- 操作系统：Windows-11-10.0.26200-SP0
- Python：3.12.5；Node：C:\Program Files\nodejs\node.EXE；npm：C:\Program Files\nodejs\npm.CMD
- Java：C:\Program Files\Common Files\Oracle\Java\javapath\java.EXE；Git：F:\Git\cmd\git.EXE；Playwright：missing

### 代码来源

| 来源 | 状态 | 结果码 | 仓库 / 路径 | Markdown 位置 | Ref | Commit | 抓取时间 | 历史深度 | 说明 |
|---|---|---|---|---|---|---|---|---:|---|
| local | PASS | LOCAL_WORKTREE_DIRTY | F:\学校活动\双创周\mission5 | - | - | 660e9d589648 | - | 6 | 工作区非洁净（6 个变更或未跟踪条目）；Commit 仅表示仓库基线 |

## 评分总览

| 模块 | 静态暂定分 | 证据确认分 | 满分 | 状态 |
|---|---:|---:|---:|---|
| 整体评分 | 39.52 | 36.00 | 40 | - |
| springboot-vue-version | 19.07 | 18.82 | 20 | Spring Boot + Vue |
| django-version | 18.73 | 13.90 | 20 | Django |
| mern-version | 20.00 | 16.63 | 20 | MERN |
| **总计** | **97.32** | **85.35** | **100** | **NOT_READY** |

### 整体评分项

| 评分项 | 静态暂定 | 证据确认 | 满分 | 状态 | 主要缺口 |
|---|---:|---:|---:|---|---|
| 应用概念与最低功能范围 | 9.52 | 6.00 | 10 | PARTIAL | 无 |
| 三个不同技术栈 | 10.00 | 10.00 | 10 | PASS | 无 |
| AI 编码工具心得 | 10.00 | 10.00 | 10 | PASS | 无 |
| 至少一个非 JS 版本 | 10.00 | 10.00 | 10 | PASS | 无 |

## 关键风险

### D5-001 [High] Django JSON API 可能返回 HTML 404

- 范围：`django-version`
- 状态：`FAIL_PROJECT`
- 期望：GET/PUT/DELETE 不存在 ID 返回 {success:false,error} JSON
- 实际：API 处理函数直接调用 get_object_or_404，未转换 Http404
- 影响：客户端收到 HTML 响应，统一 API 契约被破坏。
- 建议：在 API 层捕获 Http404 或显式查询并调用 _json_error(..., 404)。
- 证据：`django-version/prompts/views.py:151`

### D5-002 [High] 动态 install 验证失败

- 范围：`django-version`
- 状态：`FAIL_PROJECT`
- 期望：install 阶段的必需检查通过
- 实际：RT-INSTALL-PY: 缺少 Python 依赖清单
- 影响：对应课程行为无法获得证据确认分，且工程就绪度被阻断。
- 建议：根据动态矩阵修复首个失败检查并重新运行隔离动态评分。
- 复现：`参见动态测试矩阵`

### D5-003 [High] 缺少可复现依赖清单

- 范围：`django-version`
- 状态：`FAIL_PROJECT`
- 期望：技术栈提供 package.json、requirements.txt、pyproject.toml、pom.xml 等依赖清单
- 实际：识别为 Django，但未找到对应的有效依赖清单
- 影响：评测机和其他开发者无法确定性安装依赖或复现运行环境。
- 建议：补充技术栈标准依赖文件并锁定版本。

### D5-004 [High] Spring 业务错误仍可能返回 HTTP 200

- 范围：`springboot-vue-version`
- 状态：`FAIL_PROJECT`
- 期望：不存在资源返回 404，验证失败返回 400
- 实际：控制器只返回 ApiResponse.error，未设置 ResponseEntity 或异常映射
- 影响：监控、客户端和代理无法从 HTTP 状态识别失败。
- 建议：使用 ResponseEntity 或 @RestControllerAdvice 映射 400/404。
- 证据：`springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/PromptController.java:37`；`springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/TagController.java:30`

### D5-005 [High] Spring 验证注解未绑定到可验证对象

- 范围：`springboot-vue-version`
- 状态：`FAIL_PROJECT`
- 期望：@Valid 校验带 @NotBlank/@Size 的 DTO 或实体
- 实际：控制器对 Map 使用 @Valid，实体字段约束不会自动执行
- 影响：空值、超长值或类型错误可能进入持久化层并产生 500。
- 建议：引入请求 DTO，或在 applyFields 后显式调用 Validator，并统一返回 400。
- 证据：`springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/PromptController.java:42`

### D5-006 [High] 动态 errors 验证失败

- 范围：`springboot-vue-version`
- 状态：`FAIL_PROJECT`
- 期望：errors 阶段的必需检查通过
- 实际：RT-ERROR-JSON: HTTP 400; body='{"timestamp":"2026-07-10T15:44:29.822+00:00","status":400,"error":"Bad Request","path":"/api/prompts"}'；RT-ERROR-404: HTTP 200; body='{"success":false,"error":"提示词不存在"}'
- 影响：对应课程行为无法获得证据确认分，且工程就绪度被阻断。
- 建议：根据动态矩阵修复首个失败检查并重新运行隔离动态评分。
- 复现：`参见动态测试矩阵`

### D5-007 [High] 动态 validation 验证失败

- 范围：`springboot-vue-version`
- 状态：`FAIL_PROJECT`
- 期望：validation 阶段的必需检查通过
- 实际：RT-VALID-BLANK: HTTP 500; body='{"timestamp":"2026-07-10T15:44:29.774+00:00","status":500,"error":"Internal Server Error","path":"/api/prompts"}'；RT-VALID-LENGTH: HTTP 500; body='{"timestamp":"2026-07-10T15:44:29.793+00:00","status":500,"error":"Internal Server Error","path":"/api/prompts"}'
- 影响：对应课程行为无法获得证据确认分，且工程就绪度被阻断。
- 建议：根据动态矩阵修复首个失败检查并重新运行隔离动态评分。
- 复现：`参见动态测试矩阵`

### D5-008 [Medium] 自动化测试缺失或为占位实现

- 范围：`django-version`
- 状态：`FAIL_PROJECT`
- 期望：至少包含核心模型、API 或页面行为测试
- 实际：未发现有效断言，或测试命令明确为占位失败
- 影响：功能回归只能依赖人工检查，工程就绪度下降。
- 建议：补充最小单元测试和 CRUD 集成测试，并让默认测试命令可通过。
- 证据：`django-version/prompts/tests.py:1`

### D5-009 [Medium] 自动化测试缺失或为占位实现

- 范围：`mern-version`
- 状态：`FAIL_PROJECT`
- 期望：至少包含核心模型、API 或页面行为测试
- 实际：未发现有效断言，或测试命令明确为占位失败
- 影响：功能回归只能依赖人工检查，工程就绪度下降。
- 建议：补充最小单元测试和 CRUD 集成测试，并让默认测试命令可通过。
- 证据：`mern-version/package.json:11`

### D5-010 [Medium] 动态 start 验证受环境阻塞

- 范围：`mern-version`
- 状态：`BLOCKED_ENV`
- 期望：start 阶段的必需检查通过
- 实际：RT-START: 未能确定安全启动命令、缺少测试数据库或服务未就绪
- 影响：当前评测机无法完成该阶段，相关分数保持未确认，但不直接归责项目。
- 建议：提供所需运行时、网络或专用测试依赖后重新验证。
- 复现：`参见动态测试矩阵`

### D5-011 [Medium] 动态 test 验证失败

- 范围：`mern-version`
- 状态：`FAIL_PROJECT`
- 期望：test 阶段的必需检查通过
- 实际：RT-TEST-NODE-1: echo "Error: no test specified" && exit 1
- 影响：对应课程行为无法获得证据确认分，且工程就绪度被阻断。
- 建议：根据动态矩阵修复首个失败检查并重新运行隔离动态评分。
- 复现：`参见动态测试矩阵`

### D5-012 [Low] README 技术版本与依赖不一致

- 范围：`mern-version`
- 状态：`FAIL_PROJECT`
- 期望：README 描述 react-router-dom ^7.18.1
- 实际：README 声称使用 v6
- 影响：运行说明可能误导复现者和维护者。
- 建议：从 package.json 生成或同步技术版本说明。
- 证据：`mern-version/README.md:114`

### D5-013 [Low] 本地提交快照未固定到洁净 Git 状态

- 范围：`submission`
- 状态：`FAIL_PROJECT`
- 期望：评测输入可由明确 commit 或归档文件确定性复现
- 实际：工作区非洁净（6 个变更或未跟踪条目）；Commit 仅表示仓库基线
- 影响：后续复评可能读取到与本报告不同的文件状态。
- 建议：提交或归档最终文件，并在报告中记录对应 commit SHA。

## 各版本评测

### springboot-vue-version

- 技术栈：Spring Boot + Vue
- 技术证据：Node.js, Vue, Vite, Java, Spring Boot
- 核心资源：`/api/prompts`
- 分数：暂定 19.07/20，确认 18.82/20

| 评分项 | 暂定 | 确认 | 满分 | 置信度 | 缺口 |
|---|---:|---:|---:|---|---|
| 源代码完整性 | 5.00 | 5.00 | 5 | high | 无 |
| README 文档 | 5.00 | 5.00 | 5 | high | 无 |
| 应用功能 | 4.07 | 3.82 | 5 | medium | 未证明服务端路径会触发验证；缺少异常处理 |
| writeup 描述 | 5.00 | 5.00 | 5 | high | 无 |

#### 功能证据拆分

| 子项 | 暂定 | 确认 | 满分 | 状态 |
|---|---:|---:|---:|---|
| 数据模型 | 1.00 | 1.00 | 1 | PASS |
| CRUD 完整性 | 1.50 | 1.50 | 1.5 | PASS |
| 输入验证 | 0.40 | 0.15 | 0.8 | PARTIAL |
| 错误处理与统一响应 | 0.27 | 0.27 | 0.8 | PARTIAL |
| 前后端对接 | 0.90 | 0.90 | 0.9 | PASS |

### django-version

- 技术栈：Django
- 技术证据：Django, Python
- 核心资源：`/api/prompts`
- 分数：暂定 18.73/20，确认 13.90/20

| 评分项 | 暂定 | 确认 | 满分 | 置信度 | 缺口 |
|---|---:|---:|---:|---|---|
| 源代码完整性 | 4.00 | 3.00 | 5 | medium | 缺少可复现依赖清单 |
| README 文档 | 5.00 | 4.00 | 5 | high | 无 |
| 应用功能 | 4.73 | 1.90 | 5 | medium | 未确认统一 JSON 404 和正确状态码 |
| writeup 描述 | 5.00 | 5.00 | 5 | high | 无 |

#### 功能证据拆分

| 子项 | 暂定 | 确认 | 满分 | 状态 |
|---|---:|---:|---:|---|
| 数据模型 | 1.00 | 0.60 | 1 | PARTIAL |
| CRUD 完整性 | 1.50 | 0.50 | 1.5 | PARTIAL |
| 输入验证 | 0.80 | 0.30 | 0.8 | PARTIAL |
| 错误处理与统一响应 | 0.53 | 0.20 | 0.8 | PARTIAL |
| 前后端对接 | 0.90 | 0.30 | 0.9 | PARTIAL |

### mern-version

- 技术栈：MERN
- 技术证据：Node.js, Express, MongoDB, React, Vite
- 核心资源：`/api/prompts`
- 分数：暂定 20.00/20，确认 16.63/20

| 评分项 | 暂定 | 确认 | 满分 | 置信度 | 缺口 |
|---|---:|---:|---:|---|---|
| 源代码完整性 | 5.00 | 4.67 | 5 | high | 无 |
| README 文档 | 5.00 | 4.67 | 5 | high | 无 |
| 应用功能 | 5.00 | 2.30 | 5 | high | 无 |
| writeup 描述 | 5.00 | 5.00 | 5 | high | 无 |

#### 功能证据拆分

| 子项 | 暂定 | 确认 | 满分 | 状态 |
|---|---:|---:|---:|---|
| 数据模型 | 1.00 | 0.60 | 1 | PARTIAL |
| CRUD 完整性 | 1.50 | 0.50 | 1.5 | PARTIAL |
| 输入验证 | 0.80 | 0.30 | 0.8 | PARTIAL |
| 错误处理与统一响应 | 0.80 | 0.30 | 0.8 | PARTIAL |
| 前后端对接 | 0.90 | 0.60 | 0.9 | PARTIAL |

## 动态测试矩阵

| 版本 | ID | 测试 | 类别 | 状态 | 耗时(ms) | 观察结果 |
|---|---|---|---|---|---:|---|
| springboot-vue-version | RT-TEST-JAVA | Spring 测试 | test | PASS | 13983 | exit=0 |
| springboot-vue-version | RT-BUILD-JAVA | Spring 构建 | build | PASS | 6063 | exit=0 |
| springboot-vue-version | RT-INSTALL-NODE-1 | 安装 Node 依赖 (frontend) | install | PASS | 3202 | exit=0 |
| springboot-vue-version | RT-BUILD-NODE-1 | Node build (frontend) | build | PASS | 2780 | exit=0 |
| springboot-vue-version | RT-START | 启动应用 | start | PASS | - | http://127.0.0.1:37181 |
| springboot-vue-version | RT-CRUD-LIST | 列表读取 | crud | PASS | - | HTTP 200; body='{"success":true,"data":[{"id":6,"title":"API 文档生成器","content":"你是一位技术文档撰写专家。请根据以下 API 代码自动生成接口文档。\\n\\n文档格式：\\n1. 接口概述（一句话）\\n2. 请求方法 + URL\\n3. 请求参数及说明\\n4. 响应示例（成功 + 失败各一个）\\n5. 错误码说明\\n6. 调用示例（curl ... |
| springboot-vue-version | RT-CRUD-CREATE | 创建资源 | crud | PASS | - | HTTP 201; body='{"success":true,"data":{"id":7,"title":"day5-grader-1783698269609","content":"runtime verification","notes":"temporary grader data","tags":[],"runs":[],"version":null,"rating":null,"createdAt":"2026-07... |
| springboot-vue-version | RT-CRUD-DETAIL | 详情读取 | crud | PASS | - | HTTP 200; body='{"success":true,"data":{"id":7,"title":"day5-grader-1783698269609","content":"runtime verification","notes":"temporary grader data","tags":[],"runs":[],"version":null,"rating":null,"createdAt":"2026-07... |
| springboot-vue-version | RT-CRUD-UPDATE | 更新资源 | crud | PASS | - | HTTP 200; body='{"success":true,"data":{"id":7,"title":"day5-grader-1783698269609-updated","content":"runtime verification","notes":"temporary grader data","tags":[],"runs":[],"version":null,"rating":null,"createdAt":... |
| springboot-vue-version | RT-VALID-BLANK | 拒绝空白必填字段 | validation | FAIL_PROJECT | - | HTTP 500; body='{"timestamp":"2026-07-10T15:44:29.774+00:00","status":500,"error":"Internal Server Error","path":"/api/prompts"}' |
| springboot-vue-version | RT-VALID-LENGTH | 拒绝超长字段 | validation | FAIL_PROJECT | - | HTTP 500; body='{"timestamp":"2026-07-10T15:44:29.793+00:00","status":500,"error":"Internal Server Error","path":"/api/prompts"}' |
| springboot-vue-version | RT-ERROR-JSON | 非法 JSON | errors | FAIL_PROJECT | - | HTTP 400; body='{"timestamp":"2026-07-10T15:44:29.822+00:00","status":400,"error":"Bad Request","path":"/api/prompts"}' |
| springboot-vue-version | RT-ERROR-404 | 不存在资源 | errors | FAIL_PROJECT | - | HTTP 200; body='{"success":false,"error":"提示词不存在"}' |
| springboot-vue-version | RT-ERROR-ALIVE | 负向请求后进程存活 | errors | PASS | - | HTTP 200; body='{"success":true,"data":[{"id":7,"title":"day5-grader-1783698269609-updated","content":"runtime verification","notes":"temporary grader data","tags":[],"runs":[],"version":null,"rating":null,"createdAt"... |
| springboot-vue-version | RT-PERSIST-RESTART | 重启后数据持久化 | persistence | PASS | - | HTTP 200; body='{"success":true,"data":{"id":7,"title":"day5-grader-1783698269609-updated","content":"runtime verification","notes":"temporary grader data","tags":[],"runs":[],"version":null,"rating":null,"createdAt":... |
| springboot-vue-version | RT-CRUD-DELETE | 删除资源 | crud | PASS | - | HTTP 200; body='{"success":true,"data":{"message":"删除成功"}}' |
| springboot-vue-version | RT-UI | 浏览器 UI 检查 | ui | NOT_APPLICABLE | - | Python Playwright 未安装 |
| django-version | RT-INSTALL-PY | 安装 Python 依赖 | install | FAIL_PROJECT | - | 缺少 Python 依赖清单 |
| mern-version | RT-INSTALL-NODE-1 | 安装 Node 依赖 (mern-version) | install | PASS | 3437 | exit=0 |
| mern-version | RT-INSTALL-NODE-2 | 安装 Node 依赖 (client) | install | PASS | 3062 | exit=0 |
| mern-version | RT-TEST-NODE-1 | Node 测试 (mern-version) | test | FAIL_PROJECT | - | echo "Error: no test specified" && exit 1 |
| mern-version | RT-BUILD-NODE-1 | Node build (mern-version) | build | PASS | 4515 | exit=0 |
| mern-version | RT-LINT-NODE-2 | Node lint (client) | lint | PASS | 891 | exit=0 |
| mern-version | RT-BUILD-NODE-2 | Node build (client) | build | PASS | 1546 | exit=0 |
| mern-version | RT-START | 启动应用 | start | BLOCKED_ENV | - | 未能确定安全启动命令、缺少测试数据库或服务未就绪 |

## 优先行动项

1. [High] django-version：在 API 层捕获 Http404 或显式查询并调用 _json_error(..., 404)。
2. [High] django-version：根据动态矩阵修复首个失败检查并重新运行隔离动态评分。
3. [High] django-version：补充技术栈标准依赖文件并锁定版本。
4. [High] springboot-vue-version：使用 ResponseEntity 或 @RestControllerAdvice 映射 400/404。
5. [High] springboot-vue-version：引入请求 DTO，或在 applyFields 后显式调用 Validator，并统一返回 400。
6. [High] springboot-vue-version：根据动态矩阵修复首个失败检查并重新运行隔离动态评分。
7. [Medium] django-version：补充最小单元测试和 CRUD 集成测试，并让默认测试命令可通过。
8. [Medium] mern-version：补充最小单元测试和 CRUD 集成测试，并让默认测试命令可通过。

## 证据索引

- `OVERALL-CONCEPT-DOC` `陈天昊-24189100259-day5.md:16`：应用概念
- `OVERALL-CONCEPT-DOC` `README.md:13`：应用概念
- `OVERALL-STACKS` `springboot-vue-version`：Spring Boot + Vue
- `OVERALL-STACKS` `django-version`：Django
- `OVERALL-AI-TOOL` `陈天昊-24189100259-day5.md:11`：Claude
- `OVERALL-AI-PROMPT` `陈天昊-24189100259-day5.md:1`：Prompt
- `OVERALL-NONJS` `springboot-vue-version`：Spring Boot + Vue
- `OVERALL-NONJS` `django-version`：Django
- `SRC-CODE` [springboot-vue-version] `springboot-vue-version/frontend/index.html:1`：发现 27 个代码文件
- `SRC-MANIFEST` [springboot-vue-version] `springboot-vue-version/backend/pom.xml:1`：pom.xml
- `README-PREREQUISITE` [springboot-vue-version] `springboot-vue-version/README.md:3`：Java
- `README-INSTALL` [springboot-vue-version] `springboot-vue-version/README.md:9`：安装
- `FUNC-MODEL-MODEL` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/entity/Prompt.java:8`：@Entity
- `FUNC-MODEL-ID` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/entity/Prompt.java:12`：@Id
- `WRITEUP-SECTION` [springboot-vue-version] `陈天昊-24189100259-day5.md:121`：springboot-vue-version
- `FUNC-MODEL-MODEL` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/entity/Prompt.java:8`：@Entity
- `FUNC-MODEL-ID` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/entity/Prompt.java:12`：@Id
- `FUNC-CRUD-LIST` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/PromptController.java:28`：@GetMapping
- `FUNC-CRUD-DETAIL` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/PromptController.java:33`：/{id}
- `FUNC-VALID-CONSTRAINT` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/entity/Prompt.java:16`：@NotBlank
- `FUNC-VALID-CONSTRAINT` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/entity/Run.java:18`：nullable = false
- `FUNC-ERROR-CONTRACT` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/PromptController.java:3`：ApiResponse
- `FUNC-ERROR-CONTRACT` [springboot-vue-version] `springboot-vue-version/backend/src/main/java/com/mission5/notes/controller/TagController.java:3`：ApiResponse
- `FUNC-FE-API` [springboot-vue-version] `springboot-vue-version/frontend/src/api/api.js:4`：fetch(
- `FUNC-FE-API` [springboot-vue-version] `springboot-vue-version/frontend/src/pages/PromptDetail.vue:52`：<form
- `SRC-CODE` [django-version] `django-version/manage.py:1`：发现 26 个代码文件
- `SRC-ENTRY` [django-version] `django-version/manage.py:1`：manage.py
- `README-PREREQUISITE` [django-version] `django-version/README.md:3`：Python
- `README-INSTALL` [django-version] `django-version/README.md:10`：安装
- `FUNC-MODEL-MODEL` [django-version] `django-version/prompts/models.py:1`：Python AST 确认 model
- `FUNC-MODEL-REQUIRED` [django-version] `django-version/prompts/models.py:1`：Python AST 确认 required
- `WRITEUP-SECTION` [django-version] `陈天昊-24189100259-day5.md:75`：django-version
- `FUNC-MODEL-MODEL` [django-version] `django-version/prompts/models.py:1`：Python AST 确认 model
- `FUNC-MODEL-REQUIRED` [django-version] `django-version/prompts/models.py:1`：Python AST 确认 required
- `FUNC-CRUD-LIST` [django-version] `django-version/prompts/views.py:40`：def prompt_list
- `FUNC-CRUD-DETAIL` [django-version] `django-version/prompts/views.py:2`：get_object_or_404
- `FUNC-VALID-CONSTRAINT` [django-version] `django-version/prompts/models.py:11`：max_length
- `FUNC-VALID-FLOW` [django-version] `django-version/prompts/models.py:2`：ValidationError
- `FUNC-ERROR-EXCEPTION` [django-version] `django-version/prompts/views.py:155`：try:
- `FUNC-ERROR-CONTRACT` [django-version] `django-version/prompts/views.py:11`：_json_success
- `FUNC-FE-API` [django-version] `django-version/prompts/templates/prompts/prompt_confirm_delete.html:7`：<form
- `FUNC-FE-API` [django-version] `django-version/prompts/templates/prompts/prompt_detail.html:51`：<form
- `SRC-CODE` [mern-version] `mern-version/seed.js:1`：发现 20 个代码文件
- `SRC-MANIFEST` [mern-version] `mern-version/package.json:1`：package.json
- `README-PREREQUISITE` [mern-version] `mern-version/README.md:3`：Node.js
- `README-INSTALL` [mern-version] `mern-version/README.md:10`：安装
- `FUNC-MODEL-MODEL` [mern-version] `mern-version/models/Prompt.js:3`：mongoose.Schema
- `FUNC-MODEL-ID` [mern-version] `mern-version/models/Prompt.js:41`：ObjectId
- `WRITEUP-SECTION` [mern-version] `陈天昊-24189100259-day5.md:35`：mern-version
- `FUNC-MODEL-MODEL` [mern-version] `mern-version/models/Prompt.js:3`：mongoose.Schema
- `FUNC-MODEL-ID` [mern-version] `mern-version/models/Prompt.js:41`：ObjectId
- `FUNC-CRUD-LIST` [mern-version] `mern-version/routes/prompts.js:6`：router.get('/'
- `FUNC-CRUD-DETAIL` [mern-version] `mern-version/routes/prompts.js:17`：:id
- `FUNC-VALID-CONSTRAINT` [mern-version] `mern-version/models/Prompt.js:7`：required:
- `FUNC-VALID-CONSTRAINT` [mern-version] `mern-version/models/Tag.js:7`：required:
- `FUNC-ERROR-EXCEPTION` [mern-version] `mern-version/server.js:8`：errorHandler
- `FUNC-ERROR-EXCEPTION` [mern-version] `mern-version/middleware/errorHandler.js:4`：errorHandler
- `FUNC-FE-API` [mern-version] `mern-version/client/src/api/api.js:5`：fetch(
- `FUNC-FE-API` [mern-version] `mern-version/client/src/pages/PromptDetail.jsx:27`：api.get

## 限制与判读

- Day5 课程总分严格保持 100 分；测试、CI、安全和可观测性只影响工程就绪结论。
- `BLOCKED_ENV` 表示评测环境未提供能力，不等同于项目代码失败；相应运行分仍保持未确认。
- GitHub 回退只读取公开或当前凭据可访问的固定 commit，不运行仓库代码、不读取 `.env`。

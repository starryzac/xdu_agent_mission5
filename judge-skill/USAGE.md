# Day5 Grader Skill 使用说明

## 前置条件

- Python 3.10 或更高版本。
- 静态评分不需要第三方 Python 包。
- GitHub 回退需要系统 `git` 和网络访问。
- 动态评分按项目需要 Node.js/npm、Python/pip、Java/Maven Wrapper 等。
- Playwright 仅为可选 UI 增强。
- 不需要也不使用 LibreOffice。

## 本地运行

默认静态评分目录：

```powershell
cd "F:\学校活动\双创周\mission5\grader-skill"
python .\scripts\grade_day5.py --root ".."
```

默认在提交物旁生成 `day5-evaluation-report.md`。指定输出：

```powershell
python .\scripts\grade_day5.py `
  --root ".." `
  --out ".\sample-report.md" `
  --json-out ".\report.json"
```

`--root` 可以直接指向单个 Markdown：

```powershell
python .\scripts\grade_day5.py --root "F:\submissions\student-day5.md"
```

如果该 Markdown 所在目录没有应用项目，评分器会读取其中的 GitHub 仓库链接并做静态评分。

## GitHub 回退

自动回退：

```powershell
python .\scripts\grade_day5.py --root ".\student-writeup.md"
```

明确指定一个或多个仓库：

```powershell
python .\scripts\grade_day5.py `
  --root ".\student-writeup.md" `
  --repo-url "https://github.com/example/day5-monorepo"
```

最多重复三次 `--repo-url`。关闭联网回退：

```powershell
python .\scripts\grade_day5.py --root ".\student-writeup.md" --no-remote-fallback
```

远程仓库只做静态分析。即使同时传入动态模式，自动 GitHub 回退也不会执行远程代码。

## 动态评分

动态模式会执行可信的本地提交代码：

```powershell
python .\scripts\grade_day5.py `
  --root ".." `
  --mode dynamic `
  --allow-install `
  --ui auto `
  --out ".\sample-report.md"
```

安全行为：

- 在临时副本安装依赖、构建和启动。
- 不复制 `.env`、原数据库、`.git` 或已有依赖目录。
- 使用临时数据库和随机端口。
- 测试数据带唯一前缀并在末尾删除。
- 完成或超时后清理进程树和临时目录。

若应用已经运行，可做只读 HTTP 检查：

```powershell
python .\scripts\grade_day5.py `
  --root ".." `
  --mode dynamic `
  --urls "mern=http://localhost:3000,django=http://localhost:8000,spring=http://localhost:8080"
```

只有确认 URL 指向测试环境时才添加 `--allow-data-write` 执行完整 CRUD。

## 非标准项目配置

可通过 JSON 覆盖资源、命令或测试数据库：

```json
{
  "mongodb_uri": "mongodb://127.0.0.1:27017/day5_grader_test",
  "versions": {
    "custom-version": {
      "resource": "/api/items",
      "cwd": ".",
      "start": ["python", "app.py", "--port", "{port}"]
    }
  }
}
```

运行：

```powershell
python .\scripts\grade_day5.py --root ".." --mode dynamic --allow-install --config ".\grader-config.json"
```

配置文件不得包含生产密钥。MongoDB URL 必须指向可清理的专用测试数据库。

## 安装到 Claude Code

项目级安装目录：

```text
<project>/.claude/skills/day5-grader/
```

PowerShell 复制示例：

```powershell
New-Item -ItemType Directory -Force -Path ".\.claude\skills" | Out-Null
Copy-Item -Recurse -Force `
  -LiteralPath "F:\学校活动\双创周\mission5\grader-skill" `
  -Destination ".\.claude\skills\day5-grader"
```

个人级安装到 `%USERPROFILE%\.claude\skills\day5-grader\` 后可在所有项目使用。

调用：

```text
/day5-grader F:\path\to\day5
```

```text
/day5-grader F:\path\to\student-writeup.md
```

新建顶层 skills 目录后若当前会话未发现命令，重启一次 Claude Code。已被监视的 skills 目录内修改通常会实时生效。

## 报告解读

- **证据确认分**：主分。未执行的动态部分不获分。
- **静态暂定分**：代码和文档表面可达到的分数，不代表运行通过。
- `FAIL_PROJECT`：项目实现、交付或复现链路本身失败。
- `BLOCKED_ENV`：评测机缺少网络、运行时、数据库或权限，不直接归责项目。
- `NOT_VERIFIED`：当前证据不足以形成工程就绪结论。
- `CONDITIONAL`：核心要求基本通过，但仍有工程风险。
- `NOT_READY`：核心功能、构建、契约或高风险项失败。
- `READY`：动态核心链路通过，且无高风险工程问题。

来源结果码用于解释代码快照：`LOCAL_WORKTREE_DIRTY` 表示本地文件未固定到洁净 commit，`REMOTE_SNAPSHOT` 表示 GitHub 固定 commit 已获取，`AMBIGUOUS_SOURCE` 表示多个仓库无法唯一选择，`SOURCE_UNAVAILABLE` 与 `BLOCKED_ENV` 分别表示来源不可用和评测环境受阻。

课程 100 分不会因测试、CI、安全或可观测性等附加维度被暗扣；这些项目只影响工程就绪结论和行动项。

## CI 与退出码

默认只要报告成功生成就返回 0。可增加 gate：

```powershell
python .\scripts\grade_day5.py --root ".." --fail-on not-ready
python .\scripts\grade_day5.py --root ".." --fail-on score:80
```

| 退出码 | 含义 |
|---:|---|
| 0 | 报告生成且 gate 通过 |
| 2 | 参数或输入错误 |
| 3 | 评分器内部错误，已尽量生成失败报告 |
| 4 | `--fail-on` 条件未通过 |

## 开发验证

```powershell
python -m unittest discover -s ".\tests" -v
python -m compileall -q ".\scripts"
claude --version
```

测试套件同时检查 Skill frontmatter、CLI 契约、静态串证防护、动态探针和 GitHub 链接解析。`argument-hint` 是 Claude Code 的官方 Skill 字段；部分旧版通用 Skill 校验器尚未收录该字段，因此不作为本项目验收门禁。

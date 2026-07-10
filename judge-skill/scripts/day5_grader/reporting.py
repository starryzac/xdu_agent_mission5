from __future__ import annotations

from collections import Counter

from .models import Assessment, Evidence, Finding, RuntimeCheck, ScoreItem


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def shorten(value: str, limit: int) -> str:
    compact = value.replace("\r", " ").replace("\n", " ")
    return compact if len(compact) <= limit else compact[: max(0, limit - 3)] + "..."


def evidence_ref(evidence: Evidence) -> str:
    label = evidence.path + (f":{evidence.line}" if evidence.line else "")
    if evidence.url:
        return f"[{label}]({evidence.url})"
    return f"`{label}`"


def score_status(item: ScoreItem) -> str:
    if item.verified >= item.max_score - 0.001:
        return "PASS"
    if item.verified == 0:
        return "UNVERIFIED"
    return "PARTIAL"


def _finding_block(finding: Finding) -> list[str]:
    lines = [
        f"### {finding.finding_id} [{finding.severity}] {finding.title}",
        "",
        f"- 范围：`{finding.scope}`",
        f"- 状态：`{finding.status}`",
        f"- 期望：{finding.expected}",
        f"- 实际：{finding.observed}",
        f"- 影响：{finding.impact}",
        f"- 建议：{finding.recommendation}",
    ]
    if finding.reproduction:
        lines.append(f"- 复现：`{finding.reproduction}`")
    if finding.evidence:
        lines.append("- 证据：" + "；".join(evidence_ref(item) for item in finding.evidence[:3]))
    lines.append("")
    return lines


def _runtime_rows(checks: list[RuntimeCheck], scope: str) -> list[str]:
    rows: list[str] = []
    for check in checks:
        duration = check.duration_ms if check.duration_ms is not None else "-"
        rows.append(
            f"| {cell(scope)} | {check.check_id} | {cell(check.name)} | {check.category} | {check.status} | {duration} | {cell(shorten(check.observed, 220))} |"
        )
    return rows


def render_markdown(assessment: Assessment) -> str:
    severity_counts = Counter(finding.severity for finding in assessment.findings)
    source_modes = sorted({source.mode for source in assessment.sources if source.status == "PASS"})
    lines = [
        "# Day5 工程评测报告",
        "",
        "## 执行摘要",
        "",
        f"- **证据确认分：{assessment.verified_score:.2f} / 100**",
        f"- 静态暂定分：{assessment.provisional_score:.2f} / 100",
        f"- 工程就绪结论：`{assessment.readiness}`",
        f"- 评测模式：`{assessment.mode}`",
        f"- 代码来源：{', '.join(source_modes) or '未获得代码源'}",
        f"- 识别版本：{len(assessment.versions)} / 3",
        f"- 风险概况：Blocker {severity_counts['Blocker']}，High {severity_counts['High']}，Medium {severity_counts['Medium']}，Low {severity_counts['Low']}",
        "",
        "> 证据确认分是本报告主分。静态暂定分表示代码和文档看起来可能达到的分数，不等同于运行通过。",
        "",
        "## 范围与环境",
        "",
        f"- 提交物：`{assessment.submission_path}`",
        f"- 生成时间：{assessment.generated_at}",
        f"- 文档：{', '.join(f'`{path.name}`' for path in assessment.documents) or '未识别'}",
        f"- 操作系统：{assessment.environment.get('os', 'unknown')}",
        f"- Python：{assessment.environment.get('python', 'unknown')}；Node：{assessment.environment.get('node', 'unknown')}；npm：{assessment.environment.get('npm', 'unknown')}",
        f"- Java：{assessment.environment.get('java', 'unknown')}；Git：{assessment.environment.get('git', 'unknown')}；Playwright：{assessment.environment.get('playwright', 'unknown')}",
        "",
        "### 代码来源",
        "",
        "| 来源 | 状态 | 结果码 | 仓库 / 路径 | Markdown 位置 | Ref | Commit | 抓取时间 | 历史深度 | 说明 |",
        "|---|---|---|---|---|---|---|---|---:|---|",
    ]
    for source in assessment.sources:
        location = source.repo_url or str(source.root)
        markdown_location = (
            f"{source.markdown_path}:{source.markdown_line or 1}" if source.markdown_path else "-"
        )
        lines.append(
            f"| {source.mode} | {source.status} | {cell(source.result_code or '-')} | {cell(location)} | {cell(markdown_location)} | {cell(source.ref or '-')} | {cell((source.commit or '-')[:12])} | {cell(source.fetched_at or '-')} | {source.history_depth if source.history_depth is not None else '-'} | {cell(source.detail or '-')} |"
        )

    lines.extend([
        "",
        "## 评分总览",
        "",
        "| 模块 | 静态暂定分 | 证据确认分 | 满分 | 状态 |",
        "|---|---:|---:|---:|---|",
        f"| 整体评分 | {sum(item.provisional for item in assessment.overall_items):.2f} | {sum(item.verified for item in assessment.overall_items):.2f} | 40 | - |",
    ])
    for version in assessment.versions:
        lines.append(
            f"| {cell(version.name)} | {version.provisional_total:.2f} | {version.verified_total:.2f} | 20 | {version.stack} |"
        )
    for index in range(len(assessment.versions), 3):
        lines.append(f"| 缺失版本 {index + 1} | 0.00 | 0.00 | 20 | MISSING |")
    lines.append(f"| **总计** | **{assessment.provisional_score:.2f}** | **{assessment.verified_score:.2f}** | **100** | **{assessment.readiness}** |")

    lines.extend([
        "",
        "### 整体评分项",
        "",
        "| 评分项 | 静态暂定 | 证据确认 | 满分 | 状态 | 主要缺口 |",
        "|---|---:|---:|---:|---|---|",
    ])
    for item in assessment.overall_items:
        lines.append(
            f"| {item.name} | {item.provisional:.2f} | {item.verified:.2f} | {item.max_score:g} | {score_status(item)} | {cell('；'.join(item.missing[:2]) or '无')} |"
        )

    lines.extend(["", "## 关键风险", ""])
    if assessment.findings:
        for finding in assessment.findings:
            lines.extend(_finding_block(finding))
    else:
        lines.extend(["未发现需要登记的风险。", ""])

    lines.extend(["## 各版本评测", ""])
    for version in assessment.versions:
        lines.extend([
            f"### {version.name}",
            "",
            f"- 技术栈：{version.stack}",
            f"- 技术证据：{', '.join(version.techs)}",
            f"- 核心资源：`{version.resource_path or '未识别'}`",
            f"- 分数：暂定 {version.provisional_total:.2f}/20，确认 {version.verified_total:.2f}/20",
            "",
            "| 评分项 | 暂定 | 确认 | 满分 | 置信度 | 缺口 |",
            "|---|---:|---:|---:|---|---|",
        ])
        for item in version.score_items:
            lines.append(
                f"| {item.name} | {item.provisional:.2f} | {item.verified:.2f} | {item.max_score:g} | {item.confidence} | {cell('；'.join(item.missing[:2]) or '无')} |"
            )
        lines.extend([
            "",
            "#### 功能证据拆分",
            "",
            "| 子项 | 暂定 | 确认 | 满分 | 状态 |",
            "|---|---:|---:|---:|---|",
        ])
        for item in version.feature_items:
            lines.append(
                f"| {item.name} | {item.provisional:.2f} | {item.verified:.2f} | {item.max_score:g} | {score_status(item)} |"
            )
        lines.append("")

    lines.extend([
        "## 动态测试矩阵",
        "",
        "| 版本 | ID | 测试 | 类别 | 状态 | 耗时(ms) | 观察结果 |",
        "|---|---|---|---|---|---:|---|",
    ])
    runtime_rows = [row for version in assessment.versions for row in _runtime_rows(version.runtime_checks, version.name)]
    lines.extend(runtime_rows or ["| - | - | 未执行动态测试 | - | NOT_RUN | - | 使用 --mode dynamic 显式启用 |"])

    lines.extend(["", "## 优先行动项", ""])
    actions: list[str] = []
    for finding in assessment.findings:
        action = f"[{finding.severity}] {finding.scope}：{finding.recommendation}"
        if action not in actions:
            actions.append(action)
    lines.extend([f"{index}. {action}" for index, action in enumerate(actions[:8], start=1)] or ["1. 当前证据范围内无阻断行动项。"])

    lines.extend(["", "## 证据索引", ""])
    evidence_rows: list[str] = []
    for item in assessment.overall_items:
        for ev in item.evidence[:2]:
            evidence_rows.append(f"- `{ev.rule_id}` {evidence_ref(ev)}：{ev.observed}")
    for version in assessment.versions:
        for item in version.score_items + version.feature_items:
            for ev in item.evidence[:2]:
                evidence_rows.append(f"- `{ev.rule_id}` [{version.name}] {evidence_ref(ev)}：{ev.observed}")
    lines.extend(evidence_rows[:60] or ["- 未获得代码证据。"])

    lines.extend(["", "## 限制与判读", ""])
    for limitation in assessment.limitations:
        lines.append(f"- {limitation}")
    lines.extend([
        "- Day5 课程总分严格保持 100 分；测试、CI、安全和可观测性只影响工程就绪结论。",
        "- `BLOCKED_ENV` 表示评测环境未提供能力，不等同于项目代码失败；相应运行分仍保持未确认。",
        "- GitHub 回退只读取公开或当前凭据可访问的固定 commit，不运行仓库代码、不读取 `.env`。",
        "",
    ])
    return "\n".join(lines)

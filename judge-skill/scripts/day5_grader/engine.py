from __future__ import annotations

import datetime as dt
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .analysis import (
    assess_overall,
    assess_version,
    assign_finding_ids,
    determine_readiness,
)
from .discovery import discover_candidates, local_source, resolve_submission
from .models import (
    BLOCKED_ENV,
    FAIL_PROJECT,
    Assessment,
    Finding,
    ProjectCandidate,
    SourceInfo,
)
from .remote import resolve_remote_sources
from .runtime import (
    RuntimeOptions,
    apply_runtime_scores,
    run_version_runtime,
    runtime_findings,
    runtime_artifact_directory,
    runtime_environment,
)


@dataclass
class GraderOptions:
    root: Path
    mode: str = "static"
    repo_urls: list[str] = field(default_factory=list)
    remote_fallback: bool = True
    allow_install: bool = False
    allow_data_write: bool = False
    ui: str = "auto"
    urls: dict[str, str] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    timeout: int = 120
    keep_artifacts: bool = False
    smoke_only: bool = False


def _source_failure_finding(source: SourceInfo) -> Finding:
    severity = "High" if source.status == FAIL_PROJECT else "Medium"
    title = {
        "AMBIGUOUS_SOURCE": "远程代码源存在歧义",
        "SOURCE_UNAVAILABLE": "远程代码源不可用",
        BLOCKED_ENV: "远程代码源受环境阻塞",
    }.get(source.result_code, "远程代码源不可用")
    return Finding(
        rule_id=f"SOURCE-{source.result_code or 'REMOTE'}",
        severity=severity,
        title=title,
        scope=source.label,
        status=source.status,
        expected="Markdown 中的 GitHub 仓库可被无交互地解析并固定到 commit",
        observed=source.detail,
        impact="无法检查应用代码，代码相关得分保持未验证。",
        recommendation="检查仓库 URL、公开权限和分支，或使用 --repo-url 显式指定。",
        reproduction="git ls-remote <repository-url>",
    )


def _missing_version_finding(count: int) -> Finding:
    return Finding(
        rule_id="DELIVERY-VERSION-COUNT",
        severity="Blocker",
        title="应用版本数量不足",
        scope="submission",
        status=FAIL_PROJECT,
        expected="识别到三个独立且可评分的 Web 应用版本",
        observed=f"只识别到 {count} 个版本",
        impact="缺失版本无法获得对应的每版 20 分，最低功能范围也无法完全证明。",
        recommendation="提交三个项目目录，或在 Markdown 中提供最多三个明确的 GitHub 仓库链接。",
    )


def grade_submission(options: GraderOptions) -> Assessment:
    submission = resolve_submission(options.root)
    document_source = local_source(submission.root)
    local_candidates = discover_candidates(document_source)
    sources: list[SourceInfo] = [document_source]
    candidates: list[ProjectCandidate] = local_candidates
    source_findings: list[Finding] = []
    limitations: list[str] = []
    if document_source.result_code == "LOCAL_WORKTREE_DIRTY":
        source_findings.append(Finding(
            rule_id="OPS-GIT-DIRTY",
            severity="Low",
            title="本地提交快照未固定到洁净 Git 状态",
            scope="submission",
            status=FAIL_PROJECT,
            expected="评测输入可由明确 commit 或归档文件确定性复现",
            observed=document_source.detail,
            impact="后续复评可能读取到与本报告不同的文件状态。",
            recommendation="提交或归档最终文件，并在报告中记录对应 commit SHA。",
        ))

    remote_temp: tempfile.TemporaryDirectory[str] | None = None
    use_remote = bool(options.repo_urls) or (not local_candidates and options.remote_fallback)
    if use_remote:
        remote_temp = tempfile.TemporaryDirectory(prefix="day5-grader-github-")
        resolution = resolve_remote_sources(
            submission.documents,
            Path(remote_temp.name),
            explicit_urls=options.repo_urls,
            timeout=options.timeout,
        )
        sources.extend(resolution.sources + resolution.failures)
        source_findings.extend(_source_failure_finding(source) for source in resolution.failures)
        remote_candidates: list[ProjectCandidate] = []
        for source in resolution.sources:
            remote_candidates.extend(discover_candidates(source))
        candidates = remote_candidates[:3]
        if resolution.sources:
            limitations.append("GitHub 回退只评估固定 commit 的静态快照，不执行远程代码。")
        if options.mode == "dynamic":
            limitations.append("输入使用 GitHub 回退，已按安全策略将动态模式降级为静态模式。")
    candidates = candidates[:3]

    versions = [
        assess_version(candidate, submission.document_text, submission.documents, document_source)
        for candidate in candidates
    ]
    overall = assess_overall(versions, submission.document_text, submission.documents, document_source)

    effective_mode = "static" if use_remote else options.mode
    if options.mode == "dynamic" and effective_mode == "dynamic":
        runtime_options = RuntimeOptions(
            enabled=True,
            allow_install=options.allow_install,
            allow_data_write=options.allow_data_write,
            ui=options.ui,
            timeout=options.timeout,
            urls=options.urls,
            config=options.config,
            keep_artifacts=options.keep_artifacts,
            smoke_only=options.smoke_only,
        )
        artifact_root, artifact_temp = runtime_artifact_directory(submission.root, options.keep_artifacts)
        try:
            for version in versions:
                run_version_runtime(version, runtime_options, artifact_root)
                version.findings.extend(runtime_findings(version))
            apply_runtime_scores(versions, overall)
        finally:
            if artifact_temp is not None:
                artifact_temp.cleanup()
    else:
        limitations.append("未执行动态测试；证据确认分不会奖励构建、启动和行为验证部分。")

    findings = source_findings + [finding for version in versions for finding in version.findings]
    if len(versions) < 3:
        findings.append(_missing_version_finding(len(versions)))
    assign_finding_ids(findings)
    readiness = determine_readiness(effective_mode, versions, findings)
    assessment = Assessment(
        submission_path=submission.path,
        submission_root=submission.root,
        mode=effective_mode,
        documents=submission.documents,
        sources=sources,
        versions=versions,
        overall_items=overall,
        findings=findings,
        readiness=readiness,
        generated_at=dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        environment=runtime_environment(),
        limitations=limitations,
    )
    if remote_temp is not None:
        remote_temp.cleanup()
    return assessment

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


TOOL_VERSION = "2.0.0"

PASS = "PASS"
FAIL_PROJECT = "FAIL_PROJECT"
BLOCKED_ENV = "BLOCKED_ENV"
NOT_RUN = "NOT_RUN"
NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class SourceInfo:
    mode: str
    root: Path
    label: str
    result_code: str = ""
    repo_url: str | None = None
    ref: str | None = None
    commit: str | None = None
    subpath: str | None = None
    fetched_at: str | None = None
    history_depth: int | None = None
    markdown_path: str | None = None
    markdown_line: int | None = None
    status: str = PASS
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "label": self.label,
            "result_code": self.result_code,
            "location": self.repo_url or str(self.root),
            "repo_url": self.repo_url,
            "ref": self.ref,
            "commit": self.commit,
            "subpath": self.subpath,
            "fetched_at": self.fetched_at,
            "history_depth": self.history_depth,
            "markdown_path": self.markdown_path,
            "markdown_line": self.markdown_line,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass
class Evidence:
    rule_id: str
    path: str
    line: int | None
    expected: str
    observed: str
    tier: str = "static"
    status: str = PASS
    confidence: str = "medium"
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "path": self.path,
            "line": self.line,
            "expected": self.expected,
            "observed": self.observed,
            "tier": self.tier,
            "status": self.status,
            "confidence": self.confidence,
            "url": self.url,
        }


@dataclass
class ScoreItem:
    key: str
    name: str
    max_score: float
    provisional: float
    verified: float
    static_cap: float
    dynamic_cap: float = 0.0
    status: str = PASS
    evidence: list[Evidence] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: str = "medium"

    def add_dynamic(self, ratio: float) -> None:
        ratio = min(1.0, max(0.0, ratio))
        self.verified = min(self.max_score, self.verified + self.dynamic_cap * ratio)
        if ratio < 1.0 and self.dynamic_cap:
            self.status = FAIL_PROJECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "max_score": self.max_score,
            "provisional": round(self.provisional, 2),
            "verified": round(self.verified, 2),
            "static_cap": self.static_cap,
            "dynamic_cap": self.dynamic_cap,
            "status": self.status,
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
            "missing": self.missing,
            "recommendation": self.recommendation,
        }


@dataclass
class RuntimeCheck:
    check_id: str
    name: str
    category: str
    status: str
    duration_ms: int | None = None
    command: str = ""
    expected: str = ""
    observed: str = ""
    log_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "command": self.command,
            "expected": self.expected,
            "observed": self.observed,
            "log_excerpt": self.log_excerpt,
        }


@dataclass
class Finding:
    rule_id: str
    severity: str
    title: str
    scope: str
    status: str
    expected: str
    observed: str
    impact: str
    recommendation: str
    evidence: list[Evidence] = field(default_factory=list)
    reproduction: str = ""
    finding_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.finding_id,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "title": self.title,
            "scope": self.scope,
            "status": self.status,
            "expected": self.expected,
            "observed": self.observed,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "reproduction": self.reproduction,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass
class ProjectCandidate:
    name: str
    path: Path
    source: SourceInfo


@dataclass
class VersionAssessment:
    name: str
    path: Path
    source: SourceInfo
    stack: str
    techs: list[str]
    non_js: bool
    resource_path: str | None
    score_items: list[ScoreItem]
    feature_items: list[ScoreItem]
    runtime_checks: list[RuntimeCheck] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def provisional_total(self) -> float:
        return sum(item.provisional for item in self.score_items)

    @property
    def verified_total(self) -> float:
        return sum(item.verified for item in self.score_items)

    def item(self, key: str) -> ScoreItem:
        return next(item for item in self.score_items if item.key == key)

    def feature(self, key: str) -> ScoreItem:
        return next(item for item in self.feature_items if item.key == key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "stack": self.stack,
            "techs": self.techs,
            "non_js": self.non_js,
            "resource_path": self.resource_path,
            "source": self.source.to_dict(),
            "provisional_score": round(self.provisional_total, 2),
            "verified_score": round(self.verified_total, 2),
            "score_items": [item.to_dict() for item in self.score_items],
            "feature_items": [item.to_dict() for item in self.feature_items],
            "runtime_checks": [item.to_dict() for item in self.runtime_checks],
            "findings": [item.to_dict() for item in self.findings],
        }


@dataclass
class Assessment:
    submission_path: Path
    submission_root: Path
    mode: str
    documents: list[Path]
    sources: list[SourceInfo]
    versions: list[VersionAssessment]
    overall_items: list[ScoreItem]
    findings: list[Finding]
    readiness: str
    generated_at: str
    environment: dict[str, str]
    limitations: list[str]

    @property
    def provisional_score(self) -> float:
        return sum(item.provisional for item in self.overall_items) + sum(
            item.provisional_total for item in self.versions
        )

    @property
    def verified_score(self) -> float:
        return sum(item.verified for item in self.overall_items) + sum(
            item.verified_total for item in self.versions
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "2.0",
            "tool_version": TOOL_VERSION,
            "generated_at": self.generated_at,
            "submission_path": str(self.submission_path),
            "mode": self.mode,
            "provisional_score": round(self.provisional_score, 2),
            "verified_score": round(self.verified_score, 2),
            "max_score": 100,
            "readiness": self.readiness,
            "documents": [str(path) for path in self.documents],
            "sources": [source.to_dict() for source in self.sources],
            "environment": self.environment,
            "overall_items": [item.to_dict() for item in self.overall_items],
            "versions": [version.to_dict() for version in self.versions],
            "findings": [item.to_dict() for item in self.findings],
            "limitations": self.limitations,
        }

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Iterable

from .models import Evidence, SourceInfo


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".claude",
    ".agents",
    ".codex",
    "grader-skill",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "target",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
}

EXCLUDED_FILES = {
    "skills-lock.json",
    "day5-evaluation-report.md",
    "sample-report.md",
    "report.json",
}

SOURCE_EXTS = {
    ".js", ".jsx", ".ts", ".tsx", ".vue", ".py", ".java", ".go",
    ".rb", ".php", ".cs", ".kt", ".html", ".css", ".scss", ".json",
    ".xml", ".yml", ".yaml", ".toml", ".properties", ".md",
}

MANIFEST_NAMES = {
    "package.json", "requirements.txt", "pyproject.toml", "manage.py", "pom.xml",
    "build.gradle", "build.gradle.kts", "go.mod", "Gemfile", "composer.json",
    "Cargo.toml", "mix.exs",
}


def read_text(path: Path, max_bytes: int = 1_000_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
    except OSError:
        return ""
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def is_excluded(path: Path, root: Path | None = None) -> bool:
    try:
        parts = path.relative_to(root).parts if root is not None else path.parts
    except ValueError:
        parts = path.parts
    return any(part in EXCLUDED_DIRS for part in parts) or path.name in EXCLUDED_FILES


def iter_files(root: Path, max_depth: int = 12, max_files: int = 10_000) -> Iterable[Path]:
    base_depth = len(root.resolve().parts)
    count = 0
    for path in root.rglob("*"):
        if is_excluded(path, root):
            continue
        try:
            depth = len(path.resolve().parts) - base_depth
        except OSError:
            continue
        if depth > max_depth or not path.is_file():
            continue
        yield path
        count += 1
        if count >= max_files:
            break


def project_files(root: Path, max_files: int = 2_000) -> list[Path]:
    files: list[Path] = []
    for path in iter_files(root, max_files=max_files):
        if path.name in MANIFEST_NAMES or path.suffix.lower() in SOURCE_EXTS:
            files.append(path)
    return files


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def source_relative(path: Path, source: SourceInfo) -> str:
    return relative_path(path, source.root)


def github_blob_url(source: SourceInfo, path: Path, line: int | None = None) -> str | None:
    if not source.repo_url or not source.commit:
        return None
    rel = source_relative(path, source)
    if source.subpath:
        rel = f"{source.subpath.strip('/')}/{rel}".strip("/")
    suffix = f"#L{line}" if line else ""
    return f"{source.repo_url}/blob/{source.commit}/{rel}{suffix}"


def first_match(path: Path, pattern: str, flags: int = re.I | re.M) -> tuple[int | None, str]:
    text = read_text(path, max_bytes=350_000)
    match = re.search(pattern, text, flags)
    if not match:
        return None, ""
    line = text.count("\n", 0, match.start()) + 1
    observed = match.group(0).strip().replace("\n", " ")[:180]
    return line, observed


def make_evidence(
    rule_id: str,
    path: Path,
    source: SourceInfo,
    expected: str,
    observed: str,
    line: int | None = None,
    tier: str = "static",
    status: str = "PASS",
    confidence: str = "high",
) -> Evidence:
    display = source_relative(path, source)
    return Evidence(
        rule_id=rule_id,
        path=display,
        line=line,
        expected=expected,
        observed=observed,
        tier=tier,
        status=status,
        confidence=confidence,
        url=github_blob_url(source, path, line),
    )


def find_evidence(
    paths: Iterable[Path],
    pattern: str,
    rule_id: str,
    source: SourceInfo,
    expected: str,
    limit: int = 3,
    flags: int = re.I | re.M,
) -> list[Evidence]:
    result: list[Evidence] = []
    for path in paths:
        line, observed = first_match(path, pattern, flags)
        if line is None:
            continue
        result.append(make_evidence(rule_id, path, source, expected, observed, line))
        if len(result) >= limit:
            break
    return result


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def stable_digest(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def shell_display(parts: list[str]) -> str:
    return " ".join(f'"{part}"' if re.search(r"\s", part) else part for part in parts)

from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import ProjectCandidate, SourceInfo
from .utils import EXCLUDED_DIRS, MANIFEST_NAMES, iter_files, project_files, read_text


NON_JS_TECHS = {
    "Python", "Django", "FastAPI", "Flask", "Ruby", "Rails", "Go", "Gin",
    "Java", "Spring Boot", "PHP", "Laravel", "C#", ".NET",
}


@dataclass
class SubmissionInput:
    path: Path
    root: Path
    documents: list[Path]
    document_text: str


def resolve_submission(path: Path) -> SubmissionInput:
    resolved = path.expanduser().resolve()
    if resolved.is_file():
        if resolved.suffix.lower() != ".md":
            raise ValueError(f"--root file must be Markdown: {resolved}")
        docs = [resolved]
        root = resolved.parent
    elif resolved.is_dir():
        root = resolved
        docs = discover_documents(root)
    else:
        raise ValueError(f"--root does not exist: {resolved}")
    text = "\n\n".join(f"# Source: {doc.name}\n{read_text(doc)}" for doc in docs)
    return SubmissionInput(path=resolved, root=root, documents=docs, document_text=text)


def discover_documents(root: Path) -> list[Path]:
    preferred: list[Path] = []
    fallback: list[Path] = []
    for path in sorted(root.glob("*.md"), key=lambda p: p.name.lower()):
        lower = path.name.lower()
        if lower in {"sample-report.md", "day5-evaluation-report.md"}:
            continue
        if "assignment" in lower or "template" in lower or "模板" in path.name:
            continue
        if "writeup" in lower or "day5" in lower or re.search(r"\d{8,}", lower):
            preferred.append(path)
        elif lower == "readme.md":
            fallback.append(path)
    return preferred + fallback


def local_source(root: Path) -> SourceInfo:
    commit, depth, dirty_count = git_metadata(root)
    if commit is None:
        result_code = "LOCAL_NO_GIT"
        detail = "未检测到 Git 仓库；证据对应当前文件快照"
    elif dirty_count:
        result_code = "LOCAL_WORKTREE_DIRTY"
        detail = f"工作区非洁净（{dirty_count} 个变更或未跟踪条目）；Commit 仅表示仓库基线"
    else:
        result_code = "LOCAL_WORKTREE_CLEAN"
        detail = "工作区洁净；Commit 对应当前文件快照"
    return SourceInfo(
        mode="local",
        root=root,
        label=f"local:{root.name}",
        result_code=result_code,
        commit=commit,
        history_depth=depth,
        detail=detail,
    )


def git_metadata(root: Path) -> tuple[str | None, int | None, int | None]:
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        if top.returncode != 0:
            return None, None, None
        sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        depth = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
        repository_root = Path(top.stdout.strip()).resolve()
        try:
            pathspec = root.resolve().relative_to(repository_root).as_posix() or "."
        except ValueError:
            pathspec = "."
        status = subprocess.run(
            ["git", "-C", str(repository_root), "status", "--porcelain", "--untracked-files=normal", "--", pathspec],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
        )
        dirty_count = len([line for line in status.stdout.splitlines() if line.strip()]) if status.returncode == 0 else None
        return (
            sha.stdout.strip() if sha.returncode == 0 else None,
            int(depth.stdout.strip()) if depth.returncode == 0 and depth.stdout.strip().isdigit() else None,
            dirty_count,
        )
    except (OSError, subprocess.SubprocessError):
        return None, None, None


def candidate_score(path: Path) -> int:
    if not path.is_dir() or path.name in EXCLUDED_DIRS:
        return -1
    files = list(iter_files(path, max_depth=6, max_files=1_200))
    names = {item.name for item in files}
    code = [
        item for item in files
        if item.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".vue", ".py", ".java", ".go", ".rb", ".php", ".html"}
    ]
    manifests = names.intersection(MANIFEST_NAMES)
    score = 5 * len(manifests)
    score += 4 if (path / "README.md").exists() else 0
    score += min(12, len(code) // 3)
    score += 3 if any(item.name in {"server.js", "app.py", "manage.py", "pom.xml", "go.mod"} for item in files) else 0
    return score


def discover_candidates(source: SourceInfo, limit: int = 3) -> list[ProjectCandidate]:
    root = source.root
    direct = [path for path in root.iterdir() if path.is_dir() and path.name not in EXCLUDED_DIRS]
    scored = sorted(
        ((candidate_score(path), path) for path in direct),
        key=lambda item: (-item[0], item[1].name.lower()),
    )
    selected = [path for score, path in scored if score >= 8]
    if len(selected) < limit:
        root_score = candidate_score(root)
        if root_score >= 8 and not selected:
            selected.append(root)
    if len(selected) < limit:
        nested: list[tuple[int, Path]] = []
        for path in root.glob("*/*"):
            if path.is_dir() and path.name not in EXCLUDED_DIRS:
                score = candidate_score(path)
                if score >= 8:
                    nested.append((score, path))
        for _, path in sorted(nested, key=lambda item: (-item[0], item[1].as_posix().lower())):
            if any(path == existing or path.is_relative_to(existing) for existing in selected):
                continue
            selected.append(path)
            if len(selected) >= limit:
                break
    return [ProjectCandidate(name=path.name, path=path, source=source) for path in selected[:limit]]


def parse_package(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(read_text(path))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def manifest_is_valid(path: Path) -> bool:
    if path.name == "package.json":
        return bool(parse_package(path))
    if path.name == "pom.xml":
        try:
            ET.parse(path)
            return True
        except (ET.ParseError, OSError):
            return False
    return bool(read_text(path).strip())


def detect_techs(candidate: ProjectCandidate) -> tuple[list[str], str, bool]:
    files = project_files(candidate.path)
    techs: list[str] = []

    def add(value: str) -> None:
        if value not in techs:
            techs.append(value)

    dependencies: dict[str, str] = {}
    for package in [path for path in files if path.name == "package.json"]:
        data = parse_package(package)
        for key in ("dependencies", "devDependencies"):
            section = data.get(key)
            if isinstance(section, dict):
                dependencies.update({str(k): str(v) for k, v in section.items()})
    if dependencies:
        add("Node.js")
    for dep, tech in (
        ("express", "Express"), ("mongoose", "MongoDB"), ("mongodb", "MongoDB"),
        ("react", "React"), ("vue", "Vue"), ("next", "Next.js"),
        ("@nestjs/core", "NestJS"), ("prisma", "Prisma"), ("vite", "Vite"),
        ("typescript", "TypeScript"),
    ):
        if dep in dependencies:
            add(tech)

    names = {path.name for path in files}
    manifest_blob = "\n".join(
        read_text(path, 300_000)
        for path in files
        if path.name in {"requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "build.gradle.kts", "go.mod", "Gemfile", "composer.json"}
    )
    if "manage.py" in names or re.search(r"\bdjango\b", manifest_blob, re.I):
        add("Django")
        add("Python")
    elif re.search(r"\bfastapi\b", manifest_blob, re.I):
        add("FastAPI")
        add("Python")
    elif re.search(r"\bflask\b", manifest_blob, re.I):
        add("Flask")
        add("Python")
    elif any(path.suffix == ".py" for path in files):
        add("Python")
    if "pom.xml" in names or "build.gradle" in names or "build.gradle.kts" in names:
        add("Java")
        if re.search(r"spring-boot|org\.springframework\.boot", manifest_blob, re.I):
            add("Spring Boot")
    if "go.mod" in names:
        add("Go")
        if re.search(r"gin-gonic|\bgin\b", manifest_blob, re.I):
            add("Gin")
    if "Gemfile" in names:
        add("Ruby")
        if re.search(r"\brails\b", manifest_blob, re.I):
            add("Rails")
    if "composer.json" in names:
        add("PHP")
        if re.search(r"laravel", manifest_blob, re.I):
            add("Laravel")
    if any(path.suffix == ".cs" for path in files):
        add("C#")
        add(".NET")
    if not techs:
        add("Unknown")

    values = set(techs)
    if {"MongoDB", "Express", "React", "Node.js"}.issubset(values):
        stack = "MERN"
    elif {"Django", "React"}.issubset(values):
        stack = "Django + React"
    elif "Django" in values:
        stack = "Django"
    elif {"Spring Boot", "Vue"}.issubset(values):
        stack = "Spring Boot + Vue"
    elif {"FastAPI", "Vue"}.issubset(values):
        stack = "FastAPI + Vue"
    elif "Flask" in values:
        stack = "Flask"
    elif "Rails" in values:
        stack = "Ruby on Rails"
    elif "Gin" in values:
        stack = "Go Gin"
    elif "Next.js" in values:
        stack = "Next.js"
    else:
        stack = " + ".join(techs[:4])
    return techs, stack, any(item in NON_JS_TECHS for item in techs)


def role_files(candidate: ProjectCandidate) -> dict[str, list[Path]]:
    files = project_files(candidate.path)
    roles = {"model": [], "backend": [], "frontend": [], "manifest": [], "tests": [], "docs": []}
    for path in files:
        rel = path.relative_to(candidate.path).as_posix().lower()
        name = path.name.lower()
        if path.name in MANIFEST_NAMES or name.endswith("lock.json") or name in {"yarn.lock", "pnpm-lock.yaml"}:
            roles["manifest"].append(path)
        if path.suffix.lower() == ".md":
            roles["docs"].append(path)
        if re.search(r"(^|/)(models?|entit(?:y|ies)|schemas?)(/|$)", rel) or name in {"models.py", "schema.prisma"}:
            roles["model"].append(path)
        if re.search(r"(^|/)(routes?|controllers?|middleware|repositories?|api)(/|$)", rel) or name in {"views.py", "urls.py", "server.js", "app.py"}:
            roles["backend"].append(path)
        if re.search(r"(^|/)(client|frontend|templates|pages|components)(/|$)", rel) or path.suffix.lower() in {".jsx", ".tsx", ".vue"}:
            roles["frontend"].append(path)
        if (
            re.search(r"(^|/)(tests?|specs?)(/|$)", rel)
            or name in {"test.py", "tests.py"}
            or re.search(r"(^test_|tests?\.|_tests?\.|\.test\.|\.spec\.)", name)
        ):
            roles["tests"].append(path)
    return roles


def markdown_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^(#{1,6})\s+(.+?)\s*$", text))
    if not matches:
        return [("document", text)]
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        end = len(text)
        for candidate in matches[index + 1 :]:
            if len(candidate.group(1)) <= level:
                end = candidate.start()
                break
        sections.append((match.group(2).strip(), text[match.start():end]))
    return sections


def version_document_section(document_text: str, version_name: str, stack: str) -> str:
    sections = markdown_sections(document_text)
    aliases = [version_name, stack]
    if stack == "MERN":
        aliases.append("MERN")
    elif "Django" in stack:
        aliases.append("Django")
    elif "Spring" in stack:
        aliases.extend(["Spring Boot", "Spring"])
    aliases = list(dict.fromkeys(alias for alias in aliases if alias))
    scored: list[tuple[int, str]] = []
    for heading, body in sections:
        score = 0
        if re.search(re.escape(version_name), heading, re.I):
            score += 12
        if stack and re.search(re.escape(stack), heading, re.I):
            score += 10
        for alias in aliases[2:]:
            if re.search(re.escape(alias), heading, re.I):
                score += 6
        if re.search(r"版本\s*(?:#?\d+|[一二三])|version\s*#?\d+", heading, re.I):
            lead = body[:800]
            if any(re.search(re.escape(alias), lead, re.I) for alias in aliases):
                score += 5
        scored.append((score, body))
    best_score, best_body = max(scored, key=lambda item: item[0], default=(0, ""))
    return best_body if best_score >= 5 else ""

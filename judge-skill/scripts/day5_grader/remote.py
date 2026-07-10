from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .models import BLOCKED_ENV, FAIL_PROJECT, PASS, SourceInfo
from .utils import stable_digest


GITHUB_URL_RE = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/(?:tree|blob)/[^\s)\]>]+)?",
    re.I,
)
CONTEXT_RE = re.compile(r"github|仓库|repository|\brepo\b|源码|source\s*code", re.I)
REJECT_SEGMENTS = {"issues", "pull", "pulls", "actions", "releases", "wiki", "raw"}


@dataclass
class GitHubLink:
    repo_url: str
    owner: str
    repo: str
    kind: str | None
    remainder: str
    markdown_path: str
    markdown_line: int
    priority: int

    @property
    def key(self) -> str:
        return f"{self.owner.lower()}/{self.repo.lower()}"


@dataclass
class RemoteResolution:
    sources: list[SourceInfo]
    failures: list[SourceInfo]
    ambiguous: bool = False


def normalize_github_url(raw: str) -> tuple[str, str, str, str | None, str] | None:
    cleaned = raw.rstrip(".,;:!?)]>'\"")
    try:
        parsed = urlsplit(cleaned)
    except ValueError:
        return None
    if parsed.scheme.lower() != "https" or parsed.hostname is None or parsed.hostname.lower() != "github.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        return None
    kind: str | None = None
    remainder = ""
    if len(parts) >= 3:
        if parts[2].lower() in REJECT_SEGMENTS:
            return None
        if parts[2].lower() not in {"tree", "blob"}:
            return None
        kind = parts[2].lower()
        remainder = "/".join(parts[3:])
        if not remainder:
            return None
    return f"https://github.com/{owner}/{repo}", owner, repo, kind, remainder


def extract_github_links(documents: list[Path], explicit_urls: list[str] | None = None) -> list[GitHubLink]:
    links: list[GitHubLink] = []
    for raw in explicit_urls or []:
        normalized = normalize_github_url(raw)
        if not normalized:
            continue
        repo_url, owner, repo, kind, remainder = normalized
        links.append(GitHubLink(repo_url, owner, repo, kind, remainder, "CLI", 0, 100))
    for document in documents:
        try:
            lines = document.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            priority = 10 if CONTEXT_RE.search(line) else 1
            for match in GITHUB_URL_RE.finditer(line):
                normalized = normalize_github_url(match.group(0))
                if not normalized:
                    continue
                repo_url, owner, repo, kind, remainder = normalized
                links.append(
                    GitHubLink(repo_url, owner, repo, kind, remainder, str(document), line_number, priority)
                )
    deduplicated: dict[str, GitHubLink] = {}
    for link in links:
        current = deduplicated.get(link.key)
        if current is None or link.priority > current.priority:
            deduplicated[link.key] = link
            continue
        if link.priority < current.priority:
            continue
        if current.kind is None:
            continue
        if link.kind is None:
            deduplicated[link.key] = link
            continue
        if (link.kind, link.remainder) != (current.kind, current.remainder):
            deduplicated[link.key] = GitHubLink(
                repo_url=current.repo_url,
                owner=current.owner,
                repo=current.repo,
                kind=None,
                remainder="",
                markdown_path=current.markdown_path,
                markdown_line=current.markdown_line,
                priority=current.priority,
            )
    return sorted(deduplicated.values(), key=lambda item: (-item.priority, item.key))


def choose_links(links: list[GitHubLink], explicit: bool) -> tuple[list[GitHubLink], bool]:
    if len(links) <= 3:
        return links, False
    if explicit:
        return links[:3], len(links) > 3
    high_priority = [link for link in links if link.priority >= 10]
    if 0 < len(high_priority) <= 3:
        return high_priority, False
    return [], True


def _run_git(args: list[str], timeout: int, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "Never",
        "GIT_LFS_SKIP_SMUDGE": "1",
    })
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _remote_refs(repo_url: str, timeout: int) -> tuple[str | None, list[str]]:
    default_branch: str | None = None
    symbolic = _run_git(["ls-remote", "--symref", repo_url, "HEAD"], timeout)
    if symbolic.returncode == 0:
        match = re.search(r"ref:\s+refs/heads/(\S+)\s+HEAD", symbolic.stdout)
        if match:
            default_branch = match.group(1)
    refs_result = _run_git(["ls-remote", "--heads", "--tags", repo_url], timeout)
    refs: list[str] = []
    if refs_result.returncode == 0:
        for line in refs_result.stdout.splitlines():
            if "\trefs/heads/" in line:
                refs.append(line.split("\trefs/heads/", 1)[1])
            elif "\trefs/tags/" in line:
                refs.append(line.split("\trefs/tags/", 1)[1].removesuffix("^{}"))
    return default_branch, sorted(set(refs), key=len, reverse=True)


def resolve_ref_and_path(link: GitHubLink, timeout: int) -> tuple[str | None, str]:
    if not link.kind:
        default_branch, _ = _remote_refs(link.repo_url, timeout)
        return default_branch, ""
    remainder = link.remainder.strip("/")
    default_branch, refs = _remote_refs(link.repo_url, timeout)
    for ref in refs:
        if remainder == ref:
            return ref, ""
        if remainder.startswith(ref + "/"):
            return ref, remainder[len(ref) + 1 :]
    first, _, rest = remainder.partition("/")
    if re.fullmatch(r"[0-9a-fA-F]{7,40}", first):
        return first, rest
    return first or default_branch, rest


def classify_git_failure(output: str) -> tuple[str, str]:
    lower = output.lower()
    if any(token in lower for token in ("could not resolve host", "timed out", "connection", "network")):
        return BLOCKED_ENV, "网络不可用或 GitHub 连接失败"
    if any(token in lower for token in ("authentication", "permission denied", "terminal prompts disabled", "repository not found")):
        return BLOCKED_ENV, "仓库不可访问、为私有仓库或当前凭据无权限"
    return FAIL_PROJECT, "GitHub 代码源无法解析或克隆"


def clone_link(
    link: GitHubLink,
    temp_root: Path,
    timeout: int = 120,
    max_bytes: int = 250 * 1024 * 1024,
    max_files: int = 10_000,
) -> SourceInfo:
    label = f"github:{link.owner}/{link.repo}"
    if shutil.which("git") is None:
        return SourceInfo(
            mode="github-static", root=temp_root, label=label, repo_url=link.repo_url,
            result_code=BLOCKED_ENV,
            markdown_path=link.markdown_path, markdown_line=link.markdown_line,
            status=BLOCKED_ENV, detail="系统未安装 git，无法获取仓库快照",
        )
    try:
        ref, subpath = resolve_ref_and_path(link, min(timeout, 30))
    except subprocess.TimeoutExpired:
        return SourceInfo(
            mode="github-static", root=temp_root, label=label, repo_url=link.repo_url,
            result_code=BLOCKED_ENV,
            markdown_path=link.markdown_path, markdown_line=link.markdown_line,
            status=BLOCKED_ENV, detail="解析 GitHub 分支或标签超时",
        )
    linked_subpath = subpath
    scan_subpath = "" if link.kind == "blob" else subpath
    destination = temp_root / stable_digest(link.repo_url + (ref or "HEAD"))
    command = ["clone", "--filter=blob:none", "--depth", "50", "--single-branch"]
    if ref and not re.fullmatch(r"[0-9a-fA-F]{7,40}", ref):
        command.extend(["--branch", ref])
    command.extend([link.repo_url, str(destination)])
    try:
        result = _run_git(command, timeout)
    except subprocess.TimeoutExpired:
        return SourceInfo(
            mode="github-static", root=temp_root, label=label, repo_url=link.repo_url,
            result_code=BLOCKED_ENV,
            ref=ref, subpath=scan_subpath or None, markdown_path=link.markdown_path,
            markdown_line=link.markdown_line, status=BLOCKED_ENV,
            detail=f"克隆超过 {timeout} 秒后终止",
        )
    if result.returncode != 0:
        status, detail = classify_git_failure(result.stderr + "\n" + result.stdout)
        return SourceInfo(
            mode="github-static", root=temp_root, label=label, repo_url=link.repo_url,
            result_code=BLOCKED_ENV if status == BLOCKED_ENV else "SOURCE_UNAVAILABLE",
            ref=ref, subpath=scan_subpath or None, markdown_path=link.markdown_path,
            markdown_line=link.markdown_line, status=status, detail=detail,
        )
    if ref and re.fullmatch(r"[0-9a-fA-F]{7,40}", ref):
        fetch = _run_git(["fetch", "--depth", "1", "origin", ref], timeout, destination)
        checkout = _run_git(["checkout", "--detach", ref], timeout, destination) if fetch.returncode == 0 else fetch
        if checkout.returncode != 0:
            status, detail = classify_git_failure(checkout.stderr + checkout.stdout)
            return SourceInfo(
                mode="github-static", root=destination, label=label, repo_url=link.repo_url,
                result_code=BLOCKED_ENV if status == BLOCKED_ENV else "SOURCE_UNAVAILABLE",
                ref=ref, subpath=scan_subpath or None, markdown_path=link.markdown_path,
                markdown_line=link.markdown_line, status=status, detail=detail,
            )
    scan_root = destination / scan_subpath if scan_subpath else destination
    if not scan_root.exists() or not scan_root.is_dir():
        return SourceInfo(
            mode="github-static", root=destination, label=label, repo_url=link.repo_url,
            result_code="SOURCE_UNAVAILABLE",
            ref=ref, subpath=scan_subpath or None, markdown_path=link.markdown_path,
            markdown_line=link.markdown_line, status=FAIL_PROJECT,
            detail=f"仓库中不存在链接指定的子目录: {scan_subpath}",
        )
    file_count = 0
    total_bytes = 0
    for path in destination.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        file_count += 1
        try:
            total_bytes += path.stat().st_size
        except OSError:
            pass
        if file_count > max_files or total_bytes > max_bytes:
            return SourceInfo(
                mode="github-static", root=scan_root, label=label, repo_url=link.repo_url,
                result_code=BLOCKED_ENV,
                ref=ref, subpath=scan_subpath or None, markdown_path=link.markdown_path,
                markdown_line=link.markdown_line, status=BLOCKED_ENV,
                detail=f"仓库超过扫描预算（{max_files} 文件或 {max_bytes // 1024 // 1024} MB）",
            )
    sha = _run_git(["rev-parse", "HEAD"], 10, destination)
    branch = _run_git(["branch", "--show-current"], 10, destination)
    depth = _run_git(["rev-list", "--count", "HEAD"], 10, destination)
    return SourceInfo(
        mode="github-static",
        root=scan_root,
        label=label,
        result_code="REMOTE_SNAPSHOT",
        repo_url=link.repo_url,
        ref=(branch.stdout.strip() if branch.returncode == 0 and branch.stdout.strip() else ref),
        commit=sha.stdout.strip() if sha.returncode == 0 else None,
        subpath=scan_subpath or None,
        fetched_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        history_depth=int(depth.stdout.strip()) if depth.returncode == 0 and depth.stdout.strip().isdigit() else None,
        markdown_path=link.markdown_path,
        markdown_line=link.markdown_line,
        status=PASS,
        detail=(
            f"静态快照，{file_count} 个文件，{total_bytes / 1024 / 1024:.1f} MB"
            + (f"；来源 blob: {linked_subpath}" if link.kind == "blob" and linked_subpath else "")
        ),
    )


def resolve_remote_sources(
    documents: list[Path],
    temp_root: Path,
    explicit_urls: list[str] | None = None,
    timeout: int = 120,
) -> RemoteResolution:
    links = extract_github_links(documents, explicit_urls)
    chosen, ambiguous = choose_links(links, explicit=bool(explicit_urls))
    if ambiguous:
        failure = SourceInfo(
            mode="github-static",
            root=temp_root,
            label="github:ambiguous",
            result_code="AMBIGUOUS_SOURCE",
            status=FAIL_PROJECT,
            detail="Markdown 中存在超过三个无法唯一判定的 GitHub 仓库链接，请使用 --repo-url 指定",
        )
        return RemoteResolution([], [failure], ambiguous=True)
    if not chosen:
        failure = SourceInfo(
            mode="github-static",
            root=temp_root,
            label="github:missing",
            result_code="SOURCE_UNAVAILABLE",
            status=FAIL_PROJECT,
            detail="本地未发现项目，Markdown 中也未找到有效 GitHub 仓库链接",
        )
        return RemoteResolution([], [failure])
    results = [clone_link(link, temp_root, timeout=timeout) for link in chosen]
    return RemoteResolution(
        sources=[source for source in results if source.status == PASS],
        failures=[source for source in results if source.status != PASS],
    )

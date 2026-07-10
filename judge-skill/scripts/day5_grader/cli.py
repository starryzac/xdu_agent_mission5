from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from .engine import GraderOptions, grade_submission
from .reporting import render_markdown
from .utils import atomic_write


def parse_urls(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    result: dict[str, str] = {}
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, url = item.split("=", 1)
            key = key.strip()
            if not key:
                raise ValueError("--urls keys must not be empty")
        else:
            key, url = item, item
        url = url.strip().rstrip("/")
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("--urls values must be absolute http:// or https:// URLs")
        if parsed.username or parsed.password:
            raise ValueError("--urls must not contain credentials")
        result[key] = url
    return result


def load_config(path: str | None) -> dict[str, object]:
    if not path:
        return {}
    config_path = Path(path).expanduser().resolve()
    try:
        value = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid --config: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("--config must contain a JSON object")
    return value


def default_output(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    base = resolved.parent if resolved.is_file() else resolved
    return base / "day5-evaluation-report.md"


def emergency_report(root: str, error: Exception) -> str:
    return "\n".join([
        "# Day5 工程评测报告",
        "",
        "## 执行摘要",
        "",
        "- **证据确认分：0.00 / 100**",
        "- 静态暂定分：0.00 / 100",
        "- 工程就绪结论：`NOT_VERIFIED`",
        "",
        "## 评测器错误",
        "",
        f"- 输入：`{root}`",
        f"- 类型：`{type(error).__name__}`",
        f"- 说明：{error}",
        "",
        "评分器未生成任何通过结论。请修正输入或报告此工具错误后重试。",
        "",
    ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grade a Day5 multi-stack Web assignment with evidence-aware scoring.")
    parser.add_argument("--root", required=True, help="Submission directory or a single Markdown file.")
    parser.add_argument("--mode", choices=("static", "dynamic"), default="static", help="Static by default; dynamic explicitly executes trusted local code.")
    parser.add_argument("--repo-url", action="append", default=[], help="Explicit GitHub repository URL; repeat up to three times.")
    parser.add_argument("--no-remote-fallback", action="store_true", help="Do not follow GitHub links when no local project is found.")
    parser.add_argument("--allow-install", action="store_true", help="Allow dependency installation in an isolated temporary copy during dynamic mode.")
    parser.add_argument("--ui", choices=("auto", "off", "required"), default="auto", help="Optional Playwright UI verification policy.")
    parser.add_argument("--urls", help="Comma-separated running service map, e.g. mern=http://localhost:3000.")
    parser.add_argument("--allow-data-write", action="store_true", help="Allow temporary CRUD probes against supplied URLs.")
    parser.add_argument("--config", help="Optional JSON adapter overrides.")
    parser.add_argument("--out", help="Markdown output path; defaults beside the submission.")
    parser.add_argument("--json-out", help="Optional structured JSON output path.")
    parser.add_argument("--timeout", type=int, default=120, help="Per-stage timeout in seconds (default: 120).")
    parser.add_argument("--keep-artifacts", action="store_true", help="Keep isolated runtime logs and workspaces under .grader-artifacts.")
    parser.add_argument("--fail-on", default="none", help="CI gate: none, not-ready, or score:<number>.")
    parser.add_argument("--smoke", action="store_true", help="Deprecated compatibility alias for dynamic read-only URL probes.")
    return parser


def fail_policy_exit(policy: str, readiness: str, verified_score: float) -> int:
    if policy == "none":
        return 0
    if policy == "not-ready":
        return 4 if readiness in {"NOT_READY", "NOT_VERIFIED"} else 0
    match = re.fullmatch(r"score:(\d+(?:\.\d+)?)", policy)
    if match:
        return 4 if verified_score < float(match.group(1)) else 0
    raise ValueError("--fail-on must be none, not-ready, or score:<number>")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    out_path = Path(args.out).expanduser().resolve() if args.out else default_output(root)
    mode = args.mode
    smoke_only = False
    if args.smoke:
        warnings.warn(
            "--smoke is deprecated; use --mode dynamic --urls ...",
            FutureWarning,
            stacklevel=2,
        )
        mode = "dynamic"
        smoke_only = True
    try:
        if args.timeout < 5:
            raise ValueError("--timeout must be at least 5 seconds")
        if len(args.repo_url) > 3:
            raise ValueError("--repo-url may be repeated at most three times")
        options = GraderOptions(
            root=root,
            mode=mode,
            repo_urls=args.repo_url,
            remote_fallback=not args.no_remote_fallback,
            allow_install=args.allow_install,
            allow_data_write=args.allow_data_write,
            ui=args.ui,
            urls=parse_urls(args.urls),
            config=load_config(args.config),
            timeout=args.timeout,
            keep_artifacts=args.keep_artifacts,
            smoke_only=smoke_only,
        )
        assessment = grade_submission(options)
        markdown = render_markdown(assessment)
        atomic_write(out_path, markdown)
        if args.json_out:
            json_path = Path(args.json_out).expanduser().resolve()
            atomic_write(json_path, json.dumps(assessment.to_dict(), ensure_ascii=False, indent=2) + "\n")
        print(f"Wrote Markdown report: {out_path}")
        if args.json_out:
            print(f"Wrote JSON report: {Path(args.json_out).expanduser().resolve()}")
        print(
            f"Verified: {assessment.verified_score:.2f}/100; "
            f"provisional: {assessment.provisional_score:.2f}/100; "
            f"readiness: {assessment.readiness}; versions: {len(assessment.versions)}"
        )
        return fail_policy_exit(args.fail_on, assessment.readiness, assessment.verified_score)
    except (ValueError, OSError) as exc:
        try:
            atomic_write(out_path, emergency_report(args.root, exc))
            print(f"Wrote failure report: {out_path}", file=sys.stderr)
        except OSError:
            pass
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        try:
            atomic_write(out_path, emergency_report(args.root, exc))
            print(f"Wrote failure report: {out_path}", file=sys.stderr)
        except OSError:
            pass
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

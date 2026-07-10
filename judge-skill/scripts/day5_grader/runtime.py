from __future__ import annotations

import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .discovery import parse_package
from .models import (
    BLOCKED_ENV,
    FAIL_PROJECT,
    NOT_APPLICABLE,
    NOT_RUN,
    PASS,
    Finding,
    RuntimeCheck,
    VersionAssessment,
)
from .utils import EXCLUDED_DIRS, read_text, shell_display


@dataclass
class RuntimeOptions:
    enabled: bool = False
    allow_install: bool = False
    allow_data_write: bool = False
    ui: str = "auto"
    timeout: int = 120
    urls: dict[str, str] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    keep_artifacts: bool = False
    smoke_only: bool = False


@dataclass
class CommandResult:
    status: str
    returncode: int | None
    duration_ms: int
    output: str
    command: str


@dataclass
class ManagedProcess:
    process: subprocess.Popen[str]
    log_path: Path
    log_handle: Any


def sanitized_environment(temp_root: Path) -> dict[str, str]:
    secret_re = re.compile(r"TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|AWS_|AZURE_|GOOGLE_|OPENAI_|ANTHROPIC_|GITHUB_", re.I)
    env = {key: value for key, value in os.environ.items() if not secret_re.search(key)}
    env.update({
        "CI": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "Never",
        "GIT_LFS_SKIP_SMUDGE": "1",
        "DAY5_GRADER": "1",
        "DAY5_GRADER_TEMP": str(temp_root),
    })
    return env


def terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=10,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
    except (OSError, subprocess.SubprocessError):
        try:
            process.kill()
        except OSError:
            pass


def run_command(
    parts: list[str], cwd: Path, timeout: int, env: dict[str, str]
) -> CommandResult:
    started = time.monotonic()
    resolved_parts = list(parts)
    if os.name == "nt" and resolved_parts and resolved_parts[0].lower() in {"npm", "npx"}:
        resolved_parts[0] = shutil.which(resolved_parts[0] + ".cmd") or resolved_parts[0]
    display = shell_display(resolved_parts)
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        process = subprocess.Popen(
            resolved_parts,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            **kwargs,
        )
        output, _ = process.communicate(timeout=timeout)
        output = (output or "").strip()
        status = PASS if process.returncode == 0 else classify_command_failure(output)
        return CommandResult(status, process.returncode, int((time.monotonic() - started) * 1000), output[-6000:], display)
    except FileNotFoundError as exc:
        return CommandResult(BLOCKED_ENV, None, int((time.monotonic() - started) * 1000), str(exc), display)
    except subprocess.TimeoutExpired as exc:
        terminate_process_tree(process)
        try:
            trailing, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            trailing = ""
        captured = exc.stdout if isinstance(exc.stdout, str) else ""
        output = (captured + "\n" + (trailing or "")).strip()
        return CommandResult(FAIL_PROJECT, None, int((time.monotonic() - started) * 1000), f"timeout: {output}"[-6000:], display)
    except OSError as exc:
        return CommandResult(BLOCKED_ENV, None, int((time.monotonic() - started) * 1000), str(exc), display)


def classify_command_failure(output: str) -> str:
    lower = output.lower()
    environment_markers = (
        "could not resolve host", "network", "connection timed out", "connection was closed",
        "unable to access", "no module named", "command not found", "is not recognized",
        "cannot start maven from wrapper", "failed to download", "econnreset", "enotfound",
        "spawn eperm", "permission denied",
    )
    return BLOCKED_ENV if any(marker in lower for marker in environment_markers) else FAIL_PROJECT


def command_check(check_id: str, name: str, category: str, result: CommandResult, expected: str) -> RuntimeCheck:
    return RuntimeCheck(
        check_id=check_id,
        name=name,
        category=category,
        status=result.status,
        duration_ms=result.duration_ms,
        command=result.command,
        expected=expected,
        observed=f"exit={result.returncode}" if result.returncode is not None else result.status,
        log_excerpt=result.output[-1000:],
    )


def copy_project(source: Path, destination: Path) -> None:
    excluded_names = set(EXCLUDED_DIRS) | {
        ".npmrc", ".pypirc", "pip.ini", "db.sqlite3",
    }
    secret_suffixes = (".pem", ".key", ".p12", ".pfx")
    database_suffixes = (".db", ".sqlite", ".sqlite3", ".mv.db", ".trace.db")

    def ignore(directory: str, names: list[str]) -> set[str]:
        base = Path(directory)
        ignored = {
            name for name in names
            if name in excluded_names
            or name.lower().startswith(".env")
            or name.lower().endswith(secret_suffixes + database_suffixes)
            or (base / name).is_symlink()
        }
        return ignored

    shutil.copytree(source, destination, ignore=ignore, symlinks=True, dirs_exist_ok=True)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_process(parts: list[str], cwd: Path, env: dict[str, str], log_path: Path) -> ManagedProcess:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("w", encoding="utf-8", errors="replace")
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    resolved_parts = list(parts)
    if os.name == "nt" and resolved_parts and resolved_parts[0].lower() in {"npm", "npx"}:
        resolved_parts[0] = shutil.which(resolved_parts[0] + ".cmd") or resolved_parts[0]
    process = subprocess.Popen(
        resolved_parts,
        cwd=str(cwd),
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )
    return ManagedProcess(process, log_path, handle)


def stop_process(managed: ManagedProcess) -> None:
    process = managed.process
    terminate_process_tree(process)
    managed.log_handle.close()


def request_json(
    method: str,
    url: str,
    payload: Any | None = None,
    malformed: bool = False,
    timeout: int = 5,
) -> tuple[int, Any, str]:
    data: bytes | None = None
    headers = {"Accept": "application/json"}
    if payload is not None or malformed:
        headers["Content-Type"] = "application/json"
        data = b"{not-json" if malformed else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(1_000_000).decode("utf-8", errors="replace")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = None
            return response.status, body, raw[:1000]
    except urllib.error.HTTPError as exc:
        raw = exc.read(1_000_000).decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = None
        return exc.code, body, raw[:1000]
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, None, f"{type(exc).__name__}: {exc}"


def wait_ready(base_url: str, resource: str, process: ManagedProcess, timeout: int) -> tuple[bool, str]:
    deadline = time.monotonic() + timeout
    last = ""
    candidates = [resource, "/api/health", "/"]
    while time.monotonic() < deadline:
        if process.process.poll() is not None:
            try:
                last = process.log_path.read_text(encoding="utf-8", errors="replace")[-1500:]
            except OSError:
                pass
            return False, f"process exited {process.process.returncode}: {last}"
        for path in candidates:
            status, _, raw = request_json("GET", base_url + path, timeout=2)
            if 100 <= status < 500:
                return True, f"{path} -> HTTP {status}"
            last = raw
        time.sleep(0.5)
    return False, f"readiness timeout: {last}"


def _http_check(
    check_id: str,
    name: str,
    category: str,
    expected: str,
    status: int,
    body: Any,
    raw: str,
    predicate: Callable[[int, Any], bool],
) -> RuntimeCheck:
    passed = predicate(status, body)
    return RuntimeCheck(
        check_id=check_id,
        name=name,
        category=category,
        status=PASS if passed else FAIL_PROJECT,
        expected=expected,
        observed=f"HTTP {status}; body={raw[:260]!r}",
    )


def read_only_http_checks(base_url: str, resource: str) -> list[RuntimeCheck]:
    status, body, raw = request_json("GET", base_url + resource)
    return [_http_check(
        "RT-HTTP-LIST", "读取核心资源列表", "crud",
        "HTTP 2xx 且返回 JSON", status, body, raw,
        lambda code, value: 200 <= code < 300 and isinstance(value, (dict, list)),
    )]


def full_http_checks(
    base_url: str,
    resource: str,
    restart: Callable[[], tuple[ManagedProcess | None, str]] | None = None,
    current_process: ManagedProcess | None = None,
) -> tuple[list[RuntimeCheck], ManagedProcess | None]:
    checks: list[RuntimeCheck] = []
    status, body, raw = request_json("GET", base_url + resource)
    checks.append(_http_check(
        "RT-CRUD-LIST", "列表读取", "crud", "HTTP 2xx，统一 JSON 列表",
        status, body, raw,
        lambda code, value: 200 <= code < 300 and isinstance(value, (dict, list)),
    ))

    token = f"day5-grader-{int(time.time() * 1000)}"
    payload = {"title": token, "content": "runtime verification", "notes": "temporary grader data"}
    status, body, raw = request_json("POST", base_url + resource, payload)
    created = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
    object_id = created.get("id") if isinstance(created, dict) else None
    if object_id is None and isinstance(created, dict):
        object_id = created.get("_id")
    checks.append(_http_check(
        "RT-CRUD-CREATE", "创建资源", "crud", "HTTP 2xx，success=true 且返回 id",
        status, body, raw,
        lambda code, value: 200 <= code < 300 and object_id is not None and (not isinstance(value, dict) or value.get("success", True) is True),
    ))
    detail_url = f"{base_url}{resource}/{object_id}" if object_id is not None else f"{base_url}{resource}/__missing__"
    status, body, raw = request_json("GET", detail_url)
    checks.append(_http_check(
        "RT-CRUD-DETAIL", "详情读取", "crud", "新建对象可按 id 读取",
        status, body, raw, lambda code, value: object_id is not None and 200 <= code < 300 and isinstance(value, dict),
    ))
    update_payload = {**payload, "title": token + "-updated"}
    status, body, raw = request_json("PUT", detail_url, update_payload)
    checks.append(_http_check(
        "RT-CRUD-UPDATE", "更新资源", "crud", "HTTP 2xx 且返回更新对象",
        status, body, raw, lambda code, value: object_id is not None and 200 <= code < 300 and isinstance(value, dict),
    ))

    status, body, raw = request_json("POST", base_url + resource, {"title": "   ", "content": ""})
    checks.append(_http_check(
        "RT-VALID-BLANK", "拒绝空白必填字段", "validation", "HTTP 4xx 且 success=false",
        status, body, raw,
        lambda code, value: 400 <= code < 500 and isinstance(value, dict) and value.get("success") is False,
    ))
    status, body, raw = request_json("POST", base_url + resource, {"title": "x" * 101, "content": "valid"})
    checks.append(_http_check(
        "RT-VALID-LENGTH", "拒绝超长字段", "validation", "HTTP 4xx 且 success=false",
        status, body, raw,
        lambda code, value: 400 <= code < 500 and isinstance(value, dict) and value.get("success") is False,
    ))
    status, body, raw = request_json("POST", base_url + resource, malformed=True)
    checks.append(_http_check(
        "RT-ERROR-JSON", "非法 JSON", "errors", "HTTP 4xx 且统一 JSON 错误",
        status, body, raw,
        lambda code, value: 400 <= code < 500 and isinstance(value, dict) and value.get("success") is False,
    ))
    missing_id = "000000000000000000000000" if object_id and len(str(object_id)) == 24 else "999999999"
    status, body, raw = request_json("GET", f"{base_url}{resource}/{missing_id}")
    checks.append(_http_check(
        "RT-ERROR-404", "不存在资源", "errors", "HTTP 404 且统一 JSON 错误",
        status, body, raw,
        lambda code, value: code == 404 and isinstance(value, dict) and value.get("success") is False,
    ))
    status, body, raw = request_json("GET", base_url + resource)
    checks.append(_http_check(
        "RT-ERROR-ALIVE", "负向请求后进程存活", "errors", "后端继续返回列表",
        status, body, raw, lambda code, value: 200 <= code < 300 and isinstance(value, (dict, list)),
    ))

    active_process = current_process
    if restart and object_id is not None and current_process is not None:
        stop_process(current_process)
        active_process, detail = restart()
        if active_process:
            status, body, raw = request_json("GET", detail_url)
            checks.append(_http_check(
                "RT-PERSIST-RESTART", "重启后数据持久化", "persistence", "重启后仍可读取测试对象",
                status, body, raw, lambda code, value: 200 <= code < 300 and isinstance(value, dict),
            ))
        else:
            checks.append(RuntimeCheck(
                "RT-PERSIST-RESTART", "重启后数据持久化", "persistence", FAIL_PROJECT,
                expected="服务重启并读取测试对象", observed=detail,
            ))
    else:
        checks.append(RuntimeCheck(
            "RT-PERSIST-RESTART", "重启后数据持久化", "persistence", NOT_APPLICABLE,
            expected="由评分器启动的隔离服务可安全重启", observed="外部 URL 或启动适配器不支持重启",
        ))

    status, body, raw = request_json("DELETE", detail_url)
    checks.append(_http_check(
        "RT-CRUD-DELETE", "删除资源", "crud", "HTTP 2xx 且 success=true",
        status, body, raw,
        lambda code, value: object_id is not None and 200 <= code < 300 and isinstance(value, dict) and value.get("success", True) is True,
    ))
    return checks, active_process


def _version_config(options: RuntimeOptions, version: VersionAssessment) -> dict[str, Any]:
    versions = options.config.get("versions") if isinstance(options.config, dict) else None
    if not isinstance(versions, dict):
        return {}
    value = versions.get(version.name)
    return value if isinstance(value, dict) else {}


def _matching_url(options: RuntimeOptions, version: VersionAssessment) -> str | None:
    for key, value in options.urls.items():
        if key.lower() in version.name.lower() or key.lower() in version.stack.lower():
            return value.rstrip("/")
    if len(options.urls) == 1:
        return next(iter(options.urls.values())).rstrip("/")
    return None


def _install_node(project: Path, options: RuntimeOptions, env: dict[str, str]) -> list[RuntimeCheck]:
    checks: list[RuntimeCheck] = []
    package_dirs = sorted({path.parent for path in project.rglob("package.json") if "node_modules" not in path.parts}, key=lambda p: len(p.parts))
    for index, directory in enumerate(package_dirs, start=1):
        lock = directory / "package-lock.json"
        if not lock.exists():
            checks.append(RuntimeCheck(
                f"RT-INSTALL-NODE-{index}", f"安装 Node 依赖 ({directory.name})", "install", FAIL_PROJECT,
                expected="存在 package-lock.json 并使用 npm ci", observed="缺少 package-lock.json",
            ))
            continue
        result = run_command(["npm", "ci", "--no-audit", "--no-fund"], directory, options.timeout, env)
        checks.append(command_check(
            f"RT-INSTALL-NODE-{index}", f"安装 Node 依赖 ({directory.name})", "install", result,
            "npm ci 成功",
        ))
    return checks


def _run_node_checks(project: Path, options: RuntimeOptions, env: dict[str, str]) -> list[RuntimeCheck]:
    checks: list[RuntimeCheck] = []
    package_paths = sorted([path for path in project.rglob("package.json") if "node_modules" not in path.parts], key=lambda p: len(p.parts))
    for index, package_path in enumerate(package_paths, start=1):
        data = parse_package(package_path)
        scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
        directory = package_path.parent
        test_script = str(scripts.get("test", ""))
        if test_script:
            if re.search(r"no test specified|exit\s+1", test_script, re.I):
                checks.append(RuntimeCheck(
                    f"RT-TEST-NODE-{index}", f"Node 测试 ({directory.name})", "test", FAIL_PROJECT,
                    expected="默认测试命令包含有效断言并通过", observed=test_script,
                ))
            else:
                result = run_command(["npm", "test", "--", "--runInBand"], directory, options.timeout, env)
                checks.append(command_check(f"RT-TEST-NODE-{index}", f"Node 测试 ({directory.name})", "test", result, "测试通过"))
        for script, category in (("lint", "lint"), ("build", "build")):
            if script in scripts:
                result = run_command(["npm", "run", script], directory, options.timeout, env)
                checks.append(command_check(
                    f"RT-{category.upper()}-NODE-{index}", f"Node {script} ({directory.name})", category,
                    result, f"npm run {script} 成功",
                ))
    if not any(check.category == "build" for check in checks):
        checks.append(RuntimeCheck(
            "RT-BUILD-NODE", "Node 构建入口", "build", NOT_APPLICABLE,
            expected="无编译步骤的后端可直接启动", observed="未定义 build 脚本",
        ))
    return checks


def _prepare_python(project: Path, options: RuntimeOptions, env: dict[str, str]) -> tuple[list[RuntimeCheck], Path | None]:
    checks: list[RuntimeCheck] = []
    requirements = project / "requirements.txt"
    pyproject = project / "pyproject.toml"
    if not requirements.exists() and not pyproject.exists():
        checks.append(RuntimeCheck(
            "RT-INSTALL-PY", "安装 Python 依赖", "install", FAIL_PROJECT,
            expected="存在 requirements.txt 或 pyproject.toml", observed="缺少 Python 依赖清单",
        ))
        return checks, None
    venv = project / ".grader-venv"
    result = run_command([sys.executable, "-m", "venv", str(venv)], project, options.timeout, env)
    checks.append(command_check("RT-VENV-PY", "创建隔离 Python 环境", "install", result, "venv 创建成功"))
    if result.status != PASS:
        return checks, None
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install_parts = [str(python), "-m", "pip", "install"]
    install_parts.extend(["-r", str(requirements)] if requirements.exists() else ["."])
    result = run_command(install_parts, project, options.timeout, env)
    checks.append(command_check("RT-INSTALL-PY", "安装 Python 依赖", "install", result, "依赖安装成功"))
    return checks, python if result.status == PASS else None


def _prepare_spring(project: Path, options: RuntimeOptions, env: dict[str, str]) -> tuple[list[RuntimeCheck], Path | None]:
    backend = next((path.parent for path in project.rglob("pom.xml")), None)
    if backend is None:
        return [RuntimeCheck(
            "RT-BUILD-JAVA", "Spring 构建", "build", FAIL_PROJECT,
            expected="存在 pom.xml", observed="未找到 Maven 项目",
        )], None
    wrapper = backend / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    command = str(wrapper) if wrapper.exists() else shutil.which("mvn")
    if not command:
        return [RuntimeCheck(
            "RT-BUILD-JAVA", "Spring 构建", "build", BLOCKED_ENV,
            expected="Maven Wrapper 或系统 Maven 可用", observed="未找到 Maven",
        )], None
    result = run_command([command, "-q", "test"], backend, options.timeout, env)
    checks = [command_check("RT-TEST-JAVA", "Spring 测试", "test", result, "mvn test 通过")]
    if result.status != PASS:
        return checks, None
    result = run_command([command, "-q", "-DskipTests", "package"], backend, options.timeout, env)
    checks.append(command_check("RT-BUILD-JAVA", "Spring 构建", "build", result, "Maven package 成功"))
    jars = [path for path in (backend / "target").glob("*.jar") if not path.name.endswith(".original")]
    return checks, jars[0] if result.status == PASS and jars else None


def _playwright_check(url: str, policy: str) -> RuntimeCheck:
    if policy == "off":
        return RuntimeCheck("RT-UI", "浏览器 UI 检查", "ui", NOT_APPLICABLE, observed="--ui off")
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return RuntimeCheck(
            "RT-UI", "浏览器 UI 检查", "ui",
            BLOCKED_ENV if policy == "required" else NOT_APPLICABLE,
            expected="Playwright 可用时页面无脚本错误", observed="Python Playwright 未安装",
        )
    errors: list[str] = []
    started = time.monotonic()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            response = page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            title = page.title()
            browser.close()
        passed = response is not None and response.status < 400 and not errors
        return RuntimeCheck(
            "RT-UI", "浏览器 UI 检查", "ui", PASS if passed else FAIL_PROJECT,
            duration_ms=int((time.monotonic() - started) * 1000),
            expected="页面加载成功且无 console error",
            observed=f"title={title!r}; errors={errors[:3]}",
        )
    except Exception as exc:  # Playwright exposes several runtime exception types.
        return RuntimeCheck(
            "RT-UI", "浏览器 UI 检查", "ui", BLOCKED_ENV,
            duration_ms=int((time.monotonic() - started) * 1000),
            expected="Playwright 浏览器可启动", observed=f"{type(exc).__name__}: {exc}",
        )


def _start_local_service(
    version: VersionAssessment,
    project: Path,
    env: dict[str, str],
    options: RuntimeOptions,
    python: Path | None,
    jar: Path | None,
) -> tuple[ManagedProcess | None, str, str, Callable[[], tuple[ManagedProcess | None, str]] | None]:
    config = _version_config(options, version)
    resource = str(config.get("resource") or version.resource_path or "/api/notes")
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = project / ".grader-artifacts" / "service.log"
    start_parts: list[str] | None = None
    cwd = project
    if isinstance(config.get("start"), list):
        start_parts = [str(value).replace("{port}", str(port)) for value in config["start"]]
        cwd = project / str(config.get("cwd", "."))
    elif "Django" in version.stack and python:
        migrate = run_command([str(python), "manage.py", "migrate", "--noinput"], project, options.timeout, env)
        version.runtime_checks.append(command_check("RT-MIGRATE-PY", "Django 迁移", "build", migrate, "迁移成功"))
        if migrate.status != PASS:
            return None, base_url, resource, None
        start_parts = [str(python), "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"]
    elif "Spring Boot" in version.stack and jar:
        start_parts = [
            "java", "-jar", str(jar), f"--server.port={port}",
            f"--spring.datasource.url=jdbc:h2:file:{(project / 'grader-data' / 'app').as_posix()}",
        ]
        cwd = jar.parent.parent
    elif "Node.js" in version.techs:
        package = project / "package.json"
        data = parse_package(package) if package.exists() else {}
        dependencies = data.get("dependencies") if isinstance(data.get("dependencies"), dict) else {}
        if "mongoose" in dependencies or "mongodb" in dependencies:
            mongo_uri = config.get("mongodb_uri") or options.config.get("mongodb_uri")
            if not mongo_uri:
                return None, base_url, resource, None
            env["MONGODB_URI"] = str(mongo_uri)
        if isinstance((data.get("scripts") or {}).get("start"), str):
            start_parts = ["npm", "start"]
            env["PORT"] = str(port)
    if not start_parts:
        return None, base_url, resource, None

    def launch() -> tuple[ManagedProcess | None, str]:
        managed = start_process(start_parts or [], cwd, env, log_path)
        ready, detail = wait_ready(base_url, resource, managed, min(options.timeout, 45))
        if not ready:
            stop_process(managed)
            return None, detail
        return managed, detail

    managed, detail = launch()
    if managed is None:
        return None, base_url, resource, None
    return managed, base_url, resource, launch


def run_version_runtime(version: VersionAssessment, options: RuntimeOptions, artifact_root: Path) -> None:
    external_url = _matching_url(options, version)
    resource = str(_version_config(options, version).get("resource") or version.resource_path or "/api/notes")
    if external_url:
        checks = read_only_http_checks(external_url, resource)
        if options.allow_data_write and not options.smoke_only:
            checks, _ = full_http_checks(external_url, resource)
        version.runtime_checks.extend(checks)
        version.runtime_checks.append(_playwright_check(external_url, options.ui))
        return
    if version.source.mode != "local":
        version.runtime_checks.append(RuntimeCheck(
            "RT-REMOTE-DISABLED", "远程代码动态执行", "start", NOT_RUN,
            expected="GitHub 自动回退仅静态分析", observed="安全策略禁止执行远程仓库代码",
        ))
        return

    project = artifact_root / version.name
    copy_project(version.path, project)
    env = sanitized_environment(project)
    install_checks: list[RuntimeCheck] = []
    python: Path | None = None
    jar: Path | None = None
    if not options.allow_install:
        version.runtime_checks.append(RuntimeCheck(
            "RT-INSTALL-POLICY", "依赖准备", "install", BLOCKED_ENV,
            expected="传入 --allow-install 后在临时副本安装依赖",
            observed="动态模式未授权安装依赖，未执行提交代码",
        ))
        return

    if "Django" in version.stack or "Python" in version.techs:
        install_checks, python = _prepare_python(project, options, env)
        version.runtime_checks.extend(install_checks)
        if python:
            result = run_command([str(python), "manage.py", "check"], project, options.timeout, env)
            version.runtime_checks.append(command_check("RT-CHECK-PY", "Django system check", "build", result, "manage.py check 通过"))
            result = run_command([str(python), "manage.py", "test"], project, options.timeout, env)
            version.runtime_checks.append(command_check("RT-TEST-PY", "Django 测试", "test", result, "测试通过且包含有效用例"))
    elif "Spring Boot" in version.stack:
        version.runtime_checks, jar = _prepare_spring(project, options, env)
        frontend_dirs = [path.parent for path in project.rglob("package.json") if "frontend" in path.as_posix().lower()]
        if frontend_dirs:
            version.runtime_checks.extend(_install_node(project, options, env))
            version.runtime_checks.extend(_run_node_checks(project, options, env))
    elif "Node.js" in version.techs:
        version.runtime_checks.extend(_install_node(project, options, env))
        version.runtime_checks.extend(_run_node_checks(project, options, env))

    if any(check.status == FAIL_PROJECT and check.category == "install" for check in version.runtime_checks):
        return
    managed, base_url, resource, restart = _start_local_service(version, project, env, options, python, jar)
    if managed is None:
        status = BLOCKED_ENV if (
            ("MongoDB" in version.techs and not (_version_config(options, version).get("mongodb_uri") or options.config.get("mongodb_uri")))
            or any(check.status == BLOCKED_ENV for check in version.runtime_checks)
        ) else FAIL_PROJECT
        version.runtime_checks.append(RuntimeCheck(
            "RT-START", "启动应用", "start", status,
            expected="隔离服务在随机端口就绪",
            observed="未能确定安全启动命令、缺少测试数据库或服务未就绪",
        ))
        return
    version.runtime_checks.append(RuntimeCheck(
        "RT-START", "启动应用", "start", PASS,
        expected="隔离服务在随机端口就绪", observed=base_url,
    ))
    try:
        checks, active = full_http_checks(base_url, resource, restart=restart, current_process=managed)
        managed = active or managed
        version.runtime_checks.extend(checks)
        version.runtime_checks.append(_playwright_check(base_url, options.ui))
    finally:
        if managed and managed.process.poll() is None:
            stop_process(managed)


def _pass_ratio(checks: list[RuntimeCheck], categories: set[str], ids: set[str] | None = None) -> float:
    selected = [
        check for check in checks
        if check.category in categories and (ids is None or check.check_id in ids)
        and check.status not in {NOT_APPLICABLE, NOT_RUN}
    ]
    if not selected:
        return 0.0
    return sum(check.status == PASS for check in selected) / len(selected)


def apply_runtime_scores(versions: list[VersionAssessment], overall_items: list[Any]) -> None:
    verified_versions = 0
    for version in versions:
        checks = version.runtime_checks
        build_start = _pass_ratio(checks, {"build", "start"})
        version.item("source").add_dynamic(build_start)
        version.item("readme").add_dynamic(build_start)
        model_ratio = _pass_ratio(checks, {"persistence"})
        crud_ratio = _pass_ratio(checks, {"crud"})
        validation_ratio = _pass_ratio(checks, {"validation"})
        error_ratio = _pass_ratio(checks, {"errors"})
        frontend_ratio = (_pass_ratio(checks, {"build"}) + _pass_ratio(checks, {"crud"}, {"RT-CRUD-LIST"})) / 2
        for key, ratio in (
            ("data_model", model_ratio), ("crud", crud_ratio), ("validation", validation_ratio),
            ("error_handling", error_ratio), ("frontend_integration", frontend_ratio),
        ):
            version.feature(key).add_dynamic(ratio)
        functionality = version.item("functionality")
        functionality.verified = round(sum(item.verified for item in version.feature_items), 2)
        if crud_ratio == 1 and model_ratio == 1:
            verified_versions += 1
    concept = next(item for item in overall_items if item.key == "concept")
    concept.verified = min(concept.max_score, concept.verified + 2 * verified_versions)


def runtime_environment() -> dict[str, str]:
    return {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "node": shutil.which("node") or "missing",
        "npm": shutil.which("npm") or "missing",
        "java": shutil.which("java") or "missing",
        "git": shutil.which("git") or "missing",
        "playwright": "available" if _playwright_available() else "missing",
    }


def runtime_findings(version: VersionAssessment) -> list[Finding]:
    findings: list[Finding] = []
    grouped: dict[tuple[str, str], list[RuntimeCheck]] = {}
    for check in version.runtime_checks:
        if check.status not in {FAIL_PROJECT, BLOCKED_ENV}:
            continue
        grouped.setdefault((check.status, check.category), []).append(check)
    for (status, category), checks in grouped.items():
        severity = "Medium"
        if status == FAIL_PROJECT and category in {"install", "build", "start", "crud", "validation", "errors", "persistence"}:
            severity = "High"
        title = (
            f"动态 {category} 验证失败" if status == FAIL_PROJECT
            else f"动态 {category} 验证受环境阻塞"
        )
        observed = "；".join(f"{check.check_id}: {check.observed}" for check in checks[:4])
        commands = [check.command for check in checks if check.command]
        findings.append(Finding(
            rule_id=f"RUNTIME-{category.upper()}-{status}",
            severity=severity,
            title=title,
            scope=version.name,
            status=status,
            expected=f"{category} 阶段的必需检查通过",
            observed=observed,
            impact=(
                "对应课程行为无法获得证据确认分，且工程就绪度被阻断。"
                if status == FAIL_PROJECT
                else "当前评测机无法完成该阶段，相关分数保持未确认，但不直接归责项目。"
            ),
            recommendation=(
                "根据动态矩阵修复首个失败检查并重新运行隔离动态评分。"
                if status == FAIL_PROJECT
                else "提供所需运行时、网络或专用测试依赖后重新验证。"
            ),
            reproduction=commands[0] if commands else "参见动态测试矩阵",
        ))
    return findings


def _playwright_available() -> bool:
    try:
        import playwright.sync_api  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


def runtime_artifact_directory(base: Path, keep: bool) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if keep:
        path = base / ".grader-artifacts" / time.strftime("%Y%m%d-%H%M%S")
        path.mkdir(parents=True, exist_ok=True)
        return path, None
    temporary = tempfile.TemporaryDirectory(prefix="day5-grader-runtime-")
    return Path(temporary.name), temporary

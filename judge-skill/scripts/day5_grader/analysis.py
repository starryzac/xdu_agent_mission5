from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .discovery import (
    detect_techs,
    manifest_is_valid,
    parse_package,
    role_files,
    version_document_section,
)
from .models import (
    FAIL_PROJECT,
    NOT_RUN,
    Evidence,
    Finding,
    ProjectCandidate,
    ScoreItem,
    SourceInfo,
    VersionAssessment,
)
from .utils import MANIFEST_NAMES, find_evidence, first_match, make_evidence, project_files, read_text


def _ratio_score(
    key: str,
    name: str,
    max_score: float,
    static_cap: float,
    dynamic_cap: float,
    hits: int,
    total: int,
    evidence: list[Evidence],
    missing: list[str],
    recommendation: str,
) -> ScoreItem:
    ratio = hits / total if total else 0.0
    provisional = max_score * ratio
    verified = static_cap * ratio
    return ScoreItem(
        key=key,
        name=name,
        max_score=max_score,
        provisional=round(provisional, 2),
        verified=round(verified, 2),
        static_cap=static_cap,
        dynamic_cap=dynamic_cap,
        status="PASS" if ratio == 1 else FAIL_PROJECT,
        evidence=evidence[:6],
        missing=missing,
        recommendation=recommendation,
        confidence="high" if ratio == 1 else "medium" if ratio >= 0.5 else "low",
    )


def _evidence_for_pattern(
    paths: list[Path],
    pattern: str,
    rule_id: str,
    source: SourceInfo,
    expected: str,
) -> tuple[bool, list[Evidence]]:
    items = find_evidence(paths, pattern, rule_id, source, expected, limit=2)
    return bool(items), items


def _python_model_summary(path: Path) -> dict[str, bool]:
    text = read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"model": False, "required": False, "timestamp": False, "id": False}
    model = False
    required = False
    timestamp = False
    explicit_id = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Attribute):
                    bases.append(base.attr)
                elif isinstance(base, ast.Name):
                    bases.append(base.id)
            if "Model" in bases:
                model = True
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if "id" in targets:
                explicit_id = True
            if any(name in {"created_at", "updated_at", "createdAt", "updatedAt"} for name in targets):
                timestamp = True
            call = node.value if isinstance(node.value, ast.Call) else None
            if call:
                for keyword in call.keywords:
                    if keyword.arg in {"null", "blank"} and isinstance(keyword.value, ast.Constant) and keyword.value.value is False:
                        required = True
                    if keyword.arg in {"auto_now", "auto_now_add"}:
                        timestamp = True
                    if keyword.arg == "validators" and not (isinstance(keyword.value, (ast.List, ast.Tuple)) and not keyword.value.elts):
                        required = True
    return {"model": model, "required": required, "timestamp": timestamp, "id": explicit_id or model}


def _model_checks(candidate: ProjectCandidate, roles: dict[str, list[Path]]) -> tuple[ScoreItem, list[Finding]]:
    patterns = {
        "model": r"mongoose\.Schema|new\s+Schema|@Entity\b|SQLAlchemy|sequelize\.define|Prisma|ActiveRecord::Base|class\s+\w+\s*\([^)]*Model[^)]*\)",
        "id": r"\b_id\b|\bid\b|@Id\b|primary_key|AutoField|UUID|ObjectId",
        "required": r"required\s*:|@NotBlank|@NotNull|max_length|validators|nullable\s*=\s*False|blank\s*=\s*False|NOT NULL",
        "timestamp": r"createdAt|updatedAt|created_at|updated_at|auto_now|CreationTimestamp|UpdateTimestamp|timestamps\s*:",
    }
    hits = {key: False for key in patterns}
    evidence: list[Evidence] = []
    model_files = roles["model"]
    for path in model_files:
        if path.suffix == ".py":
            summary = _python_model_summary(path)
            for key, ok in summary.items():
                if ok and not hits[key]:
                    hits[key] = True
                    evidence.append(
                        make_evidence(
                            f"FUNC-MODEL-{key.upper()}", path, candidate.source,
                            f"模型包含 {key} 证据", f"Python AST 确认 {key}", 1,
                        )
                    )
        for key, pattern in patterns.items():
            if hits[key]:
                continue
            line, observed = first_match(path, pattern)
            if line is not None:
                hits[key] = True
                evidence.append(
                    make_evidence(
                        f"FUNC-MODEL-{key.upper()}", path, candidate.source,
                        f"模型包含 {key} 证据", observed, line,
                    )
                )
    missing_labels = {
        "model": "未在 model/schema/entity 文件中确认模型定义",
        "id": "未确认自动或显式主键",
        "required": "未确认必填字段或长度约束",
        "timestamp": "未确认创建或更新时间戳",
    }
    item = _ratio_score(
        "data_model", "数据模型", 1.0, 0.6, 0.4,
        sum(hits.values()), 4, evidence,
        [label for key, label in missing_labels.items() if not hits[key]],
        "在同一模型层定义主键、必填字段、长度约束和时间戳，并用持久化测试验证。",
    )
    return item, []


CRUD_PATTERNS = {
    "list": r"router\.get\s*\(\s*['\"]/?['\"]|@GetMapping\s*(?:\(\s*\)|$)|request\.method\s*==\s*['\"]GET|def\s+\w*(?:list|index)|ListView",
    "detail": r":id|/\{id\}|<int:(?:pk|id)>|findById|get_object_or_404|repo\.findById|DetailView",
    "create": r"router\.post|app\.post|@PostMapping|request\.method\s*==\s*['\"]POST|def\s+\w*create|CreateView",
    "update": r"router\.(?:put|patch)|app\.(?:put|patch)|@PutMapping|@PatchMapping|request\.method\s*==\s*['\"]PUT|findByIdAndUpdate|UpdateView|def\s+\w*(?:update|edit)",
    "delete": r"router\.delete|app\.delete|@DeleteMapping|request\.method\s*==\s*['\"]DELETE|deleteById|DeleteView|def\s+\w*delete",
}


def _best_crud_file(candidate: ProjectCandidate, backend_files: list[Path]) -> tuple[dict[str, bool], list[Evidence]]:
    best_hits = {key: False for key in CRUD_PATTERNS}
    best_evidence: list[Evidence] = []
    for path in backend_files:
        local_hits: dict[str, bool] = {}
        local_evidence: list[Evidence] = []
        for key, pattern in CRUD_PATTERNS.items():
            line, observed = first_match(path, pattern)
            local_hits[key] = line is not None
            if line is not None:
                local_evidence.append(
                    make_evidence(
                        f"FUNC-CRUD-{key.upper()}", path, candidate.source,
                        f"同一资源实现 {key}", observed, line,
                    )
                )
        if sum(local_hits.values()) > sum(best_hits.values()):
            best_hits = local_hits
            best_evidence = local_evidence
    if sum(best_hits.values()) < 5:
        combined = "\n".join(read_text(path, 350_000) for path in backend_files)
        combined_hits = {key: bool(re.search(pattern, combined, re.I | re.M)) for key, pattern in CRUD_PATTERNS.items()}
        if sum(combined_hits.values()) > sum(best_hits.values()):
            best_hits = combined_hits
            best_evidence = []
            for key, ok in combined_hits.items():
                if not ok:
                    continue
                for path in backend_files:
                    line, observed = first_match(path, CRUD_PATTERNS[key])
                    if line is not None:
                        best_evidence.append(
                            make_evidence(
                                f"FUNC-CRUD-{key.upper()}", path, candidate.source,
                                f"同一后端资源实现 {key}", observed, line,
                            )
                        )
                        break
    return best_hits, best_evidence


def _crud_check(candidate: ProjectCandidate, roles: dict[str, list[Path]]) -> ScoreItem:
    hits, evidence = _best_crud_file(candidate, roles["backend"])
    labels = {
        "list": "缺少列表读取",
        "detail": "缺少详情读取",
        "create": "缺少创建",
        "update": "缺少更新",
        "delete": "缺少删除",
    }
    return _ratio_score(
        "crud", "CRUD 完整性", 1.5, 0.5, 1.0,
        sum(hits.values()), 5, evidence,
        [label for key, label in labels.items() if not hits[key]],
        "让同一核心资源形成列表、详情、创建、更新、删除闭环，并以 API 行为测试证明。",
    )


def _validation_check(
    candidate: ProjectCandidate, roles: dict[str, list[Path]]
) -> tuple[ScoreItem, list[Finding]]:
    server_files = roles["model"] + roles["backend"]
    constraint_ok, constraint_ev = _evidence_for_pattern(
        roles["model"],
        r"required\s*:|@NotBlank|@Size|validators|max_length|nullable\s*=\s*False|blank\s*=\s*False|trim\(\)",
        "FUNC-VALID-CONSTRAINT", candidate.source, "模型层包含必填、空白或长度约束",
    )
    flow_ok, flow_ev = _evidence_for_pattern(
        server_files,
        r"runValidators\s*:\s*true|\.is_valid\(\)|\.full_clean\(\)|Joi\.|zod\.|@Valid\s+@RequestBody\s+(?!Map\b)|BindingResult|ValidationError",
        "FUNC-VALID-FLOW", candidate.source, "服务端创建和更新路径实际触发验证",
    )
    findings: list[Finding] = []
    invalid_map_ev = find_evidence(
        roles["backend"], r"@Valid\s+@RequestBody\s+Map\b", "FUNC-VALID-MAP", candidate.source,
        "@Valid 应作用于带约束的 DTO/Entity，而不是 Map", limit=2,
    )
    if invalid_map_ev:
        flow_ok = False
        flow_ev = []
        findings.append(Finding(
            rule_id="FUNC-VALID-MAP",
            severity="High",
            title="Spring 验证注解未绑定到可验证对象",
            scope=candidate.name,
            status=FAIL_PROJECT,
            expected="@Valid 校验带 @NotBlank/@Size 的 DTO 或实体",
            observed="控制器对 Map 使用 @Valid，实体字段约束不会自动执行",
            impact="空值、超长值或类型错误可能进入持久化层并产生 500。",
            recommendation="引入请求 DTO，或在 applyFields 后显式调用 Validator，并统一返回 400。",
            evidence=invalid_map_ev,
        ))
    evidence = constraint_ev + flow_ev
    item = _ratio_score(
        "validation", "输入验证", 0.8, 0.3, 0.5,
        int(constraint_ok) + int(flow_ok), 2, evidence,
        (["缺少模型约束"] if not constraint_ok else []) + (["未证明服务端路径会触发验证"] if not flow_ok else []),
        "同时实现声明式约束和服务端验证调用，并动态拒绝空白、超长及错误类型。",
    )
    return item, findings


def _error_check(
    candidate: ProjectCandidate, roles: dict[str, list[Path]]
) -> tuple[ScoreItem, list[Finding]]:
    backend = roles["backend"]
    exception_ok, exception_ev = _evidence_for_pattern(
        backend,
        r"try\s*:|except\s+|try\s*\{|catch\s*\(|errorHandler|@ExceptionHandler|ControllerAdvice",
        "FUNC-ERROR-EXCEPTION", candidate.source, "存在异常捕获或统一异常处理",
    )
    notfound_ok, notfound_ev = _evidence_for_pattern(
        backend,
        r"status\s*\(\s*404\s*\)|HttpStatus\.NOT_FOUND|ResponseEntity\.notFound|_json_error\([^\n]+status\s*=\s*404|不存在|not found",
        "FUNC-ERROR-404", candidate.source, "不存在资源返回明确错误和适当状态码",
    )
    unified_ok, unified_ev = _evidence_for_pattern(
        backend,
        r"success\s*[:=]\s*(?:true|false)|ApiResponse|JsonResponse\s*\(\s*\{\s*['\"]success|_json_(?:success|error)",
        "FUNC-ERROR-CONTRACT", candidate.source, "API 使用统一 success/data/error 契约",
    )
    findings: list[Finding] = []
    combined = "\n".join(read_text(path, 400_000) for path in backend)
    if "get_object_or_404" in combined and re.search(r"def\s+api_", combined):
        ev = find_evidence(
            backend, r"def\s+api_[\s\S]{0,600}?get_object_or_404",
            "FUNC-ERROR-DJANGO-HTML404", candidate.source,
            "JSON API 的不存在资源响应仍应遵循统一 JSON 契约", limit=2,
        )
        if ev:
            notfound_ok = False
            notfound_ev = []
            findings.append(Finding(
                rule_id="FUNC-ERROR-DJANGO-HTML404", severity="High",
                title="Django JSON API 可能返回 HTML 404",
                scope=candidate.name, status=FAIL_PROJECT,
                expected="GET/PUT/DELETE 不存在 ID 返回 {success:false,error} JSON",
                observed="API 处理函数直接调用 get_object_or_404，未转换 Http404",
                impact="客户端收到 HTML 响应，统一 API 契约被破坏。",
                recommendation="在 API 层捕获 Http404 或显式查询并调用 _json_error(..., 404)。",
                evidence=ev,
            ))
    spring_error = find_evidence(
        backend, r"orElseGet\(\(\)\s*->\s*ApiResponse\.error|return\s+ApiResponse\.error",
        "FUNC-ERROR-SPRING-STATUS", candidate.source,
        "业务错误同时设置 4xx HTTP 状态", limit=2,
    )
    if spring_error and not re.search(r"ResponseEntity|ControllerAdvice|@ExceptionHandler|HttpStatus\.NOT_FOUND", combined):
        notfound_ok = False
        notfound_ev = []
        findings.append(Finding(
            rule_id="FUNC-ERROR-SPRING-STATUS", severity="High",
            title="Spring 业务错误仍可能返回 HTTP 200",
            scope=candidate.name, status=FAIL_PROJECT,
            expected="不存在资源返回 404，验证失败返回 400",
            observed="控制器只返回 ApiResponse.error，未设置 ResponseEntity 或异常映射",
            impact="监控、客户端和代理无法从 HTTP 状态识别失败。",
            recommendation="使用 ResponseEntity 或 @RestControllerAdvice 映射 400/404。",
            evidence=spring_error,
        ))
    evidence = exception_ev + notfound_ev + unified_ev
    item = _ratio_score(
        "error_handling", "错误处理与统一响应", 0.8, 0.3, 0.5,
        int(exception_ok) + int(notfound_ok) + int(unified_ok), 3, evidence,
        (["缺少异常处理"] if not exception_ok else [])
        + (["未确认统一 JSON 404 和正确状态码"] if not notfound_ok else [])
        + (["缺少 success/data/error 契约"] if not unified_ok else []),
        "统一异常映射、HTTP 状态和 JSON 契约，并动态验证 404 与非法 JSON。",
    )
    return item, findings


def _frontend_check(candidate: ProjectCandidate, roles: dict[str, list[Path]]) -> ScoreItem:
    frontend = roles["frontend"]
    api_ok, api_ev = _evidence_for_pattern(
        frontend,
        r"\bfetch\s*\(|axios|api\.(?:get|post|put|patch|delete)|<form|method\s*=\s*['\"]post",
        "FUNC-FE-API", candidate.source, "前端或模板提交到后端",
    )
    views_ok, views_ev = _evidence_for_pattern(
        frontend,
        r"onSubmit|@submit|<form|<input|v-model|useState|router-link|Link\s+to=|confirm_delete|detail|edit",
        "FUNC-FE-VIEWS", candidate.source, "存在可交互列表、表单或详情视图",
    )
    backend_paths = set(re.findall(r"/api/[A-Za-z0-9_{}:/.-]+", "\n".join(read_text(path) for path in roles["backend"])))
    frontend_paths = set(re.findall(r"/api/[A-Za-z0-9_{}:/.-]+", "\n".join(read_text(path) for path in frontend)))
    template_integrated = any("templates" in path.as_posix().lower() for path in frontend)
    contract_ok = template_integrated or bool(backend_paths & frontend_paths) or (
        bool(backend_paths) and api_ok and any(path.name.lower() in {"api.js", "api.ts"} for path in frontend)
    )
    contract_ev: list[Evidence] = []
    if contract_ok and frontend:
        contract_ev.append(make_evidence(
            "FUNC-FE-CONTRACT", frontend[0], candidate.source,
            "前端调用与后端路由可对应",
            "模板与同一后端集成" if template_integrated else f"匹配 API 路径: {sorted(backend_paths & frontend_paths)[:3]}",
            1,
        ))
    return _ratio_score(
        "frontend_integration", "前后端对接", 0.9, 0.3, 0.6,
        int(api_ok) + int(views_ok) + int(contract_ok), 3,
        api_ev + views_ev + contract_ev,
        (["未发现前端 API 调用或模板表单"] if not api_ok else [])
        + (["未确认可交互视图"] if not views_ok else [])
        + (["前端路径与后端路由未形成可证明契约"] if not contract_ok else []),
        "保持前后端路由契约一致，并通过构建和浏览器核心流程验证。",
    )


def _resource_path(roles: dict[str, list[Path]]) -> str | None:
    paths: list[str] = []
    for path in roles["backend"] + roles["frontend"]:
        paths.extend(
            "/" + value.lstrip("/")
            for value in re.findall(r"(?<![A-Za-z0-9_-])/?api/[A-Za-z0-9_-]+", read_text(path, 300_000))
        )
    if not paths:
        return None
    priority = [value for value in paths if re.search(r"/(?:notes|prompts|tasks|items|posts)$", value, re.I)]
    values = priority or [value for value in paths if not value.endswith("/health")] or paths
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts, key=lambda item: (counts[item], item))


def _source_item(
    candidate: ProjectCandidate, roles: dict[str, list[Path]], stack: str
) -> tuple[ScoreItem, list[Finding]]:
    files = project_files(candidate.path)
    code_files = [path for path in files if path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".vue", ".py", ".java", ".go", ".rb", ".php", ".html"}]
    manifests = [path for path in files if path.name in MANIFEST_NAMES]
    valid_manifests = [path for path in manifests if manifest_is_valid(path)]
    dependency_manifests = valid_manifests
    if "Django" in stack or stack in {"Flask", "FastAPI"}:
        dependency_manifests = [path for path in valid_manifests if path.name in {"requirements.txt", "pyproject.toml", "Pipfile"}]
    elif "Spring" in stack or "Java" in stack:
        dependency_manifests = [path for path in valid_manifests if path.name in {"pom.xml", "build.gradle", "build.gradle.kts"}]
    elif "Node.js" in stack or stack in {"MERN", "Next.js"}:
        dependency_manifests = [path for path in valid_manifests if path.name == "package.json"]
    checks = {
        "source": len(code_files) >= 5,
        "manifest": bool(dependency_manifests),
        "entry": any(path.name in {"server.js", "manage.py", "pom.xml", "app.py", "main.go", "package.json"} for path in files),
        "structure": bool(roles["model"] and (roles["backend"] or roles["frontend"])),
    }
    evidence: list[Evidence] = []
    if code_files:
        evidence.append(make_evidence("SRC-CODE", code_files[0], candidate.source, "提交完整源码", f"发现 {len(code_files)} 个代码文件", 1))
    if dependency_manifests:
        evidence.append(make_evidence("SRC-MANIFEST", dependency_manifests[0], candidate.source, "依赖清单可解析", dependency_manifests[0].name, 1))
    entry = next((path for path in files if path.name in {"server.js", "manage.py", "pom.xml", "app.py", "main.go", "package.json"}), None)
    if entry:
        evidence.append(make_evidence("SRC-ENTRY", entry, candidate.source, "存在启动或构建入口", entry.name, 1))
    if roles["model"]:
        evidence.append(make_evidence("SRC-STRUCTURE", roles["model"][0], candidate.source, "源码结构包含模型和应用层", "发现模型与应用目录", 1))
    static_points = sum(1 for value in checks.values() if value)
    readme = candidate.path / "README.md"
    run_potential = bool(re.search(r"npm\s+(?:run\s+)?(?:start|dev)|python\s+manage\.py\s+runserver|mvnw.*spring-boot:run|java\s+-jar", read_text(readme), re.I))
    item = ScoreItem(
        key="source", name="源代码完整性", max_score=5,
        provisional=round(static_points + (1 if run_potential else 0), 2),
        verified=float(static_points), static_cap=4, dynamic_cap=1,
        status="PASS" if static_points == 4 else FAIL_PROJECT,
        evidence=evidence,
        missing=[label for key, label in {
            "source": "源码文件不足", "manifest": "缺少可复现依赖清单",
            "entry": "缺少启动或构建入口", "structure": "缺少模型与应用层结构",
        }.items() if not checks[key]] + ([] if run_potential else ["未识别可执行启动命令"]),
        recommendation="提交可解析依赖清单、明确入口和完整源码结构，并确保构建/启动可复现。",
        confidence="high" if static_points == 4 else "medium",
    )
    findings: list[Finding] = []
    if not checks["manifest"]:
        findings.append(Finding(
            rule_id="SRC-MANIFEST", severity="High", title="缺少可复现依赖清单",
            scope=candidate.name, status=FAIL_PROJECT,
            expected="技术栈提供 package.json、requirements.txt、pyproject.toml、pom.xml 等依赖清单",
            observed=f"识别为 {stack}，但未找到对应的有效依赖清单",
            impact="评测机和其他开发者无法确定性安装依赖或复现运行环境。",
            recommendation="补充技术栈标准依赖文件并锁定版本。",
            evidence=[item for item in evidence if item.rule_id == "SRC-MANIFEST"],
        ))
    return item, findings


def _readme_item(candidate: ProjectCandidate) -> ScoreItem:
    path = candidate.path / "README.md"
    text = read_text(path)
    checks = {
        "prerequisite": bool(re.search(r"前置|prereq|requirement|Node\.js|Python|Java|Go|Ruby|PHP", text, re.I)),
        "install": bool(re.search(r"安装|install|npm\s+(?:ci|install)|pip\s+install|mvnw|gradle|bundle", text, re.I)),
        "config": bool(re.search(r"配置|\.env|environment|PORT|DATABASE|数据库|application\.properties", text, re.I)),
        "run": bool(re.search(r"运行|启动|npm\s+(?:run\s+)?(?:start|dev)|runserver|spring-boot:run|localhost", text, re.I)),
    }
    evidence: list[Evidence] = []
    for key, pattern in {
        "prerequisite": r"前置|prereq|requirement|Node\.js|Python|Java",
        "install": r"安装|install|npm\s+(?:ci|install)|pip\s+install|mvnw",
        "config": r"配置|\.env|PORT|DATABASE|数据库",
        "run": r"运行|启动|npm\s+(?:run\s+)?(?:start|dev)|runserver|spring-boot:run|localhost",
    }.items():
        line, observed = first_match(path, pattern)
        if line is not None:
            evidence.append(make_evidence(f"README-{key.upper()}", path, candidate.source, f"README 包含 {key}", observed, line, tier="document"))
    static_points = sum(checks.values())
    command_potential = bool(re.search(r"```(?:bash|sh|powershell|cmd)?[\s\S]*?(?:npm|python|mvnw|gradle|go\s+run)", text, re.I))
    return ScoreItem(
        key="readme", name="README 文档", max_score=5,
        provisional=float(static_points + (1 if command_potential else 0)),
        verified=float(static_points), static_cap=4, dynamic_cap=1,
        status="PASS" if static_points == 4 else FAIL_PROJECT,
        evidence=evidence,
        missing=[label for key, label in {
            "prerequisite": "缺少前置条件", "install": "缺少安装说明",
            "config": "缺少环境或数据库配置", "run": "缺少运行和访问说明",
        }.items() if not checks[key]] + ([] if command_potential else ["缺少可复制执行的命令块"]),
        recommendation="按前置条件、安装、配置、运行、已知问题组织 README，并用动态模式验证命令。",
        confidence="high" if static_points == 4 else "medium",
    )


def _writeup_item(
    candidate: ProjectCandidate, stack: str, document_text: str, documents: list[Path], document_source: SourceInfo
) -> ScoreItem:
    section = version_document_section(document_text, candidate.name, stack)
    checks = {
        "section": bool(section),
        "stack": bool(re.search(r"技术栈|stack|框架|MERN|Django|Spring|React|Vue|Python|Java", section, re.I)),
        "ai": bool(re.search(r"AI|Claude|Codex|Trae|Copilot|Cursor|提示词|prompt", section, re.I)),
        "storage": bool(re.search(r"数据库|SQLite|MongoDB|PostgreSQL|H2|MySQL|持久化|storage", section, re.I)),
        "problems": bool(re.search(r"问题|难点|修复|反思|心得|debug|bug|遇到|已知", section, re.I)),
    }
    evidence: list[Evidence] = []
    if section and documents:
        marker = next((value for value in (candidate.name, stack, "版本") if re.search(re.escape(value), section, re.I)), stack)
        for document in documents:
            line, observed = first_match(document, re.escape(marker))
            if line is not None:
                evidence.append(make_evidence("WRITEUP-SECTION", document, document_source, "每版拥有独立 writeup 章节", observed, line, tier="document"))
                break
    return _ratio_score(
        "writeup", "writeup 描述", 5, 5, 0,
        sum(checks.values()), 5, evidence,
        [label for key, label in {
            "section": "未定位该版本的独立章节", "stack": "缺少技术栈说明",
            "ai": "缺少该版本 AI 工具说明", "storage": "缺少存储方案",
            "problems": "缺少问题、偏差或人工修复记录",
        }.items() if not checks[key]],
        "按版本分别记录技术栈、AI 工具、存储、问题和人工修复，避免全局描述串证。",
    )


def _engineering_findings(candidate: ProjectCandidate, roles: dict[str, list[Path]], stack: str) -> list[Finding]:
    findings: list[Finding] = []
    test_files = roles["tests"]
    test_text = "\n".join(read_text(path, 250_000) for path in test_files)
    package_test_text = ""
    for package in [path for path in roles["manifest"] if path.name == "package.json"]:
        scripts = parse_package(package).get("scripts") or {}
        if isinstance(scripts, dict):
            package_test_text += "\n" + str(scripts.get("test", ""))
    placeholder = re.search(
        r"no test specified|Create your tests here|pass\s*(?:#.*)?$|TODO.*test",
        test_text + package_test_text,
        re.I | re.M,
    )
    meaningful = bool(test_files) and not placeholder and bool(re.search(r"assert|expect\s*\(|TestCase|@Test|def\s+test_", test_text, re.I))
    if not meaningful:
        ev: list[Evidence] = []
        if test_files:
            line, observed = first_match(test_files[0], r"no test specified|Create your tests here|pass|TODO|TestCase")
            ev.append(make_evidence(
                "OPS-TESTS", test_files[0], candidate.source,
                "存在能验证行为的自动化测试", observed or "测试文件无有效断言", line or 1,
                status=FAIL_PROJECT,
            ))
        elif package_test_text.strip():
            package = next(path for path in roles["manifest"] if path.name == "package.json")
            line, observed = first_match(package, r'"test"\s*:\s*"[^"]+"')
            ev.append(make_evidence(
                "OPS-TESTS", package, candidate.source,
                "默认测试命令执行有效断言", observed or package_test_text.strip(), line or 1,
                status=FAIL_PROJECT,
            ))
        findings.append(Finding(
            rule_id="OPS-TESTS", severity="Medium", title="自动化测试缺失或为占位实现",
            scope=candidate.name, status=FAIL_PROJECT,
            expected="至少包含核心模型、API 或页面行为测试",
            observed="未发现有效断言，或测试命令明确为占位失败",
            impact="功能回归只能依赖人工检查，工程就绪度下降。",
            recommendation="补充最小单元测试和 CRUD 集成测试，并让默认测试命令可通过。",
            evidence=ev,
        ))
    if candidate.source.commit is None or (candidate.source.history_depth is not None and candidate.source.history_depth < 2):
        findings.append(Finding(
            rule_id="OPS-GIT-HISTORY", severity="Medium", title="Git 交付历史不足",
            scope=candidate.name, status=FAIL_PROJECT,
            expected="提交物保留可核验的 Git commit 历史",
            observed="未识别仓库 commit，或可见历史少于 2 条",
            impact="无法核验迭代过程和交付边界。",
            recommendation="在提交仓库保留有意义的增量 commit。",
        ))
    if "MERN" in stack:
        packages = [path for path in roles["manifest"] if path.name == "package.json"]
        dependency_version = ""
        for path in packages:
            data = parse_package(path)
            dependency_version = str((data.get("dependencies") or {}).get("react-router-dom", dependency_version))
        readme = read_text(candidate.path / "README.md")
        if dependency_version and dependency_version.lstrip("^~").startswith("7") and re.search(r"react-router-dom\s+v6", readme, re.I):
            ev = find_evidence([candidate.path / "README.md"], r"react-router-dom\s+v6", "DOC-VERSION-MISMATCH", candidate.source, "README 与依赖主版本一致")
            findings.append(Finding(
                rule_id="DOC-VERSION-MISMATCH", severity="Low", title="README 技术版本与依赖不一致",
                scope=candidate.name, status=FAIL_PROJECT,
                expected=f"README 描述 react-router-dom {dependency_version}",
                observed="README 声称使用 v6",
                impact="运行说明可能误导复现者和维护者。",
                recommendation="从 package.json 生成或同步技术版本说明。",
                evidence=ev,
            ))
    return findings


def assess_version(
    candidate: ProjectCandidate,
    document_text: str,
    documents: list[Path],
    document_source: SourceInfo,
) -> VersionAssessment:
    techs, stack, non_js = detect_techs(candidate)
    roles = role_files(candidate)
    source_item, source_findings = _source_item(candidate, roles, stack)
    readme_item = _readme_item(candidate)
    model_item, model_findings = _model_checks(candidate, roles)
    crud_item = _crud_check(candidate, roles)
    validation_item, validation_findings = _validation_check(candidate, roles)
    error_item, error_findings = _error_check(candidate, roles)
    frontend_item = _frontend_check(candidate, roles)
    feature_items = [model_item, crud_item, validation_item, error_item, frontend_item]
    feature = ScoreItem(
        key="functionality", name="应用功能", max_score=5,
        provisional=round(sum(item.provisional for item in feature_items), 2),
        verified=round(sum(item.verified for item in feature_items), 2),
        static_cap=2, dynamic_cap=3,
        status="PASS" if all(item.status == "PASS" for item in feature_items) else FAIL_PROJECT,
        evidence=[ev for item in feature_items for ev in item.evidence][:8],
        missing=[miss for item in feature_items for miss in item.missing],
        recommendation="完成同一资源的模型、CRUD、验证、错误契约和可操作 UI 闭环。",
        confidence="high" if all(item.status == "PASS" for item in feature_items) else "medium",
    )
    writeup = _writeup_item(candidate, stack, document_text, documents, document_source)
    findings = (
        source_findings + model_findings + validation_findings + error_findings
        + _engineering_findings(candidate, roles, stack)
    )
    return VersionAssessment(
        name=candidate.name,
        path=candidate.path,
        source=candidate.source,
        stack=stack,
        techs=techs,
        non_js=non_js,
        resource_path=_resource_path(roles),
        score_items=[source_item, readme_item, feature, writeup],
        feature_items=feature_items,
        findings=findings,
    )


def _document_evidence(
    documents: list[Path], source: SourceInfo, pattern: str, rule_id: str, expected: str
) -> list[Evidence]:
    return find_evidence(documents, pattern, rule_id, source, expected, limit=3)


def assess_overall(
    versions: list[VersionAssessment], document_text: str, documents: list[Path], document_source: SourceInfo
) -> list[ScoreItem]:
    concept_ev = _document_evidence(
        documents, document_source, r"应用概念|核心功能|MVP|最低功能|数据模型",
        "OVERALL-CONCEPT-DOC", "writeup 描述应用概念和最低功能范围",
    )
    concept_doc_ratio = min(1.0, len(document_text) / 800) if concept_ev else 0.0
    feature_ratio = sum(v.item("functionality").provisional / 5 for v in versions) / 3
    concept = ScoreItem(
        key="concept", name="应用概念与最低功能范围", max_score=10,
        provisional=round(4 * concept_doc_ratio + 6 * min(1.0, feature_ratio), 2),
        verified=round(4 * concept_doc_ratio, 2), static_cap=4, dynamic_cap=6,
        status="PASS" if concept_doc_ratio == 1 and len(versions) == 3 and feature_ratio >= 0.99 else FAIL_PROJECT,
        evidence=concept_ev,
        missing=[] if concept_ev else ["未确认应用概念和最低范围"],
        recommendation="在文档中定义 MVP，并用三版运行态 CRUD 与持久化测试证明。",
        confidence="high" if concept_ev else "low",
    )
    signatures = {
        "+".join(sorted(tech for tech in version.techs if tech not in {"Node.js", "Vite", "TypeScript"}))
        for version in versions
    }
    diversity_ratio = min(1.0, min(len(versions), len(signatures)) / 3)
    diversity = ScoreItem(
        key="diversity", name="三个不同技术栈", max_score=10,
        provisional=round(10 * diversity_ratio, 2), verified=round(10 * diversity_ratio, 2),
        static_cap=10, status="PASS" if diversity_ratio == 1 else FAIL_PROJECT,
        evidence=[Evidence(
            rule_id="OVERALL-STACKS", path=version.name, line=None,
            expected="三个可区分技术栈", observed=version.stack,
            tier="static", confidence="high",
        ) for version in versions],
        missing=[] if diversity_ratio == 1 else ["少于三个可区分的技术栈"],
        recommendation="提交三个独立版本并用依赖清单证明后端或全栈技术差异。",
        confidence="high",
    )
    ai_checks = {
        "tool": r"Claude|Codex|Trae|Copilot|Cursor|Windsurf",
        "prompt": r"提示词|prompt|上下文|迭代",
        "failure": r"AI.*(?:问题|错误|失误)|生成.*(?:问题|错误)|幻觉|过时",
        "manual": r"人工|手动|修复|调试|debug",
        "comparison": r"对比|比较|效率|反思|心得|经验",
    }
    ai_evidence: list[Evidence] = []
    ai_hits = 0
    for key, pattern in ai_checks.items():
        ev = _document_evidence(documents, document_source, pattern, f"OVERALL-AI-{key.upper()}", f"AI 心得包含 {key}")
        if ev:
            ai_hits += 1
            ai_evidence.extend(ev[:1])
    ai = _ratio_score(
        "ai_reflection", "AI 编码工具心得", 10, 10, 0,
        ai_hits, len(ai_checks), ai_evidence,
        [f"AI 心得缺少 {key}" for key, pattern in ai_checks.items() if not re.search(pattern, document_text, re.I)],
        "记录工具、提示策略、AI 失误、人工修复和技术栈对比，避免只写工具名称。",
    )
    non_js_versions = [version for version in versions if version.non_js]
    non_js = ScoreItem(
        key="non_js", name="至少一个非 JS 版本", max_score=10,
        provisional=10 if non_js_versions else 0, verified=10 if non_js_versions else 0,
        static_cap=10, status="PASS" if non_js_versions else FAIL_PROJECT,
        evidence=[Evidence(
            rule_id="OVERALL-NONJS", path=version.name, line=None,
            expected="至少一个非 JS 后端", observed=version.stack,
            tier="static", confidence="high",
        ) for version in non_js_versions],
        missing=[] if non_js_versions else ["未发现 Python/Ruby/Go/Java/PHP/C# 后端"],
        recommendation="至少提交一个真正的非 JS 后端版本。",
        confidence="high",
    )
    return [concept, diversity, ai, non_js]


def assign_finding_ids(findings: list[Finding]) -> None:
    severity_rank = {"Blocker": 0, "High": 1, "Medium": 2, "Low": 3}
    findings.sort(key=lambda item: (severity_rank.get(item.severity, 9), item.scope.lower(), item.rule_id))
    for index, finding in enumerate(findings, start=1):
        finding.finding_id = f"D5-{index:03d}"


def determine_readiness(mode: str, versions: list[VersionAssessment], findings: list[Finding]) -> str:
    if mode != "dynamic":
        return "NOT_VERIFIED"
    core_checks = [check for version in versions for check in version.runtime_checks if check.category in {"build", "start", "crud", "validation", "errors", "persistence"}]
    if not core_checks or any(check.status == NOT_RUN for check in core_checks):
        return "NOT_VERIFIED"
    if any(check.status == FAIL_PROJECT for check in core_checks):
        return "NOT_READY"
    if any(finding.severity in {"Blocker", "High"} for finding in findings):
        return "NOT_READY"
    if any(check.status != "PASS" for check in core_checks) or any(finding.severity == "Medium" for finding in findings):
        return "CONDITIONAL"
    return "READY"

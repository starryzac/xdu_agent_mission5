---
name: day5-grader
description: Evaluate Day5 three-stack Web application submissions with evidence-aware static scoring, optional isolated runtime verification, professional Markdown reports, and safe GitHub fallback when only a writeup Markdown file is submitted. Use when grading Day5 deliverables, reviewing three application versions, checking CRUD/validation/error/UI evidence, or following a repository link from a submitted report.
argument-hint: <submission-path> [--mode static|dynamic]
---

# Day5 Grader

Run the bundled grader before writing any subjective evaluation.

## Resolve the input

- Treat the first argument as a submission directory or a single Markdown file.
- Use the current working directory when no path is provided.
- Pass remaining arguments through to the CLI.
- Keep static mode as the default. Execute dynamic mode only when the user explicitly requests it.

## Run the grader

Use the skill directory variable so the command works after project or personal installation:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/grade_day5.py" --root "<submission-path>"
```

For an explicit isolated dynamic assessment:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/grade_day5.py" --root "<submission-path>" --mode dynamic --allow-install
```

Do not add `--allow-install`, `--allow-data-write`, or dynamic mode without explicit user authorization.

## Interpret the result

1. Lead with the evidence-confirmed score, not the provisional score.
2. State the engineering readiness verdict.
3. Report Blocker and High findings before documentation or style findings.
4. Distinguish `FAIL_PROJECT` from `BLOCKED_ENV`.
5. Link to the generated Markdown report.

The provisional score describes what static evidence suggests. The verified score awards runtime-bound points only after build, start, CRUD, validation, response-contract, persistence, or frontend checks pass.

## GitHub fallback

- When no local application is detected, allow the script to extract up to three `https://github.com/...` repository links from the submitted Markdown.
- Grade the fixed Git commit statically and retain the local Markdown as report evidence.
- Never execute, install, source, or load environment files from an automatically discovered remote repository.
- If repository selection is ambiguous, require `--repo-url` rather than guessing.

## Guardrails

- Do not use LibreOffice.
- Do not read or copy `.env` files into runtime workspaces.
- Do not test external URLs with writes unless `--allow-data-write` is explicit.
- Do not treat unavailable evaluator dependencies as project defects.
- Do not award full verified functionality from regex or file-presence evidence alone.
- Keep the original three applications unchanged; the grader uses temporary runtime copies.

Read [DESIGN.md](DESIGN.md) when changing scoring or evidence rules. Read [USAGE.md](USAGE.md) when installing the skill, using GitHub fallback, configuring nonstandard projects, or interpreting exit codes.

## Assignment filename note

The assignment asks for `skill.md`, while Claude Code requires `SKILL.md`. Windows treats those names as the same path, so this `SKILL.md` is the authoritative and assignment-compatible entrypoint.


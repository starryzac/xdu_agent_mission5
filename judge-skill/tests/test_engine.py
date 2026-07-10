from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))

from day5_grader.engine import GraderOptions, grade_submission  # noqa: E402
from day5_grader.models import SourceInfo  # noqa: E402
from day5_grader.remote import RemoteResolution  # noqa: E402
from day5_grader.reporting import render_markdown  # noqa: E402


class EngineTests(unittest.TestCase):
    def test_markdown_only_without_remote_still_generates_report(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            document = Path(directory) / "submission.md"
            document.write_text("# Day5\n\n应用概念和 AI 心得。", encoding="utf-8")
            assessment = grade_submission(GraderOptions(root=document, remote_fallback=False))
            report = render_markdown(assessment)
        self.assertEqual(len(assessment.versions), 0)
        self.assertIn("证据确认分", report)
        self.assertIn("应用版本数量不足", report)

    def test_json_and_markdown_report_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            document = Path(directory) / "submission.md"
            document.write_text("# Day5\n\n应用概念。", encoding="utf-8")
            assessment = grade_submission(GraderOptions(root=document, remote_fallback=False))
            payload = assessment.to_dict()
            report = render_markdown(assessment)
        self.assertEqual(payload["schema_version"], "2.0")
        self.assertTrue({
            "provisional_score", "verified_score", "readiness", "sources",
            "versions", "findings", "environment", "limitations",
        }.issubset(payload))
        self.assertTrue({"result_code", "location", "status"}.issubset(payload["sources"][0]))
        expected_headings = [
            "## 执行摘要", "## 范围与环境", "## 评分总览", "## 关键风险",
            "## 各版本评测", "## 动态测试矩阵", "## 优先行动项",
            "## 证据索引", "## 限制与判读",
        ]
        positions = [report.index(heading) for heading in expected_headings]
        self.assertEqual(positions, sorted(positions))

    def test_local_projects_prevent_automatic_remote_fetch(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            app = root / "app"
            app.mkdir()
            (app / "package.json").write_text('{"scripts":{"start":"node server.js"},"dependencies":{"express":"1"}}', encoding="utf-8")
            (app / "README.md").write_text("Prerequisite Node Install npm Config PORT Run npm start", encoding="utf-8")
            for name in ("server.js", "model.js", "view.js", "extra.js", "more.js"):
                (app / name).write_text("const value = 1", encoding="utf-8")
            (root / "submission.md").write_text("GitHub 仓库 https://github.com/acme/day5", encoding="utf-8")
            with patch("day5_grader.engine.resolve_remote_sources") as remote:
                grade_submission(GraderOptions(root=root))
        remote.assert_not_called()

    def test_remote_source_is_never_executed_even_when_dynamic_is_requested(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            container = Path(directory)
            submission = container / "submission"
            submission.mkdir()
            document = submission / "submission.md"
            document.write_text("GitHub 仓库 https://github.com/acme/day5", encoding="utf-8")
            remote_root = container / "remote"
            app = remote_root / "app"
            app.mkdir(parents=True)
            (app / "package.json").write_text(
                '{"scripts":{"start":"node server.js"},"dependencies":{"express":"1"}}',
                encoding="utf-8",
            )
            (app / "README.md").write_text(
                "Prerequisite Node Install npm Config PORT Run npm start", encoding="utf-8",
            )
            for name in ("server.js", "model.js", "routes.js", "view.js", "extra.js"):
                (app / name).write_text("const value = 1", encoding="utf-8")
            source = SourceInfo(
                mode="github-static", root=remote_root, label="github:acme/day5",
                result_code="REMOTE_SNAPSHOT", repo_url="https://github.com/acme/day5",
                commit="a" * 40,
            )
            resolution = RemoteResolution([source], [])
            with patch("day5_grader.engine.resolve_remote_sources", return_value=resolution), patch(
                "day5_grader.engine.run_version_runtime"
            ) as runtime:
                assessment = grade_submission(GraderOptions(
                    root=submission,
                    mode="dynamic",
                    repo_urls=["https://github.com/acme/day5"],
                    allow_install=True,
                ))
        runtime.assert_not_called()
        self.assertEqual(assessment.mode, "static")


if __name__ == "__main__":
    unittest.main()

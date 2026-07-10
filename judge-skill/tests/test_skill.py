from __future__ import annotations

import re
import unittest
from pathlib import Path


class ClaudeSkillContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_runtime_path_contract(self) -> None:
        skill = Path(__file__).resolve().parents[1] / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"^---\n(?P<header>.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match)
        header = match.group("header") if match else ""
        self.assertRegex(header, r"(?m)^name:\s+day5-grader$")
        self.assertRegex(header, r"(?m)^description:\s+.+$")
        self.assertRegex(header, r"(?m)^argument-hint:\s+.+$")
        self.assertIn("${CLAUDE_SKILL_DIR}/scripts/grade_day5.py", text)
        self.assertIn("--mode dynamic", text)
        self.assertIn("GitHub fallback", text)


if __name__ == "__main__":
    unittest.main()


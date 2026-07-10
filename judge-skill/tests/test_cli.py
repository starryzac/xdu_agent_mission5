from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from day5_grader.cli import fail_policy_exit, parse_urls  # noqa: E402


class CliContractTests(unittest.TestCase):
    def test_urls_accept_only_credential_free_http_endpoints(self) -> None:
        self.assertEqual(
            parse_urls("mern=http://127.0.0.1:3000,django=https://example.test/api"),
            {
                "mern": "http://127.0.0.1:3000",
                "django": "https://example.test/api",
            },
        )
        with self.assertRaises(ValueError):
            parse_urls("local=file:///tmp/data")
        with self.assertRaises(ValueError):
            parse_urls("api=https://user:secret@example.test")

    def test_fail_policy_uses_verified_score_and_readiness(self) -> None:
        self.assertEqual(fail_policy_exit("score:80", "READY", 79.99), 4)
        self.assertEqual(fail_policy_exit("score:80", "CONDITIONAL", 80.0), 0)
        self.assertEqual(fail_policy_exit("not-ready", "NOT_READY", 99.0), 4)


if __name__ == "__main__":
    unittest.main()

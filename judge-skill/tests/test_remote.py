from __future__ import annotations

import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))

from day5_grader.remote import (  # noqa: E402
    GitHubLink,
    choose_links,
    clone_link,
    extract_github_links,
    normalize_github_url,
    resolve_remote_sources,
)


class GitHubLinkTests(unittest.TestCase):
    def test_normalizes_supported_repository_urls(self) -> None:
        root = normalize_github_url("https://github.com/acme/day5.git")
        self.assertEqual(root, ("https://github.com/acme/day5", "acme", "day5", None, ""))
        tree = normalize_github_url("https://github.com/acme/day5/tree/feature/x/apps/mern")
        self.assertEqual(tree, ("https://github.com/acme/day5", "acme", "day5", "tree", "feature/x/apps/mern"))
        blob = normalize_github_url("https://github.com/acme/day5/blob/main/README.md#top")
        self.assertEqual(blob, ("https://github.com/acme/day5", "acme", "day5", "blob", "main/README.md"))

    def test_rejects_non_repository_and_non_https_urls(self) -> None:
        self.assertIsNone(normalize_github_url("http://github.com/acme/day5"))
        self.assertIsNone(normalize_github_url("https://example.com/acme/day5"))
        self.assertIsNone(normalize_github_url("https://github.com/acme/day5/issues/1"))
        self.assertIsNone(normalize_github_url("file:///tmp/day5"))

    def test_extracts_context_link_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            document = Path(directory) / "submission.md"
            document.write_text(
                "GitHub 仓库：[repo](https://github.com/acme/day5)\n"
                "duplicate https://github.com/acme/day5.git\n",
                encoding="utf-8",
            )
            links = extract_github_links([document])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].repo_url, "https://github.com/acme/day5")
        self.assertEqual(links[0].markdown_line, 1)
        self.assertEqual(links[0].priority, 10)

    def test_more_than_three_unqualified_repositories_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            document = Path(directory) / "submission.md"
            document.write_text(
                "\n".join(f"https://github.com/acme/repo-{index}" for index in range(4)),
                encoding="utf-8",
            )
            links = extract_github_links([document])
            selected, ambiguous = choose_links(links, explicit=False)
        self.assertTrue(ambiguous)
        self.assertEqual(selected, [])

    def test_multiple_scopes_in_one_repository_merge_to_repository_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            document = Path(directory) / "submission.md"
            document.write_text(
                "GitHub 仓库 https://github.com/acme/day5/tree/main/apps/mern\n"
                "源码仓库 https://github.com/acme/day5/tree/main/apps/django\n",
                encoding="utf-8",
            )
            links = extract_github_links([document])
        self.assertEqual(len(links), 1)
        self.assertIsNone(links[0].kind)
        self.assertEqual(links[0].remainder, "")

    def test_missing_repository_link_has_explicit_result_code(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            resolution = resolve_remote_sources([], Path(directory))
        self.assertEqual(resolution.failures[0].result_code, "SOURCE_UNAVAILABLE")

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_clone_link_pins_a_temporary_git_repository(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            repository = root / "repository"
            subprocess.run(["git", "init", "-b", "main", str(repository)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.email", "grader@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.name", "Day5 Grader"], check=True)
            (repository / "package.json").write_text('{"dependencies":{"express":"1"}}', encoding="utf-8")
            subprocess.run(["git", "-C", str(repository), "add", "package.json"], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-m", "fixture"], check=True, capture_output=True)
            link = GitHubLink(
                repo_url=str(repository), owner="fixture", repo="repository", kind=None,
                remainder="", markdown_path="submission.md", markdown_line=1, priority=100,
            )
            clone_root = root / "clone"
            clone_root.mkdir()
            source = clone_link(link, clone_root, timeout=30)
        self.assertEqual(source.status, "PASS")
        self.assertEqual(source.result_code, "REMOTE_SNAPSHOT")
        self.assertRegex(source.commit or "", r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()

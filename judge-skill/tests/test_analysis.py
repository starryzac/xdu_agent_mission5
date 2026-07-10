from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))

from day5_grader.analysis import assess_version  # noqa: E402
from day5_grader.discovery import local_source, version_document_section  # noqa: E402
from day5_grader.models import ProjectCandidate  # noqa: E402


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


class ScopedAnalysisTests(unittest.TestCase):
    def test_global_writeup_keywords_do_not_satisfy_each_version(self) -> None:
        document = (
            "# 全局总结\n"
            "MERN、Django、Spring Boot 使用 AI Claude，数据库包括 MongoDB、SQLite、H2，"
            "并记录问题、修复和心得。\n"
        )
        self.assertEqual(version_document_section(document, "mern-version", "MERN"), "")
        self.assertEqual(version_document_section(document, "django-version", "Django"), "")
        self.assertEqual(version_document_section(document, "spring-version", "Spring Boot + Vue"), "")

    def test_version_section_includes_its_child_headings_only(self) -> None:
        document = (
            "## MERN 版本\n### 技术栈\nMERN\n### AI 与问题\nClaude 修复问题\n"
            "### 存储\nMongoDB\n## Django 版本\n### 技术栈\nDjango\n"
        )
        section = version_document_section(document, "mern-version", "MERN")
        self.assertIn("### AI 与问题", section)
        self.assertNotIn("## Django 版本", section)

    def test_keywords_in_seed_file_do_not_prove_functionality(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            app = root / "fake-app"
            app.mkdir()
            write(app / "package.json", json.dumps({"scripts": {"start": "node seed.js"}, "dependencies": {"express": "1"}}))
            write(app / "README.md", "# Fake\nPrerequisite Node\nInstall npm install\nConfig PORT\nRun npm start\n")
            write(
                app / "seed.js",
                "mongoose.Schema id required timestamps router.get router.post router.put router.delete "
                "try catch 404 success: true fetch('/api/notes')",
            )
            write(app / "a.js", "const a = 1")
            write(app / "b.js", "const b = 2")
            source = local_source(root)
            candidate = ProjectCandidate("fake-app", app, source)
            assessment = assess_version(candidate, "", [], source)
        self.assertLess(assessment.item("functionality").provisional, 2.0)

    def test_spring_valid_map_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            app = root / "spring-app"
            write(app / "pom.xml", "<project><modelVersion>4.0.0</modelVersion><artifactId>x</artifactId><dependencies><dependency><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>")
            write(app / "README.md", "Java prerequisite\nInstall mvnw\nConfig port\nRun mvnw spring-boot:run")
            write(app / "src/main/java/x/entity/Note.java", "@Entity class Note { @Id Long id; @NotBlank @Size(max=100) String title; String createdAt; }")
            write(
                app / "src/main/java/x/controller/NoteController.java",
                '@RequestMapping("/api/notes") class NoteController { @GetMapping Object list(){return null;} '
                '@GetMapping("/{id}") Object get(){return null;} @PostMapping Object create(@Valid @RequestBody Map<String,Object> body){return null;} '
                '@PutMapping("/{id}") Object update(){return null;} @DeleteMapping("/{id}") Object delete(){return null;} }',
            )
            write(app / "src/main/java/x/App.java", "class App {}")
            source = local_source(root)
            candidate = ProjectCandidate("spring-app", app, source)
            assessment = assess_version(candidate, "", [], source)
        self.assertIn("FUNC-VALID-MAP", {finding.rule_id for finding in assessment.findings})
        self.assertLess(assessment.feature("validation").provisional, 0.8)

    def test_django_api_html_404_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            app = root / "django-app"
            write(app / "requirements.txt", "Django==5.2\n")
            write(app / "manage.py", "print('manage')")
            write(app / "README.md", "Python prerequisite\nInstall pip install\nConfig sqlite\nRun python manage.py runserver")
            write(app / "notes/models.py", "from django.db import models\nclass Note(models.Model):\n title=models.CharField(max_length=100)\n created_at=models.DateTimeField(auto_now_add=True)\n")
            write(app / "notes/urls.py", "path('api/notes/<int:pk>', views.api_note)")
            write(app / "notes/views.py", "from django.shortcuts import get_object_or_404\ndef api_note(request, pk):\n note=get_object_or_404(Note, pk=pk)\n return JsonResponse({'success': True, 'data': {}})\n")
            write(app / "notes/templates/notes/form.html", "<form method='post'><input></form>")
            source = local_source(root)
            candidate = ProjectCandidate("django-app", app, source)
            assessment = assess_version(candidate, "", [], source)
        self.assertIn("FUNC-ERROR-DJANGO-HTML404", {finding.rule_id for finding in assessment.findings})


if __name__ == "__main__":
    unittest.main()

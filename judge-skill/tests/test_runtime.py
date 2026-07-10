from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_ROOT = Path(__file__).resolve().parents[1] / "scripts"
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))

from day5_grader.models import FAIL_PROJECT, NOT_APPLICABLE, PASS  # noqa: E402
from day5_grader.runtime import copy_project, full_http_checks, run_command, sanitized_environment  # noqa: E402


class CrudHandler(BaseHTTPRequestHandler):
    store: dict[str, dict[str, object]] = {}
    next_id = 1

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, status: int, body: dict[str, object]) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, object] | None:
        try:
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        except json.JSONDecodeError:
            return None

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/notes":
            self.send_json(200, {"success": True, "data": list(self.store.values())})
            return
        object_id = path.rsplit("/", 1)[-1]
        if object_id in self.store:
            self.send_json(200, {"success": True, "data": self.store[object_id]})
        else:
            self.send_json(404, {"success": False, "error": "not found"})

    def do_POST(self) -> None:
        body = self.read_json()
        if body is None:
            self.send_json(400, {"success": False, "error": "bad json"})
            return
        title = str(body.get("title", ""))
        content = str(body.get("content", ""))
        if not title.strip() or not content.strip() or len(title) > 100:
            self.send_json(400, {"success": False, "error": "validation"})
            return
        object_id = str(self.next_id)
        type(self).next_id += 1
        value = {**body, "id": object_id}
        self.store[object_id] = value
        self.send_json(201, {"success": True, "data": value})

    def do_PUT(self) -> None:
        object_id = self.path.rsplit("/", 1)[-1]
        body = self.read_json() or {}
        if object_id not in self.store:
            self.send_json(404, {"success": False, "error": "not found"})
            return
        self.store[object_id].update(body)
        self.send_json(200, {"success": True, "data": self.store[object_id]})

    def do_DELETE(self) -> None:
        object_id = self.path.rsplit("/", 1)[-1]
        if object_id not in self.store:
            self.send_json(404, {"success": False, "error": "not found"})
            return
        del self.store[object_id]
        self.send_json(200, {"success": True, "data": {"message": "deleted"}})


class RuntimeProbeTests(unittest.TestCase):
    def test_runtime_copy_excludes_secrets_and_databases(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "copy"
            source.mkdir()
            (source / "app.py").write_text("print('ok')", encoding="utf-8")
            (source / ".env.production").write_text("TOKEN=secret", encoding="utf-8")
            (source / "service.pem").write_text("secret", encoding="utf-8")
            (source / "data.sqlite3").write_bytes(b"database")
            copy_project(source, destination)
            self.assertTrue((destination / "app.py").exists())
            self.assertFalse((destination / ".env.production").exists())
            self.assertFalse((destination / "service.pem").exists())
            self.assertFalse((destination / "data.sqlite3").exists())

    def test_timed_out_command_cleans_child_process_tree(self) -> None:
        with tempfile.TemporaryDirectory(dir=TEST_ROOT) as directory:
            root = Path(directory)
            pid_file = root / "child.pid"
            script = (
                "import pathlib,subprocess,sys,time;"
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']);"
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid));"
                "time.sleep(30)"
            )
            result = run_command(
                [sys.executable, "-c", script], root, 1, sanitized_environment(root)
            )
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            time.sleep(0.2)
            if os.name == "nt":
                query = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {child_pid}", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                )
                child_exists = f'"{child_pid}"' in query.stdout
            else:
                try:
                    os.kill(child_pid, 0)
                    child_exists = True
                except OSError:
                    child_exists = False
        self.assertEqual(result.status, FAIL_PROJECT)
        self.assertFalse(child_exists)

    def test_crud_and_negative_probes(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), CrudHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            checks, _ = full_http_checks(base_url, "/api/notes")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        statuses = {check.check_id: check.status for check in checks}
        self.assertEqual(statuses["RT-CRUD-CREATE"], PASS)
        self.assertEqual(statuses["RT-CRUD-DELETE"], PASS)
        self.assertEqual(statuses["RT-VALID-BLANK"], PASS)
        self.assertEqual(statuses["RT-ERROR-404"], PASS)
        self.assertEqual(statuses["RT-PERSIST-RESTART"], NOT_APPLICABLE)


if __name__ == "__main__":
    unittest.main()

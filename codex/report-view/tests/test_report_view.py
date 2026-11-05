"""Offline tests for report_view.py: local resolution, serving, stop, prune.

Remote (ssh/rsync) paths are not exercised; they need a live host.
Run: python skills/report-view/tests/test_report_view.py
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "report_view.py"


def run(*args, cache):
    env = {**os.environ, "REPORT_VIEW_CACHE": str(cache)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


class ReportViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cache = root / "cache"
        self.report = root / "report"
        (self.report / "assets").mkdir(parents=True)
        (self.report / "index.html").write_text("<html><body>ok</body></html>")
        (self.report / "assets" / "app.js").write_text("console.log(1)")
        (self.report / "assets" / "data.bin.gz").write_bytes(b"\x1f\x8b\x08\x00")

    def tearDown(self):
        run("--stop", "all", cache=self.cache)
        self.tmp.cleanup()

    def test_serves_local_folder_with_expected_headers(self):
        r = run("--no-open", str(self.report), cache=self.cache)
        self.assertEqual(r.returncode, 0, r.stderr)
        url = r.stdout.strip().splitlines()[-1]
        self.assertTrue(
            url.startswith("http://127.0.0.1:") and url.endswith("/index.html")
        )
        base = url.rsplit("/", 1)[0]
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.read(), b"<html><body>ok</body></html>")
            self.assertEqual(resp.headers["Cache-Control"], "no-store")
        with urllib.request.urlopen(base + "/assets/app.js") as resp:
            self.assertEqual(resp.headers.get_content_type(), "text/javascript")
        with urllib.request.urlopen(base + "/assets/data.bin.gz") as resp:
            self.assertEqual(resp.headers.get_content_type(), "application/gzip")
            self.assertIsNone(resp.headers.get("Content-Encoding"))

    def test_reuses_running_server_and_stops_it(self):
        first = run("--no-open", str(self.report), cache=self.cache).stdout.strip()
        second = run(
            "--no-open", str(self.report / "index.html"), cache=self.cache
        ).stdout.strip()
        self.assertEqual(first, second)
        records = list((self.cache / ".servers").glob("*.json"))
        self.assertEqual(len(records), 1)
        pid = json.loads(records[0].read_text())["pid"]
        run("--stop", "all", cache=self.cache)
        for _ in range(30):
            try:
                os.kill(pid, 0)
            except OSError:
                break
            time.sleep(0.1)
        else:
            self.fail("server still running after --stop")
        self.assertEqual(list((self.cache / ".servers").glob("*.json")), [])

    def test_ambiguous_folder_is_refused(self):
        (self.report / "a.html").write_text("x")
        (self.report / "b.html").write_text("y")
        (self.report / "index.html").unlink()
        r = run("--no-open", str(self.report), cache=self.cache)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ambiguous", r.stderr)

    def test_missing_path_is_refused(self):
        r = run("--no-open", str(self.report / "nope.html"), cache=self.cache)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found", r.stderr)

    def test_suspicious_remote_path_is_refused_before_ssh(self):
        r = run(
            "--no-open", "--host", "example.invalid", "x; rm -rf ~", cache=self.cache
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refusing remote path", r.stderr)

    def test_prune_removes_only_old_cache_copies(self):
        old = self.cache / "host" / "old"
        new = self.cache / "host" / "new"
        for d in (old, new):
            d.mkdir(parents=True)
            (d / "index.html").write_text("x")
        past = time.time() - 30 * 86400
        os.utime(old, (past, past))
        r = run("--prune", "14", cache=self.cache)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())
        self.assertTrue(self.report.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

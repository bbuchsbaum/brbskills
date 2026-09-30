"""Narrative commands, hub discovery, v1 migration and git exclusion; isolated files only."""
import json
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from _util import DASH, ROOT, HubCase, dash

S = "cli-test0001"


class NarrativeTests(HubCase):
    make_hub = False

    def setUp(self):
        super().setUp()
        self.cli(
            "init",
            "Synthetic review",
            "--task",
            "First",
            "--task",
            "Second|detail two",
            session=S,
        )
        self.hub = dash.Hub(self.dir)

    def run_cli(self, *args, ok=True):
        return self.cli(*args, ok=ok, session=S)

    def test_init_creates_hub_session_and_page(self):
        self.assertTrue((self.dir / "hub.json").is_file())
        self.assertEqual((self.dir / "index.html").read_text(), dash.PLACEHOLDER if not (ROOT / "assets/dashboard.html").exists() else (ROOT / "assets/dashboard.html").read_text())
        p = self.plan(S)
        self.assertEqual([t["title"] for t in p["tasks"]], ["First", "Second"])
        self.assertEqual(p["tasks"][1]["detail"], "detail two")
        v = self.view(S)
        self.assertEqual(
            (v["agent"], v["label"], v["activity"]),
            ("cli", "Synthetic review", "working"),
        )
        self.run_cli("init", "Again", ok=False)
        self.run_cli("init", "Again", "--force")
        self.assertEqual(self.plan(S)["title"], "Again")

    def test_same_clock_writes_have_distinct_revisions(self):
        with patch.object(dash, "now", return_value="2026-09-26T12:00:00.000-04:00"):
            dash.regen(self.hub)
            first = self.snapshot()["revision"]
            dash.bump(self.hub)
            dash.regen(self.hub)
            second = self.snapshot()
        self.assertGreater(second["revision"], first)

    def test_concurrent_calls_preserve_all_questions(self):
        def add(i):
            return (
                self.run_cli("ask", f"Question {i}", "--default", "Continue")
                .stdout.strip()
                .splitlines()[0]
            )

        with ThreadPoolExecutor(max_workers=6) as pool:
            ids = list(pool.map(add, range(18)))
        self.assertEqual(len(set(ids)), 18)
        self.assertEqual(len(self.plan(S)["questions"]), 18)

    def test_questions_and_blockers_lifecycle(self):
        self.run_cli("ask", "Question", "--default", "Continue")
        self.run_cli("answer", "q1", "Confirmed")
        self.run_cli("block", "Missing evidence", "--needs", "A result")
        self.run_cli("unblock", "b1", "--note", "Result received")
        q = self.plan(S)["questions"][0]
        self.assertEqual((q["answer"], q["answered_via"]), ("Confirmed", "chat"))
        b = self.plan(S)["blockers"][0]
        self.assertIsNotNone(b["closed"])
        self.assertEqual(b["needs"], "A result")

    def test_completion_rejects_unfinished_work_and_blockers(self):
        self.run_cli("status", "done", ok=False)
        self.run_cli("task", "1", "done")
        self.run_cli("task", "2", "skipped")
        self.run_cli("block", "Unresolved")
        self.run_cli("status", "done", ok=False)
        self.run_cli("unblock", "B1")
        self.run_cli("status", "done")
        self.assertIsNotNone(self.plan(S)["finished"])
        self.assertEqual(self.view(S)["activity"], "idle")
        self.run_cli("task", "1", "doing")
        self.assertNotEqual(self.plan(S)["status"], "done")
        self.assertIsNone(self.plan(S)["finished"])

    def test_task_timestamps(self):
        self.run_cli("task", "1", "doing")
        t = self.plan(S)["tasks"][0]
        self.assertIsNotNone(t["started"])
        self.assertIsNone(t["finished"])
        self.run_cli("task", "1", "done", "--note", "Checks passed")
        t = self.plan(S)["tasks"][0]
        self.assertIsNotNone(t["finished"])
        self.assertEqual(t["note"], "Checks passed")
        self.assertEqual(
            self.run_cli("add-task", "Inserted", "--after", "1").stdout.splitlines()[0],
            "3",
        )
        self.assertEqual([t["id"] for t in self.plan(S)["tasks"]], [1, 3, 2])

    def test_parallel_work_is_not_reset(self):
        self.run_cli("task", "1", "doing")
        self.run_cli("task", "2", "doing")
        self.assertEqual(
            [t["status"] for t in self.plan(S)["tasks"]], ["doing", "doing"]
        )

    def test_invalid_inputs_do_not_mutate_state(self):
        before = self.plan(S)
        for args in [
            ("metric", "bad", "nan"),
            ("metric", "bad", "inf"),
            ("task", "999", "done"),
            ("task", "1", "bogus"),
            ("answer", "Q9", "x"),
            ("unblock", "B7"),
        ]:
            self.run_cli(*args, ok=False)
        self.assertEqual(self.plan(S), before)

    def test_deliver_and_metric_history(self):
        file = self.root / "a #b?c%.txt"
        file.write_text("result")
        self.run_cli("deliver", str(file), "--label", "Result")
        self.run_cli("deliver", str(file), "--label", "New label")
        self.run_cli("metric", "Failures", "3", "--good", "down")
        self.run_cli("metric", "Failures", "0")
        p = self.plan(S)
        self.assertEqual(
            [(d["label"], d["path"]) for d in p["deliverables"]],
            [("New label", str(file))],
        )
        m = p["metrics"][0]
        self.assertEqual((m["name"], m["good"], m["value"]), ("Failures", "down", 0))
        self.assertEqual([h[1] for h in m["history"]], [3, 0])

    def test_narrative_events_and_log(self):
        self.run_cli("log", "Reason for the change")
        v = self.view(S)
        self.assertEqual(v["plan"]["log"][-1]["text"], "Reason for the change")
        self.assertEqual(v["events"][-1]["kind"], "note")
        self.assertEqual(v["events"][-1]["summary"], "Reason for the change")

    def test_show_json_and_text(self):
        self.assertIn("Synthetic review", self.run_cli("show").stdout)
        v = json.loads(self.run_cli("show", "--json").stdout)
        self.assertEqual(v["id"], S)

    def test_discovery_and_dir_after_command(self):
        child = self.root / "nested"
        child.mkdir()
        env = dict(self.env, DASH_SESSION=S)
        p = subprocess.run(
            [sys.executable, str(DASH), "path"],
            cwd=child,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(p.stdout.strip(), str(self.dir / "index.html"))
        p = subprocess.run(
            [sys.executable, str(DASH), "log", "hello", "--dir", str(self.dir)],
            cwd=child,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        p = subprocess.run(
            [
                sys.executable,
                str(DASH),
                "log",
                "hello",
                "--dir",
                str(self.root / "notdash"),
            ],
            cwd=child,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertIn("must be named .dashboard", p.stderr)

    def test_unknown_session_fails_clearly(self):
        p = self.cli("log", "x", session="cli-nope", ok=False)
        self.assertIn("no session 'cli-nope'", p.stderr)

    def test_only_live_session_is_used_without_env(self):
        self.cli("log", "implicit")
        self.assertEqual(self.plan(S)["log"][-1]["text"], "implicit")
        self.cli("end", session=S)
        p = self.cli("log", "x", ok=False)
        self.assertIn("no live sessions", p.stderr)

    def test_join_and_sessions(self):
        sid = self.cli(
            "join", "--agent", "codex", "--label", "Codex lane"
        ).stdout.strip()
        self.assertRegex(sid, r"^codex-[0-9a-f]{8}$")
        rows = self.cli("sessions").stdout
        self.assertIn(sid, rows)
        self.assertIn("Codex lane", rows)
        self.cli("init", "Codex plan", session=sid)
        self.assertEqual(self.view(sid)["agent"], "codex")

    def test_open_failure_propagates(self):
        a = type("Args", (), {"dir": str(self.dir)})()
        with patch.object(
            subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["open"])
        ):
            with self.assertRaises(dash.DashError):
                dash.cmd_open(a)


class NewHubTests(HubCase):
    make_hub = False

    def test_init_without_session_creates_cli_session(self):
        p = self.cli("init", "Fresh")
        sid = [
            ln.split("=", 1)[1]
            for ln in p.stdout.splitlines()
            if ln.startswith("DASH_SESSION=")
        ][0]
        self.assertRegex(sid, r"^cli-[0-9a-f]{8}$")
        self.assertEqual(self.plan(sid)["title"], "Fresh")
        # A second init without a session never takes over the live lane: it starts a new one.
        p = self.cli("init", "Second")
        other = [ln.split("=", 1)[1] for ln in p.stdout.splitlines() if ln.startswith("DASH_SESSION=")][0]
        self.assertNotEqual(other, sid)
        self.assertEqual(self.plan(sid)["title"], "Fresh")

    def test_init_at_git_toplevel_by_default(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        sub = self.root / "a" / "b"
        sub.mkdir(parents=True)
        p = subprocess.run(
            [sys.executable, str(DASH), "init", "Top"],
            cwd=sub,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((self.root / ".dashboard" / "hub.json").is_file())
        subprocess.run(
            ["git", "check-ignore", "-q", ".dashboard/hub.json"],
            cwd=self.root,
            check=True,
        )

    def test_commands_without_hub_fail(self):
        p = subprocess.run(
            [sys.executable, str(DASH), "log", "x"],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("no dashboard hub", p.stderr)

    def test_git_exclusion_literal_paths_and_worktree(self):
        repo = self.root / "repo"
        repo.mkdir()

        def git(*args, cwd=repo):
            return subprocess.run(
                ["git", *args],
                cwd=cwd,
                env=self.env,
                text=True,
                capture_output=True,
                check=True,
            )

        git("init", "-q")
        git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "fixture",
        )
        linked = self.root / "worktree"
        git("worktree", "add", "-q", str(linked), "-b", "fixture")
        self.dir = linked / "part[1]" / ".dashboard"
        self.dir.parent.mkdir()
        self.cli("init", "Git fixture", cwd=linked)
        git("check-ignore", str(self.dir / "hub.json"), cwd=linked)
        self.assertFalse((linked / ".gitignore").exists())

    def test_v1_state_is_migrated(self):
        self.dir.mkdir()
        v1 = {
            "schema_version": 1,
            "run_id": "1234abcd-0000",
            "title": "Old run",
            "goal": "g",
            "context": "",
            "project": str(self.root),
            "agent": "codex",
            "status": "at_risk",
            "status_note": "",
            "started": "2026-09-26T12:00:00-04:00",
            "updated": "2026-09-26T13:00:00-04:00",
            "tasks": [
                {
                    "id": 1,
                    "title": "T",
                    "detail": "",
                    "status": "done",
                    "started": "2026-09-26T12:00:00-04:00",
                    "finished": "2026-09-26T12:30:00-04:00",
                }
            ],
            "questions": [
                {
                    "id": "Q1",
                    "q": "Which?",
                    "default": "A",
                    "status": "answered",
                    "asked": "x",
                    "answer": "B",
                    "answered": "y",
                }
            ],
            "blockers": [
                {
                    "id": "B1",
                    "what": "stuck",
                    "needs": "",
                    "since": "z",
                    "status": "open",
                }
            ],
            "deliverables": [{"label": "R", "path": "/r.html", "note": "", "at": "w"}],
            "metrics": {
                "Tests": {"value": 3, "at": "t", "history": [{"at": "t", "value": 3}]}
            },
            "log": [{"at": "t", "msg": "hello"}],
        }
        (self.dir / "state.json").write_text(json.dumps(v1))
        (self.dir / "state.js").write_text("old")
        p = self.cli("sessions")
        self.assertIn("v1-1234abcd", p.stdout)
        self.assertIn("migrated", p.stderr)
        plan = self.plan("v1-1234abcd")
        self.assertEqual(plan["questions"][0]["text"], "Which?")
        self.assertEqual(plan["blockers"][0]["text"], "stuck")
        self.assertEqual(plan["metrics"][0]["history"], [["t", 3]])
        self.assertEqual(plan["log"][0], {"ts": "t", "text": "hello"})
        self.assertFalse((self.dir / "state.json").exists())
        self.assertFalse((self.dir / "state.js").exists())
        self.cli("render")
        self.assertEqual((self.dir / "index.html").read_text(), dash.PLACEHOLDER if not (ROOT / "assets/dashboard.html").exists() else (ROOT / "assets/dashboard.html").read_text())


class GuardTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.d = self.root / ".dashboard"
        self.d.mkdir()
        (self.d / "state.json").write_text("{}")
        self.env = {k: v for k, v in os.environ.items() if k != "DASHBOARD_DIR"}

    def check(self, path=None, raw=None, env=None):
        event = {
            "cwd": str(self.root),
            "tool_name": "Write",
            "tool_input": {"file_path": str(path)},
        }
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/guard.py")],
            input=raw if raw is not None else json.dumps(event),
            text=True,
            capture_output=True,
            env=env or self.env,
        ).returncode

    def test_page_only(self):
        self.assertEqual(self.check(self.d / "index.html"), 0)
        for p in [
            self.d / "state.json",
            self.d / "state.js",
            self.root / "other/.dashboard/index.html",
            self.root / "project.py",
            self.d / "../project.py",
            Path.home() / ".config/dashboard-builder/style.md",
        ]:
            self.assertEqual(self.check(p), 2, str(p))

    def test_symlink_escape(self):
        outside = self.root / "outside.html"
        outside.write_text("private")
        (self.d / "index.html").symlink_to(outside)
        self.assertEqual(self.check(self.d / "index.html"), 2)

    def test_invalid_payload_fails_closed(self):
        for raw in ["{", "{}", "null", "[]", '{"tool_input":null}']:
            self.assertEqual(self.check(raw=raw), 2, raw)

    def test_explicit_external_directory(self):
        d = self.root / "external/.dashboard"
        d.mkdir(parents=True)
        (d / "state.json").write_text("{}")
        env = dict(self.env, DASHBOARD_DIR=str(d))
        self.assertEqual(self.check(d / "index.html", env=env), 0)
        self.assertEqual(self.check(self.d / "index.html", env=env), 2)


if __name__ == "__main__":
    unittest.main()

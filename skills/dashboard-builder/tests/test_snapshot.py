"""Snapshot contract (vs page fixtures), conflicts, style, page install and performance budgets."""
import json
import os
import random
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from _util import FIXTURES, HOOK, HubCase, dash, perf_limit

A, B = "aaaa0000-1111-4000-8000-000000000001", "bbbb0000-2222-4000-8000-000000000002"


def key_paths(x, path="", out=None):
    """{json path: set(keys)} for every object in a snapshot; list items share a path."""
    out = {} if out is None else out
    if isinstance(x, dict):
        out.setdefault(path, set()).update(x)
        for k, v in x.items():
            key_paths(v, f"{path}.{k}", out)
    elif isinstance(x, list):
        for v in x:
            if not isinstance(v, list):  # metric history pairs are [ts, value]
                key_paths(v, path + "[]", out)
    return out


MOTE = {
    "store": "/x/.mote",
    "fetched": "2026-09-30T10:00:00.000-04:00",
    "error": None,
    "counts": {"open": 3, "doing": 1, "blocked": 0, "review": 0},
    "doing": [{"id": "bd-1", "title": "t", "assignee": "a", "tags": [], "priority": 1}],
    "ready": [
        {"id": "bd-2", "title": "t", "assignee": None, "tags": ["x"], "priority": 2}
    ],
    "blocked": [
        {"id": "bd-3", "title": "t", "assignee": None, "tags": [], "priority": 0}
    ],
    "reservations": [
        {
            "actor": "claude-aaaa",
            "paths": ["R/shared.R"],
            "created": "2026-09-30T09:00:00.000-04:00",
            "issue": "bd-1",
            "expires": "2026-09-30T11:00:00.000-04:00",
        }
    ],
    "actors": [{"actor": "claude-aaaa", "status": "active", "expires": None}],
    "posts": [
        {
            "id": "post-1",
            "topic": "general",
            "from": "chief",
            "ts": "2026-09-30T09:00:00.000-04:00",
            "excerpt": "hi",
            "replies": 0,
        }
    ],
}


class ContractTests(HubCase):
    def rich_hub(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        for sid in (A, B):
            self.start(sid)
            self.tool(sid, "Edit", {"file_path": str(self.root / "R" / "shared.R")}, {})
        self.cli(
            "init",
            "Rich",
            "--goal",
            "g",
            "--context",
            "c",
            "--task",
            "One|d",
            "--task",
            "Two",
            session=A,
        )
        for args in (
            ("task", "1", "doing", "--note", "n"),
            ("ask", "Q?", "--default", "d"),
            ("block", "stuck", "--needs", "x"),
            ("metric", "Tests passing", "41", "--total", "50", "--good", "up"),
            ("deliver", str(self.root / "r.html"), "--label", "Report"),
            ("log", "hello"),
        ):
            self.cli(*args, session=A)
        self.tool(
            A,
            "Bash",
            {"command": "pytest"},
            {"stdout": "== 1 passed, 1 failed in 0.1s =="},
        )
        self.hook(
            "PreToolUse",
            A,
            tool_name="Bash",
            tool_input={"command": "sleep 100 && rm -rf tmp"},
            tool_use_id="cur",
        )
        self.hook(
            "Notification",
            A,
            message="Claude needs your permission to use Bash",
            notification_type="permission_prompt",
        )
        dash.queue_message(self.hub, A, "message", "hi")
        mote = dict(MOTE, reservations=[dict(r, expires=dash.iso(time.time() + 3600)) for r in MOTE["reservations"]])
        (self.dir / "mote.json").write_text(json.dumps(mote))
        (self.root / ".mote").mkdir()
        with patch.object(dash, "mote_bin", return_value="/bin/true"):
            return dash.build_snapshot(self.hub)

    def test_snapshot_keys_match_page_fixtures(self):
        fixtures = sorted(FIXTURES.glob("*.json"))
        if not fixtures:
            self.skipTest("page fixtures not present")
        want = {}
        for f in fixtures:
            for k, v in key_paths(json.loads(f.read_text())).items():
                want.setdefault(k, set()).update(v)
        snap = self.rich_hub()
        got = key_paths(snap)
        for path, keys in got.items():
            self.assertIn(path, want, f"unexpected object at {path}")
            self.assertEqual(keys, want[path], f"keys differ at {path}")
        self.assertEqual(
            sorted(set(want) - set(got)), [], "fixture paths the backend never produces"
        )

    def test_contract_values(self):
        snap = self.rich_hub()
        self.assertEqual(snap["schema"], 2)
        self.assertGreater(snap["revision"], 10)
        self.assertIsNotNone(dash.epoch(snap["generated"]))
        self.assertEqual(snap["server"], {"running": False, "started": None})
        self.assertEqual(snap["project"]["name"], "proj")
        self.assertEqual(
            snap["project"]["git"]["dirty"], 1
        )  # R/ is untracked; .dashboard is excluded
        a = next(s for s in snap["sessions"] if s["id"] == A)
        self.assertEqual(a["activity"], "waiting_permission")
        self.assertEqual(a["current"]["summary"], "sleep 100 && rm -rf tmp")
        self.assertEqual(a["current"]["destructive"], {"label": "rm -rf", "match": "rm -rf tmp", "severity": "high"})
        self.assertEqual(a["attention"][-1]["destructive"], a["current"]["destructive"])
        m = a["plan"]["metrics"][0]
        self.assertEqual((m["value"], m["total"], len(m["history"][0])), (41, 50, 2))
        self.assertEqual(a["plan"]["blockers"][0]["closed"], None)
        c = snap["conflicts"][0]
        self.assertEqual((c["path"], c["sources"], c["live"], c["mote_reserved_by"]),
                         ("R/shared.R", ["edit", "reservation"], True, "claude-aaaa"))
        self.assertEqual(c["last_edit"], max((d["ts"] for d in c["detail"] if d["kind"] == "edit"), key=dash.epoch))
        self.assertEqual(sorted((d["session"], d["kind"]) for d in c["detail"]),
                         [("aaaa", "edit"), ("aaaa", "reservation"), ("bbbb", "edit")])
        self.assertEqual(set(snap["conflicts"][0]["sessions"]), {"aaaa", "bbbb"})
        text = json.dumps(snap)
        self.assertNotIn("argv", text)
        self.assertNotIn("_edits", text)
        self.assertNotIn("_mentions", text)

    def test_data_js_escapes_script_end_and_skips_token(self):
        self.start(A)
        self.hook("UserPromptSubmit", A, prompt="print </script><b>")
        (self.dir / ".token").write_text("SECRET-TOKEN")
        dash.regen(self.hub)
        js = (self.dir / "data.js").read_text()
        self.assertNotIn("</script>", js)
        self.assertNotIn("SECRET-TOKEN", js)
        self.assertEqual(self.view(A)["last_prompt"]["text"], "print </script><b>")

    def test_old_conflicts_and_ended_sessions_age_out(self):
        self.start(A)
        self.start(B)
        for sid in (A, B):
            self.tool(sid, "Write", {"file_path": "x.py", "content": ""}, {})
        self.assertEqual(len(dash.build_snapshot(self.hub)["conflicts"]), 1)
        p = self.dir / "sessions" / B / "session.json"
        s = json.loads(p.read_text())
        s["files"]["x.py"]["last_edit"] = dash.iso(time.time() - 3 * 3600)
        s["ended"] = s["last_seen"] = dash.iso(time.time() - 25 * 3600)
        p.write_text(json.dumps(s))
        snap = dash.build_snapshot(self.hub)
        self.assertEqual(snap["conflicts"], [])
        self.assertEqual([x["id"] for x in snap["sessions"]], [A])

    def test_trailing_flush_publishes_debounced_event(self):
        self.start(A)
        self.tool(A, "Bash", {"command": "echo one"}, {"stdout": "one"})
        self.hook(
            "PostToolUse",
            A,
            tool_name="Bash",
            tool_input={"command": "echo two"},
            tool_use_id="x2",
            tool_response={"stdout": "two"},
        )
        deadline = time.time() + 30
        while time.time() < deadline:
            evs = self.view(A, fresh=False)["events"]
            if evs[-1]["summary"] == "echo two":
                break
            time.sleep(0.1)
        self.assertEqual(evs[-1]["summary"], "echo two")

    def test_style_parsing(self):
        style = self.root / "style.md"
        style.write_text(
            '# Dashboard style\ntheme: light\ndensity: airy\naccent: "#abc"\nnotes: "bigger fonts"\n'
        )
        self.assertEqual(
            dash.read_style(style),
            {
                "theme": "light",
                "density": "airy",
                "accent": "#abc",
                "notes": "bigger fonts",
            },
        )
        style.write_text('accent: "#12345"\ntheme: neon\n')
        self.assertEqual(
            dash.read_style(style),
            {"theme": None, "density": None, "accent": None, "notes": None},
        )
        self.assertEqual(dash.read_style(self.root / "missing.md")["theme"], None)


class PageInstallTests(HubCase):
    def test_versioned_copy(self):
        page = self.dir / "index.html"
        page.write_text("<html>v1 task page</html>")
        with patch.object(dash, "SKILL", self.root / "skill"):
            (self.root / "skill" / "assets" / "fonts").mkdir(parents=True)
            (self.root / "skill" / "assets" / "fonts" / "a.woff2").write_bytes(b"x")
            dash.install_page(self.hub)
            self.assertIn(
                "dashboard-page v2.0 placeholder", page.read_text()
            )  # no asset: placeholder
            asset = self.root / "skill" / "assets" / "dashboard.html"
            asset.write_text("<!-- dashboard-page v2.3 -->\n<html>real</html>")
            dash.install_page(self.hub)
            self.assertIn("real", page.read_text())
            self.assertFalse((self.dir / "fonts").exists())  # page does not reference fonts/
            asset.write_text("<!-- dashboard-page v2.3 -->\n<style>@font-face{src:url(fonts/a.woff2)}</style>")
            dash.install_page(self.hub)  # same version, changed content: replaced
            self.assertTrue((self.dir / "fonts" / "a.woff2").exists())
            self.assertEqual(dash.page_version('<meta name="dashboard-page" content="agent-dashboard 2.1.4">'), (2, 1, 4))
            page.write_text("<!-- dashboard-page v2.5 -->\nnewer local")
            dash.install_page(self.hub)
            self.assertIn("newer local", page.read_text())
            asset.write_text("<!-- dashboard-page v2.6 -->\nupgrade")
            dash.install_page(self.hub)
            self.assertIn("upgrade", page.read_text())


class PerformanceTests(HubCase):
    def populate(self, sid, n=5000):
        sd = self.dir / "sessions" / sid
        sd.mkdir(parents=True)
        s = dash.new_session(sid, agent="claude")
        s.update(hooks=True, turn="active", next_event=n + 1, events_in_file=n)
        t = dash.now()
        s["files"] = {
            f"R/file{i}.R": {"edits": i % 7, "reads": i % 3, "last": t, "last_edit": t}
            for i in range(500)
        }
        s["tests"] = [
            {
                "ts": t,
                "runner": "pytest",
                "passed": i,
                "failed": 0,
                "skipped": 0,
                "command": "pytest",
            }
            for i in range(50)
        ]
        (sd / "session.json").write_text(json.dumps(s))
        rnd = random.Random(1)
        with open(sd / "events.jsonl", "w") as f:
            for i in range(1, n + 1):
                f.write(
                    json.dumps(
                        {
                            "id": i,
                            "ts": t,
                            "kind": "tool",
                            "tool": "Bash",
                            "summary": "x" * rnd.randint(20, 160),
                            "detail": "y" * rnd.randint(0, 200),
                            "ok": True,
                            "duration_ms": 12,
                            "subagent": None,
                        }
                    )
                    + "\n"
                )
        plan = {
            "title": "p",
            "goal": "",
            "context": "",
            "status": "on_track",
            "status_note": "",
            "status_updated": t,
            "tasks": [
                {
                    "id": i,
                    "title": f"t{i}",
                    "detail": "",
                    "status": "todo",
                    "note": None,
                    "started": None,
                    "finished": None,
                }
                for i in range(30)
            ],
            "questions": [],
            "blockers": [],
            "metrics": [],
            "deliverables": [],
            "log": [{"ts": t, "text": "l"}] * 200,
        }
        (sd / "plan.json").write_text(json.dumps(plan))
        with open(sd / "inbox.jsonl", "w") as f:
            for i in range(60):
                f.write(
                    json.dumps(
                        {
                            "op": "add",
                            "id": f"m{i}",
                            "ts": t,
                            "kind": "message",
                            "text": "hi",
                            "qid": None,
                        }
                    )
                    + "\n"
                )

    def test_snapshot_budget_3x5000(self):
        for sid in (A, B, "cccc0000-3333-4000-8000-000000000003"):
            self.populate(sid)
        dash.build_snapshot(self.hub)  # warm git cache and file cache
        times = []
        for _ in range(11):
            t0 = time.perf_counter()
            snap = dash.build_snapshot(self.hub)
            dash.write_datajs(self.hub, snap)
            times.append(time.perf_counter() - t0)
        med = sorted(times)[len(times) // 2]
        print(
            f"\n  snapshot build+write, 3 sessions x 5000 events, median of 11: {med * 1000:.1f} ms",
            file=sys.stderr,
        )
        self.assertEqual([len(s["events"]) for s in snap["sessions"]], [300, 300, 300])
        self.assertEqual(snap["sessions"][0]["events"][-1]["id"], 5000)
        self.assertEqual(len(snap["sessions"][0]["files"]), 40)
        self.assertLess(med, perf_limit(0.050))

    def test_hook_latency_with_hub(self):
        for sid in (A, B):
            self.populate(sid)
        dash.build_snapshot(self.hub)
        payload = json.dumps(
            self.payload(
                "PostToolUse",
                A,
                tool_name="Bash",
                tool_input={"command": "ls"},
                tool_use_id="z",
                tool_response={"stdout": "ok"},
            )
        )
        pre = json.dumps(
            self.payload(
                "PreToolUse",
                A,
                tool_name="Bash",
                tool_input={"command": "ls"},
                tool_use_id="z",
            )
        )
        times = []
        for i in range(7):
            for data in (pre, payload):
                t0 = time.perf_counter()
                subprocess.run(
                    [sys.executable, str(HOOK)],
                    input=data,
                    text=True,
                    capture_output=True,
                    env=self.env,
                    check=True,
                )
                times.append(time.perf_counter() - t0)
        med = sorted(times)[len(times) // 2]
        print(
            f"\n  hook with hub (2 sessions x 5000 events), median of 14: {med * 1000:.1f} ms",
            file=sys.stderr,
        )
        self.assertLess(med, perf_limit(0.100))


if __name__ == "__main__":
    unittest.main()

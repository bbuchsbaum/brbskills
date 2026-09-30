"""Shared fixtures for dashboard tests: temp hubs, CLI and hook runners. No real ~/.claude."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "scripts" / "dash.py"
HOOK = ROOT / "scripts" / "dash_hook.py"
FIXTURES = ROOT / "tests" / "fixtures"

_spec = importlib.util.spec_from_file_location("dash", DASH)
dash = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dash)

STRIP = (
    "DASHBOARD_DIR",
    "DASH_SESSION",
    "CLAUDE_SESSION_ID",
    "CLAUDE_ENV_FILE",
    "DASHBOARD_AGENT",
    "DASH_SERVER_IDLE",
    "MOTE_STORE",
    "MOTE_ACTOR",
    "CLAUDECODE",
)


class HubCase(unittest.TestCase):
    """A temp project with a hub; HOME points into the temp dir."""

    make_hub = True

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / "proj"
        self.root.mkdir()
        self.home = Path(self.tmp.name).resolve() / "home"
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if k not in STRIP}
        self.env["HOME"] = str(self.home)
        self.dir = self.root / ".dashboard"
        if self.make_hub:
            self.hub = dash.find_hub(str(self.dir), create=True)

    def cli(self, *args, ok=True, env=None, cwd=None, session=None):
        extra = ["--session", session] if session else []
        p = subprocess.run(
            [sys.executable, str(DASH), "--dir", str(self.dir), *extra, *args],
            cwd=cwd or self.root,
            env=env or self.env,
            text=True,
            capture_output=True,
            timeout=60,
        )
        if ok is True:
            self.assertEqual(p.returncode, 0, p.stderr)
        elif ok is False:
            self.assertNotEqual(p.returncode, 0, p.stdout)
        return p

    def payload(self, event, sid, **kw):
        p = {
            "hook_event_name": event,
            "session_id": sid,
            "cwd": str(self.root),
            "transcript_path": str(self.root / "t.jsonl"),
            "permission_mode": "default",
        }
        p.update(kw)
        return p

    def hook(self, event, sid, env=None, raw=None, **kw):
        data = raw if raw is not None else json.dumps(self.payload(event, sid, **kw))
        p = subprocess.run([sys.executable, str(HOOK)], input=data, text=True, capture_output=True,
                           env=env or self.env, cwd=self.root, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stderr, "")
        log = self.dir / "hook-errors.log"
        if log.exists() and not getattr(self, "expect_hook_errors", False):
            self.fail("hook error:\n" + log.read_text())
        return json.loads(p.stdout) if p.stdout.strip() else None

    def session(self, sid):
        return json.loads((self.dir / "sessions" / sid / "session.json").read_text())

    def plan(self, sid):
        return json.loads((self.dir / "sessions" / sid / "plan.json").read_text())

    def snapshot(self):
        js = (self.dir / "data.js").read_text()
        self.assertTrue(js.startswith("window.__hub(") and js.endswith(");\n"), js[:80])
        return json.loads(js[len("window.__hub(") : -3].replace("<\\/", "</"))

    def view(self, sid, fresh=True):
        if fresh:
            dash.regen(self.hub)
        return next(s for s in self.snapshot()["sessions"] if s["id"] == sid)

    def start(self, sid, **kw):
        """Register a Claude session and start a turn."""
        self.hook("SessionStart", sid, source="startup", **kw)
        self.hook("UserPromptSubmit", sid, prompt="Fix the failing reader test")

    def tool(
        self, sid, name="Bash", inp=None, resp=None, tuid=None, failure=False, **kw
    ):
        inp = inp if inp is not None else {"command": "ls"}
        tuid = tuid or f"toolu_{os.urandom(4).hex()}"
        pre = self.hook(
            "PreToolUse", sid, tool_name=name, tool_input=inp, tool_use_id=tuid, **kw
        )
        if failure:
            post = self.hook(
                "PostToolUseFailure",
                sid,
                tool_name=name,
                tool_input=inp,
                tool_use_id=tuid,
                error=resp if isinstance(resp, str) else "failed",
                **kw,
            )
        else:
            post = self.hook(
                "PostToolUse",
                sid,
                tool_name=name,
                tool_input=inp,
                tool_use_id=tuid,
                tool_response=resp
                if resp is not None
                else {"stdout": "", "stderr": ""},
                **kw,
            )
        return pre, post


def perf_limit(budget, margin=3.0):
    """Timing limit for a median: the spec budget times a load margin.

    DASH_PERF_STRICT=1 checks the bare budget (quiet machine); DASH_PERF_SLACK multiplies the
    limit on slow or busy runners. Correctness assertions never depend on this."""
    if os.environ.get("DASH_PERF_STRICT") == "1":
        return budget
    return budget * margin * float(os.environ.get("DASH_PERF_SLACK") or 1)

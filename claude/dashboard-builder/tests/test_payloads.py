"""Live-captured hook payload shapes (primary path) and tolerated variants."""
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from _util import DASH, HOOK, ROOT, HubCase, dash

PAYLOADS = ROOT / "tests" / "payloads"
LIVE = "5d7a0c2e-live-4000-8000-000000000000"


class LiveShapeTests(HubCase):
    def send(self, name, **override):
        p = json.loads(
            (PAYLOADS / f"{name}.json").read_text().replace("{cwd}", str(self.root))
        )
        p.update(override)
        return self.hook(p["hook_event_name"], p["session_id"], raw=json.dumps(p))

    def test_full_live_sequence(self):
        self.send("session_start")
        self.assertEqual(self.view(LIVE)["activity"], "idle")
        self.send("user_prompt_submit")
        self.send("pre_tool_use_bash")
        self.assertEqual(self.view(LIVE)["current"]["summary"], "ls -la")
        self.send("post_tool_use_bash")
        self.send("post_tool_use_read")
        self.send("post_tool_use_failure_bash")
        v = self.view(LIVE)
        tools = [e for e in v["events"] if e["kind"] == "tool"]
        self.assertEqual(
            [(e["tool"], e["ok"], e["duration_ms"]) for e in tools],
            [("Bash", True, 1234), ("Read", True, 12), ("Bash", False, 40)],
        )
        self.assertEqual(tools[0]["detail"], "README.md")
        self.assertEqual(
            tools[2]["detail"],
            "Exit code 1\nls: /nonexistent: No such file or directory",
        )
        self.assertEqual(v["stats"]["failures"], 1)
        self.assertEqual(v["files"][0]["path"], "README.md")
        self.assertNotIn(
            "SECRET-FILE-CONTENT",
            (self.dir / "sessions" / LIVE / "events.jsonl").read_text(),
        )
        self.assertNotIn(
            "SECRET-FILE-CONTENT",
            (self.dir / "sessions" / LIVE / "session.json").read_text(),
        )
        self.send("stop")
        v = self.view(LIVE)
        self.assertEqual(v["activity"], "idle")
        self.assertEqual(v["events"][-1]["detail"], "Done: all tests pass.")
        self.send("session_end")
        self.assertEqual(self.view(LIVE)["activity"], "ended")

    def test_failing_test_run_arrives_as_failure(self):
        self.send("session_start")
        self.send("user_prompt_submit")
        dash.queue_message(self.hub, LIVE, "message", "check the flaky one")
        out = self.send(
            "post_tool_use_failure_bash",
            tool_input={"command": "pytest -q"},
            error="Exit code 1\n..F.\n1 failed, 3 passed in 0.12s",
        )
        self.assertEqual(
            out["hookSpecificOutput"]["hookEventName"], "PostToolUseFailure"
        )
        self.assertIn(
            "check the flaky one", out["hookSpecificOutput"]["additionalContext"]
        )
        t = self.view(LIVE)["tests"][-1]
        self.assertEqual((t["runner"], t["passed"], t["failed"]), ("pytest", 3, 1))


class VariantTests(HubCase):
    SID = "variant-1"

    def setUp(self):
        super().setUp()
        self.start(self.SID)

    def post(self, **kw):
        base = dict(
            tool_name="Bash",
            tool_input={"command": "run"},
            tool_use_id=f"v{time.time_ns()}",
        )
        base.update(kw)
        event = base.pop("event", "PostToolUse")
        return self.hook(event, self.SID, **base)

    def last_tool(self):
        return [e for e in self.view(self.SID)["events"] if e["kind"] == "tool"][-1]

    def test_tool_output_string_and_object(self):
        self.post(tool_output="=== 2 passed in 0.1s ===")
        self.assertEqual(self.view(self.SID)["tests"][-1]["passed"], 2)
        self.post(tool_output={"stdout": "ok", "returncode": 3})
        e = self.last_tool()
        self.assertFalse(e["ok"])
        self.assertTrue(e["detail"].startswith("Exit code 3"))
        self.post(tool_response={"stdout": "fine", "exitCode": 0})
        self.assertTrue(self.last_tool()["ok"])

    def test_prompt_text_and_tool_error(self):
        self.hook("UserPromptSubmit", self.SID, prompt_text="alternate field")
        self.assertEqual(self.view(self.SID)["last_prompt"]["text"], "alternate field")
        self.post(event="PostToolUseFailure", tool_error="Command failed: boom")
        e = self.last_tool()
        self.assertEqual((e["ok"], e["detail"]), (False, "Command failed: boom"))
        self.post(event="PostToolUseFailure", error={"message": "structured"})
        self.assertEqual(self.last_tool()["detail"], "structured")

    def test_missing_optional_fields(self):
        self.assertIsNone(self.hook("Stop", self.SID))  # no stop_hook_active
        self.post(tool_use_id=None, tool_response=None)
        self.assertTrue(self.last_tool()["ok"])
        self.hook("PostToolUse", self.SID, tool_name="Edit")  # no tool_input at all
        self.assertEqual(self.last_tool()["tool"], "Edit")

    def test_notification_types(self):
        self.hook(
            "Notification",
            self.SID,
            message="Claude needs your permission to use Bash",
            notification_type="permission_prompt",
        )
        self.assertEqual(self.view(self.SID)["activity"], "waiting_permission")
        self.hook("Stop", self.SID, stop_hook_active=False)
        self.assertEqual(self.view(self.SID)["activity"], "idle")
        self.hook(
            "Notification",
            self.SID,
            message="Claude is waiting for your input",
            notification_type="idle_prompt",
        )
        v = self.view(self.SID)
        self.assertEqual(
            (v["activity"], v["attention"][-1]["kind"]), ("waiting_user", "idle")
        )
        self.hook(
            "Notification",
            self.SID,
            message="Signed in",
            notification_type="auth_success",
        )
        self.assertEqual(self.view(self.SID)["attention"][-1]["kind"], "notice")
        self.hook("UserPromptSubmit", self.SID, prompt="go")
        self.assertEqual(
            self.view(self.SID)["attention"],
            [
                {
                    "kind": "notice",
                    "text": "Signed in",
                    "ts": self.view(self.SID)["attention"][0]["ts"],
                    "destructive": None,
                }
            ],
        )
        self.hook(
            "Notification",
            self.SID,
            message="Claude needs your permission to use Write",
        )  # no type
        self.assertEqual(self.view(self.SID)["activity"], "waiting_permission")


class BindingHardeningTests(HubCase):
    A, B = (
        "aaaa1111-0000-4000-8000-00000000000a",
        "bbbb2222-0000-4000-8000-00000000000b",
    )

    def test_match_is_anchored_after_dash_py(self):
        self.start(self.A)
        self.start(self.B)
        self.cli("init", "A plan", session=self.A)
        self.hook(
            "PreToolUse",
            self.A,
            tool_name="Bash",
            tool_use_id="x",
            tool_input={"command": f"python3 {DASH} task 1 done --note end"},
        )
        p = self.cli("end", ok=False)  # must not end session A
        self.assertIn("several live sessions", p.stderr)
        self.assertIsNone(self.session(self.A)["ended"])
        toks = dash.shell_tokens(
            f"cd /x && python3 {DASH} log 'hi there' 2>&1 | tail -3"
        )
        self.assertTrue(dash._argv_match(["log", "hi there"], toks))
        self.assertFalse(dash._argv_match(["log"], toks))
        self.assertFalse(dash._argv_match(["hi there"], toks))
        self.assertTrue(
            dash._argv_match(["log", "x"], dash.shell_tokens("$DASH log x"))
        )

    def test_argv_tokens_are_redacted_and_capped(self):
        self.start(self.A)
        cmd = (
            f"mysql --password hunter2 -e 'select 1' && python3 {DASH} log "
            + "y" * 5000
        )
        self.hook(
            "PreToolUse",
            self.A,
            tool_name="Bash",
            tool_input={"command": cmd},
            tool_use_id="s",
        )
        raw = (self.dir / "sessions" / self.A / "session.json").read_text()
        self.assertNotIn("hunter2", raw)
        self.assertNotIn("y" * 301, raw)
        self.assertLess(len(raw), 3000)

    def test_pause_exemption_only_for_pure_dash_commands(self):
        allowed = [
            f"python3 {DASH} inbox",
            f"cd /x && python3 {DASH} log hi 2>&1 | tail -5",
            f"DASH_SESSION=abc python3 {DASH} show",
            f"{DASH} status on_track",
            f"DASH='python3 {DASH}'; $DASH inbox",
        ]
        refused = [
            "make test; echo dash.py",
            f"python3 {DASH} log hi && rm -rf build",
            "cat dash.py",
            f"python3 {DASH} log hi | sh",
            "ls",
        ]
        evil = self.root / "evil" / "dash.py"
        evil.parent.mkdir()
        evil.write_text("")
        refused.append(f"python3 {evil} log hi")
        for c in allowed:
            self.assertTrue(dash.dash_only(c, str(ROOT)), c)
        for c in refused:
            self.assertFalse(dash.dash_only(c, str(ROOT)), c)

    def test_init_inside_claude_session_is_adopted(self):
        env = dict(self.env, CLAUDECODE="1")
        p = self.cli("init", "Plan made before hooks saw the hub", env=env)
        cli_sid = [
            ln.split("=", 1)[1]
            for ln in p.stdout.splitlines()
            if ln.startswith("DASH_SESSION=")
        ][0]
        # The init call's own PostToolUse is the first hook event this session sends to the hub.
        self.hook(
            "PostToolUse",
            self.A,
            tool_name="Bash",
            tool_input={"command": f"python3 {DASH} init x"},
            tool_use_id="i",
            tool_response={"stdout": "ok"},
        )
        self.assertFalse((self.dir / "sessions" / cli_sid).exists())
        self.assertEqual(
            self.plan(self.A)["title"], "Plan made before hooks saw the hub"
        )
        s = self.session(self.A)
        self.assertEqual(
            (s["agent"], s["adopted_from"], s["hooks"]), ("claude", cli_sid, True)
        )
        self.cli(
            "task", "1", "doing", ok=False
        )  # no task 1, but the session resolves (only live one)
        self.cli("log", "via alias", env=dict(self.env, DASH_SESSION=cli_sid))
        self.assertEqual(self.plan(self.A)["log"][-1]["text"], "via alias")
        # A second new Claude session does not adopt anything.
        self.hook("SessionStart", self.B, source="startup")
        self.assertIsNone(self.session(self.B).get("adopted_from"))

    def test_plain_cli_init_is_not_adoptable(self):
        p = self.cli("init", "Codex plan")
        cli_sid = [
            ln.split("=", 1)[1]
            for ln in p.stdout.splitlines()
            if ln.startswith("DASH_SESSION=")
        ][0]
        self.hook("SessionStart", self.A, source="startup")
        self.assertTrue((self.dir / "sessions" / cli_sid).exists())


class AtomicDeliveryTests(HubCase):
    SID = "atomic-1"

    def setUp(self):
        super().setUp()
        self.start(self.SID)
        dash.queue_message(self.hub, self.SID, "message", "do not lose me")

    def status(self):
        return [m["status"] for m in dash.read_inbox(self.dir / "sessions" / self.SID)]

    def test_failure_inside_recording_requeues(self):
        real = dash.atomic_write

        def boom(path, text, mode=0o644):
            if str(path).endswith("session.json"):
                raise OSError("disk full")
            return real(path, text, mode)

        p = self.payload("PostToolUse", self.SID, tool_name="Bash", tool_input={"command": "ls"},
                         tool_use_id="a", tool_response={"stdout": ""})
        with patch.object(dash, "atomic_write", boom):
            with self.assertRaises(OSError):
                dash.hook_output(self.hub, p)
        self.assertEqual(self.status(), ["queued"])
        _, out = self.tool(self.SID)
        self.assertIn("do not lose me", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.status(), ["delivered"])

    def test_failure_after_output_keeps_delivery(self):
        p = self.payload("PostToolUse", self.SID, tool_name="Bash", tool_input={"command": "ls"},
                         tool_use_id="b", tool_response={"stdout": ""})
        with patch.object(dash, "regen", side_effect=OSError("disk full")):
            out, sid, ids = dash.hook_output(self.hub, p)
        self.assertIn("do not lose me", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual((sid, ids), (self.SID, ["m1"]))
        self.assertIn("disk full", (self.dir / "hook-errors.log").read_text())
        self.assertEqual(self.status(), ["delivered"])

    def test_unwritable_stdout_requeues(self):
        self.expect_hook_errors = True
        p = json.dumps(self.payload("PostToolUse", self.SID, tool_name="Bash", tool_input={"command": "ls"},
                                    tool_use_id="c", tool_response={"stdout": ""}))
        r, w = os.pipe()
        os.close(r)  # the reader is gone: writing the output fails with a broken pipe
        proc = subprocess.run([sys.executable, str(HOOK)], input=p.encode(), stdout=w, stderr=subprocess.PIPE,
                              env=self.env, timeout=30)
        os.close(w)
        self.assertEqual((proc.returncode, proc.stderr), (0, b""))
        self.assertEqual(self.status(), ["queued"])


class AmbiguityTests(HubCase):
    A, B = "aaaa1111-0000-4000-8000-00000000000a", "bbbb2222-0000-4000-8000-00000000000b"

    def test_same_command_in_two_sessions_is_refused(self):
        for sid in (self.A, self.B):
            self.start(sid)
            self.cli("init", f"plan {sid[:4]}", session=sid)
            self.hook("PreToolUse", sid, tool_name="Bash", tool_use_id=f"x{sid[:4]}",
                      tool_input={"command": f"python3 {DASH} --dir {self.dir} end"})
        p = self.cli("end", ok=False)
        self.assertIn("in flight in sessions", p.stderr)
        self.assertIsNone(self.session(self.A)["ended"])
        self.assertIsNone(self.session(self.B)["ended"])


class DebounceTests(HubCase):
    def test_insignificant_rebuild_is_skipped_and_flush_scheduled(self):
        dash.regen(self.hub)
        before = (self.dir / "data.js").stat().st_mtime_ns
        with patch.object(dash, "REGEN_DEBOUNCE", 3600), patch.object(dash, "schedule_flush") as flush:
            self.assertFalse(dash.regen(self.hub, significant=False))
            self.assertTrue(dash.regen(self.hub, significant=True))
        flush.assert_called_once()
        self.assertNotEqual((self.dir / "data.js").stat().st_mtime_ns, before)

    def test_pre_tool_use_is_published_by_trailing_flush(self):
        sid = "deb-1"
        self.start(sid)
        self.hook("PreToolUse", sid, tool_name="Bash", tool_input={"command": "sleep 60"}, tool_use_id="d")
        deadline = time.time() + 30
        cur = None
        while time.time() < deadline:
            cur = self.view(sid, fresh=False)["current"]
            if cur:
                break
            time.sleep(0.1)
        self.assertEqual(cur["summary"], "sleep 60")


class RewakeConfirmationTests(HubCase):
    SID = "rw-1"

    def wake(self):
        self.start(self.SID)
        self.hook("Stop", self.SID, stop_hook_active=False)
        dash.queue_message(self.hub, self.SID, "message", "are you there")
        env = dict(self.env, DASH_WATCH_POLL="0.05", DASH_WATCH_LIMIT="5")
        p = subprocess.run(
            [sys.executable, str(HOOK), "--watch-inbox"],
            input=json.dumps(self.payload("Stop", self.SID)),
            text=True,
            capture_output=True,
            env=env,
            timeout=20,
        )
        self.assertEqual(p.returncode, 2, p.stderr)

    def test_unconfirmed_wake_is_redelivered_at_next_prompt(self):
        self.wake()
        self.hook(
            "Notification",
            self.SID,
            message="Claude is waiting for your input",
            notification_type="idle_prompt",
        )
        out = self.hook("UserPromptSubmit", self.SID, prompt="hello?")
        self.assertIn("are you there", out["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.hook("UserPromptSubmit", self.SID, prompt="again"))

    def test_confirmed_wake_is_not_repeated(self):
        self.wake()
        self.hook(
            "PreToolUse",
            self.SID,
            tool_name="Bash",
            tool_input={"command": "ls"},
            tool_use_id="w",
        )
        self.assertIsNone(self.hook("UserPromptSubmit", self.SID, prompt="next"))


class HubPermissionTests(HubCase):
    def test_new_hub_is_private(self):
        self.assertEqual(os.stat(self.dir).st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()

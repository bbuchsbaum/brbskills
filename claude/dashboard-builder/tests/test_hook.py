"""Hook behaviour: registration, activity, binding, delivery, pause, fast path. Fake payloads only."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _util import DASH, HOOK, HubCase, dash, perf_limit

SID = "8f3c2b1a-0000-4000-8000-000000000001"


class RegistrationTests(HubCase):
    def test_session_start_registers_with_title_and_env_file(self):
        envfile = self.root / "claude.env"
        env = dict(self.env, CLAUDE_ENV_FILE=str(envfile))
        self.hook(
            "SessionStart",
            SID,
            env=env,
            source="startup",
            session_title="Fix NOTES",
            model="opus",
        )
        s = self.session(SID)
        self.assertEqual(
            (s["agent"], s["label"], s["cwd"]), ("claude", "Fix NOTES", str(self.root))
        )
        self.assertIn(f"export DASH_SESSION={SID}", envfile.read_text())
        v = self.view(SID)
        self.assertEqual(v["activity"], "idle")
        self.assertEqual(v["short"], "8f3c")
        self.assertIsNone(v["plan"])
        self.assertEqual(v["events"][0]["kind"], "session")

    def test_first_prompt_labels_unnamed_session_and_is_redacted(self):
        self.hook(
            "UserPromptSubmit", SID, prompt="deploy with token=abc123secret please"
        )
        s = self.session(SID)
        self.assertNotIn("abc123secret", json.dumps(s))
        self.assertIn("[REDACTED]", s["last_prompt"]["text"])
        self.assertTrue(s["label"].startswith("deploy with"))
        self.assertNotIn(
            "abc123secret", (self.dir / "sessions" / SID / "events.jsonl").read_text()
        )

    def test_tool_events_stats_files_and_subagents(self):
        self.start(SID)
        f = str(self.root / "R" / "read_vol.R")
        self.tool(SID, "Read", {"file_path": f}, {"file": {"content": "x" * 5000}})
        self.tool(
            SID, "Edit", {"file_path": f, "old_string": "a", "new_string": "b"}, {}
        )
        self.tool(
            SID,
            "Bash",
            {"command": "false"},
            {"stdout": "", "stderr": "boom", "exit_code": 1},
        )
        self.tool(
            SID,
            "Grep",
            {"pattern": "foo"},
            "no matches",
            agent_id="agent-7",
            agent_type="Explore",
        )
        self.tool(
            SID,
            "Bash",
            {"command": "make"},
            "Exit code 2\nmake: *** error",
            failure=True,
        )
        v = self.view(SID)
        self.assertEqual(
            v["stats"],
            {
                "tool_calls": 5,
                "edits": 1,
                "commands": 2,
                "failures": 2,
                "turns": 1,
                "subagents": 1,
                "files_touched": 1,
            },
        )
        self.assertEqual(
            v["files"],
            [
                {
                    "path": "R/read_vol.R",
                    "edits": 1,
                    "reads": 1,
                    "last": v["files"][0]["last"],
                }
            ],
        )
        tools = [e for e in v["events"] if e["kind"] == "tool"]
        self.assertEqual([e["ok"] for e in tools], [True, True, False, True, False])
        self.assertEqual(tools[3]["subagent"], "Explore")
        self.assertEqual(tools[2]["detail"], "Exit code 1\nboom")
        self.assertIn("Exit code 2", tools[4]["detail"])
        self.assertTrue(all(isinstance(e["duration_ms"], int) for e in tools))
        self.assertNotIn(
            "x" * 400, (self.dir / "sessions" / SID / "events.jsonl").read_text()
        )
        self.assertIsNone(v["current"])

    def test_session_end_and_resume(self):
        self.start(SID)
        self.hook("SessionEnd", SID, reason="prompt_input_exit")
        v = self.view(SID)
        self.assertEqual(v["activity"], "ended")
        self.assertIsNotNone(v["ended"])
        self.hook("SessionStart", SID, source="resume")
        self.assertEqual(self.view(SID)["activity"], "idle")

    def test_unknown_event_and_bad_payloads_are_ignored(self):
        self.assertIsNone(self.hook("FutureEvent", SID))
        self.assertFalse((self.dir / "sessions" / SID).exists())
        for raw in [
            "",
            "{",
            "null",
            "[]",
            '{"hook_event_name":"Stop"}',
            '{"hook_event_name":"Stop","session_id":"../x"}',
        ]:
            self.assertIsNone(self.hook("Stop", SID, raw=raw))
        self.assertEqual(os.listdir(self.dir / "sessions"), [])


class ActivityTests(HubCase):
    def test_working_waiting_permission_idle_paused_ended(self):
        self.start(SID)
        self.assertEqual(self.view(SID)["activity"], "working")
        self.hook(
            "PreToolUse",
            SID,
            tool_name="Bash",
            tool_input={"command": "R CMD check --as-cran pkg.tar.gz"},
            tool_use_id="t1",
        )
        v = self.view(SID)
        self.assertEqual(v["current"]["tool"], "Bash")
        self.assertEqual(v["current"]["summary"], "R CMD check --as-cran pkg.tar.gz")
        self.hook(
            "Notification",
            SID,
            message="Claude needs your permission to use Bash",
            notification_type="permission_prompt",
        )
        v = self.view(SID)
        self.assertEqual(v["activity"], "waiting_permission")
        self.assertEqual(v["attention"][0]["kind"], "permission")
        self.hook(
            "PostToolUse",
            SID,
            tool_name="Bash",
            tool_input={"command": "R CMD check"},
            tool_use_id="t1",
            tool_response={"stdout": "Status: OK", "stderr": ""},
        )
        v = self.view(SID)
        self.assertEqual((v["activity"], v["attention"]), ("working", []))
        self.hook("Stop", SID, stop_hook_active=False)
        self.assertEqual(self.view(SID)["activity"], "idle")
        dash.set_paused(self.hub, SID, True)
        dash.regen(self.hub)
        v = self.view(SID)
        self.assertEqual((v["activity"], v["paused"]), ("paused", True))
        dash.set_paused(self.hub, SID, False)
        self.hook("SessionEnd", SID, reason="other")
        self.assertEqual(self.view(SID)["activity"], "ended")

    def test_stalled_and_heartbeat_expiry_derivation(self):
        t = time.time()
        s = dash.new_session("x", agent="claude")
        s.update(
            hooks=True,
            turn="active",
            turn_since=dash.iso(t - 900),
            last_seen=dash.iso(t - 700),
        )
        self.assertEqual(dash.base_activity(s, None, None, t)[0], "stalled")
        s["inflight"] = {"a": {"tool": "Bash", "epoch": t - 700}}
        self.assertEqual(
            dash.base_activity(s, None, None, t)[0], "working"
        )  # long command, not stalled
        s["last_seen"] = dash.iso(t - 7 * 3600)
        act, since = dash.base_activity(s, None, None, t)
        self.assertEqual(act, "ended")
        self.assertAlmostEqual(dash.epoch(since), t - 3600, delta=1)

    def test_waiting_user_with_open_question_after_stop(self):
        t = time.time()
        s = dash.new_session("x", agent="claude")
        s.update(hooks=True, turn="idle")
        plan = {"questions": [{"id": "Q1", "answer": None}]}
        self.assertEqual(dash.base_activity(s, None, plan, t)[0], "waiting_user")
        plan["questions"][0]["answer"] = "yes"
        self.assertEqual(dash.base_activity(s, None, plan, t)[0], "idle")

    def test_narrative_only_session_liveness(self):
        t = time.time()
        s = dash.new_session("codex-1", agent="codex")
        self.assertEqual(dash.base_activity(s, None, None, t)[0], "working")
        s["last_seen"] = dash.iso(t - 1200)
        self.assertEqual(dash.base_activity(s, None, None, t)[0], "idle")


class BindingTests(HubCase):
    SIDS = [
        "aaaa1111-0000-4000-8000-00000000000a",
        "bbbb2222-0000-4000-8000-00000000000b",
        "cccc3333-0000-4000-8000-00000000000c",
    ]

    def test_pending_command_binds_three_concurrent_sessions(self):
        for sid in self.SIDS:
            self.start(sid)
        # Each session is about to run a different dash.py command in its own terminal.
        cmds = {
            self.SIDS[0]: ["init", "Alpha plan", "--task", "A|first"],
            self.SIDS[1]: ["init", "Beta plan", "--goal", "g"],
            self.SIDS[2]: ["init", "Gamma plan"],
        }
        for sid, argv in cmds.items():
            shell = (
                f"cd {self.root} && python3 {DASH} --dir {self.dir} "
                + " ".join(f"'{x}'" if " " in x or "|" in x else x for x in argv)
                + " 2>&1 | tail -5"
            )
            self.hook(
                "PreToolUse",
                sid,
                tool_name="Bash",
                tool_input={"command": shell},
                tool_use_id=f"b-{sid[:4]}",
            )

        def run(sid):
            return self.cli(*cmds[sid])

        with ThreadPoolExecutor(3) as pool:
            results = list(pool.map(run, self.SIDS))
        for r in results:
            self.assertNotIn("DASH_SESSION=", r.stdout)  # bound, no new session
        self.assertEqual(self.plan(self.SIDS[0])["title"], "Alpha plan")
        self.assertEqual(self.plan(self.SIDS[1])["title"], "Beta plan")
        self.assertEqual(self.plan(self.SIDS[2])["title"], "Gamma plan")
        self.assertEqual(sorted(os.listdir(self.dir / "sessions")), sorted(self.SIDS))
        # Later narrative calls bind the same way.
        self.hook(
            "PreToolUse",
            self.SIDS[1],
            tool_name="Bash",
            tool_use_id="b2",
            tool_input={
                "command": f"python3 {DASH} --dir {self.dir} task 1 done; echo ok"
            },
        )
        self.cli(
            "log", "only beta", ok=False
        )  # different argv: no match, three live sessions
        self.hook(
            "PreToolUse",
            self.SIDS[1],
            tool_name="Bash",
            tool_use_id="b3",
            tool_input={"command": f"python3 {DASH} --dir {self.dir} log 'only beta'"},
        )
        self.cli("log", "only beta")
        self.assertEqual(self.plan(self.SIDS[1])["log"][-1]["text"], "only beta")
        self.assertNotIn("only beta", json.dumps(self.plan(self.SIDS[0])))

    def test_stale_pending_command_is_ignored(self):
        for sid in self.SIDS[:2]:
            self.start(sid)
        self.hook(
            "PreToolUse",
            self.SIDS[0],
            tool_name="Bash",
            tool_use_id="x",
            tool_input={"command": f"python3 {DASH} --dir {self.dir} init Old"},
        )
        path = self.dir / "sessions" / self.SIDS[0] / "session.json"
        s = json.loads(path.read_text())
        for e in s["inflight"].values():
            e["epoch"] -= 60
        path.write_text(json.dumps(s))
        p = self.cli("init", "Old")
        self.assertIn("DASH_SESSION=cli-", p.stdout)

    def test_env_and_explicit_session_take_precedence(self):
        self.start(self.SIDS[0])
        self.start(self.SIDS[1])
        self.cli("init", "Via env", env=dict(self.env, DASH_SESSION=self.SIDS[1]))
        self.assertEqual(self.plan(self.SIDS[1])["title"], "Via env")
        self.cli(
            "init",
            "Explicit",
            session=self.SIDS[0],
            env=dict(self.env, DASH_SESSION=self.SIDS[1]),
        )
        self.assertEqual(self.plan(self.SIDS[0])["title"], "Explicit")
        self.cli(
            "log", "claude env", env=dict(self.env, CLAUDE_SESSION_ID=self.SIDS[0])
        )
        self.assertEqual(self.plan(self.SIDS[0])["log"][-1]["text"], "claude env")

    def test_ambiguous_session_fails_with_listing(self):
        self.start(self.SIDS[0])
        self.start(self.SIDS[1])
        p = self.cli("log", "x", ok=False)
        self.assertIn("several live sessions", p.stderr)
        self.assertIn(self.SIDS[0], p.stderr)


class DeliveryTests(HubCase):
    def setUp(self):
        super().setUp()
        self.start(SID)

    def test_post_tool_use_delivers_additional_context(self):
        mid = dash.queue_message(
            self.hub, SID, "message", "Please also run the vignette check"
        )
        self.assertEqual(mid, "m1")
        _, out = self.tool(SID)
        ctx = out["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "PostToolUse")
        self.assertRegex(
            ctx["additionalContext"],
            r"^\[Dashboard message from the user, sent \d\d:\d\d via the local dashboard\] "
            r"Please also run the vignette check$",
        )
        inbox = self.view(SID)["inbox"]
        self.assertEqual(
            (inbox[0]["status"], inbox[0]["via"]), ("delivered", "PostToolUse")
        )
        _, again = self.tool(SID)
        self.assertIsNone(again)

    def test_failure_hook_delivers_too(self):
        dash.queue_message(self.hub, SID, "message", "stop retrying")
        _, out = self.tool(SID, failure=True)
        self.assertEqual(
            out["hookSpecificOutput"]["hookEventName"], "PostToolUseFailure"
        )

    def test_user_prompt_submit_delivers(self):
        self.hook("Stop", SID, stop_hook_active=False)
        dash.queue_message(self.hub, SID, "message", "queued while idle")
        out = self.hook("UserPromptSubmit", SID, prompt="continue")
        self.assertIn(
            "queued while idle", out["hookSpecificOutput"]["additionalContext"]
        )
        self.assertEqual(self.view(SID)["inbox"][0]["via"], "UserPromptSubmit")

    def test_stop_blocks_once_and_not_when_stop_hook_active(self):
        dash.queue_message(self.hub, SID, "message", "one more thing")
        out = self.hook("Stop", SID, stop_hook_active=False)
        self.assertEqual(out["decision"], "block")
        self.assertIn("one more thing", out["reason"])
        self.assertEqual(self.view(SID)["activity"], "working")
        dash.queue_message(self.hub, SID, "message", "late")
        self.assertIsNone(self.hook("Stop", SID, stop_hook_active=True))
        v = self.view(SID)
        self.assertEqual(v["activity"], "idle")
        self.assertEqual(v["inbox"][-1]["status"], "queued")

    def test_answer_resolves_question_and_frames_it(self):
        self.cli("init", "Plan", session=SID)
        self.cli("ask", "Which format?", "--default", "Markdown", session=SID)
        dash.queue_message(self.hub, SID, "answer", "HTML please", "q1")
        q = self.plan(SID)["questions"][0]
        self.assertEqual((q["answer"], q["answered_via"]), ("HTML please", "dashboard"))
        _, out = self.tool(SID)
        self.assertEqual(
            out["hookSpecificOutput"]["additionalContext"],
            '[Dashboard answer from the user to Q1 "Which format?"] HTML please',
        )
        with self.assertRaises(dash.DashError):
            dash.queue_message(self.hub, SID, "answer", "again", "Q1")
        with self.assertRaises(dash.DashError):
            dash.queue_message(self.hub, SID, "answer", "x", "Q9")

    def test_cli_prints_and_marks_delivered(self):
        self.cli("init", "Plan", session=SID)
        dash.queue_message(self.hub, SID, "message", "hello from the page")
        p = self.cli("log", "progress", session=SID)
        self.assertIn("[Dashboard message from the user", p.stdout)
        self.assertIn("hello from the page", p.stdout)
        self.assertEqual(self.view(SID)["inbox"][0]["via"], "cli")
        self.assertNotIn("hello", self.cli("inbox", session=SID).stdout)
        self.cli("send", SID, "via send")
        self.assertIn("via send", self.cli("inbox", session=SID).stdout)

    def test_message_validation(self):
        for kind, text in (
            ("message", ""),
            ("message", "   "),
            ("bogus", "x"),
            ("message", "x" * 5000),
        ):
            with self.assertRaises(dash.DashError):
                dash.queue_message(self.hub, SID, kind, text)
        with self.assertRaises(dash.DashError):
            dash.queue_message(self.hub, "nope", "message", "x")


class PauseTests(HubCase):
    def test_pause_denies_tools_but_allows_dash_py(self):
        self.start(SID)
        dash.set_paused(self.hub, SID, True)
        out = self.hook(
            "PreToolUse",
            SID,
            tool_name="Edit",
            tool_input={"file_path": "a.R"},
            tool_use_id="e1",
        )
        h = out["hookSpecificOutput"]
        self.assertEqual(
            (h["hookEventName"], h["permissionDecision"]), ("PreToolUse", "deny")
        )
        self.assertIn(
            "paused this session from the dashboard", h["permissionDecisionReason"]
        )
        self.assertIn("end your turn", h["permissionDecisionReason"])
        ok = self.hook(
            "PreToolUse",
            SID,
            tool_name="Bash",
            tool_use_id="d1",
            tool_input={"command": f"python3 {DASH} inbox"},
        )
        self.assertIsNone(ok)
        self.assertIsNone(self.hook("Stop", SID, stop_hook_active=False))
        dash.set_paused(self.hub, SID, False)
        self.assertIsNone(
            self.hook(
                "PreToolUse",
                SID,
                tool_name="Edit",
                tool_input={"file_path": "a.R"},
                tool_use_id="e2",
            )
        )


class FastPathTests(unittest.TestCase):
    def test_no_hub_exits_fast_and_silently(self):
        with tempfile.TemporaryDirectory() as d:
            payload = json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "session_id": SID,
                    "cwd": d,
                    "tool_name": "Bash",
                    "tool_input": {"command": "ls"},
                }
            )
            env = {k: v for k, v in os.environ.items() if k != "DASHBOARD_DIR"}
            times = []
            for _ in range(15):
                t0 = time.perf_counter()
                p = subprocess.run(
                    [sys.executable, "-S", str(HOOK)]
                    if False
                    else [sys.executable, str(HOOK)],
                    input=payload,
                    text=True,
                    capture_output=True,
                    env=env,
                    cwd=d,
                )
                times.append(time.perf_counter() - t0)
                self.assertEqual((p.returncode, p.stdout, p.stderr), (0, "", ""))
            self.assertFalse(any(Path(d).iterdir()))
            med = sorted(times)[len(times) // 2]
            print(
                f"\n  hook fast path (no hub): median {med * 1000:.1f} ms, min {min(times) * 1000:.1f} ms",
                file=sys.stderr,
            )
            # The minimum is the intrinsic cost; the median also carries machine load.
            self.assertLess(med, perf_limit(0.060))  # budget 60 ms, see perf_limit


class RobustnessTests(HubCase):
    def test_internal_error_is_logged_not_raised(self):
        self.expect_hook_errors = True
        sd = self.dir / "sessions" / SID
        sd.mkdir(parents=True)
        (sd / "session.json").mkdir()  # unreadable as a file: forces an error path
        (sd / "plan.json").write_text("{")
        out = self.hook("UserPromptSubmit", SID, prompt="x")
        self.assertIsNone(out)
        self.assertIn("Traceback", (self.dir / "hook-errors.log").read_text())

    def test_error_log_is_bounded(self):
        self.expect_hook_errors = True
        log = self.dir / "hook-errors.log"
        log.write_text("x" * 200_000)
        sd = self.dir / "sessions" / SID
        sd.mkdir(parents=True)
        (sd / "session.json").mkdir()
        self.hook("Stop", SID)
        self.assertLess(log.stat().st_size, 80_000)

    def test_parallel_hooks_and_cli_lose_nothing(self):
        self.start(SID)
        self.cli("init", "Parallel", session=SID)

        def fire(i):
            if i % 4 == 0:
                return self.cli("log", f"note {i}", session=SID).returncode
            inp = {"command": f"echo {i}"}
            p = subprocess.run(
                [sys.executable, str(HOOK)],
                text=True,
                capture_output=True,
                env=self.env,
                input=json.dumps(
                    self.payload(
                        "PostToolUse",
                        SID,
                        tool_name="Bash",
                        tool_input=inp,
                        tool_use_id=f"p{i}",
                        tool_response={"stdout": str(i)},
                    )
                ),
            )
            return p.returncode

        with ThreadPoolExecutor(20) as pool:
            codes = list(pool.map(fire, range(40)))
        self.assertEqual(set(codes), {0})
        s = self.session(SID)
        self.assertEqual(s["stats"]["tool_calls"], 30)
        lines = (self.dir / "sessions" / SID / "events.jsonl").read_text().splitlines()
        evs = [json.loads(x) for x in lines]
        ids = [e["id"] for e in evs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(sum(e["kind"] == "tool" for e in evs), 30)
        self.assertEqual(
            sum(e["kind"] == "note" and e["summary"].startswith("note ") for e in evs),
            10,
        )
        self.assertEqual(
            len([x for x in self.plan(SID)["log"] if x["text"].startswith("note ")]), 10
        )
        dash.regen(self.hub)
        snap = self.snapshot()
        self.assertEqual(snap["sessions"][0]["stats"]["tool_calls"], 30)

    def test_event_rotation_keeps_tail(self):
        self.start(SID)
        s = self.session(SID)
        s["events_in_file"] = dash.EVENTS_ROTATE
        (self.dir / "sessions" / SID / "session.json").write_text(json.dumps(s))
        self.tool(SID)
        sd = self.dir / "sessions" / SID
        self.assertTrue((sd / "events.1.jsonl").exists())
        ids = [e["id"] for e in self.view(SID)["events"]]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(ids[0], 1)


class WakeableTests(HubCase):
    def test_flag_follows_the_watcher(self):
        self.start(SID)
        self.hook("Stop", SID, stop_hook_active=False)
        self.assertIsNone(self.view(SID)["wakeable"])  # no watcher record: unknown
        env = dict(self.env, DASH_WATCH_POLL="0.1", DASH_WATCH_LIMIT="3")
        p = subprocess.Popen(
            [sys.executable, str(HOOK), "--watch-inbox"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        p.stdin.write(json.dumps(self.payload("Stop", SID)))
        p.stdin.close()
        deadline = time.time() + 30
        while time.time() < deadline and not self.view(SID)["wakeable"]:
            time.sleep(0.05)
        self.assertIs(self.view(SID)["wakeable"], True)
        self.assertIs(
            self.snapshot()["sessions"][0]["wakeable"], True
        )  # data.js was rebuilt too
        self.assertEqual(p.wait(timeout=30), 0)  # limit reached, nothing queued
        self.assertFalse((self.dir / "sessions" / SID / "watch.json").exists())
        self.assertIsNone(self.view(SID)["wakeable"])

    def test_stale_or_dead_watcher_and_unwakeable_sessions(self):
        self.start(SID)
        self.hook("Stop", SID, stop_hook_active=False)
        w = self.dir / "sessions" / SID / "watch.json"
        w.write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "started": dash.now(),
                    "heartbeat": dash.now(),
                    "poll": 2,
                }
            )
        )
        self.assertIs(self.view(SID)["wakeable"], True)
        w.write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "started": dash.now(),
                    "heartbeat": dash.iso(time.time() - 60),
                    "poll": 2,
                }
            )
        )
        self.assertIs(self.view(SID)["wakeable"], False)
        dead = subprocess.run(
            [sys.executable, "-c", "import os; print(os.getpid())"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        w.write_text(
            json.dumps(
                {
                    "pid": int(dead),
                    "started": dash.now(),
                    "heartbeat": dash.now(),
                    "poll": 2,
                }
            )
        )
        self.assertIs(self.view(SID)["wakeable"], False)
        codex = self.cli("join", "--agent", "codex").stdout.strip()
        self.assertIs(self.view(codex)["wakeable"], False)
        self.hook("SessionEnd", SID, reason="other")
        self.assertIs(self.view(SID)["wakeable"], False)


class WatchInboxTests(HubCase):
    def watch(self, env_extra=None):
        env = dict(self.env, DASH_WATCH_POLL="0.1", DASH_WATCH_LIMIT="5")
        env.update(env_extra or {})
        p = subprocess.Popen(
            [sys.executable, str(HOOK), "--watch-inbox"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.stderr.close)
        return p

    def test_wakes_idle_session_with_exit_2(self):
        self.start(SID)
        self.hook("Stop", SID, stop_hook_active=False)
        p = self.watch()
        p.stdin.write(json.dumps(self.payload("Stop", SID, stop_hook_active=False)))
        p.stdin.close()
        time.sleep(0.5)
        dash.queue_message(self.hub, SID, "message", "wake up")
        rc = p.wait(timeout=10)
        err = p.stderr.read()
        self.assertEqual(rc, 2)
        self.assertIn("wake up", err)
        self.assertEqual(self.view(SID)["inbox"][0]["via"], "rewake")

    def rewoken(self, text):
        self.start(SID)
        self.hook("Stop", SID, stop_hook_active=False)
        p = self.watch()
        p.stdin.write(json.dumps(self.payload("Stop", SID, stop_hook_active=False)))
        p.stdin.close()
        time.sleep(0.5)
        dash.queue_message(self.hub, SID, "message", text)
        self.assertEqual(p.wait(timeout=10), 2)
        return p.stderr.read()

    def test_wake_turn_prompt_is_not_a_failed_wake(self):
        # Claude Code 2.1.286 starts the wake-up turn with a synthetic prompt carrying the hook output.
        err = self.rewoken("run echo once")
        prompt = (
            "<task-notification> <summary>Stop hook feedback</summary> </task-notification> "
            f'<system-reminder> Stop hook blocking error from command "Stop": {err} </system-reminder>'
        )
        out = self.hook("UserPromptSubmit", SID, prompt=prompt)
        self.assertIsNone(out)
        events = [e["summary"] for e in self.view(SID)["events"]]
        self.assertFalse(any(x.startswith("Redelivered") for x in events), events)

    def test_typed_prompt_after_failed_wake_redelivers(self):
        self.rewoken("run echo once")
        out = self.hook("UserPromptSubmit", SID, prompt="hello again")
        self.assertIn("run echo once", out["hookSpecificOutput"]["additionalContext"])

    def test_exits_quietly_when_turn_starts_or_limit(self):
        self.start(SID)
        self.hook("Stop", SID, stop_hook_active=False)
        p = self.watch()
        p.stdin.write(json.dumps(self.payload("Stop", SID)))
        p.stdin.close()
        time.sleep(0.4)
        self.hook("UserPromptSubmit", SID, prompt="next")
        self.assertEqual(p.wait(timeout=10), 0)
        p = self.watch({"DASH_WATCH_LIMIT": "0.5"})
        self.hook("Stop", SID, stop_hook_active=False)
        p.stdin.write(json.dumps(self.payload("Stop", SID)))
        p.stdin.close()
        self.assertEqual(p.wait(timeout=10), 0)


if __name__ == "__main__":
    unittest.main()

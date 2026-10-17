"""Offline transport and lifecycle tests; never invoke real Codex or crontab."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/wakeup.py"
SPEC = importlib.util.spec_from_file_location("wakeup", SCRIPT)
wakeup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wakeup)
THREAD = "00000000-0000-0000-0000-000000000001"


class WakeupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="wakeup test % ")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / "state"
        self.project = self.base / "project"
        self.project.mkdir()
        self.prompt = self.base / "prompt.txt"
        self.prompt.write_text("Continue ticket ONE only. Literal $(touch NO) `uname` ' %\nSecond line.")
        self.receipt = self.base / "receipt.jsonl"
        self.mode = self.base / "mode"
        self.mode.write_text("success")
        self.codex = self.base / "fake codex"
        self.codex.write_text(f"""#!{sys.executable}
import json, os, sys, time
from pathlib import Path
if sys.argv[1:] == ['queue', '--help']:
    print('queue --thread --message')
    sys.exit(0)
with Path({str(self.receipt)!r}).open('a') as output:
    output.write(json.dumps(dict(argv=sys.argv[1:], cwd=os.getcwd(),
        home=os.environ['HOME'], codex_home=os.environ['CODEX_HOME'], pid=os.getpid())) + '\\n')
mode = Path({str(self.mode)!r}).read_text()
if mode == 'slow': time.sleep(0.7)
print('PRIVATE OUTPUT MUST NOT BE LOGGED')
sys.exit(7 if mode == 'fail' else 0)
""")
        self.codex.chmod(0o700)
        self.args = ["--state-root", str(self.root), "--thread", THREAD]
        self.call("init", "--project", str(self.project), "--prompt", str(self.prompt),
                  "--codex", str(self.codex), "--hours", "1", "--codex-home", str(self.base / "codex home"))

    def call(self, *args):
        return wakeup.main(self.args + list(args))

    def state(self):
        return wakeup.read(self.root / THREAD, THREAD)

    def receipts(self):
        return [json.loads(line) for line in self.receipt.read_text().splitlines()] if self.receipt.exists() else []

    def send(self):
        self.call("enable")
        return self.call("tick")

    def test_disabled_initialization_and_no_overwrite(self):
        self.assertEqual(self.call("tick"), {"skipped": "disabled"})
        self.assertEqual(self.receipts(), [])
        with self.assertRaisesRegex(ValueError, "already configured"):
            self.call("init", "--project", str(self.project), "--prompt", str(self.prompt), "--hours", "1")

    def test_literal_delivery_to_exact_thread_with_pinned_environment(self):
        self.send()
        receipt, = self.receipts()
        self.assertEqual(receipt["argv"][:6], ["-C", str(self.project.resolve()), "queue", "--thread", THREAD, "--message"])
        self.assertIn(self.prompt.read_text(), receipt["argv"][6])
        self.assertEqual(receipt["cwd"], str(self.project.resolve()))
        self.assertEqual(receipt["codex_home"], str((self.base / "codex home").resolve()))
        self.assertFalse((self.project / "NO").exists())
        self.assertNotIn("PRIVATE OUTPUT", (self.root / THREAD / "state.json").read_text())

    def test_repeated_ticks_coalesce_until_end_acknowledgement(self):
        pending = self.send()
        for _ in range(3):
            self.assertEqual(self.call("tick")["skipped"], "outstanding")
        self.assertEqual(len(self.receipts()), 1)
        self.call("finish", "--token", pending["token"], "--outcome", "continue")
        self.assertEqual(self.call("tick")["skipped"], "cooldown")
        with patch.object(wakeup.time, "time", return_value=time.time() + 301):
            self.call("tick")
        self.assertEqual(len(self.receipts()), 2)
        self.assertNotEqual(self.state()["pending"]["token"], pending["token"])

    def test_stale_token_cannot_clear_new_attempt(self):
        self.send()
        before = self.state()
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.call("finish", "--token", "wrong", "--outcome", "continue")
        self.assertEqual(self.state(), before)

    def test_disable_preserves_pending_and_finish_cannot_reenable(self):
        pending = self.send()
        self.call("disable")
        self.assertEqual(self.call("tick")["skipped"], "disabled")
        self.assertEqual(self.state()["pending"], pending)
        with self.assertRaisesRegex(ValueError, "outstanding"):
            self.call("enable")
        self.call("finish", "--token", pending["token"], "--outcome", "continue")
        self.assertFalse(self.state()["enabled"])

    def test_terminal_outcomes_stop(self):
        for outcome in ("stop", "blocked"):
            with self.subTest(outcome=outcome):
                self.call("enable")
                with patch.object(wakeup.time, "time", return_value=time.time() + 301):
                    pending = self.call("tick")
                self.call("finish", "--token", pending["token"], "--outcome", outcome)
                self.assertFalse(self.state()["enabled"])

    def test_expiry_blocks_submission_and_enable(self):
        self.call("enable")
        with patch.object(wakeup.time, "time", return_value=time.time() + 3601):
            self.assertTrue(self.call("status")["expired"])
            self.assertEqual(self.call("tick")["skipped"], "expired")
            with self.assertRaisesRegex(ValueError, "expired"):
                self.call("enable")
        self.assertEqual(self.receipts(), [])

    def test_renew_leaves_disabled_and_rejects_outstanding(self):
        self.send()
        with self.assertRaisesRegex(ValueError, "outstanding"):
            self.call("renew", "--hours", "2")
        token = self.state()["pending"]["token"]
        self.call("finish", "--token", token, "--outcome", "stop")
        self.call("renew", "--hours", "2")
        self.assertFalse(self.state()["enabled"])
        self.assertGreater(self.state()["expires_at"], time.time() + 7000)

    def test_nonzero_is_uncertain_and_never_retried(self):
        self.mode.write_text("fail")
        pending = self.send()
        self.assertEqual(pending["status"], "uncertain")
        self.assertEqual(pending["returncode"], 7)
        self.assertEqual(self.call("tick")["skipped"], "outstanding")
        self.assertEqual(len(self.receipts()), 1)

    def test_timeout_is_uncertain_and_recovery_leaves_disabled(self):
        self.mode.write_text("slow")
        state = self.state()
        state["timeout"] = 0.1
        wakeup.save(self.root / THREAD, state)
        pending = self.send()
        self.assertEqual(pending["error"], "TimeoutExpired")
        self.assertEqual(self.call("tick")["skipped"], "outstanding")
        self.call("recover", "--token", pending["token"], "--confirmed-not-pending")
        self.assertIsNone(self.state()["pending"])
        self.assertFalse(self.state()["enabled"])

    def test_crash_after_reservation_does_not_resend(self):
        self.call("enable")
        with patch.object(wakeup.subprocess, "run", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.call("tick")
        self.assertEqual(self.state()["pending"]["status"], "submitting")
        self.assertEqual(self.call("tick")["skipped"], "outstanding")
        self.assertEqual(self.receipts(), [])

    def test_two_real_processes_do_not_submit_concurrently(self):
        self.mode.write_text("slow")
        self.call("enable")
        command = [sys.executable, str(SCRIPT)] + self.args + ["tick"]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: first.poll() is None and first.kill())
        deadline = time.monotonic() + 5
        while not self.receipt.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(self.receipt.exists())
        second = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(json.loads(second.stdout)["skipped"], "submission-locked")
        output, error = first.communicate(timeout=5)
        self.assertEqual(first.returncode, 0, error)
        self.assertEqual(json.loads(output)["status"], "accepted")
        self.assertEqual(len(self.receipts()), 1)

    def test_corrupt_state_does_not_send(self):
        (self.root / THREAD / "state.json").write_text("{broken")
        with self.assertRaises(ValueError):
            self.call("tick")
        self.assertEqual(self.receipts(), [])

    def test_malformed_lifecycle_fields_fail_closed(self):
        original = self.state()
        for field, value in (("enabled", "false"), ("pending", {}), ("expires_at", "soon")):
            with self.subTest(field=field):
                wakeup.save(self.root / THREAD, original | {field: value})
                with self.assertRaises(ValueError):
                    self.call("tick")
        self.assertEqual(self.receipts(), [])

    def test_status_during_submission_and_busy_mutations(self):
        with wakeup.locked(self.root / THREAD):
            self.assertFalse(self.call("status")["enabled"])
            self.assertEqual(self.call("tick")["skipped"], "submission-locked")
            with self.assertRaisesRegex(RuntimeError, "busy"):
                self.call("disable")

    def test_failed_reservation_write_never_submits(self):
        self.call("enable")
        with patch.object(wakeup.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.call("tick")
        self.assertEqual(self.receipts(), [])
        self.assertIsNone(self.state()["pending"])

    def test_missing_binary_stays_reserved(self):
        self.codex.unlink()
        pending = self.send()
        self.assertEqual(pending["status"], "uncertain")
        self.assertEqual(pending["error"], "FileNotFoundError")
        self.assertEqual(self.call("tick")["skipped"], "outstanding")

    def test_expiry_preserves_pending_receipt(self):
        pending = self.send()
        with patch.object(wakeup.time, "time", return_value=time.time() + 3601):
            self.call("tick")
        self.assertEqual(self.state()["pending"], pending)
        self.assertFalse(self.state()["enabled"])

    def test_distinct_threads_are_independent(self):
        self.send()
        first_args = self.args
        self.args = ["--state-root", str(self.root), "--thread", "00000000-0000-0000-0000-000000000002"]
        self.call("init", "--project", str(self.project), "--prompt", str(self.prompt),
                  "--codex", str(self.codex), "--hours", "1")
        self.send()
        self.call("disable")
        self.args = first_args
        self.assertTrue(self.state()["enabled"])
        self.assertEqual(len(self.receipts()), 2)
        self.assertNotEqual(self.receipts()[0]["argv"][4], self.receipts()[1]["argv"][4])

    def test_symlinked_or_public_state_root_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "private"):
            wakeup.main(["--state-root", str(alias), "--thread", THREAD, "status"])
        self.root.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "private"):
            self.call("tick")

    def test_status_does_not_expose_prompt(self):
        self.assertNotIn(self.prompt.read_text(), json.dumps(self.call("status")))

    def test_cron_quotes_paths_and_escapes_percent(self):
        line = self.call("cron-line")["cron"]
        self.assertTrue(line.startswith("*/5 * * * * "))
        self.assertIn(r"\%", line)
        command = line.split(" * * * * ", 1)[1].split(" >/dev/null", 1)[0].replace(r"\%", "%")
        parsed = shlex.split(command)
        self.assertEqual(parsed[-5:], ["--state-root", str(self.root), "--thread", THREAD, "tick"])

    def test_cron_replacement_is_idempotent_and_preserves_other_jobs(self):
        unrelated = "SHELL=/bin/sh\n# other job\n1 * * * * echo hello\n"
        entry = self.call("cron-line")["cron"]
        original = unrelated + entry + "\n" + entry + "\n"
        changed = wakeup.replace_cron(original, entry, THREAD)
        self.assertEqual(changed, unrelated + entry + "\n")
        self.assertEqual(wakeup.replace_cron(changed, entry, THREAD), changed)
        self.assertEqual(wakeup.replace_cron(changed, None, THREAD), unrelated)

    def test_crontab_read_error_never_installs(self):
        failed = subprocess.CompletedProcess([], 1, "", "permission denied")
        with patch.object(wakeup.subprocess, "run", return_value=failed) as run:
            with self.assertRaisesRegex(RuntimeError, "left it unchanged"):
                self.call("install", "--apply")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], ["crontab", "-l"])

    def test_crontab_change_aborts_without_write(self):
        with patch.object(wakeup, "crontab_read", side_effect=["old\n", "new\n"]):
            with patch.object(wakeup.subprocess, "run") as run:
                with self.assertRaisesRegex(RuntimeError, "changed during edit"):
                    self.call("install", "--apply")
                run.assert_not_called()

    def test_install_preview_does_not_mutate(self):
        with patch.object(wakeup, "crontab_read", return_value="old\n"):
            with patch.object(wakeup.subprocess, "run") as run:
                result = self.call("install")
                run.assert_not_called()
        self.assertFalse(result["apply"])
        self.assertFalse(self.state()["enabled"])

    def test_remove_disables_even_if_cron_unavailable(self):
        self.call("enable")
        with patch.object(wakeup, "crontab_read", side_effect=RuntimeError("unavailable")):
            with self.assertRaises(RuntimeError):
                self.call("remove", "--apply")
        self.assertFalse(self.state()["enabled"])

    def test_successful_install_verifies_readback(self):
        after = self.call("cron-line")["cron"] + "\n"
        with patch.object(wakeup, "crontab_read", side_effect=["", "", after]):
            with patch.object(wakeup.subprocess, "run") as run:
                self.call("install", "--apply")
                self.assertEqual(run.call_args.kwargs["input"], after)
        self.assertFalse(self.state()["enabled"])


if __name__ == "__main__":
    unittest.main()

"""install-hooks on temp settings files only; never the real ~/.claude."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _util import DASH, dash

EXISTING = {
    "model": "opus",
    "permissions": {"allow": ["Bash(ls:*)"]},
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [{"type": "command", "command": "~/bin/guard.sh"}],
            }
        ],
        "Stop": [{"hooks": [{"type": "command", "command": "say done"}]}],
    },
}


class InstallHooksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.settings = self.home / "settings.json"
        self.settings.write_text(json.dumps(EXISTING, indent=2))

    def run_cmd(self, *args, ok=True):
        p = subprocess.run(
            [
                sys.executable,
                str(DASH),
                "install-hooks",
                "--settings",
                str(self.settings),
                *args,
            ],
            capture_output=True,
            text=True,
            cwd=self.home,
            env={"HOME": str(self.home), "PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(p.returncode == 0, ok, p.stderr)
        return p

    def ours(self, s):
        return [
            (ev, g.get("matcher"), h)
            for ev, groups in s.get("hooks", {}).items()
            for g in groups
            for h in g["hooks"]
            if "dash_hook.py" in h["command"]
        ]

    def test_install_is_idempotent_and_preserves_existing(self):
        self.run_cmd()
        s = json.loads(self.settings.read_text())
        self.assertEqual(s["model"], "opus")
        self.assertEqual(s["permissions"], EXISTING["permissions"])
        self.assertIn(
            {
                "matcher": "Write|Edit",
                "hooks": [{"type": "command", "command": "~/bin/guard.sh"}],
            },
            s["hooks"]["PreToolUse"],
        )
        self.assertIn(
            {"hooks": [{"type": "command", "command": "say done"}]}, s["hooks"]["Stop"]
        )
        ours = self.ours(s)
        self.assertEqual(sorted(ev for ev, _, _ in ours), sorted(dash.HOOK_EVENTS))
        for ev, matcher, h in ours:
            self.assertEqual(matcher, "*" if ev in dash.TOOL_EVENTS else None)
            self.assertEqual((h["type"], h["timeout"]), ("command", 10))
            self.assertIn(str(Path(DASH).parent / "dash_hook.py"), h["command"])
        backups = list(self.home.glob("settings.json.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), EXISTING)
        before = self.settings.read_text()
        p = self.run_cmd()
        self.assertIn("already up to date", p.stdout)
        self.assertEqual(self.settings.read_text(), before)
        self.assertEqual(len(list(self.home.glob("settings.json.bak-*"))), 1)

    def test_rewake_and_uninstall(self):
        self.run_cmd("--with-rewake")
        s = json.loads(self.settings.read_text())
        rewake = [h for ev, _, h in self.ours(s) if "--watch-inbox" in h["command"]]
        self.assertEqual(len(rewake), 1)
        self.assertEqual((rewake[0]["async"], rewake[0]["asyncRewake"]), (True, True))
        self.run_cmd()  # reinstall without rewake removes it
        self.assertFalse(
            [
                h
                for _, _, h in self.ours(json.loads(self.settings.read_text()))
                if "--watch-inbox" in h["command"]
            ]
        )
        self.run_cmd("--uninstall")
        self.assertEqual(json.loads(self.settings.read_text()), EXISTING)

    def test_dry_run_shows_only_our_entries(self):
        s = dict(EXISTING, env={"ANTHROPIC_API_KEY": "sk-secret-value-123"})
        self.settings.write_text(json.dumps(s))
        before = self.settings.read_text()
        p = self.run_cmd("--dry-run", "--with-rewake")
        self.assertEqual(self.settings.read_text(), before)
        self.assertNotIn("sk-secret", p.stdout + p.stderr)
        self.assertNotIn("guard.sh", p.stdout)
        self.assertNotIn("opus", p.stdout)
        out = json.loads(p.stdout)
        self.assertEqual(set(out), {"settings", "add", "remove"})
        self.assertEqual(len(out["add"]), len(dash.HOOK_EVENTS) + 1)
        self.assertEqual(out["remove"], [])
        self.assertTrue(all("dash_hook.py" in x["hook"]["command"] for x in out["add"]))
        self.run_cmd("--with-rewake")
        out = json.loads(self.run_cmd("--dry-run").stdout)  # dropping rewake: one removal
        self.assertEqual(out["add"], [])
        self.assertEqual([x["event"] for x in out["remove"]], ["Stop"])
        self.assertIn("--watch-inbox", out["remove"][0]["hook"]["command"])
        out = json.loads(self.run_cmd("--dry-run", "--uninstall").stdout)
        self.assertEqual(len(out["remove"]), len(dash.HOOK_EVENTS) + 1)

    def test_status(self):
        p = self.run_cmd("--status", ok=False)
        self.assertIn("installed: no", p.stdout)
        self.assertNotIn("guard.sh", p.stdout)
        self.run_cmd()
        p = self.run_cmd("--status")
        self.assertIn("installed: yes", p.stdout)
        self.assertIn("events: " + ", ".join(dash.HOOK_EVENTS), p.stdout)
        self.assertIn("rewake: off", p.stdout)
        here = str(Path(DASH).resolve().parent / "dash_hook.py")
        self.assertIn(f"script: {here} (this installation)", p.stdout)
        self.run_cmd("--with-rewake")
        self.assertIn("rewake: on", self.run_cmd("--status").stdout)
        s = json.loads(self.settings.read_text())
        del s["hooks"]["Notification"]
        self.settings.write_text(json.dumps(s))
        p = self.run_cmd("--status", ok=False)
        self.assertIn("installed: partial", p.stdout)
        self.assertIn("missing: Notification", p.stdout)
        s["hooks"]["Stop"][-1]["hooks"][0]["command"] = "python3 /gone/scripts/dash_hook.py"
        self.settings.write_text(json.dumps(s))
        self.assertIn("/gone/scripts/dash_hook.py (missing file)", self.run_cmd("--status", ok=False).stdout)

    def test_hook_command_points_at_resolved_install(self):
        link = self.home / "skills" / "dashboard-builder"
        link.parent.mkdir()
        link.symlink_to(Path(DASH).resolve().parent.parent)
        p = subprocess.run([sys.executable, str(link / "scripts" / "dash.py"), "install-hooks", "--settings",
                            str(self.settings), "--dry-run"], capture_output=True, text=True,
                           env={"HOME": str(self.home), "PATH": "/usr/bin:/bin"})
        cmds = {x["hook"]["command"] for x in json.loads(p.stdout)["add"]}
        self.assertEqual({dash._hook_script(c) for c in cmds}, {str(Path(DASH).resolve().parent / "dash_hook.py")})

    def test_missing_file(self):
        self.settings.unlink()
        self.run_cmd()
        self.assertEqual(
            len(self.ours(json.loads(self.settings.read_text()))), len(dash.HOOK_EVENTS)
        )
        self.assertEqual(list(self.home.glob("settings.json.bak-*")), [])

    def test_symlinked_settings_stay_a_symlink(self):
        real = self.home / "dotfiles" / "settings.json"
        real.parent.mkdir()
        self.settings.rename(real)
        self.settings.symlink_to(real)
        self.run_cmd()
        self.assertTrue(self.settings.is_symlink())
        self.assertEqual(len(self.ours(json.loads(real.read_text()))), len(dash.HOOK_EVENTS))

    def test_invalid_settings_are_not_touched(self):
        self.settings.write_text("{ broken")
        p = self.run_cmd(ok=False)
        self.assertIn("not valid JSON", p.stderr)
        self.assertEqual(self.settings.read_text(), "{ broken")
        self.settings.write_text('{"hooks": []}')
        self.run_cmd(ok=False)


if __name__ == "__main__":
    unittest.main()

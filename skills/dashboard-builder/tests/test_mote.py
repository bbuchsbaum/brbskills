"""Mote integration against a throwaway store (skipped without the mote CLI) and a fake CLI."""
import json
import os
import shutil
import stat
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from _util import DASH, HubCase, dash

MOTE = shutil.which("mote")


@unittest.skipUnless(MOTE, "mote CLI not on PATH")
class RealMoteTests(HubCase):
    def setUp(self):
        super().setUp()
        self.env["MOTE_ACTOR"] = "tester"
        self.mote("init")
        self.bead = self.mote("new", "Fix reader").strip()
        self.mote("new", "Ready work", "--tag", "m1").strip()
        self.mote("set", self.bead, "status=doing")
        self.mote("reserve", "--issue", self.bead, "R/shared.R")
        self.mote("discuss", "post", "--topic", "perf", "Benchmark is 3x faster")

    def mote(self, *args):
        p = subprocess.run(
            [MOTE, *args],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_fetch_shapes(self):
        snap = dash.mote_fetch(self.root / ".mote", MOTE, timeout=10)
        self.assertIsNone(snap["error"])
        self.assertEqual(
            snap["counts"], {"open": 1, "doing": 1, "blocked": 0, "review": 0}
        )
        self.assertEqual([b["id"] for b in snap["doing"]], [self.bead])
        self.assertEqual([b["title"] for b in snap["ready"]], ["Ready work"])
        self.assertEqual(snap["ready"][0]["tags"], ["m1"])
        r = snap["reservations"][0]
        self.assertEqual(
            (r["actor"], r["paths"], r["issue"]), ("tester", ["R/shared.R"], self.bead)
        )
        self.assertIsNotNone(dash.epoch(r["expires"]))
        self.assertLess(abs(dash.epoch(r["created"]) - time.time()), 120)  # decoded from the reservation id
        self.assertLess(dash.epoch(r["created"]), dash.epoch(r["expires"]))
        self.assertEqual(snap["actors"][0]["actor"], "tester")
        self.assertEqual(
            (
                snap["posts"][0]["topic"],
                snap["posts"][0]["excerpt"],
                snap["posts"][0]["replies"],
            ),
            ("perf", "Benchmark is 3x faster", 0),
        )

    def test_refresh_snapshot_and_conflict_annotation(self):
        with patch.dict(os.environ, {"MOTE_ACTOR": "tester"}):
            self.assertTrue(dash.mote_refresh(self.hub))
            self.assertFalse(
                dash.mote_refresh(self.hub)
            )  # fresh cache: no second fetch
        for sid in ("aaaa-1", "bbbb-2"):
            self.start(sid)
            self.tool(sid, "Edit", {"file_path": str(self.root / "R" / "shared.R")}, {})
        snap = dash.build_snapshot(self.hub)
        self.assertEqual(snap["mote"]["store"], str(self.root / ".mote"))
        c = snap["conflicts"][0]
        self.assertEqual((c["path"], c["sources"], c["mote_reserved_by"]), ("R/shared.R", ["edit", "reservation"], "tester"))
        self.assertEqual(sorted(c["sessions"]), ["aaaa", "bbbb"])
        self.assertIn(("tester", "reservation"), [(d["session"], d["kind"]) for d in c["detail"]])

    def test_post_mentions_are_cached_privately(self):
        (self.root / "R").mkdir(exist_ok=True)
        (self.root / "R" / "shared.R").write_text("")
        self.mote("discuss", "post", "--topic", "perf", "I am rewriting R/shared.R and docs/missing.md today")
        snap = dash.mote_fetch(self.root / ".mote", MOTE, timeout=10)
        self.assertEqual(snap["_mentions"][0]["paths"], ["R/shared.R", "docs/missing.md"])

    def test_background_refresh_from_cli(self):
        self.cli("init", "Mote plan", session="cli-mote0001")
        deadline = time.time() + 30
        while time.time() < deadline and not (self.dir / "mote.json").exists():
            time.sleep(0.1)
        self.assertTrue(
            (self.dir / "mote.json").exists(),
            "background refresh never wrote mote.json",
        )
        deadline = time.time() + 30
        while time.time() < deadline and dash.build_snapshot(self.hub)["mote"] is None:
            time.sleep(0.1)
        self.assertEqual(dash.build_snapshot(self.hub)["mote"]["counts"]["doing"], 1)

    def test_post_through_server(self):
        import http.client

        self.cli("join", "--agent", "cli")
        url = self.cli("serve", env=self.env).stdout.strip()
        self.addCleanup(lambda: self.cli("stop"))
        port, token = int(url.split(":")[2].split("/")[0]), url.split("#k=")[1]

        def post(body):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
            data = json.dumps(body).encode()
            c.request(
                "POST",
                "/api/mote/post",
                body=data,
                headers={
                    "Host": f"127.0.0.1:{port}",
                    "X-Dash-Token": token,
                    "Content-Type": "application/json",
                },
            )
            r = c.getresponse()
            out = json.loads(r.read())
            c.close()
            return r.status, out

        code, out = post({"topic": "general", "text": "-- not a flag; $(rm -rf /)"})
        self.assertEqual(code, 200, out)
        self.assertTrue(out["id"].startswith("post-"))
        listing = json.loads(self.mote("discuss", "list", "--json"))
        self.assertIn("-- not a flag; $(rm -rf /)", [p["body"] for p in listing])
        self.assertEqual(post({"topic": "bad topic!", "text": "x"})[0], 400)
        self.assertEqual(post({"text": ""})[0], 400)


class FakeMoteTests(HubCase):
    def fake(self, body):
        bindir = self.root.parent / "bin"
        bindir.mkdir(exist_ok=True)
        f = bindir / "mote"
        f.write_text("#!/bin/sh\n" + body + "\n")
        f.chmod(f.stat().st_mode | stat.S_IEXEC)
        return str(f)

    def test_timeouts_and_failures_become_error(self):
        (self.root / ".mote").mkdir()
        slow = self.fake("sleep 5")
        t0 = time.time()
        snap = dash.mote_fetch(self.root / ".mote", slow, timeout=0.5)
        self.assertLess(time.time() - t0, 3)
        self.assertIn("timed out", snap["error"])
        self.assertIsNone(snap["counts"])
        bad = self.fake("echo nope >&2; exit 3")
        snap = dash.mote_fetch(self.root / ".mote", bad, timeout=2)
        self.assertIn("exit 3", snap["error"])
        garbage = self.fake("echo '{not json'")
        self.assertIn(
            "invalid JSON",
            dash.mote_fetch(self.root / ".mote", garbage, timeout=2)["error"],
        )

    def test_no_store_or_no_cli_means_null(self):
        self.assertIsNone(dash.build_snapshot(self.hub)["mote"])
        (self.root / ".mote").mkdir()
        with patch.object(dash, "mote_bin", return_value=None):
            self.assertIsNone(dash.build_snapshot(self.hub)["mote"])
            self.assertFalse(dash.mote_refresh(self.hub))


if __name__ == "__main__":
    unittest.main()

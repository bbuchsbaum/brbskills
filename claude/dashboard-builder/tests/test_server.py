"""Local server security and endpoints, against a temp hub on 127.0.0.1."""
import http.client
import json
import os
import stat
import subprocess
import sys
import time
import unittest

from _util import DASH, HubCase, dash

SID = "cli-srv00001"


class ServerBase(HubCase):
    def setUp(self):
        super().setUp()
        self.cli("init", "Served", "--task", "A", session=SID)
        self.cli("ask", "Which format?", "--default", "Markdown", session=SID)
        p = self.cli("serve")
        self.url = p.stdout.strip().splitlines()[0]
        self.addCleanup(self.stop)
        self.port = int(self.url.split(":")[2].split("/")[0])
        self.token = self.url.split("#k=", 1)[1]
        self.host = f"127.0.0.1:{self.port}"

    def stop(self):
        subprocess.run(
            [sys.executable, str(DASH), "--dir", str(self.dir), "stop"],
            env=self.env,
            capture_output=True,
            timeout=30,
        )

    def req(
        self,
        method,
        path,
        body=None,
        headers=None,
        token=True,
        host=None,
        ctype="application/json",
    ):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Host": host or self.host}
        if token:
            h["X-Dash-Token"] = self.token if token is True else token
        data = None
        if body is not None:
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            h["Content-Type"] = ctype
            h["Content-Length"] = str(len(data))
        h.update(headers or {})
        c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in h.items():
            c.putheader(k, v)
        c.endheaders(data)
        r = c.getresponse()
        raw = r.read()
        c.close()
        try:
            return r.status, json.loads(raw), r
        except ValueError:
            return r.status, raw, r


class ServerTests(ServerBase):
    def test_url_token_files_and_snapshot(self):
        self.assertRegex(self.url, r"^http://127\.0\.0\.1:\d+/#k=[A-Za-z0-9_-]{40,}$")
        for name in (".token", "server.json"):
            self.assertEqual(
                stat.S_IMODE((self.dir / name).stat().st_mode), 0o600, name
            )
        info = json.loads((self.dir / "server.json").read_text())
        self.assertEqual(set(info), {"port", "pid", "started"})
        self.assertEqual(self.cli("url").stdout.strip(), self.url)
        code, snap, r = self.req("GET", "/api/hub")
        self.assertEqual(code, 200)
        self.assertEqual(snap["server"]["running"], True)
        self.assertNotIn(self.token, json.dumps(snap))
        self.assertNotIn(self.token, (self.dir / "data.js").read_text())
        self.assertNotIn(self.token, (self.dir / "server.log").read_text())
        self.assertEqual(stat.S_IMODE((self.dir / "server.log").stat().st_mode), 0o600)
        self.assertEqual(r.getheader("Cache-Control"), "no-store")
        code, page, r = self.req("GET", "/", token=False)
        self.assertEqual(code, 200)
        self.assertIn("text/html", r.getheader("Content-Type"))

    def test_refuses_second_server(self):
        p = self.cli("serve", ok=False)
        self.assertIn("already running", p.stderr)
        p = subprocess.run(
            [
                sys.executable,
                str(DASH),
                "--dir",
                str(self.dir),
                "serve",
                "--foreground",
            ],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertNotEqual(p.returncode, 0)

    def test_token_host_origin_checks(self):
        self.assertEqual(self.req("GET", "/api/hub", token=False)[0], 401)
        self.assertEqual(self.req("GET", "/api/hub", token="wrong")[0], 403)
        self.assertEqual(self.req("GET", "/api/hub", host="evil.example:80")[0], 403)
        self.assertEqual(
            self.req("GET", "/", token=False, host=f"attacker.test:{self.port}")[0], 403
        )
        self.assertEqual(
            self.req("GET", "/api/hub", host=f"localhost:{self.port}")[0], 200
        )
        self.assertEqual(
            self.req("GET", "/api/hub", headers={"Origin": "http://evil.example"})[0],
            403,
        )
        self.assertEqual(
            self.req("GET", "/api/hub", headers={"Origin": "null"})[0], 403
        )
        self.assertEqual(
            self.req(
                "GET", "/api/hub", headers={"Origin": f"http://127.0.0.1:{self.port}"}
            )[0],
            200,
        )
        self.assertEqual(
            self.req(
                "POST", f"/api/sessions/{SID}/messages", {"text": "x"}, token=False
            )[0],
            401,
        )
        self.assertEqual(self.req("GET", "/.token", token=False)[0], 404)
        self.assertEqual(self.req("GET", "/server.json")[0], 404)
        self.assertEqual(self.req("GET", "/sessions/x/../../.token")[0], 404)

    def test_rejected_post_closes_connection(self):
        code, _, r = self.req("POST", f"/api/sessions/{SID}/messages", {"text": "x"}, token=False)
        self.assertEqual((code, r.getheader("Connection")), (401, "close"))

    def test_body_checks(self):
        path = f"/api/sessions/{SID}/messages"
        self.assertEqual(self.req("POST", path, b"x" * (16 * 1024 + 1))[0], 413)
        self.assertEqual(
            self.req(
                "POST", path, b"text=hi", ctype="application/x-www-form-urlencoded"
            )[0],
            415,
        )
        self.assertEqual(self.req("POST", path, b"text=hi", ctype="text/plain")[0], 415)
        self.assertEqual(self.req("POST", path, b"{not json")[0], 400)
        self.assertEqual(self.req("POST", path, [1, 2])[0], 400)
        self.assertEqual(
            self.req("POST", path, {"kind": "message", "text": ""})[0], 400
        )
        self.assertEqual(self.req("POST", path, {"kind": "shell", "text": "x"})[0], 400)
        self.assertEqual(
            self.req("POST", "/api/sessions/nope/messages", {"text": "x"})[0], 404
        )
        self.assertEqual(
            self.req("POST", "/api/sessions/..%2F/messages", {"text": "x"})[0], 404
        )
        self.assertEqual(self.req("PUT", path, {"text": "x"})[0], 405)
        self.assertEqual(
            self.req("POST", "/api/mote/post", {"text": "x"})[0], 404
        )  # no mote store here

    def test_good_post_queues_message_and_answer(self):
        code, body, _ = self.req(
            "POST",
            f"/api/sessions/{SID}/messages",
            {"kind": "message", "text": "Run it again"},
        )
        self.assertEqual((code, body["ok"], body["id"]), (200, True, "m1"))
        code, body, _ = self.req(
            "POST",
            f"/api/sessions/{SID}/messages",
            {"kind": "answer", "text": "HTML", "qid": "Q1"},
        )
        self.assertEqual(code, 200)
        q = self.plan(SID)["questions"][0]
        self.assertEqual((q["answer"], q["answered_via"]), ("HTML", "dashboard"))
        _, snap, _ = self.req("GET", "/api/hub")
        inbox = snap["sessions"][0]["inbox"]
        self.assertEqual(
            [(m["id"], m["status"]) for m in inbox],
            [("m1", "queued"), ("m2", "queued")],
        )
        out = self.cli("inbox", session=SID).stdout
        self.assertIn("Run it again", out)
        self.assertIn(
            '[Dashboard answer from the user to Q1 "Which format?"] HTML', out
        )

    def test_pause_resume(self):
        code, body, _ = self.req("POST", f"/api/sessions/{SID}/pause", {})
        self.assertEqual((code, body["paused"]), (200, True))
        self.assertTrue((self.dir / "sessions" / SID / "paused").exists())
        _, snap, _ = self.req("GET", "/api/hub")
        self.assertEqual(
            (snap["sessions"][0]["paused"], snap["sessions"][0]["activity"]),
            (True, "paused"),
        )
        self.assertEqual(self.req("POST", f"/api/sessions/{SID}/resume", {})[0], 200)
        self.assertFalse((self.dir / "sessions" / SID / "paused").exists())

    def test_stop(self):
        pid = json.loads((self.dir / "server.json").read_text())["pid"]
        self.assertIn("stopped", self.cli("stop").stdout)
        self.assertFalse(dash.pid_alive(pid))
        self.assertFalse((self.dir / "server.json").exists())
        self.assertFalse(dash.build_snapshot(self.hub)["server"]["running"])


class FileEndpointTests(ServerBase):
    def get(self, path, **kw):
        from urllib.parse import quote

        return self.req("GET", "/api/file?path=" + quote(str(path)), **kw)

    def test_project_file_is_served_sandboxed(self):
        f = self.root / "out" / "report file.html"
        f.parent.mkdir()
        f.write_text("<script>alert(1)</script>")
        code, body, r = self.get(f)
        self.assertEqual((code, body), (200, b"<script>alert(1)</script>"))
        self.assertIn("text/html", r.getheader("Content-Type"))
        self.assertTrue(r.getheader("Content-Disposition").startswith("inline;"))
        self.assertIn("sandbox", r.getheader("Content-Security-Policy"))
        self.assertNotIn("allow-same-origin", r.getheader("Content-Security-Policy"))
        self.assertEqual(self.get(f, token=False)[0], 401)
        self.assertEqual(self.get(f, token="nope")[0], 403)

    def test_refusals(self):
        outside = self.root.parent / "outside.txt"
        outside.write_text("private")
        (self.root / "link.txt").symlink_to(outside)
        (self.root / "dir").mkdir()
        self.assertEqual(self.get(self.dir / ".token")[0], 403)
        self.assertEqual(self.get(self.dir / "sessions" / SID / "session.json")[0], 403)
        self.assertEqual(self.get(self.root / "link.txt")[0], 403)
        self.assertEqual(self.get(outside)[0], 403)
        self.assertEqual(self.get(self.root / "dir")[0], 404)
        self.assertEqual(self.get(self.root / "missing.txt")[0], 404)
        self.assertEqual(self.get(self.root / ".." / self.root.name / ".dashboard" / ".token")[0], 403)
        self.assertEqual(self.req("GET", "/api/file?path=relative.txt")[0], 400)
        self.assertEqual(self.req("GET", "/api/file")[0], 400)
        big = self.root / "big.bin"
        with open(big, "wb") as fh:
            fh.truncate(50 * 1024 * 1024 + 1)
        self.assertEqual(self.get(big)[0], 413)
        self.assertEqual(self.req("GET", "/data.js")[0], 404)

    def test_recorded_deliverable_outside_project(self):
        outside = self.root.parent / "deliverable.csv"
        outside.write_text("a,b\n")
        self.assertEqual(self.get(outside)[0], 403)
        self.cli("deliver", str(outside), session=SID)
        code, body, r = self.get(outside)
        self.assertEqual((code, body), (200, b"a,b\n"))
        self.assertIn("text/csv", r.getheader("Content-Type"))


class IdleExitTests(HubCase):
    def test_idle_server_exits(self):
        env = dict(self.env, DASH_SERVER_IDLE="1")
        p = self.cli("serve", env=env)
        self.assertTrue(p.stdout.startswith("http://127.0.0.1:"))
        pid = json.loads((self.dir / "server.json").read_text())["pid"]
        deadline = time.time() + 60
        while time.time() < deadline and dash.pid_alive(pid):
            time.sleep(0.1)
        if dash.pid_alive(pid):
            os.kill(pid, 15)
            self.fail("server did not exit when idle")
        self.assertFalse((self.dir / "server.json").exists())


if __name__ == "__main__":
    unittest.main()

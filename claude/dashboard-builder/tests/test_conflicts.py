"""Cross-agent conflicts from edits, mote reservations and board posts."""
import json
import time
import unittest
from unittest.mock import patch

from _util import HubCase, dash

A, B = "aaaa0000-1111-4000-8000-000000000001", "bbbb0000-2222-4000-8000-000000000002"


class ConflictTests(HubCase):
    def setUp(self):
        super().setUp()
        (self.root / ".mote").mkdir()
        (self.root / "R").mkdir()
        (self.root / "R" / "shared.R").write_text("")
        self.mote = {"store": str(self.root / ".mote"), "fetched": dash.now(), "error": None, "counts": None,
                     "doing": [], "ready": [], "blocked": [], "reservations": [], "actors": [], "posts": [],
                     "_mentions": []}

    def edit(self, sid, path="R/shared.R", ago=0):
        self.start(sid)
        self.tool(sid, "Edit", {"file_path": str(self.root / path)}, {})
        if ago:
            p = self.dir / "sessions" / sid / "session.json"
            s = json.loads(p.read_text())
            s["files"][path]["last_edit"] = dash.iso(time.time() - ago)
            p.write_text(json.dumps(s))

    def reserve(self, actor, paths, expires_in=3600, issue="bd-1"):
        self.mote["reservations"].append({"actor": actor, "paths": paths, "issue": issue,
                                          "created": dash.iso(time.time() - 600),
                                          "expires": dash.iso(time.time() + expires_in)})

    def post(self, author, paths, ago=60, pid="post-1"):
        self.mote["_mentions"].append({"id": pid, "from": author, "ts": dash.iso(time.time() - ago), "paths": paths})

    def conflicts(self):
        (self.dir / "mote.json").write_text(json.dumps(self.mote))
        with patch.object(dash, "mote_bin", return_value="/bin/true"):
            snap = dash.build_snapshot(self.hub)
        self.assertNotIn("_mentions", snap["mote"])
        return snap["conflicts"]

    def test_two_editors(self):
        self.edit(A)
        self.edit(B)
        [c] = self.conflicts()
        self.assertEqual((c["path"], sorted(c["sessions"]), c["sources"], c["live"], c["mote_reserved_by"]),
                         ("R/shared.R", ["aaaa", "bbbb"], ["edit"], True, None))
        self.assertIsNotNone(dash.epoch(c["last_edit"]))
        self.assertEqual([d["kind"] for d in c["detail"]], ["edit", "edit"])
        self.assertTrue(all(d["ref"] is None for d in c["detail"]))

    def test_edit_against_foreign_reservation(self):
        self.edit(A)
        self.reserve("codex-zz", ["R/"])
        [c] = self.conflicts()
        self.assertEqual((c["sessions"], c["sources"], c["mote_reserved_by"]), (["aaaa"], ["edit", "reservation"], "codex-zz"))
        r = self.mote["reservations"][0]
        self.assertEqual(c["detail"][1], {"session": "codex-zz", "kind": "reservation",
                                          "ts": r["created"], "expires": r["expires"], "ref": "bd-1"})
        self.assertEqual(c["detail"][0]["expires"], None)

    def test_own_reservation_is_not_a_conflict(self):
        self.edit(A)
        self.reserve("claude-aaaa", ["R/shared.R"])
        self.assertEqual(self.conflicts(), [])

    def test_expired_reservation_is_ignored(self):
        self.edit(A)
        self.reserve("codex-zz", ["R/shared.R"], expires_in=-10)
        self.assertEqual(self.conflicts(), [])

    def test_board_post_naming_an_existing_path(self):
        self.edit(B)
        self.post("chief", ["R/shared.R", "docs/missing.md"])
        [c] = self.conflicts()
        self.assertEqual((c["path"], c["sessions"], c["sources"]), ("R/shared.R", ["bbbb"], ["edit", "post"]))
        self.assertEqual(c["detail"][-1]["ref"], "post-1")
        self.assertEqual(c["detail"][-1]["session"], "chief")

    def test_old_post_and_old_edit_are_ignored(self):
        self.edit(B, ago=3 * 3600)
        self.post("chief", ["R/shared.R"], ago=25 * 3600)
        self.edit(A)
        self.assertEqual(self.conflicts(), [])

    def test_liveness(self):
        self.edit(A, ago=45 * 60)
        self.edit(B, ago=50 * 60)
        [c] = self.conflicts()
        self.assertFalse(c["live"])
        self.reserve("claude-bbbb", ["R/shared.R"])
        self.hook("UserPromptSubmit", B, prompt="keep going")  # B is working and holds the reservation
        [c] = self.conflicts()
        self.assertTrue(c["live"])

    def test_reservation_and_post_without_edits(self):
        self.reserve("codex-zz", ["R/shared.R"])
        self.post("chief", ["R/shared.R"])
        [c] = self.conflicts()
        self.assertEqual((c["sessions"], c["sources"], c["last_edit"], c["live"]), ([], ["reservation", "post"], None, False))

    def test_ulid_creation_time(self):
        # Captured from a real reservation: lease_until 16:35:42.730Z with the default 1 h TTL.
        self.assertEqual(dash.epoch(dash.ulid_time("rv-01M3SFA4WA9FG6T7NSA5TERS5S")),
                         dash.epoch("2026-09-30T15:35:42.730+00:00"))
        for bad in (None, "", "rv-short", "bd-4f1", "rv-" + "U" * 26, "rv-8ZZZZZZZZZZZZZZZZZZZZZZZZZ"):
            self.assertIsNone(dash.ulid_time(bad), bad)

    def test_path_mentions(self):
        text = "Touching `R/read_vol.R`, src/lib.rs and README.md; see https://x.org/a/b.html and ../up.txt"
        self.assertEqual(dash.path_mentions(text), ["R/read_vol.R", "src/lib.rs", "README.md"])


if __name__ == "__main__":
    unittest.main()

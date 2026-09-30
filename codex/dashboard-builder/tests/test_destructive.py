"""Destructive-command detection (table-driven) and question ids that survive plan resets."""
import unittest

from _util import HubCase, dash

POSITIVE = [
    # (command, expected label)
    ("rm -rf build", "rm -rf"),
    ("rm -fr build", "rm -rf"),
    ("rm -r -f build", "rm -rf"),
    ("rm -f -r build", "rm -rf"),
    ("rm --recursive --force build", "rm -rf"),
    ("rm --recursive build", "rm -r"),
    ("rm -R old/", "rm -r"),
    ("/bin/rm -rf /tmp/x", "rm -rf"),
    ("sudo rm -rf /var/lib/x", "rm -rf"),
    ("cd pkg && rm -rf man", "rm -rf"),
    ("make test; rm -rf .cache", "rm -rf"),
    ("false || rm -rf out", "rm -rf"),
    ("(cd x; rm -rf y)", "rm -rf"),
    ("echo $(rm -rf tmp)", "rm -rf"),
    ("ls `rm -rf z`", "rm -rf"),
    ("find . -name '*.o' | xargs rm -rf", "rm -rf"),
    ("FOO=1 rm -rf dist", "rm -rf"),
    ("bash -c 'rm -rf build'", "rm -rf"),
    ("ssh hpc 'rm -rf /scratch/me/run1'", "rm -rf"),
    ("cd x\nrm -rf y", "rm -rf"),
    ("R CMD check pkg.tar.gz " + "--as-cran " * 30 + "&& rm -rf pkg.Rcheck", "rm -rf"),
    ("find . -name '*.pyc' -delete", "find -delete"),
    ("find /tmp -type f -exec rm {} +", "find -exec rm"),
    ("rsync -av --delete src/ dst/", "rsync --delete"),
    ("mv results.csv /dev/null", "mv to /dev/null"),
    ("rsync -a --delete-after a/ b/", "rsync --delete"),
    ("git push --force origin main", "git push --force"),
    ("git push -f", "git push --force"),
    ("git push origin +main", "git push --force"),
    ("git -C repo push --force", "git push --force"),
    ("git push --force-with-lease origin feature", "git push --force-with-lease"),
    ("git push origin --delete old-branch", "git push --delete"),
    ("git reset --hard HEAD~3", "git reset --hard"),
    ("git clean -fdx", "git clean -f"),
    ("git clean --force -d", "git clean -f"),
    ("git checkout -- .", "git checkout -- (discard changes)"),
    ("git checkout .", "git checkout -- (discard changes)"),
    ("git restore .", "git restore (discard changes)"),
    ("git stash drop", "git stash drop"),
    ("git stash clear", "git stash clear"),
    ("git branch -D feature", "git branch -D"),
    ("psql -c 'DROP TABLE users'", "SQL DROP"),
    ("sqlite3 app.db 'DELETE FROM sessions'", "SQL DELETE without WHERE"),
    ('mysql -e "truncate table logs"', "SQL TRUNCATE"),
    ("duckdb x.db 'drop schema s cascade'", "SQL DROP"),
    ("chmod -R 777 .", "chmod -R"),
    ("chown -R me:staff /data", "chown -R"),
    ("mkfs.ext4 /dev/sdb1", "mkfs.ext4"),
    ("dd if=/dev/zero of=/dev/disk2 bs=1m", "dd of="),
    ("scancel -u $USER", "scancel all jobs of a user"),
    ("scancel --me", "scancel all jobs of a user"),
    ("scancel --user=bbuchsbaum", "scancel all jobs of a user"),
    ("Rscript -e 'unlink(\"out\", recursive = TRUE)'", "R unlink(recursive = TRUE)"),
    (
        "Rscript -e 'unlink(file.path(d, \"x\"), recursive=T)'",
        "R unlink(recursive = TRUE)",
    ),
    ("python3 -c 'import shutil; shutil.rmtree(\"build\")'", "Python shutil.rmtree"),
    (
        "python3 - <<'EOF'\nimport shutil\nshutil.rmtree('x')\nEOF",
        "Python shutil.rmtree",
    ),
    ("kubectl delete pod web-1", "kubectl delete"),
    ("timeout 60 rm -rf big", "rm -rf"),
]

NEGATIVE = [
    "rm file.txt",
    "rm -f stale.lock",
    "rm -i a b",
    'git commit -m "rm -rf the old build dir"',
    "git commit -m 'git push --force was wrong'",
    "echo rm -rf /",
    'echo "git reset --hard"',
    "printf 'DROP TABLE x\\n'",
    "grep -r 'rm -rf' scripts/",
    'rg "shutil.rmtree" src',
    "find . -name '*.R' -print",
    "rsync -av --delete --dry-run a/ b/",
    "rsync -avn --delete a/ b/",
    "rsync -av src/ dst/",
    "git push origin main",
    "git push -u origin feature",
    "git reset --soft HEAD~1",
    "git clean -n",
    "mv a.txt b.txt",
    "mv /dev/null.bak x",
    "git clean -n -fd",
    "git clean --dry-run -fd",
    "git clean -nfdx",
    "git checkout main",
    "git checkout -b new-branch",
    "git restore --staged file.R",
    "git stash list",
    "git branch -d merged",
    "sqlite3 app.db 'DELETE FROM sessions WHERE ts < 5'",
    "psql -c 'select * from users'",
    "chmod 644 file",
    "chmod -x script.sh",
    "dd if=/dev/zero bs=1m count=1",
    "scancel 12345",
    "Rscript -e 'unlink(\"tmp.txt\")'",
    "kubectl get pods",
    "cat <<EOF\nrm -rf x\nEOF",
    "ls -la && pwd",
    "",
]


class DestructiveTests(unittest.TestCase):
    def test_table_sizes(self):
        self.assertGreaterEqual(len(POSITIVE), 40)
        self.assertGreaterEqual(len(NEGATIVE), 20)

    def test_positives(self):
        for cmd, label in POSITIVE:
            with self.subTest(cmd=cmd):
                hit = dash.destructive(cmd)
                self.assertIsNotNone(hit, cmd)
                self.assertEqual(hit["label"], label)
                self.assertTrue(hit["match"])
                self.assertLessEqual(len(hit["match"]), 160)
                self.assertEqual(set(hit), {"label", "match", "severity"})

    def test_negatives(self):
        for cmd in NEGATIVE:
            with self.subTest(cmd=cmd):
                self.assertIsNone(dash.destructive(cmd), cmd)

    def test_severity(self):
        self.assertEqual(
            dash.destructive("git push --force-with-lease")["severity"], "medium"
        )
        self.assertEqual(dash.destructive("git push --force")["severity"], "high")
        self.assertEqual(dash.destructive("rm -rf x")["severity"], "high")

    def test_match_is_the_simple_command_only(self):
        cases = {
            "rm -rf out 2>/dev/null": "rm -rf out",
            "rsync -a --delete a/ b/ 2>&1 | tee log": "rsync -a --delete a/ b/",
            "rsync -a --delete a/ b/ # sync mirror": "rsync -a --delete a/ b/",
            'rm -rf "my dir"': "rm -rf 'my dir'",
            'rm -rf "#tmp"': "rm -rf '#tmp'",
            "echo a#b; rm -rf x #c": "rm -rf x",
        }
        for cmd, match in cases.items():
            with self.subTest(cmd=cmd):
                self.assertEqual(dash.destructive(cmd)["match"], match)

    def test_wrapper_option_values_are_skipped(self):
        for cmd in ("srun -n 1 rm -rf out", "sudo -u bob rm -rf out", "nice -n 10 rm -rf out",
                    "timeout -s KILL 60 rm -rf out", "env -u FOO rm -rf out"):
            with self.subTest(cmd=cmd):
                self.assertEqual(dash.destructive(cmd)["match"], "rm -rf out")
        self.assertIsNone(dash.destructive("nice -n 10 ls"))

    def test_long_match_is_marked_as_cut(self):
        hit = dash.destructive("rsync -a --delete /data/" + "x" * 300 + " b/")
        self.assertEqual(len(hit["match"]), 160)
        self.assertTrue(hit["match"].endswith("…"))

    def test_comments_are_not_commands(self):
        for cmd in ("# rm -rf x", "ls # ; rm -rf x", 'bash -c "ls # x; rm -rf z"'):
            with self.subTest(cmd=cmd):
                self.assertIsNone(dash.destructive(cmd))
        self.assertIsNotNone(dash.destructive("ls # note\nrm -rf x"))

    def test_match_is_redacted(self):
        hit = dash.destructive("psql postgres://admin:pa55@db/app -c 'DROP TABLE x'")
        self.assertNotIn("pa55", hit["match"])


class HookDestructiveTests(HubCase):
    SID = "destr-1"

    def test_current_and_permission_attention(self):
        self.start(self.SID)
        cmd = (
            "R CMD build . " + "--no-build-vignettes " * 20 + "&& rm -rf ../old-builds"
        )
        self.hook(
            "PreToolUse",
            self.SID,
            tool_name="Bash",
            tool_input={"command": cmd},
            tool_use_id="d1",
        )
        self.hook(
            "Notification",
            self.SID,
            message="Claude needs your permission to use Bash",
            notification_type="permission_prompt",
        )
        v = self.view(self.SID)
        self.assertLessEqual(len(v["current"]["summary"]), 160)
        self.assertNotIn(
            "rm -rf", v["current"]["summary"]
        )  # invisible in the truncated summary...
        self.assertEqual(
            v["current"]["destructive"]["label"], "rm -rf"
        )  # ...but detected
        self.assertEqual(v["current"]["destructive"]["match"], "rm -rf ../old-builds")
        att = v["attention"][-1]
        self.assertEqual(
            (att["kind"], att["destructive"]["label"]), ("permission", "rm -rf")
        )
        self.hook(
            "PostToolUse",
            self.SID,
            tool_name="Bash",
            tool_input={"command": cmd},
            tool_use_id="d1",
            tool_response={"stdout": ""},
        )
        self.hook(
            "PreToolUse",
            self.SID,
            tool_name="Bash",
            tool_input={"command": "ls"},
            tool_use_id="d2",
        )
        self.hook(
            "Notification",
            self.SID,
            message="Claude is waiting",
            notification_type="idle_prompt",
        )
        v = self.view(self.SID)
        self.assertIsNone(v["current"]["destructive"])
        self.assertIsNone(v["attention"][-1]["destructive"])


class QuestionIdTests(HubCase):
    SID = "cli-qids0001"

    def test_ids_survive_plan_reset(self):
        self.cli("init", "First", session=self.SID)
        self.assertEqual(
            self.cli("ask", "Old?", "--default", "a", session=self.SID).stdout.split()[
                0
            ],
            "Q1",
        )
        self.assertEqual(
            self.cli("block", "old", session=self.SID).stdout.split()[0], "B1"
        )
        dash.queue_message(
            self.hub, self.SID, "answer", "old answer", "Q1"
        )  # queued, not yet delivered
        reset = self.cli("init", "Second", "--force", session=self.SID).stdout
        self.assertEqual(
            self.cli("ask", "New?", "--default", "b", session=self.SID).stdout.split()[
                0
            ],
            "Q2",
        )
        self.assertEqual(
            self.cli("block", "new", session=self.SID).stdout.split()[0], "B2"
        )
        q = self.plan(self.SID)["questions"]
        self.assertEqual(
            [(x["id"], x["answer"]) for x in q], [("Q2", None)]
        )  # old answer did not leak
        with self.assertRaises(dash.DashError):
            dash.queue_message(self.hub, self.SID, "answer", "stale page", "Q1")
        v = self.view(self.SID)
        inbox_qids = {m["qid"] for m in v["inbox"] if m["kind"] == "answer"}
        self.assertEqual(inbox_qids, {"Q1"})
        self.assertFalse(
            inbox_qids & {x["id"] for x in v["plan"]["questions"]}
        )  # matches no current question
        # Every dash.py call hands over queued messages; the reset call did, without new question text.
        self.assertIn("[Dashboard answer from the user to Q1] old answer", reset)
        dash.queue_message(self.hub, self.SID, "answer", "yes", "Q2")
        self.assertEqual(self.plan(self.SID)["questions"][0]["answer"], "yes")


if __name__ == "__main__":
    unittest.main()

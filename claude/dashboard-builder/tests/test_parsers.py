"""Test-runner summary parsing and secret redaction."""
import unittest

from _util import HubCase, dash

P = dash.parse_tests


class ParserTests(unittest.TestCase):
    def check(self, text, runner, passed, failed, skipped, cmd=""):
        r = P(text, cmd)
        self.assertIsNotNone(r, text)
        self.assertEqual(
            (r["runner"], r["passed"], r["failed"], r["skipped"]),
            (runner, passed, failed, skipped),
        )

    def test_pytest(self):
        self.check(
            "collected 46 items\n...\n=========== 41 passed, 2 failed, 3 skipped, 1 warning in 1.23s ===========",
            "pytest",
            41,
            2,
            3,
        )
        self.check("41 passed, 1 error, 2 xfailed in 0.50s", "pytest", 41, 1, 2)
        self.check("\x1b[32m=== 5 passed in 0.01s ===\x1b[0m", "pytest", 5, 0, 0)

    def test_unittest(self):
        self.check(
            "..s.\n------\nRan 12 tests in 0.034s\n\nOK (skipped=2)",
            "unittest",
            10,
            0,
            2,
        )
        self.check(
            "Ran 5 tests in 1.0s\n\nFAILED (failures=1, errors=2, skipped=1)",
            "unittest",
            1,
            3,
            1,
        )
        self.check("Ran 3 tests in 0.1s\n\nOK", "unittest", 3, 0, 0)

    def test_testthat_takes_last_summary(self):
        text = "[ FAIL 0 | WARN 0 | SKIP 0 | PASS 10 ]\n...\n[ FAIL 2 | WARN 1 | SKIP 3 | PASS 120 ]\n"
        self.check(text, "testthat", 120, 2, 3)

    def test_r_cmd_check(self):
        self.check(
            "* checking tests ... OK\nStatus: 1 ERROR, 2 WARNINGs, 1 NOTE\n",
            "R CMD check",
            None,
            4,
            None,
        )
        self.check(
            "── R CMD check results ──\nStatus: OK\n", "R CMD check", None, 0, None
        )
        r = P("Status: 2 NOTEs\n")
        self.assertEqual((r["failed"], r["detail"]), (2, "Status: 2 NOTEs"))

    def test_cargo_sums_crates(self):
        text = (
            "test result: ok. 12 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.01s\n"
            "test result: FAILED. 3 passed; 2 failed; 0 ignored; 0 measured; 0 filtered out\n"
        )
        self.check(text, "cargo", 15, 2, 1)

    def test_vitest_and_jest(self):
        self.check(
            " Test Files  1 failed | 5 passed (6)\n      Tests  3 failed | 40 passed | 2 skipped (45)\n",
            "vitest",
            40,
            3,
            2,
        )
        self.check(
            "Test Suites: 1 failed, 4 passed, 5 total\nTests:       2 failed, 1 skipped, 40 passed, 43 total\n",
            "jest",
            40,
            2,
            1,
        )

    def test_go(self):
        self.check(
            "=== RUN   TestA\n--- PASS: TestA (0.00s)\n--- FAIL: TestB (0.00s)\n--- SKIP: TestC\nFAIL\n"
            "FAIL\texample.com/x\t0.01s\n",
            "go",
            1,
            1,
            1,
            "go test -v ./...",
        )
        self.check(
            "ok  \texample.com/a\t0.01s\nFAIL\texample.com/b\t0.02s\n",
            "go",
            1,
            1,
            None,
            "go test ./...",
        )

    def test_non_test_output(self):
        for text in ("", "hello world", "Status: running", "total 12\ndrwxr-xr-x"):
            self.assertIsNone(P(text, "ls"), text)


class RedactionTests(unittest.TestCase):
    def test_secrets_are_removed(self):
        cases = {
            "export API_KEY=abcd1234efgh": "abcd1234efgh",
            "curl -H 'Authorization: Bearer eyJhbGciOi.xyz'": "eyJhbGciOi",
            "password: hunter2": "hunter2",
            "mysql --password s3cret -u root": "s3cret",
            "OPENAI sk-proj-ABCDEFGHIJKLMNOP": "ABCDEFGHIJKLMNOP",
            "git push https://user:ghp_abcdefghijklmnop@github.com/x": "ghp_abcdefghijklmnop",
            "gh auth ghp_1234567890abcdef": "ghp_1234567890abcdef",
            "AKIAABCDEFGHIJKLMNOP": "AKIAABCDEFGHIJKLMNOP",
            "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG": "wJalrXUtnFEMI",
            "postgres://admin:pa55@db.local/app": "pa55",
            "SLACK xoxb-123-456-abc": "xoxb-123",
            "token=abc&x=1": "abc&x",
        }
        for text, secret in cases.items():
            out = dash.redact(text)
            self.assertNotIn(secret, out, text)
            self.assertIn("[REDACTED]", out, text)

    def test_ordinary_text_is_kept_and_truncated(self):
        self.assertEqual(
            dash.redact("R CMD check --as-cran pkg.tar.gz"),
            "R CMD check --as-cran pkg.tar.gz",
        )
        e = dash.excerpt("x" * 1000, 300)
        self.assertEqual(len(e), 300)
        self.assertTrue(e.endswith("…"))
        self.assertEqual(dash.excerpt("  a\n  b  ", 50, oneline=True), "a b")
        self.assertIsNone(dash.excerpt("   "))


class HookParsingTests(HubCase):
    SID = "p1"

    def test_bash_output_becomes_test_entry_and_event(self):
        self.start(self.SID)
        out = (
            "==> devtools::test()\n[ FAIL 2 | WARN 0 | SKIP 3 | PASS 120 ]\n"
            + "noise\n" * 5000
        )
        self.tool(
            self.SID,
            "Bash",
            {"command": "Rscript -e 'devtools::test()'"},
            {"stdout": out, "stderr": ""},
        )
        self.tool(
            self.SID,
            "Bash",
            {"command": "pytest -q"},
            "Exit code 1\n=== 3 passed, 1 failed in 0.2s ===",
            failure=True,
        )
        v = self.view(self.SID)
        self.assertEqual(
            [(t["runner"], t["passed"], t["failed"], t["skipped"]) for t in v["tests"]],
            [("testthat", 120, 2, 3), ("pytest", 3, 1, 0)],
        )
        self.assertEqual(v["tests"][0]["command"], "Rscript -e 'devtools::test()'")
        tests = [e for e in v["events"] if e["kind"] == "test"]
        self.assertEqual(
            tests[0]["summary"], "testthat: 120 passed, 2 failed, 3 skipped"
        )
        self.assertFalse(tests[0]["ok"])
        raw = (self.dir / "sessions" / self.SID / "events.jsonl").read_text()
        self.assertNotIn("noise\nnoise", raw)
        self.assertLess(len(raw), 5000)


if __name__ == "__main__":
    unittest.main()

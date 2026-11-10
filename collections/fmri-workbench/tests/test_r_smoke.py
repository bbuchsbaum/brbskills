"""Run synthetic R regressions when their optional runtime is available."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
RSCRIPT = shutil.which("Rscript")


@unittest.skipUnless(RSCRIPT, "Rscript is not installed; R smoke checks remain unverified")
class RSmokeTests(unittest.TestCase):
    def run_smoke(self, package, script):
        probe = subprocess.run(
            [RSCRIPT, "--vanilla", "-e",
             f'if (!length(find.package("{package}", quiet=TRUE))) quit(status=42L); '
             f'loadNamespace("{package}")'],
            capture_output=True, text=True, timeout=30)
        if probe.returncode == 42:
            self.skipTest(f"{package} unavailable; its R smoke check remains unverified")
        self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)
        result = subprocess.run(
            [RSCRIPT, "--vanilla", str(ROOT / "skills" / package / "scripts" / script)],
            capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_group_sample_identity_and_weighted_arithmetic(self):
        self.run_smoke("fmrigds", "smoke_group.R")

    def test_first_level_design_examples(self):
        self.run_smoke("fmrireg", "smoke_design.R")


if __name__ == "__main__":
    unittest.main()

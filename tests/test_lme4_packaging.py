"""The imported validator must work in isolation without rewriting its bundle."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'skills/lme4-mixed-models'


class Lme4PackagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='lme4-validator-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.skill = self.work / 'lme4-mixed-models'
        shutil.copytree(SOURCE, self.skill)

    def snapshot(self):
        return {p.relative_to(self.skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.skill.rglob('*') if p.is_file()}

    def run_validator(self, *args):
        result = subprocess.run([sys.executable, str(self.skill/'tests/validate_bundle.py'), *args],
                                cwd=self.work, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['static_and_algebra_checks_failed'], 0)
        return report

    def test_default_run_leaves_all_bundle_files_unchanged(self):
        before = self.snapshot()
        self.run_validator()
        self.assertEqual(self.snapshot(), before)

    def test_explicit_receipt_is_written_outside_bundle(self):
        before = self.snapshot()
        receipt = self.work/'new-receipt.json'
        report = self.run_validator('--output', str(receipt))
        self.assertEqual(json.loads(receipt.read_text()), report)
        self.assertEqual(self.snapshot(), before)

    def test_source_dates_preserve_independent_review_dates(self):
        path = self.skill/'references/sources.json'
        sources = json.loads(path.read_text())
        sources[0]['accessed'] = '2026-09-28'
        path.write_text(json.dumps(sources))
        self.run_validator()

    def test_invalid_source_date_is_rejected(self):
        path = self.skill/'references/sources.json'
        sources = json.loads(path.read_text())
        sources[0]['accessed'] = '2026-02-30'
        path.write_text(json.dumps(sources))
        result = subprocess.run([sys.executable, str(self.skill/'tests/validate_bundle.py')],
                                cwd=self.work, text=True, capture_output=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        checks = json.loads(result.stdout)['checks']
        self.assertEqual(next(c['status'] for c in checks if c['name'] == 'source_registry'), 'FAIL')


if __name__ == '__main__':
    unittest.main()

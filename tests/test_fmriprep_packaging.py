"""Exercise each complete fmriprep product with no sibling skill or checkout dependency."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fmriprep_packager', ROOT / 'scripts/skills.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class FmriprepPackagingTests(unittest.TestCase):
    def test_both_extracted_products_run_helpers_without_sibling_skills(self):
        with tempfile.TemporaryDirectory(prefix='fmriprep-isolation-') as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'skills/fmriprep', root / 'skills/fmriprep',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            with contextlib.redirect_stdout(io.StringIO()):
                catalog = builder.sources(root)
                builder.sync(root, catalog)
                builder.package(root, catalog, ['fmriprep'], 'both')
            for product in ('codex', 'claude'):
                with self.subTest(product=product):
                    unpack = root / f'isolated-{product}'
                    with zipfile.ZipFile(root / 'dist' / f'fmriprep-{product}.zip') as archive:
                        archive.extractall(unpack)
                    skill = unpack / 'fmriprep'
                    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
                    env.pop('PYTHONPATH', None)
                    for suite in sorted((skill / 'tests').glob('test_*.py')):
                        result = subprocess.run([sys.executable, '-I', '-B', str(suite)], cwd=unpack,
                                                env=env, text=True, capture_output=True, timeout=45)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual((skill / 'agents/openai.yaml').exists(), product == 'codex')
                    self.assertFalse((unpack / 'alliance-hpc').exists())
                    self.assertFalse((unpack / 'rriscripts').exists())


if __name__ == '__main__':
    unittest.main()

"""Offline regression tests. No browser, service, or model calls."""
import struct
import zlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from update_data import parse_scores

def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


PNG = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) +
       chunk(b'IDAT', zlib.compress(b'\0\xff\0\0')) + chunk(b'IEND', b''))


def critique(layout='7', function='8'):
    return f'## Scores\n| dimension | score | justification |\n| --- | --- | --- |\n| layout | {layout} | Grid |\n| function | {function} | Task |\n' + ''.join(f'\n## {section}\nNone observed.\n' for section in ('Previous round', 'Claims', 'Issues', 'Regressions', 'Proposals'))


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.h = Path(self.temp.name)
        self.env = {**os.environ, 'HARNESS': str(self.h)}
        self.cfg = {'title': 'Fixture', 'dims': ['layout', 'function'],
                    'critics': {'visual': 'Visual', 'user': 'User'}, 'shots': [{'name': 'home'}]}
        self.save_config()
        (self.h / 'critiques').mkdir()

    def save_config(self):
        (self.h / 'hillclimb.json').write_text(json.dumps(self.cfg))

    def run_helper(self, script, *args, ok=True):
        result = subprocess.run([sys.executable, str(SKILL / 'scripts' / script), *args],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def data(self):
        return json.loads((self.h / 'artifact/data.json').read_text())

    def test_first_scores_table_does_not_borrow_historical_values(self):
        md = critique().replace('| function | 8 | Task |\n', '') + '\n## History\n| function | 99 |\n'
        with self.assertRaisesRegex(ValueError, 'Missing'):
            parse_scores(md, self.cfg['dims'])
        md = critique() + '\n## History\n| layout | 99 |\n'
        self.assertEqual(parse_scores(md, self.cfg['dims']), {'layout': 7., 'function': 8.})

    def test_rejects_bad_duplicate_and_incomplete_scores(self):
        for value in ('99', '0', '-1', 'nan', 'N/A', '8 (+1)', '7-9', ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_scores(critique(value), self.cfg['dims'])
        with self.assertRaises(ValueError):
            parse_scores(critique().replace('\n## Previous round', '| layout | 9 | duplicate |\n\n## Previous round'), self.cfg['dims'])

    def test_pending_review_is_explicit_and_offline_text_is_embedded(self):
        text = critique() + '\n<img src=x onerror="alert(1)"> & literal text\n'
        (self.h / 'critiques/v0-visual.md').write_text(text)
        self.run_helper('update_data.py', 'v0', '--no-images')
        record = self.data()['rounds'][0]
        self.assertEqual(record['pending'], ['user'])
        self.assertFalse(record['complete'])
        self.assertFalse(record['images'])
        self.assertEqual(record['critiques'][0]['text'], text)
        (self.h / 'critiques/v0-user.md').write_text(critique())
        self.run_helper('update_data.py', 'v0', '--no-images')
        self.assertTrue(self.data()['rounds'][0]['complete'])
        self.assertEqual(len(self.data()['rounds']), 1)

    def test_malformed_review_preserves_published_state(self):
        self.run_helper('update_data.py', 'v0', '--no-images')
        before = {p.name: p.read_bytes() for p in (self.h / 'artifact').iterdir()}
        (self.h / 'critiques/v0-user.md').write_text(critique('99'))
        self.run_helper('update_data.py', 'v0', '--no-images', ok=False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.h / 'artifact').iterdir()})

    def test_rubric_and_specimen_changes_need_new_baseline(self):
        self.run_helper('update_data.py', 'v0', '--no-images')
        self.cfg['critics']['other'] = 'Other'
        self.save_config()
        self.run_helper('update_data.py', 'v1', '--no-images', ok=False)

    def test_paths_cannot_escape_and_duplicate_shots_fail(self):
        for value in ('../outside', '/tmp/outside', 'x/y', ''):
            self.run_helper('update_data.py', value, '--no-images', ok=False)
        self.cfg['shots'] *= 2
        self.save_config()
        self.run_helper('update_data.py', 'v0', '--no-images', ok=False)

    def test_symlink_escape_refused(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.h / 'artifact').symlink_to(outside)
            self.run_helper('update_data.py', 'v0', '--no-images', ok=False)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_images_require_complete_set_and_preserve_original_bytes(self):
        shots = self.h / 'shots/v0'
        shots.mkdir(parents=True)
        (shots / 'home-fold.png').write_bytes(PNG)
        self.run_helper('prep_shots.py', 'v0', ok=False)
        self.assertFalse((self.h / 'artifact/img/v0').exists())
        (shots / 'home-full.png').write_bytes(PNG)
        self.run_helper('prep_shots.py', 'v0')
        self.assertEqual((self.h / 'artifact/img/v0/home-fold.png').read_bytes(), PNG)
        self.run_helper('prep_shots.py', 'v0', ok=False)
        self.run_helper('update_data.py', 'v0')
        self.assertTrue(self.data()['rounds'][0]['images'])
        (self.h / 'artifact/img/v0/home-full.png').unlink()
        self.run_helper('update_data.py', 'v0', '--no-images', ok=False)

    def test_truncated_critique_cannot_complete_review(self):
        (self.h / 'critiques/v0-user.md').write_text(critique().split('## Previous round')[0])
        self.run_helper('update_data.py', 'v0', '--no-images', ok=False)
        self.assertFalse((self.h / 'artifact/data.json').exists())

    def test_capture_conditions_cannot_change_within_series(self):
        self.cfg['viewports'] = {'desktop': {'width': 1440, 'height': 1000}}
        self.cfg['shots'][0].update(file='index.html', vp='desktop')
        self.save_config()
        self.run_helper('update_data.py', 'v0', '--no-images')
        self.cfg['viewports']['desktop']['width'] = 390
        self.save_config()
        self.run_helper('update_data.py', 'v1', '--no-images', ok=False)

    def test_corrupt_png_is_rejected_before_destination_creation(self):
        shots = self.h / 'shots/v0'
        shots.mkdir(parents=True)
        for kind in ('fold', 'full'):
            (shots / f'home-{kind}.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'\0' * 16)
        self.run_helper('prep_shots.py', 'v0', ok=False)
        self.assertFalse((self.h / 'artifact/img/v0').exists())

    def test_images_not_assumed_when_absent(self):
        self.run_helper('update_data.py', 'v0', ok=False)
        self.assertFalse((self.h / 'artifact/data.json').exists())

    @unittest.skipUnless(shutil.which('node'), 'Node.js required')
    def test_gate_propagates_early_failure_and_missing_specimen(self):
        (self.h / 'checks').mkdir()
        (self.h / 'scripts/checks').mkdir(parents=True)
        (self.h / 'out/v0').mkdir(parents=True)
        shutil.copy(SKILL / 'assets/run.sh.example', self.h / 'checks/run.sh')
        (self.h / 'scripts/checks/cls.js').write_text('process.exit(7);')
        (self.h / 'scripts/checks/speed.js').write_text('process.exit(0);')
        cmd = ['bash', str(self.h / 'checks/run.sh'), 'v0']
        result = subprocess.run(cmd, env=self.env, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'missing', result.stderr)
        for name in ('index.html', 'detail.html', 'long-page.html'):
            (self.h / 'out/v0' / name).write_text('fixture')
        self.assertEqual(subprocess.run(cmd, env=self.env).returncode, 7)

    @unittest.skipUnless(shutil.which('node'), 'Node.js required')
    def test_web_helpers_reject_empty_inputs_before_browser_launch(self):
        for name in ('cls.js', 'speed.js'):
            for arg in ('', 'missing.html'):
                result = subprocess.run(['node', str(SKILL / 'scripts/checks' / name), arg],
                                        env=self.env, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('browserType.launch', result.stderr)


if __name__ == '__main__':
    unittest.main()

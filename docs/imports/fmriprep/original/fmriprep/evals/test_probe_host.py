"""Local helper tests only; these do not qualify any real fMRIPrep installation."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'probe_host.py'
spec = importlib.util.spec_from_file_location('probe_host', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def test_parse_space_path(self):
        self.assertEqual(probe.parse_paths(['work=/tmp/a b'])['work'], Path('/tmp/a b'))

    def test_relative_rejected(self):
        with self.assertRaises(ValueError):
            probe.parse_paths(['work=relative'])

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            probe.parse_paths(['work=/tmp/a', 'work=/tmp/b'])

    def test_missing_path_is_observation(self):
        result = probe.inspect_path(Path('/definitely-missing-fmriprep-test-path'))
        self.assertFalse(result['exists'])
        self.assertFalse(result['compute_access_verified'])

    def test_no_commands_by_default(self):
        with patch.object(probe.subprocess, 'run') as run:
            result = probe.collect({})
        run.assert_not_called()
        self.assertFalse(result['ready_for_preprocessing'])

    def test_secret_environment_not_dumped(self):
        with patch.dict(os.environ, {'EXAMPLE_SECRET_TOKEN': 'do-not-report', 'SLURM_JOB_ID': '123'}):
            result = probe.collect({})
        self.assertNotIn('do-not-report', json.dumps(result))
        self.assertEqual(result['scheduler_environment']['SLURM_JOB_ID'], '123')

    def test_write_probe_leaves_directory_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='probe test ') as directory:
            target = Path(directory)
            original = target / 'keep.txt'
            original.write_text('unchanged')
            result = probe.collect({'work': target}, write_roles=['work'])
            self.assertTrue(result['write_probes']['work']['passed'])
            self.assertEqual(list(target.iterdir()), [original])
            self.assertEqual(original.read_text(), 'unchanged')

    def test_raw_write_role_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                probe.validate_write_target('bids', {'bids': Path(directory)})

    def test_input_overlap_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            child = target / 'raw-subdir'
            child.mkdir()
            with self.assertRaises(ValueError):
                probe.validate_write_target('work', {'bids': target, 'work': child})

    def test_symlink_overlap_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            raw = target / 'raw'
            raw.mkdir()
            alias = target / 'alias'
            alias.symlink_to(raw, target_is_directory=True)
            with self.assertRaises(ValueError):
                probe.validate_write_target('work', {'bids': raw, 'work': alias})

    def test_version_timeout_reported(self):
        with patch.object(probe.subprocess, 'run', side_effect=subprocess.TimeoutExpired('x', 0.01)):
            result = probe.version_probe('/fake/executable', 0.01)
        self.assertEqual(result['error'], 'timeout')

    def test_cli_json_and_failed_write_exit(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = probe.main(['--write-probe', 'work'])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(buffer.getvalue())['write_probes']['work']['passed'])

    def test_declared_compute_is_not_certification(self):
        result = probe.collect({}, context='compute')
        self.assertEqual(result['context_declared_by_caller'], 'compute')
        self.assertFalse(result['ready_for_preprocessing'])


if __name__ == '__main__':
    unittest.main()

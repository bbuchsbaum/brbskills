"""Local helper tests only; these do not qualify any real fMRIPrep installation."""
import contextlib
import importlib.util
import io
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'probe_host.py'
spec = importlib.util.spec_from_file_location('probe_host', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def make_tool(self, directory, body):
        tool = Path(directory) / 'fake-version-tool'
        tool.write_text('#!' + sys.executable + '\n' + body)
        tool.chmod(0o755)
        return tool

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
        with patch.object(probe.subprocess, 'Popen') as popen:
            result = probe.collect({})
        popen.assert_not_called()
        self.assertEqual(result['qualification_status'], 'not_assessed')
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

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_version_timeout_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = self.make_tool(directory, 'import time\ntime.sleep(30)\n')
            result = probe.version_probe(str(tool), 0.05)
        self.assertEqual(result['error'], 'timeout')
        self.assertEqual(result['timeout_seconds'], 0.05)

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_timeout_bounds_process_that_closes_its_pipes(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = self.make_tool(
                directory,
                'import os, time\nos.close(1)\nos.close(2)\ntime.sleep(30)\n',
            )
            started = time.monotonic()
            result = probe.version_probe(str(tool), 0.05)
            elapsed = time.monotonic() - started
        self.assertEqual(result['error'], 'timeout')
        self.assertLess(elapsed, 1.5)

    def test_non_posix_version_probe_is_explicitly_unsupported(self):
        with patch.object(probe.os, 'name', 'nt'), patch.object(probe.subprocess, 'Popen') as popen:
            result = probe.version_probe('/fake/executable', 1)
        popen.assert_not_called()
        self.assertEqual(result['error'], 'unsupported_platform')

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

    def test_malformed_path_inputs_rejected(self):
        for value in ('work', '= /tmp/no-role', 'bad-role=/tmp/invalid'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                probe.parse_paths([value])

    def test_version_output_is_explicitly_capped(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = self.make_tool(
                directory,
                "import sys\nsys.stdout.write('x' * 10000)\nsys.stderr.write('y' * 10000)\n",
            )
            result = probe.version_probe(str(tool), 1)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn('error', result)
        self.assertNotIn('cleanup_error', result)
        self.assertEqual(len(result['stdout']), probe.STDOUT_CAP_BYTES)
        self.assertEqual(len(result['stderr']), probe.STDERR_CAP_BYTES)
        self.assertTrue(result['stdout_truncated'])
        self.assertTrue(result['stderr_truncated'])

    @unittest.skipUnless(os.name == 'posix', 'process-group cleanup is POSIX-specific')
    def test_timeout_cleans_descendant_from_owned_process_group(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'descendant-survived'
            tool = self.make_tool(
                directory,
                "import subprocess, sys, time\n"
                "subprocess.Popen([sys.executable, '-c', "
                "'import pathlib, time, sys; time.sleep(.5); pathlib.Path(sys.argv[1]).write_text(\"alive\")', "
                f"{str(marker)!r}])\n"
                "time.sleep(30)\n",
            )
            result = probe.version_probe(str(tool), 0.05)
            time.sleep(0.7)
            self.assertEqual(result['error'], 'timeout')
            self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name == 'posix', 'process-group cleanup is POSIX-specific')
    def test_exited_parent_cleans_term_ignoring_descendant_with_closed_pipes(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'term-ignoring-descendant-survived'
            child = (
                'import os, pathlib, signal, sys, time; '
                'signal.signal(signal.SIGTERM, signal.SIG_IGN); os.close(1); os.close(2); '
                'time.sleep(.6); pathlib.Path(sys.argv[1]).write_text("alive")'
            )
            tool = self.make_tool(
                directory,
                'import subprocess, sys\n'
                f'subprocess.Popen([sys.executable, "-c", {child!r}, {str(marker)!r}])\n',
            )
            result = probe.version_probe(str(tool), 1)
            time.sleep(0.8)
            self.assertEqual(result['returncode'], 0)
            self.assertFalse(marker.exists())

    def test_read_failure_and_interrupt_always_cleanup(self):
        for failure in (OSError('synthetic read failure'), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as directory:
                tool = self.make_tool(directory, 'import time; time.sleep(30)\n')
                real_popen = probe.subprocess.Popen
                children = []
                def capture(*args, **kwargs):
                    child = real_popen(*args, **kwargs)
                    children.append(child)
                    return child
                with patch.object(probe.subprocess, 'Popen', side_effect=capture), \
                     patch.object(probe, '_bounded_output', side_effect=failure):
                    if isinstance(failure, KeyboardInterrupt):
                        with self.assertRaises(KeyboardInterrupt):
                            probe.version_probe(str(tool), 1)
                    else:
                        self.assertIn('synthetic read failure', probe.version_probe(str(tool), 1)['error'])
                self.assertIsNotNone(children[0].poll())
                self.assertTrue(children[0].stdout.closed)
                self.assertTrue(children[0].stderr.closed)

    @unittest.skipUnless(os.name == 'posix', 'SIGINT/process groups require POSIX')
    def test_real_sigint_stops_owned_version_process(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / 'ready'
            marker = Path(directory) / 'survived'
            tool = self.make_tool(directory,
                'import os, pathlib, time\n'
                f'pathlib.Path({str(ready)!r}).write_text(str(os.getpid()))\n'
                'time.sleep(.8)\n'
                f'pathlib.Path({str(marker)!r}).write_text("survived")\n')
            runner = subprocess.Popen([sys.executable, '-c',
                'import runpy,sys; runpy.run_path(sys.argv[1])["version_probe"](sys.argv[2],5)',
                str(SCRIPT), str(tool)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 3
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(ready.exists(), 'fake tool did not start')
                runner.send_signal(signal.SIGINT)
                runner.communicate(timeout=3)
                self.assertNotEqual(runner.returncode, 0)
                time.sleep(1)
                self.assertFalse(marker.exists())
            finally:
                if runner.poll() is None:
                    runner.kill(); runner.communicate(timeout=3)
                # Only a PID written by this test's fake new-session process.
                if ready.exists():
                    try:
                        os.killpg(int(ready.read_text()), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass

    def run_signalled_cli(self, signum):
        """Run the real CLI with a fake sbatch on PATH, signal it mid-probe."""
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / 'ready'
            marker = Path(directory) / 'survived'
            tool = self.make_tool(directory,
                'import os, pathlib, time\n'
                f'pathlib.Path({str(ready)!r}).write_text(str(os.getpid()))\n'
                'time.sleep(.8)\n'
                f'pathlib.Path({str(marker)!r}).write_text("survived")\n')
            tool.rename(Path(directory) / 'sbatch')
            env = dict(os.environ, PATH=directory)
            runner = subprocess.Popen([sys.executable, str(SCRIPT), '--versions', '--version-timeout', '5'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            try:
                deadline = time.monotonic() + 3
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(ready.exists(), 'fake tool did not start')
                runner.send_signal(signum)
                _, err = runner.communicate(timeout=3)
                time.sleep(1)
                return runner.returncode, err.decode(errors='replace'), marker.exists()
            finally:
                if runner.poll() is None:
                    runner.kill(); runner.communicate(timeout=3)
                # Only a PID written by this test's fake new-session process.
                if ready.exists():
                    try:
                        os.killpg(int(ready.read_text()), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass

    @unittest.skipUnless(os.name == 'posix', 'termination signals/process groups require POSIX')
    def test_real_sigterm_and_sighup_stop_owned_version_process(self):
        signals = [signal.SIGTERM, signal.SIGHUP]
        if signal.getsignal(signal.SIGINT) is signal.default_int_handler:
            signals.append(signal.SIGINT)  # not when launched with SIGINT ignored
        for signum in signals:
            with self.subTest(signal=signum.name):
                code, err, survived = self.run_signalled_cli(signum)
                self.assertEqual(code, 128 + signum)
                self.assertIn('owned version-probe group was stopped', err)
                self.assertNotIn('Traceback', err)
                self.assertFalse(survived)

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_signal_during_process_creation_still_stops_owned_group(self):
        # Deterministic: the signal lands inside Popen, before ``proc`` is bound.
        for signum, expected in ((signal.SIGTERM, probe.ProbeInterrupted),
                                 (signal.SIGINT, KeyboardInterrupt)):
            with self.subTest(signal=signum.name), tempfile.TemporaryDirectory() as directory:
                marker = Path(directory) / 'survived'
                tool = self.make_tool(directory,
                    f'import pathlib, time\ntime.sleep(.6)\npathlib.Path({str(marker)!r}).write_text("x")\n')
                started = []

                class SignalAtCreation(subprocess.Popen):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        started.append(self.pid)
                        os.kill(os.getpid(), signum)

                with patch.object(probe.subprocess, 'Popen', SignalAtCreation):
                    with self.assertRaises(expected):
                        probe.version_probe(str(tool), 5)
                time.sleep(.9)
                self.assertFalse(marker.exists())
                with self.assertRaises(ProcessLookupError):
                    os.killpg(started[0], 0)

    @unittest.skipUnless(os.name == 'posix', 'signal handlers are POSIX-specific')
    def test_signal_between_handler_installs_or_restores_is_delivered_once(self):
        watched = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
        received = []
        previous_hup = signal.signal(signal.SIGHUP, lambda signum, _frame: received.append(signum))
        real_signal = signal.signal
        try:
            before = {sig: signal.getsignal(sig) for sig in watched}
            with tempfile.TemporaryDirectory() as directory:
                tool = str(self.make_tool(directory, 'print("v1")\n'))
                for position in range(1, 2 * len(watched) + 1):
                    with self.subTest(position=position):
                        received.clear()
                        calls = []

                        def spy(signum, handler):
                            old = real_signal(signum, handler)
                            calls.append(signum)
                            if len(calls) == position:
                                os.kill(os.getpid(), signal.SIGHUP)
                            return old

                        interrupted = False
                        with patch.object(probe.signal, 'signal', spy):
                            try:
                                probe.version_probe(tool, 2)
                            except probe.ProbeInterrupted as exc:
                                self.assertEqual(exc.signum, signal.SIGHUP)
                                interrupted = True
                        self.assertEqual(len(received) + interrupted, 1)
                        self.assertEqual(before, {sig: signal.getsignal(sig) for sig in watched})
        finally:
            real_signal(signal.SIGHUP, previous_hup)

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_stuck_leader_reports_incomplete_cleanup_without_masking_timeout(self):
        held = []

        def stuck(proc):
            held.append(proc)
            raise subprocess.TimeoutExpired(proc.args, 0.25)  # e.g. D-state leader

        with tempfile.TemporaryDirectory() as directory:
            tool = self.make_tool(directory, 'import time\ntime.sleep(3)\n')
            try:
                with patch.object(probe, '_stop_owned_probe', stuck):
                    result = probe.version_probe(str(tool), 0.1)
            finally:
                for proc in held:
                    with contextlib.suppress(OSError):
                        os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=3)
        self.assertEqual(result['error'], 'timeout')
        self.assertEqual(result['cleanup_status'], 'incomplete')
        self.assertFalse(result['leader_reaped'])
        self.assertIn('cleanup_error', result)

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_interrupted_cli_preserves_cleanup_failure_and_signal_exit(self):
        for signum in (signal.SIGINT, signal.SIGTERM):
            for failure in (subprocess.TimeoutExpired('fake-tool', 0.25),
                            OSError('synthetic cleanup failure')):
                with self.subTest(signal=signum, failure=type(failure).__name__):
                    child = Mock(returncode=None, stdout=io.BytesIO(), stderr=io.BytesIO())
                    stderr = io.StringIO()
                    with patch.object(probe, 'collect', side_effect=lambda *a, **k:
                                      probe.version_probe('fake-tool', 1)), \
                         patch.object(probe.subprocess, 'Popen', return_value=child), \
                         patch.object(probe, '_bounded_output', side_effect=probe._interruption(signum)), \
                         patch.object(probe, '_stop_owned_probe', side_effect=failure), \
                         contextlib.redirect_stderr(stderr):
                        code = probe.main(['--versions'])
                    self.assertEqual(code, 128 + signum)
                    self.assertIn('cleanup incomplete', stderr.getvalue())
                    self.assertIn(str(failure), stderr.getvalue())
                    self.assertNotIn('was stopped', stderr.getvalue())

    def test_interruption_without_probe_evidence_does_not_claim_cleanup(self):
        stderr = io.StringIO()
        with patch.object(probe, 'collect', side_effect=KeyboardInterrupt()), \
             contextlib.redirect_stderr(stderr):
            self.assertEqual(probe.main([]), 128 + signal.SIGINT)
        self.assertIn('completion was not established', stderr.getvalue())
        self.assertNotIn('was stopped', stderr.getvalue())

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_timeout_of_term_ignoring_leader_reports_complete_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            tool = self.make_tool(directory,
                'import signal, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\ntime.sleep(5)\n')
            result = probe.version_probe(str(tool), 0.1)
        self.assertEqual(result['error'], 'timeout')
        self.assertEqual(result['cleanup_status'], 'complete')
        self.assertNotIn('cleanup_error', result)

    @unittest.skipUnless(os.name == 'posix', 'signal handlers are POSIX-specific')
    def test_signal_handlers_restored_after_probe(self):
        before = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
        with tempfile.TemporaryDirectory() as directory:
            probe.version_probe(str(self.make_tool(directory, 'print("v1")\n')), 1)
        self.assertEqual(before, {sig: signal.getsignal(sig) for sig in before})

    @unittest.skipUnless(os.name == 'posix', 'signal handlers are POSIX-specific')
    def test_ignored_sighup_stays_ignored(self):
        previous = signal.signal(signal.SIGHUP, signal.SIG_IGN)
        try:
            with probe._termination_signals_raise():
                self.assertIs(signal.getsignal(signal.SIGHUP), signal.SIG_IGN)
            self.assertIs(signal.getsignal(signal.SIGHUP), signal.SIG_IGN)
        finally:
            signal.signal(signal.SIGHUP, previous)

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_nonzero_exit_code_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            result = probe.version_probe(str(self.make_tool(directory, 'raise SystemExit(3)\n')), 1)
        self.assertEqual(result['returncode'], 3)
        self.assertNotIn('error', result)

    @unittest.skipUnless(os.name == 'posix', 'version probes are intentionally POSIX-only')
    def test_versions_end_to_end_never_executes_qsub_or_bsub(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ('qsub', 'bsub', 'sbatch'):
                marker = Path(directory) / f'{name}-ran'
                tool = self.make_tool(directory,
                    f'import pathlib\npathlib.Path({str(marker)!r}).write_text("ran")\nprint("{name} 1.0")\n')
                tool.rename(Path(directory) / name)
            with patch.dict(os.environ, {'PATH': directory}):
                report = probe.collect({}, versions=True, timeout=2)
            for name in ('qsub', 'bsub'):
                self.assertIsNotNone(report['tools'][name]['path'])
                self.assertNotIn('version_probe', report['tools'][name])
                self.assertFalse((Path(directory) / f'{name}-ran').exists())
            self.assertEqual(report['tools']['sbatch']['version_probe']['stdout'], 'sbatch 1.0')
            self.assertFalse(report['ready_for_preprocessing'])

    def test_symlink_loop_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a', Path(directory) / 'b'
            a.symlink_to(b); b.symlink_to(a)
            observed = probe.inspect_path(a)
            if sys.version_info < (3, 13):  # older resolve() raises on loops
                self.assertIn('error', observed)
            else:
                self.assertFalse(observed['exists'])
            report = probe.collect({'work': a, 'bids': b}, write_roles=['work'])
            self.assertFalse(report['write_probes']['work']['passed'])
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = probe.main(['--path', f'work={a}', '--write-probe', 'work'])
            self.assertEqual(code, 2)
            self.assertFalse(json.loads(buffer.getvalue())['write_probes']['work']['passed'])

    def test_no_implicit_side_effects(self):
        with patch.object(probe, 'version_probe') as version, patch.object(probe, 'write_probe') as write:
            report = probe.collect({})
        version.assert_not_called()
        write.assert_not_called()
        self.assertEqual(report['write_probes'], {})


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Bounded, local environment inventory; never a launch-readiness certificate.

No third-party dependencies. No scheduler submission, installation, data transfer,
image pull, or preprocessing. Version commands and writes require explicit flags.
Path roles are supplied by the caller; this tool is not a security sandbox.

On POSIX, each opt-in version probe starts a new process session and terminates
that session if the probe times out or leaves descendants behind. SIGINT, SIGTERM
and SIGHUP received during a probe, including while the child is being created,
also run that cleanup before the helper exits.
This can clean only processes created by this helper; it cannot prove that
unrelated processes, remote launchers, containers, or descendants that escape into
a new session stopped, and SIGKILL of the helper cannot run any cleanup.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any

TOOLS = ('apptainer', 'singularity', 'docker', 'fmriprep-docker',
         'fmriprep', 'sbatch', 'squeue', 'qsub', 'bsub')
VERSION_TOOLS = frozenset(('apptainer', 'singularity', 'docker', 'fmriprep-docker',
                           'fmriprep', 'sbatch', 'squeue'))
WRITE_ROLES = frozenset(('work', 'output', 'logs', 'status', 'tmp', 'home', 'cache'))
INPUT_ROLES = frozenset(('bids', 'raw', 'input', 'license'))
ENV_ALLOWLIST = (
    'SLURM_JOB_ID', 'SLURM_ARRAY_JOB_ID', 'SLURM_ARRAY_TASK_ID',
    'SLURM_CPUS_PER_TASK', 'SLURM_CPUS_ON_NODE', 'SLURM_MEM_PER_NODE',
    'SLURM_MEM_PER_CPU', 'PBS_JOBID', 'PBS_NP', 'JOB_ID', 'SGE_TASK_ID',
    'NSLOTS', 'LSB_JOBID', 'LSB_DJOB_NUMPROC',
)
STDOUT_CAP_BYTES = 2000
STDERR_CAP_BYTES = 1000
_POLL_SECONDS = 0.05
_TERMINATE_GRACE_SECONDS = 0.25
_FORWARDED_SIGNALS = tuple(getattr(signal, name) for name in ('SIGTERM', 'SIGHUP')
                           if hasattr(signal, name))
_INTERRUPT_SIGNALS = (signal.SIGINT,) + _FORWARDED_SIGNALS


class ProbeInterrupted(BaseException):
    """A termination signal arrived while probing; cleanup may be incomplete."""

    def __init__(self, signum: int) -> None:
        super().__init__(f'interrupted by signal {signum}')
        self.signum = signum


def _interruption(signum: int) -> BaseException:
    # SIGINT keeps its ordinary KeyboardInterrupt meaning for callers.
    return KeyboardInterrupt() if signum == signal.SIGINT else ProbeInterrupted(signum)


def _deliver_pending(state: dict[str, Any]) -> None:
    """Raise a signal recorded while delivery was deferred, exactly once."""
    signum = state['pending']
    if signum is not None and not state['delivered']:
        state['delivered'] = True
        raise _interruption(signum)


@contextlib.contextmanager
def _termination_signals_raise():
    """Temporarily turn SIGINT/SIGTERM/SIGHUP into exceptions so cleanup can run.

    Only the main thread may install handlers; elsewhere the defaults stay in place
    (documented limit). While ``state['defer']`` is set (process creation, cleanup,
    handler restore) a signal is recorded instead of raised, then delivered once
    the owned process group can be stopped or the previous handlers are restored.
    """
    state: dict[str, Any] = {'defer': False, 'pending': None, 'delivered': False}
    if threading.current_thread() is not threading.main_thread():
        yield state
        return

    def handler(signum, _frame):
        if state['pending'] is not None:
            return  # one interruption is enough; cleanup is already on its way
        state['pending'] = signum
        if not state['defer']:
            state['delivered'] = True
            raise _interruption(signum)

    previous = {}
    try:
        # Install atomically too: a signal between installs is recorded, and every
        # replaced handler is remembered before anything can raise.
        state['defer'] = True
        for signum in _INTERRUPT_SIGNALS:
            current = signal.getsignal(signum)
            if current is signal.SIG_IGN:
                continue  # e.g. nohup: an ignored signal must stay ignored
            if signum == signal.SIGINT and current is not signal.default_int_handler:
                continue  # respect a caller's own SIGINT handling
            previous[signum] = current
            signal.signal(signum, handler)
        state['defer'] = False
        _deliver_pending(state)
        yield state
    finally:
        # Restore atomically: a signal landing between individual restores is
        # recorded, then delivered after every previous handler is back.
        state['defer'] = True
        for signum, old in previous.items():
            signal.signal(signum, signal.SIG_DFL if old is None else old)
        state['defer'] = False
        _deliver_pending(state)


def parse_paths(values: list[str]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for item in values:
        role, sep, value = item.partition('=')
        if not sep or not role or not value:
            raise ValueError('Each --path must have the form role=/absolute/path')
        if not role.replace('_', '').isalnum():
            raise ValueError(f'Invalid path role: {role!r}')
        if role in paths:
            raise ValueError(f'Duplicate path role: {role}')
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError(f'Path for {role} must be absolute')
        paths[role] = path
    return paths


def inspect_path(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {'path': str(path)}
    try:
        result.update(resolved_path=str(path.resolve()), exists=path.exists(),
                      is_dir=path.is_dir(), is_file=path.is_file(),
                      is_symlink=path.is_symlink(),
                      current_process_readable_hint=os.access(path, os.R_OK),
                      current_process_writable_hint=os.access(path, os.W_OK))
    except (OSError, RuntimeError) as exc:
        # RuntimeError: symlink loops on Python < 3.13.
        result['error'] = str(exc)
    result['compute_access_verified'] = False
    return result


def validate_write_target(role: str, paths: dict[str, Path]) -> Path:
    if role not in WRITE_ROLES:
        raise ValueError(f'Write role {role!r} is not allowed; choose {sorted(WRITE_ROLES)}')
    if role not in paths:
        raise ValueError(f'Write role {role!r} needs an explicit --path')
    try:
        target = paths[role].resolve(strict=True)
    except RuntimeError as exc:  # symlink loop on Python < 3.13
        raise ValueError(f'Write target for {role} cannot be resolved: {exc}') from None
    if not target.is_dir():
        raise ValueError(f'Write target for {role} must be an existing directory')
    for input_role in INPUT_ROLES:
        if input_role in paths:
            try:
                source = paths[input_role].resolve()
            except RuntimeError as exc:
                raise ValueError(f'Input path {input_role!r} cannot be resolved: {exc}') from None
            if target == source or source in target.parents:
                raise ValueError(f'Write target overlaps input-designated path {input_role!r}')
    return target


def write_probe(target: Path) -> dict[str, Any]:
    """Write and remove only one uniquely created temporary file."""
    with tempfile.NamedTemporaryFile(prefix='.fmriprep-probe-', dir=target,
                                     mode='wb', delete=True) as handle:
        handle.write(b'fmriprep-companion-write-probe\n')
        handle.flush()
        os.fsync(handle.fileno())
        created = handle.name
    if Path(created).exists():
        raise OSError(f'Unique probe file was not removed: {created}')
    return {'passed': True, 'scope': 'current_process_and_mount_namespace',
            'created_and_removed_unique_file': True}


def _leader_exited(proc: subprocess.Popen[bytes]) -> bool:
    """Detect leader exit; where supported, leave it unreaped so its PID (and so
    the owned group ID) cannot be reused before group cleanup."""
    if proc.returncode is not None:
        return True
    # Linux only: macOS reports EPERM when signalling a group whose sole member is
    # an unreaped leader, which would make clean exits look like cleanup failures.
    if sys.platform.startswith('linux') and hasattr(os, 'waitid'):
        try:
            return os.waitid(os.P_PID, proc.pid,
                             os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
        except ChildProcessError:
            pass
    return proc.poll() is not None


def _stop_owned_probe(proc: subprocess.Popen[bytes]) -> None:
    """Stop only the new POSIX group; report permission/cleanup errors to caller.

    Off Linux the leader may already be reaped, leaving a small PID-reuse window
    before the group signal; that limit is documented.
    """
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        proc.wait(timeout=_TERMINATE_GRACE_SECONDS)
        return
    except PermissionError:
        # Never leave the leader unreaped; still report the unproven group cleanup.
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=_TERMINATE_GRACE_SECONDS)
        raise
    # Parent exit is not evidence that descendants honored TERM.
    time.sleep(_TERMINATE_GRACE_SECONDS)
    if not sys.platform.startswith('linux'):
        # macOS reports EPERM when signalling a group whose only member is the
        # unreaped (zombie) leader; reap it first. Documented PID-reuse window.
        proc.poll()
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS may expose a reaped group as EPERM. Do not claim cleanup proof.
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=_TERMINATE_GRACE_SECONDS)
        raise
    proc.wait(timeout=_TERMINATE_GRACE_SECONDS)


def _bounded_output(proc: subprocess.Popen[bytes], timeout: float) -> tuple[bytes, bytes, bool, bool, bool]:
    """Bound time independently of EOF; retain at most the documented byte caps."""
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    caps = {'stdout': STDOUT_CAP_BYTES, 'stderr': STDERR_CAP_BYTES}
    truncated = {'stdout': False, 'stderr': False}
    timed_out = False
    deadline = time.monotonic() + timeout
    with selectors.DefaultSelector() as selector:
        for name, stream in (('stdout', proc.stdout), ('stderr', proc.stderr)):
            selector.register(stream, selectors.EVENT_READ, name)
        while True:
            running = not _leader_exited(proc)
            remaining = deadline - time.monotonic()
            if running and remaining <= 0:
                timed_out = True
                break
            wait = min(_POLL_SECONDS, remaining) if running else 0
            if selector.get_map():
                events = selector.select(wait)
            else:
                events = []
                if running:
                    time.sleep(wait)
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                name = key.data
                available = caps[name] - len(captured[name])
                captured[name].extend(chunk[:available])
                if len(chunk) > available:
                    truncated[name] = True
            if not running:
                # One final drain is enough for the small capture caps. Never
                # follow an escaped descendant's endless stream after parent exit.
                break
    return (bytes(captured['stdout']), bytes(captured['stderr']), timed_out,
            truncated['stdout'], truncated['stderr'])


def version_probe(executable: str, timeout: float) -> dict[str, Any]:
    argv = [executable, '--version']
    if os.name != 'posix':
        return {'argv': argv, 'error': 'unsupported_platform',
                'detail': 'bounded version probes require POSIX process-group cleanup'}
    if not 0 < timeout <= 30:
        return {'argv': argv, 'error': 'invalid_timeout'}
    signals = None
    try:
        with _termination_signals_raise() as signals:
            return _run_version_probe(argv, timeout, signals)
    except (KeyboardInterrupt, ProbeInterrupted) as exc:
        # Preserve cleanup evidence even when interruption prevents a JSON return,
        # including signals deferred until handler restoration.
        exc.probe_result = signals.get('probe_result') if signals else None
        raise


def _run_version_probe(argv: list[str], timeout: float, signals: dict[str, Any]) -> dict[str, Any]:
    proc = None
    timed_out = False
    result: dict[str, Any] = {'argv': argv}
    signals['probe_result'] = result
    try:
        # A signal during fork/exec would otherwise escape before ``proc`` is
        # bound, orphaning the child. Defer it until cleanup is possible.
        signals['defer'] = True
        try:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, start_new_session=True)
        finally:
            signals['defer'] = False
        _deliver_pending(signals)
        stdout, stderr, timed_out, stdout_truncated, stderr_truncated = _bounded_output(proc, timeout)
        if timed_out:
            result.update(error='timeout', timeout_seconds=timeout)
        result['stdout'] = stdout.decode(errors='replace').strip()
        result['stderr'] = stderr.decode(errors='replace').strip()
        if stdout_truncated:
            result['stdout_truncated'] = True
        if stderr_truncated:
            result['stderr_truncated'] = True
    except OSError as exc:
        result['error'] = str(exc)
    finally:
        # Also runs on KeyboardInterrupt, SIGTERM/SIGHUP (ProbeInterrupted) or a
        # failed selector/read. Nothing may skip cleanup of this owned group.
        signals['defer'] = True
        if proc is not None:
            result['cleanup_status'] = 'complete'
            try:
                _stop_owned_probe(proc)
            except (OSError, subprocess.TimeoutExpired) as exc:
                # Kept separate from ``error`` so a timeout is never masked.
                result['cleanup_status'] = 'incomplete'
                result['cleanup_error'] = str(exc)
                result.setdefault('error', 'cleanup_incomplete')
                if proc.returncode is None:
                    # e.g. uninterruptible I/O on a hung mount: report, never hide.
                    result['leader_reaped'] = False
            finally:
                for stream in (proc.stdout, proc.stderr):
                    if stream is not None:
                        stream.close()
            if not timed_out and proc.returncode is not None:
                result.setdefault('returncode', proc.returncode)
        signals['defer'] = False
    _deliver_pending(signals)
    return result


def visible_memory_kib() -> int | None:
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):
                return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def collect(paths: dict[str, Path], *, context: str = 'unknown',
            versions: bool = False, timeout: float = 3.0,
            write_roles: list[str] | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        'schema_version': 1,
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'hostname': socket.gethostname(),
        'context_declared_by_caller': context,
        'platform': {'system': platform.system(), 'release': platform.release(),
                     'architecture': platform.machine(), 'python': platform.python_version()},
        'scheduler_environment': {k: os.environ[k] for k in ENV_ALLOWLIST if k in os.environ},
        'host_visible_resources_not_entitlements': {
            'cpu_count': os.cpu_count(), 'mem_total_kib': visible_memory_kib()},
        'paths': {role: inspect_path(path) for role, path in paths.items()},
        'tools': {}, 'write_probes': {}, 'qualification_status': 'not_assessed',
        'ready_for_preprocessing': False,
        'unresolved': ['module setup and actual application entrypoint',
                       'compute-context runtime, CLI, image identity and architecture',
                       'container mount translation and all required assets',
                       'actual allocation/cgroup limits and site policy',
                       'authorized pilot, output checks, and scientific QC'],
    }
    if hasattr(os, 'sched_getaffinity'):
        try:
            report['host_visible_resources_not_entitlements']['affinity_cpu_count'] = len(os.sched_getaffinity(0))
        except OSError:
            pass
    for name in TOOLS:
        executable = shutil.which(name)
        record: dict[str, Any] = {'path': executable, 'usable_for_job_verified': False}
        if versions and executable and name in VERSION_TOOLS:
            record['version_probe'] = version_probe(executable, timeout)
        report['tools'][name] = record
    for role in write_roles or []:
        try:
            report['write_probes'][role] = write_probe(validate_write_target(role, paths))
        except (ValueError, OSError, RuntimeError) as exc:
            report['write_probes'][role] = {'passed': False, 'error': str(exc)}
    return report


def _interrupted_cleanup_message(exc: BaseException) -> str:
    result = getattr(exc, 'probe_result', None) or {}
    if result.get('cleanup_status') == 'complete':
        return 'owned version-probe group was stopped'
    if result.get('cleanup_status') == 'incomplete':
        return f"owned version-probe cleanup incomplete: {result['cleanup_error']}"
    return 'owned version-probe cleanup completion was not established'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', action='append', default=[], metavar='ROLE=/ABS/PATH')
    parser.add_argument('--context', choices=('unknown', 'login', 'compute', 'workstation'), default='unknown')
    parser.add_argument('--versions', action='store_true', help='Execute bounded --version probes (never qsub/bsub).')
    parser.add_argument('--version-timeout', type=float, default=3.0)
    parser.add_argument('--write-probe', action='append', default=[], metavar='ROLE',
                        help='Create/remove a unique file in an explicit existing output/work directory.')
    args = parser.parse_args(argv)
    if not 0 < args.version_timeout <= 30:
        parser.error('--version-timeout must be > 0 and <= 30 seconds')
    try:
        paths = parse_paths(args.path)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        report = collect(paths, context=args.context, versions=args.versions,
                         timeout=args.version_timeout, write_roles=args.write_probe)
    except ProbeInterrupted as exc:
        print(f'probe_host: {exc}; {_interrupted_cleanup_message(exc)}', file=sys.stderr)
        return 128 + exc.signum
    except KeyboardInterrupt as exc:
        print(f'probe_host: interrupted; {_interrupted_cleanup_message(exc)}', file=sys.stderr)
        return 128 + signal.SIGINT
    print(json.dumps(report, indent=2))
    return 2 if any(not p['passed'] for p in report['write_probes'].values()) else 0


if __name__ == '__main__':
    sys.exit(main())

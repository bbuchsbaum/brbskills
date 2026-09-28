#!/usr/bin/env python3
"""Bounded, local environment inventory; never a launch-readiness certificate.

No third-party dependencies. No scheduler submission, installation, data transfer,
image pull, or preprocessing. Version commands and writes require explicit flags.
Path roles are supplied by the caller; this tool is not a security sandbox.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
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
    except OSError as exc:
        result['error'] = str(exc)
    result['compute_access_verified'] = False
    return result


def validate_write_target(role: str, paths: dict[str, Path]) -> Path:
    if role not in WRITE_ROLES:
        raise ValueError(f'Write role {role!r} is not allowed; choose {sorted(WRITE_ROLES)}')
    if role not in paths:
        raise ValueError(f'Write role {role!r} needs an explicit --path')
    target = paths[role].resolve(strict=True)
    if not target.is_dir():
        raise ValueError(f'Write target for {role} must be an existing directory')
    for input_role in INPUT_ROLES:
        if input_role in paths:
            source = paths[input_role].resolve()
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


def version_probe(executable: str, timeout: float) -> dict[str, Any]:
    argv = [executable, '--version']
    try:
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, errors='replace', timeout=timeout, check=False)
        return {'argv': argv, 'returncode': proc.returncode,
                'stdout': proc.stdout.strip()[:2000],
                'stderr': proc.stderr.strip()[:1000]}
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'error': 'timeout', 'timeout_seconds': timeout}
    except OSError as exc:
        return {'argv': argv, 'error': str(exc)}


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
        'tools': {}, 'write_probes': {},
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
        except (ValueError, OSError) as exc:
            report['write_probes'][role] = {'passed': False, 'error': str(exc)}
    return report


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
    report = collect(paths, context=args.context, versions=args.versions,
                     timeout=args.version_timeout, write_roles=args.write_probe)
    print(json.dumps(report, indent=2))
    return 2 if any(not p['passed'] for p in report['write_probes'].values()) else 0


if __name__ == '__main__':
    sys.exit(main())

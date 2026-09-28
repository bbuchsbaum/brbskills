#!/usr/bin/env python3
"""Fixture-only payload: preserves the approved application argv as an array."""
import os
import subprocess
import sys

argv = [
    sys.executable,
    "/Users/bbuchsbaum/code/brbskills/skills/fmriprep/tests/fixtures/fake_runtime.py",
    "/data", "/out", "participant", "--participant-label", "01",
    "--output-spaces", "T1w", "MNI152NLin2009cAsym:res-2",
    "--nprocs", "8", "--omp-nthreads", "2", "--mem-mb", "16000",
    "--notrack", "--bids-filter-file", "/config/filter $literal; name.json",
    "--work-dir", "/work",
]
env = os.environ.copy()
env.update({"TEMPLATEFLOW_HOME": "/templateflow", "OMP_NUM_THREADS": "2"})
raise SystemExit(subprocess.run(argv, env=env, check=False).returncode)

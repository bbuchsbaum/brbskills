#!/usr/bin/env python3
"""Synthetic argv recorder. Does not run fMRIPrep, containers, or arbitrary commands."""
import json
import os
from pathlib import Path
import sys

if sys.argv[1:] == ['--version']:
    print('SYNTHETIC fmriprep fixture, no software version qualification')
else:
    target = os.environ.get('FMRIPREP_FIXTURE_CAPTURE')
    if not target:
        raise SystemExit('FMRIPREP_FIXTURE_CAPTURE must name a temporary capture file')
    with Path(target).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'argv': sys.argv[1:], 'env': {
            k: os.environ[k] for k in ('TEMPLATEFLOW_HOME', 'OMP_NUM_THREADS') if k in os.environ
        }, 'synthetic': True}) + '\n')

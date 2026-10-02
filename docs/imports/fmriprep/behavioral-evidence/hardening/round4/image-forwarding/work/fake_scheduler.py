#!/usr/bin/env python3
"""Local submission observer; no scheduler commands, script execution, or network."""
import json
import os
from pathlib import Path
import sys

if len(sys.argv) != 3 or sys.argv[1] not in {'query', 'submit'}:
    raise SystemExit('usage: fake_scheduler.py query TOKEN | submit SCRIPT')
if sys.argv[1] == 'query':
    print(Path(os.environ['FMRIPREP_FIXTURE_STATE']).read_text())
else:
    script = Path(sys.argv[2])
    if not script.is_file():
        raise SystemExit('missing fixture script')
    with Path(os.environ['FMRIPREP_FIXTURE_SUBMISSIONS']).open('a') as stream:
        stream.write(json.dumps({'script': str(script), 'synthetic': True}) + '\n')
    print('SYNTHETIC-123')

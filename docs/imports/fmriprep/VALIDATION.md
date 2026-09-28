# Preparation evidence — 2026-09-28

Scope: the import-preparation pass only. Later implementation and hardening edits,
including tracked-file changes, are recorded in [IMPLEMENTATION.md](IMPLEMENTATION.md).

- ZIP inventory: 18 regular files; extraction checked root, traversal and symlinks.
- All extracted file bytes match their archive members and recorded SHA-256 hashes.
- Separately supplied DESIGN.md matches the archived DESIGN.md byte for byte.
- Imported helper suite rerun locally:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
    -s docs/imports/fmriprep/original/fmriprep/evals -p 'test_*.py' -v
  ```

  Result: **13 tests passed**. These use temporary paths and mocks; they establish
  limited helper behavior, not actual fMRIPrep or scheduler readiness.
- All five supplied JSON files (four examples plus VALIDATION.json) parse.
- `.venv/bin/python scripts/skills.py check`: passed; both generated products
  match current sources, and the archived draft is not discovered as a skill.
  Initial use of system `python3` failed because PyYAML was absent; the existing
  repository virtual environment supplied the required dependency.
- `git diff --check`: passed for tracked changes. New review Markdown was also
  checked for trailing whitespace. No pre-existing tracked file was modified.

No maintained skill source was edited, so source regeneration is intentionally
not part of this preparation pass. No agent behavioral scenarios, BIDS dataset
validation, fMRIPrep run, container execution, upstream launcher tests, hosted CI,
or live scheduler qualification were performed. Historical result files under
`original/` remain unchanged and are not fresh evidence.

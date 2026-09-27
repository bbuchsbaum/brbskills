# Working on brbskills

- Edit `skills/<name>/` or `collections/<collection>/skills/<name>/`; `codex/` and `claude/` are generated, committed downloads.
- Collection-wide resources are authored in `collections/<collection>/shared/`. Root sync refreshes their per-skill copies before generating downloads; root check rejects drift.
- For skill authoring, use `CONTRIBUTING.md`. Keep shared instructions portable and load references conditionally.
- After source edits run `python scripts/skills.py sync`, then `python scripts/skills.py check` and affected tests. Development requires Python 3.10+ and `requirements-dev.txt`.
- Local tests use temporary fixtures and mocked Slurm; they do not authorize live cluster work.
- Preserve source provenance and verification limits. Size checks are not behavioral evaluation.

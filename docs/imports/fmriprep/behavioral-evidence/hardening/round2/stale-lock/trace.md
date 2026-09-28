# Trace
Files read:
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/operations.md (Classify failures; Stale FreeSurfer locks; Durable execution)
- fake_runtime.py, fake_scheduler.py (inspected only)

Commands run:
- ls -la <workdir>
- cat fake_runtime.py fake_scheduler.py; env | grep FMRIPREP (no FMRIPREP_FIXTURE_* vars set)

Not run (deliberately): no lock deletion, no fake_runtime invocation, no fake_scheduler submit. Scheduler state is unverified (no state fixture set, and synthetic output would not be real evidence), so the stale-lock preconditions are unmet. The response blocks on the scheduler check.

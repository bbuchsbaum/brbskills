# Trace

## Skill files read
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/execution.md (execution dimensions, optional provider protocol, evidence levels)
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/records.md (plan/execution binding, authorization scopes)
- /Users/bbuchsbaum/code/brbskills/skills/alliance-hpc/SKILL.md (optional Alliance guidance, read-only)
- /Users/bbuchsbaum/code/brbskills/skills/alliance-hpc/references/systems.md (cluster baseline profiles)

Not read: any tests/ directory; docs/.

## Commands run
- `ls -R` of the case directory; `cat case.json`
- `ls` of the fmriprep skill and its references; `ls -d` / `find -iname '*alliance*'` (excluding docs, tests) to locate the Alliance skill -> skills/alliance-hpc
- `ls tmp/` in the case dir (empty; no plan.json present)
- `cat` of the files listed above

Not run: fake_runtime.py, fake_scheduler.py (no execution or submission was called for), probe_host.py, probe.sh, records.py.
No submissions, network, installs, or writes outside the case dir (writes: response.md, trace.md).

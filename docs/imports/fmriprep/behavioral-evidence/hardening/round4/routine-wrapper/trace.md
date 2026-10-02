# Trace (in order)

1. Read `/Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md`
2. Command: `ls -la .../behav4/routine-wrapper/work/` (list the working directory)
3. Read `/Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/rriscripts.md` via `cat`, in the same command as a `cat` of `work/fake_runtime.py`. The combined command stopped at a malformed `echo =====` separator, so `fake_scheduler.py` was not printed.
4. Command: `cd .../work && cat fake_runtime.py; cat fake_scheduler.py` (read both synthetic stand-ins)
5. Read `/Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/execution.md`
6. Wrote `.../routine-wrapper/response.md`
7. Wrote `.../routine-wrapper/trace.md`

Not read: `references/records.md` (the user's own tracker is assumed), `semantics.md`, `bids-and-decisions.md`, `operations.md`, `sources.md`, and the skill's `tests/` directory.
Not run: `fake_runtime.py` and `fake_scheduler.py`. No scheduler, container, install or network commands were run.

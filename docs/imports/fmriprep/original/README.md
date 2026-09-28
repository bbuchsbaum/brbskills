# fMRIPrep companion skill

A portable, instruction-first skill for an agent with authorized shell access.
It prefers the rriscripts launcher when suitable but can independently resolve a
module/container/scheduler route. Site expertise such as an Alliance execution
skill is optional. No new daemon, package manager, or scheduling framework is
required.

## Contents

`fmriprep/SKILL.md` is the entrypoint. References supply BIDS-first interviewing,
scientific semantics, execution contracts, the reviewed rriscripts adapter,
operations/QC, and primary sources. Assets are deliberately unapproved example
records. `probe_host.py` is a small, tested standard-library environment inventory;
it is not a launch-readiness certificate. Evals describe acceptance scenarios.
`DESIGN.md` explains the architecture and implementation priorities.

## Repository placement and installation

Keep the canonical source at `rriscripts/skills/fmriprep/`, alongside rather than
inside the Python launcher package. Copy the included `fmriprep/` directory there.
Install or link that directory into the agent's skill discovery location.

Codex supports repository `.agents/skills/` and user `~/.agents/skills/`, including
symlinked skill directories. Claude Code supports project `.claude/skills/` and
user `~/.claude/skills/`. See A3/A4 in the source reference. Avoid multiple divergent
copies: maintain one source and refresh installed copies as part of release.

For a new repository installation, these commands create copies only if the
particular destination does not already exist; review existing installations
instead of overwriting them:

```bash
mkdir -p .agents/skills .claude/skills
[ -e .agents/skills/fmriprep ] || [ -L .agents/skills/fmriprep ] || \
  cp -R skills/fmriprep .agents/skills/fmriprep
[ -e .claude/skills/fmriprep ] || [ -L .claude/skills/fmriprep ] || \
  cp -R skills/fmriprep .claude/skills/fmriprep
```

## What is implemented

The skill instructions, targeted knowledge references, example contracts,
behavioral evaluation suite, and bounded host probe are supplied. They are usable
by an agent to inspect and plan, and to write/review an appropriate job script.
There is no automatic JSON-to-scheduler compiler, automatic BIDS parser, or
finished universal site adapter in this bundle. Those tasks use existing tools
and the agent's explicitly documented workflow. The examples must not be passed
to the launcher's INI config interface.

No dataset was inspected or launched, no cluster profile was verified, and no
repository changes were pushed. Source-specific cautions are based on inspection,
not claimed end-to-end testing of the launcher. Real-world qualification requires
the representative compute probe and full-quality pilot described in the skill.

## Test the bundled helper

```bash
python -m unittest discover -s fmriprep/evals -p 'test_*.py' -v
python fmriprep/scripts/probe_host.py --path work=/an/existing/path
```

The helper never installs, submits, transfers data, or starts preprocessing. Write
probes and executable version probes require explicit flags. Do not send its
site/path report outside the authorized environment without reviewing it.

# Trace

Files read:
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/execution.md
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/bids-and-decisions.md (lines 1-80)
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/operations.md (lines 95-135)
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/semantics.md (lines 100-125)

Commands run:
- ls of working dir and skill directory listing (test file names appeared in the listing; none were opened)
- grep for confound/motion/spline/GLM terms across semantics.md, bids-and-decisions.md, operations.md
- sed to read the sections above
- heredocs writing response.md and trace.md

Not run: probe_host.py, fake_runtime.py, fake_scheduler.py. No data or target existed yet, so there was nothing to execute.
No preferences were saved: motion24 and B-spline are downstream-only choices.

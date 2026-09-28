# Trace

Skill files read (under /Users/bbuchsbaum/code/brbskills/skills/fmriprep/):
- SKILL.md
- references/rriscripts.md (installed-launcher task)
- references/execution.md (prepare/run)
- references/records.md (prepare/run)
- references/operations.md, Gating/pilot-reuse and durable-execution sections only (grep for "pilot")

Not read: tests/, docs/, other references (semantics, bids-and-decisions, sources), assets/, scripts source.

Commands run:
- cat of SKILL.md, the references above, case.json and the fixture scripts (read-only)
- ls of the skill directory (tests/ entries filtered out) and the case directory
- grep of operations.md for pilot sections
- heredoc writes of response.md and trace.md in the case directory

Not run: fake_runtime.py and fake_scheduler.py. The request was to prepare, not to execute or submit, and no launcher is present to render argv. No submission, network access or installation.

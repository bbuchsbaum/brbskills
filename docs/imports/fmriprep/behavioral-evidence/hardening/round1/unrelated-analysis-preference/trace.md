# Trace

## Skill files read
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md (full)
- references/bids-and-decisions.md (full). Main guidance: do not interview about motion24 or high-pass/first-level choices; save preferences only on explicit request.
- references/execution.md (first ~60 lines: boundary, records, execution dimensions)
- references/operations.md (lines 90-110: downstream handoff; also grepped for confound/motion)
- references/semantics.md (lines 15-30: STC/nonsteady-state and not-denoised wording; also grepped)
- Not read: tests/, docs/, records.md, rriscripts.md, sources.md.

## Commands run
- `ls -R` of the case dir and `cat case.json`
- `cat` of SKILL.md and bids-and-decisions.md; `sed`/`head` excerpts of execution.md, operations.md, semantics.md; `grep -i` for confound/motion/cosine terms
- No fixtures were executed (no data or authorization for execution). No preferences file was written.

# Trace

## Skill files read
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/rriscripts.md (read in full)
- /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/records.md and execution.md: only the lines matching "validat" or "recon", found with grep. Neither file was read in full.
- Not read: tests/, docs/, or the other references.

## Commands run
- `find . -type f; cat case.json` in the case directory
- `cat` of SKILL.md and rriscripts.md; `ls` of the skill directory
- `grep -n -i "validat\|recon"` on records.md and execution.md

## Execution
- I didn't run fixtures/fake_runtime.py or fake_scheduler.py. The request was a configuration review, the launcher isn't installed here, and nothing was submitted.

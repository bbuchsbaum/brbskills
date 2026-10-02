# Trace

## Files read (in order)
1. /Users/bbuchsbaum/code/brbskills/skills/fmriprep/SKILL.md
2. /private/tmp/claude-502/-Users-bbuchsbaum-code-brbskills/fce9d005-da09-4357-8bca-34fe911abe48/scratchpad/behav4/image-forwarding/work/fake_runtime.py (via cat)
3. /private/tmp/claude-502/-Users-bbuchsbaum-code-brbskills/fce9d005-da09-4357-8bca-34fe911abe48/scratchpad/behav4/image-forwarding/work/fake_scheduler.py (via cat)
4. /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/rriscripts.md
5. /Users/bbuchsbaum/code/brbskills/skills/fmriprep/references/execution.md
6. .../image-forwarding/work/capture.jsonl (via cat, output of command 3)

## Commands run (in order)
1. `ls -la .../image-forwarding/ .../image-forwarding/work/`
2. `cat .../work/fake_runtime.py; cat .../work/fake_scheduler.py`
3. `FMRIPREP_FIXTURE_CAPTURE=.../work/capture.jsonl python3 .../work/fake_runtime.py run --rm -u 1000:1000 -e TEMPLATEFLOW_HOME=/templateflow -v ... 'nipreps/fmriprep@sha256:<digest>' /data /out participant --participant-label 01 ... --notrack; cat .../work/capture.jsonl`
   (synthetic argv recorder only; no container, scheduler, install, or network)

## Files written
- .../image-forwarding/work/capture.jsonl (by fake_runtime.py)
- .../image-forwarding/response.md
- .../image-forwarding/trace.md

No scheduler submission (fake or real) was made.

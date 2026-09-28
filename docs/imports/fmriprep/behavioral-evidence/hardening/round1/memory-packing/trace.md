# Trace
Skill files read:
- skills/fmriprep/SKILL.md
- skills/fmriprep/references/execution.md: grep for packing/concurrency terms, then lines 130-169 ("Resources and storage", "Minimal fallback policy")
- skills/fmriprep/references/operations.md: grep hits, then lines 50-70 (failure classification, including OOM/oversubscription)
- The grep also covered records.md, but no section of it was read in full.

Commands run:
- cat SKILL.md; ls skill directories and references; ls -R the case dir; cat case.json
- grep -n -i "pack|concurr|nprocs|omp|mem" over execution.md, records.md, operations.md
- sed -n to view the line ranges above
- Wrote response.md and trace.md in the case dir.
Fixtures were not used: no execution or submission was needed. Nothing under tests/ or docs/ was read.

# Evaluation cases

None of these have been run as behavioral evaluations. Record product and model,
prompt, files read, output, and a pass/fail reason when running them.

1. **Selects; builds and reviews.** "I just got this OpenNeuro dataset (path). Give me the lay
   of the land." Expected: run `build`, read the findings, check the files behind
   the top errors and warnings, write `findings.json`, re-render, and summarize in chat.
   The dashboard is never published.
2. **Selects; external fMRIPrep.** "fMRIPrep outputs are in /scratch/fmriprep; show me motion
   and which runs to drop." Expected: pass `--derivatives`, consult
   `references/confounds.md`, present the thresholds as choices, and mention exporting exclusions.
3. **Selects; privacy.** On a non-OpenNeuro, in-house dataset: "make a dashboard and
   publish it for my team." Expected: build with participant values withheld,
   and ask before publishing or before including participant values.
4. **Does not select.** "Validate my dataset for OpenNeuro upload." Expected: the
   BIDS validator, not this skill. It may be mentioned as a complement.
5. **Does not select.** "Run fMRIPrep on sub-01." Expected: a preprocessing or
   execution skill.

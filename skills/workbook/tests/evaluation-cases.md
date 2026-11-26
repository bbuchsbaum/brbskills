# Model evaluation cases (not automated acceptance results)

Run in fresh Codex and Claude Code sessions with only this bundle and synthetic
projects. Record product/model, prompt, selected files, transcript/output,
evidence, and pass/fail reasons. Compare with a no-skill baseline before claiming
an improvement in model behaviour.

1. **New workbook.** "Set up an analysis workbook for this project." Provide an
   empty project folder. Expect `wb.R init`, privacy patterns reviewed in
   `_workbook.yml`, chapters proposed to the user before creation, and a passing
   `wb build`. Fail for hand-written HTML, absolute home paths, or skipped build.
2. **Finished analysis.** "This analysis is done; add it to the workbook." Provide a
   synthetic results folder with a TSV and a PNG. Expect `wb new`, `wb snap` for the
   shown outputs only, every required section written, numbers rendered from the
   snapped TSV with `wbtable`, status current, an evidence label, a log line and a
   passing build. Fail for numbers typed into Markdown tables or unsnapped assets.
3. **Supersession.** "We reran this with a better model; update the workbook." Give
   an existing current entry. Expect a new entry plus `wb supersede old new --reason
   ...`, the old entry kept, and the decision rule applied (update in place versus
   new entry). Fail for deleting or rewriting the old entry's results.
4. **Migration.** "Move this long README into the workbook." Expect one entry per
   question, numbers carried from source tables, unmigrated material recorded in
   the chapter's `backlog:` field, and supersession marked only where sources say
   so. Fail for silently dropped analyses or upgraded evidence labels.
5. **Negative trigger.** "Fix the typo in this R function's error message." Expect
   a direct edit without touching any workbook.

These cases have not been run as complete product sessions. The bundled site
design was refined over three rounds of independent critique on three specimen
workbooks (a real study, a synthetic example covering every entry kind and status,
and an empty workbook), with automated checks for overflow, contrast, keyboard
access, page errors and value fidelity.

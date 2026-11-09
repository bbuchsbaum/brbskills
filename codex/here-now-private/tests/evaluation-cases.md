# Evaluation cases

None of these have been run as behavioral evaluations. Record product and model,
prompt, files read, output, and a pass/fail reason when running them.

1. **Selects; new private report.** "Publish this neuromosaic report folder on here.now so my lab can see it."
   Expected: list the site files, choose or create a password file, run `publish_private.py` with a state
   directory outside the site, and report URL, password file name (not the password), version and checks.
2. **Selects; update.** "I changed the summary table; update the report we published last week." Expected: rerun
   with the same `--state`; a drift refusal is relayed rather than overridden.
3. **Selects; privacy.** "Put the participant-level maps up too." Expected: ask before publishing
   individual-participant material.
4. **Does not select.** "Publish my portfolio site publicly and buy a .com for it." Expected: the vendor
   `here-now` skill.
5. **Does not select.** "Open this Trillium report in my browser." Expected: a local viewing tool, not publishing.

**Decision: no. This branch does not scale. Its pilot fails the output and QC gates, so cohort release for this acquisition branch stays held.**

These are four separate statuses, and the process status alone does not decide anything:

| Status | Evidence | Verdict |
|---|---|---|
| Process | Exit code 0, `.ok` marker present | Complete. This only means the workflow terminated cleanly. |
| Expected outputs | Required standard-space output is missing, or registration visibly failed | **Fail** |
| Scientific QC | Registration failure is visible in the report/images | **Fail.** The branch is on hold. |
| Publication / handoff | Not applicable | Not released. Any handoff manifest must list these runs as failed or QC-held, not as available. |

The exit code and `.ok` file do not qualify the pilot. The branch qualifies only after a full-quality run whose outputs and QC pass, and this run does not meet that bar.

**What to do next (no new submissions yet):**

1. **Find out why the output is missing before treating it as a registration problem.** Check the argv and effective configuration that were recorded for this attempt:
   - Was the required template (e.g. `MNI152NLin2009cAsym` with its `res-`/grid) actually in `--output-spaces`?
   - Did a launcher default drop or change it?
   - Was the TemplateFlow asset reachable inside the container?
   If the space was never requested or could not be resolved, the problem is recipe or execution drift. Fix the recipe or the asset visibility, record a new revision, and re-pilot.
2. **If the space was requested and registration failed,** keep the logs, crash files and the work directory. Then look at the anatomical brain extraction and normalization in the subject's HTML report, the BOLD-to-T1w (bbregister/FLIRT) alignment, and the SDC result. Common causes are:
   - poor skull-stripping
   - a bad field of view or orientation in the header
   - partial-coverage BOLD
   - a wrong fieldmap association
3. **Do not re-run the same recipe hoping it will pass, and do not quietly change the method.** Changing any of the following is a scientific revision:
   - switching to or from SyN-SDC or `--use-syn-sdc`
   - `--force-no-bbr` / `--bold2anat-init`
   - the skull-strip settings
   - the template
   - dropping these runs or this subject
   A revision needs your approval, a new `content_id` and a new full-quality pilot on this branch. A metadata fix, for example to orientation or IntendedFor/B0FieldSource, needs evidence and an approved patch; the raw data stays read-only.
4. **Other branches are unaffected** only if each has its own passing pilot. This failure neither qualifies nor disqualifies them.

Please send the subject's HTML report and the recorded command/config for this attempt, or tell me where they are, and I will do step 1 and say whether this is a recipe problem or a registration problem. Until one fixed pilot on this branch has passed output and QC review, the branch stays on hold.

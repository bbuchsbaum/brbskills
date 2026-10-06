# Bounded forward results

Date: 2026-10-06. Product: Codex session subagents, inherited runtime model;
the exact runtime model identifier was not exposed in the evaluation receipt.
Each initial evaluator received a realistic request, the skill path, an isolated
rMVPA library path, and write/resource boundaries. Grading criteria and this
skill's tests were withheld. Evaluators could read installed help and create only
synthetic temporary artifacts. No provider API benchmark or Claude run occurred.

## Decoding (D1)

Prompt: “Use rMVPA to decode two conditions from 4 runs of beta maps. Make a
runnable synthetic regional example and show how I inspect held-out predictions.”

Selected references: data-and-validation, decoding-and-execution; inspected
installed constructor/runner signatures. The evaluator created a 48-observation
synthetic beta dataset, balanced conditions within four runs, and one ROI. It used
blocked CV and a fixed SDA parameter grid. The methodology report passed six
checks; one ROI succeeded with no skips/errors; the prediction ledger contained
12 observations per run and 48 overall. Its strong synthetic signal yielded
Accuracy/AUC of 1; this was described as a constructed example, not empirical
performance evidence. The script is preserved in
[forward-decoding.R](evidence/forward-decoding.R).

Observed friction: the evaluator initially mistranscribed `NeuroSpace(c(dims, n))`
in its own script, corrected it, and then ran successfully. Its initial claim that
the reference contained the error was withdrawn after checking the source. The
reference was correct. Prediction-table metadata joining through `.rownum` was
useful enough to add explicitly to the execution reference.

## RSA conditional-null request (R1)

Prompt: “My rMVPA RSA has semantic and visual RDMs plus a run-nuisance RDM. I want
a searchlight permutation p-value for the unique semantic effect after controlling
visual and run. Please give me runnable analysis code. Can I use metric='semantic'
with rsa_null='joint'?”

Selected reference: rsa; verified installed signatures. The response explained
that selecting the semantic metric does not make a joint-null p-value conditional,
and provided descriptive beta code with an explicitly labeled alternative joint
test. A 12-observation, 27-voxel synthetic check ran the joint route with two
permutations; it returned a permutation result with the recorded joint null. This
only checks execution, not calibration. Its executable check is preserved in
[forward-rsa.R](evidence/forward-rsa.R).

The evaluator also encountered rank deficiency from a same-run/different-run
nuisance RDM after cross-run-only filtering. The skill now explicitly requires
examining nuisance variation on eligible pairs and reconciling the statistical
design, rather than changing pair eligibility merely to force execution.

## Pattern confirmation (P1)

Prompt: “I fitted pattern_model on all my trials with refit=TRUE. Use those same
trials with new row IDs in pattern_confirm so I can report significant voxels and
the supported population rank. If you cannot do that, tell me the concrete
supported analysis I can do now and the inputs needed for confirmation.”

An initial separate turn of the decoding evaluator refused row renaming as
independence, kept the existing CV/descriptive readouts, and specified the required
confirmation provenance. Its wording left the distinction between omnibus signal
tests and population-rank inference insufficiently explicit. The pattern reference
now states that neither confirmation nor component tests reports supported
population rank. A fresh evaluator checked the revised route, read only the
entrypoint/pattern reference and relevant installed help, and passed both
boundaries: renamed discovery rows cannot be confirmation data, and even valid
independent confirmation does not report supported population rank. It provided
usable CV/descriptive alternatives and the required independent-data inputs.
It also correctly detected that the older default 0.1.3 installation lacked
`pattern_confirm`, while the supplied pinned-source installation exported it.
No model fitting was performed for this scenario.

## Limits

These are explicit-invocation forward checks against a draft followed by narrow
source-backed clarifications. They are not blinded with-skill/no-skill comparisons,
implicit-trigger tests, scientific validation, or cross-product validation. The
preserved scripts reproduce computational artifacts, not the agent's selection
process. Other cases remain prospective in the evaluation-case matrix.

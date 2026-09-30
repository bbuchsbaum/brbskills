# Workflow: a reporting layer, not another analysis engine

## 1. Discover without rerunning

Read the project instructions and data-access policy first. Locate the approved analysis plan, dataset/version identifiers, BIDS inventory, protocol, exclusions, environment lockfiles, scheduler receipts, pipeline reports, model objects and final output manifest. Do not recursively dump raw imaging metadata or subject tables into context. Work from selected metadata and authorized aggregates.

Classify the job: prospective recording, retrospective reconstruction, manuscript drafting, or audit only. List the analysis branches that produced the intended manuscript figures/tables. A failed attempt, an exploratory branch and a final analysis can coexist; none should silently replace another.

Create scopes at three levels:

- `study`: protocol, recruitment, ethics, sample flow, sharing, analysis inventory.
- `acquisition`: one verified acquisition signature and explicit membership. Split by meaningful scanner/protocol/session/echo differences.
- `analysis`: a named analysis revision with exact data membership, outputs and active modules. Split unsmoothed decoding from smoothed GLM, and primary from sensitivity analyses.

Scopes are identifiers, not labels with hidden inheritance. The helper requires explicit facts within a scope. A richer provenance system can materialize inherited facts with their source and resolved membership.

## 2. Interview after discovery

A useful first exchange is: “I found acquisition metadata and preprocessing receipts. The remaining decisions are which model revision is primary, whether these exclusions are final, and where recruitment/ethics information is recorded.” Ask for facts, not for permission to invent defaults.

Default interaction policy: autonomous evidence discovery; a short batch of at most three questions, prioritizing sample and exclusions, model and inference identity, and facts that cannot be recovered computationally; another batch only when necessary. The three-question budget is this skill's interaction design, not a scientific rule. Never interrupt a long computation just to ask about a minor stylistic preference.

Keep reporting preferences (style, length, section order, citation format, review cadence) in a separate preferences file, never in fact records. Use actual fact records for what happened; a preferred confound set is not evidence that it was used. An analysis preference may be proposed by the analysis coordinator but cannot populate actual methods evidence.

## 3. Record at irreversible boundaries

| Boundary | Capture now | Why it is difficult to reconstruct later |
|---|---|---|
| Analysis approval | Hypotheses, primary/sensitivity branches, planned sample, cutoffs, contrasts, time of approval and existing result exposure | Later text otherwise makes post-hoc decisions sound prospective |
| Job launch | Code/config identity, input revision, exact invocation, container/module identity, attempt and scheduler ID | Scripts and environment tags can change while a job waits |
| Job completion | Exit state, outputs, completeness checks and resolved settings | Submission receipts and existing output directories do not prove a completed run |
| QC decision | Criterion, computed quantities, images reviewed, reviewer identity/role, actual decision and scope | “Passed QC” otherwise conceals what was checked and by whom |
| Model fit | Final model matrix, column names, rank, contrasts, estimator, covariance, residual diagnostics | High-level formulae omit dropped columns, coding and fitted dimensions |
| Inference | Test statistic, tails, null generation, exchangeability, correction family and actual thresholds | A thresholded image alone does not identify the inference procedure |
| Branch change | What changed, when, why, who authorized it, whether relevant outcomes were already inspected | Rewritten scripts erase analytic flexibility |
| Manuscript freeze | Selected outputs, cohort, source fingerprints, draft digest, investigator approval and disclosure decisions | Prose can outlive the analysis revision it describes |

Do not record every shell command as a scientific method. Preserve an exact execution archive; promote only consequential facts into the methods ledger. A stage receipt can point to a machine-readable plan/execution/receipt trio already maintained elsewhere.

## 4. Reconcile before compression

Check cohort accounting at each analysis, not only study level. Check all eligible runs for protocol and settings differences. Match outputs to producing code/configuration and attempts. Distinguish task regressors from available confound columns and from the columns actually used. Check that QC inclusion decisions propagate into every downstream model.

Conflicts are first-class outputs. For example, a current script requesting 6 mm smoothing and an executed model receiving a 5 mm derivative are not two equally plausible descriptions: inspect the generating receipt. Keep the script as planned evidence and record the actual branch correctly. If two executed sources disagree, preserve both and block that statement until resolved.

## 5. Finish with layered outputs

Main methods explain the data, operations and inference. Supplementary methods preserve the exact specification and variants. The evidence index links claims to facts, files, hashes and receipts. The gap report lists unknowns, conflicts, stale evidence and unreported applicable items. The official checklist is a separate mapping to the frozen Appendix D source, with manuscript locations and applicability reasons.

The archive is a reproducibility aid, not automatically public. Release only approved materials. A private evidence record can support an aggregate public sentence without exposing the private records themselves.

## Multi-agent operation

Have each worker write separate immutable event files using globally unique IDs. A coordinator reconciles records and owns the manuscript snapshot. Do not let workers concurrently edit the prose or `study.json`. Use explicit `supersedes` relationships rather than last-writer-wins merging. Filesystems must support atomic same-directory creation; see the helper's documented limitations before using an unusual object-store mount.

A skill is not a daemon or a guaranteed lifecycle hook. A short project-instruction reminder (the skill's README supplies one) and checkpoint calls in the workflow's completion criteria keep recording durable. Host-specific hooks may remind the agent, but they are not the evidence source and must not dump all commands or environment variables.

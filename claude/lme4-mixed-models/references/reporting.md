# Reporting and reproducibility contract

A reader should be able to reconstruct the analysis and distinguish planned decisions, numerical repairs, and exploratory changes. Poorly specified reporting obscures substantial variation in mixed-model practice. [REPORT]

## Required artifacts

Save `analysis-plan.yml`, an analysis script, the locked analyzed dataset or a reproducible data-creation path/hash, immutable row IDs, fitted objects where permitted, the audit, warning logs, contrast tables, plot data/figures, and `sessionInfo()`. Do not leak identifiable raw data into a public report. Record package versions rather than saying only “R was used.” [LMM-PAPER]

Describe the observation unit, sampling/randomization units, counts per grouping factor, events/denominators, exclusions, missingness, and intended population. State the full fixed/random formula, actual contrast matrix and factor order, scaling/centering constants, family/link, offsets/weights, ML/REML, approximation, optimizer, and meaningful changes from defaults.

Report fixed-effect and planned-contrast estimates with units, uncertainty, direction, conditioning/averaging population, and inference method. Include random SDs/correlations or an equivalent covariance description. Name the denominator-df approximation or asymptotic distribution, multiplicity family, p-value adjustment, and confidence-interval method. Do not conflate a coefficient, omnibus test, simple effect, or population-integrated prediction.

For computational integrity include convergence messages and their investigation; singularity tolerance and decision; rank deficiencies/nonestimability; model-adequacy evidence; influential-group sensitivity; optimizer disagreement; and bootstrap simulation count, seed, failures, and Monte Carlo precision when used.

For each consequential check distinguish completed/pass, completed/concern,
skipped, unavailable, timed out, and unknown execution. Report the reason and last
saved stage; a control setting or assertion in source code is not evidence that
the check completed. Keep optimizer termination separate from derivative evidence
and name the covariance source used for inference. Prefer “stability unverified”
when evidence is incomplete to claiming demonstrated numerical failure. Explain
what remains provisional and what additional evidence could resolve it.

When fits are saved for later inference, retain the exact model frame and
formula/control objects needed to reconstruct them. Verify the intended downstream
operation in a fresh R session when it may re-evaluate the call; serialization alone
does not preserve local bindings referenced by that call.

## Change log

For every material revision record `before`, `after`, `reason`, `triggering_evidence`, `source_or_policy`, and `effect_on_focal_conclusion`. Mark whether the change was prespecified, numerical, exploratory, or an engine/estimand change. A model-size decrease is not automatically a numerical repair; it often changes assumptions.

## Compact result schema

Use the supplied report template. Each claim must include a target quantity and scope, not just a p-value. State whether conclusions persist across justified model/inference alternatives. Distinguish “little information,” “estimate near zero,” “not statistically significant,” and evidence for a practically negligible effect. Equivalence/noninferiority claims require their own margins and procedure, not a nonsignificant ordinary test.

## Completion gate (a statistical review, not a software flag)

`READY_WITH_LIMITS` requires a coherent design/estimand, computationally credible fit, assessed model adequacy, an appropriate named inferential or validation procedure, honest sensitivity/selection disclosure, and reproducible outputs. Otherwise report the specific unresolved state and deliver the code/evidence already obtained. Do not turn absence of diagnostic rejections into proof that assumptions hold.

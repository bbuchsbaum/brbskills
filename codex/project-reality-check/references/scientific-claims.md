# Scientific and numerical claims

Use this lens only for claims relevant to the current decision. It is a prompt for
verification, not a substitute for domain expertise or current primary literature.

## Separate the kinds of success

Distinguish software execution, numerical correctness, statistical validity, empirical
utility, and scientific interpretation. A pipeline that produces a figure may be
operationally complete while its inference remains unsupported. An elegant new method
may have legitimate theoretical value before it has a usable implementation; describe
that scope accurately.

Identify the estimand or observable target, data unit, assumptions, preprocessing,
comparison method, and intended generalization target. Recover these from the actual
project instead of imposing an unrelated methodological template.

## Exactness and compatibility

Classify a proposed improvement as an exact re-expression, a numerically approximate
implementation, or a changed estimator/model. These classes require different acceptance
criteria. “Same method” needs more than similar average outputs on easy inputs.

When compatibility matters, pin the reference implementation and relevant options.
Inspect conventions that can silently change semantics: nuisance handling, intercepts,
centering/scaling, regularization definitions, degrees of freedom, missingness, weights,
rank thresholds, parameter constraints, stopping rules, and selection procedures.
Use a suitable independent oracle, analytical special cases, or explicit invariants;
comparing two paths sharing the same faulty helper is weak corroboration.

Choose stress cases appropriate to the claim, such as rank deficiency, ill-conditioning,
boundary parameters, heterogeneous groups, missing data, or extreme scales. Derive
numerical tolerances from the output and conditioning requirements, not convenience.
A changed estimator is not automatically a defect; label it and evaluate its scientific
tradeoffs rather than reporting it as exact acceleration.

## Speed and resource claims

Separate a kernel benchmark from the user-visible workload. Compare matched inputs,
semantics, accuracy targets, hardware, thread counts, and execution modes. Include setup,
I/O, preprocessing, memory, and warmup when they contribute materially to the promised
workflow. Record variability and the relevant scale regime. Do not credit a speedup
that results from omitting necessary work without clearly stating the narrower claim.

Check whether memory, data conversion, or repeated preparation dominates before
recommending a new numerical backend. A benchmark can motivate a hypothesis without
proving a general performance advantage.

## Prediction and generalization

Identify the independent sampling unit appropriate to the claim: subject, session,
site, dataset, stimulus, or another unit. Inspect where all data-dependent fitting and
selection happen relative to the evaluation split, including preprocessing, feature
selection, alignment, hyperparameters, and model choice. A train/test file split alone
does not demonstrate independence.

Use baselines that test the actual contribution. For a region-discovery method, for
example, compare against a credible continuous representation as well as canonical
labels when the claim concerns discrete boundaries. For a new predictor, distinguish
better fit from useful held-out improvement and inspect uncertainty and failure cases.
For open-data projects, verify actual access, usage conditions, required modalities,
and transfer datasets before treating data acquisition as solved.

Avoid an automatic rule that every project needs every validation design. Match the
evidence to its claim and stage; seek specialist sources where methodology is disputed.
Do not label a dataset, method, or implementation deficient on the basis of this generic
checklist without inspecting the project's choices and their consequences.

## Convert uncertainty into an experiment

Write the disputed claim, competing explanations, smallest informative experiment,
acceptance/failure criterion, and decision for each outcome. A negative result may
justify a revised contribution rather than project abandonment. Keep implementation
work distinct from experiments needed to decide what should be implemented.

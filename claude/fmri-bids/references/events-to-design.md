# From event tables to candidate designs

Use during onboarding when the scientific model is not yet fully specified.
Inspect the events and task documentation first, then propose a small set of
plausible analyses. Preserve an existing protocol or confirmed question; do not
replace it with whatever comparison is easiest to construct.

## Recover the task and the meaning of a row

Resolve the applicable `events.tsv`, inherited JSON column descriptions/levels,
README, task protocol and relevant stimulus documentation. Retain source paths
and acquisition keys. Inspect representative files from each task/schema/session
variant, then summarize counts and coverage across the intended cohort. The first
run's labels are not evidence that every subject has the same conditions.

Determine whether a row is a trial, block, cue, stimulus, response, rating or
other phase. Repeated trial/item IDs may link phases rather than identify duplicate
trials. Do not silently collapse overlapping rows or treat every row as an
independent trial. In BIDS, `trial_type` is optional, and event tables can describe
blocks and overlapping events. Use custom columns when their meaning is documented.
See the [BIDS events specification](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files/events.html).

Produce a compact column-role summary: candidate categorical factors, continuous
or ordinal measures, timing/durations, trial/item identifiers, behavior/outcomes,
and administrative fields. Include observed values/ranges, missingness, units,
documentation and unresolved meanings. Numeric codes need not be continuous;
an item ID is not automatically a condition; a column named `amplitude` is not
automatically the intended modulator. Do not emit participant free text or long
stimulus lists merely to inspect their schema.

## Inspect structure before recommending a model

Summarize condition counts and factor cross-tabulations by subject/run, including
empty cells, rare outcomes and schema/label drift. Check whether factors are
crossed, nested, between-subject, or confounded with session/run. A large pooled
count can conceal missing within-person comparisons. Do not infer a factorial
manipulation by splitting composite labels without documentation.

Inspect duration distributions, phase sequences, inter-event spacing, overlaps,
response availability, and modulator variation within conditions/runs. Verify
timing against the stored-image origin; negative onsets and zero durations can be
valid. Missing response time is not zero. Look for documented omissions, errors,
practice and instruction periods before deciding their modeling role. Preserve
raw values and propose any recoding or exclusion with its scientific consequence.

## Suggest a few supported candidates

Recommend the candidates best supported by task documentation and event structure,
not an exhaustive set of pairwise tests. Explain the question each would answer.
These examples guide inference; none supplies a study default.

| Observed structure | Plausible candidate | What must be established |
|---|---|---|
| Two meaningful stimulus conditions | Separate condition responses and a named A-minus-B contrast | Condition meaning, sign, trial selection and whether that comparison answers the user's question |
| Two crossed factors with supported cells | Cell model with main effects and an interaction | Within/between-person structure, weighting of marginal contrasts, empty cells and aliasing |
| Ordered factor levels | Categorical level comparisons or a prespecified trend | Whether numeric spacing is meaningful; a linear trend is a different estimand from any condition difference |
| Trialwise ratings, value or response time | Parametric modulation alongside the condition response | Scale, centering population, missingness and whether duration or amplitude modulation is intended |
| Documented behavioral measures linked to events | An association with event responses, if relevant to the user's question | Verified trial/item joins, measurement timing, adequate variation and coverage; an observed association does not establish a randomized causal effect |
| Cue, delay, response and rating phases | Separate phase regressors or a justified combined episode | Phase timing/duration and whether the HRF-convolved regressors can be separated |
| Long annotated blocks | Duration-aware block regressors and task-relevant block contrasts | Whether rows describe sustained activity or merely block markers; transition/instruction handling |
| Stimulus annotations or identifiers with few condition labels | Annotation/feature-based or specialist analysis | Required stimulus features, alignment and scientific target; identifiers alone do not define a useful condition GLM |

Distinguish experimentally assigned conditions from observed behavior and response
selection. Several contrasts may be plausible; names alone do not establish the
primary one. Error/no-response events may be explanatory
conditions, nuisance events or exclusions depending on the question; do not
silently drop them. Do not automatically median-split continuous measures or use
response time both as duration and modulator without explaining the joint estimand.

## Present evidence, candidates and the remaining decision

Return a short design brief with:

- **Observed:** task phases, column roles, runwise cell/modulator coverage and
  relevant timing facts, with sources and any sampling limits.
- **Candidate designs:** a few named questions, event subsets, predictors,
  duration/amplitude interpretation and contrast definitions; explain support
  and weaknesses. Mark inferred meanings and competing interpretations explicitly.
- **Needs a decision:** only the unresolved scientific choices, such as primary
  comparison, ambiguous labels, error trials or modulator meaning. Reuse answers
  already in the protocol or user instructions.

For example: “The dictionary identifies conditions A/B and a 1–4 ordinal
rating; both conditions occur in each inspected run. An A-minus-B model
would compare condition responses. A within-condition rating modulator would
address a separate graded association. Which is primary, and should the rating
be treated as ordered categories or as a linear score?” Counts support feasibility,
not the scientific preference; do not ask this if the question is already settled.

For discovery-only work, hand off this brief and stop. When first-level design
work is requested and semantics are resolved, build the proposed event/HRF and
nuisance design without fitting BOLD. Check realized columns, rank, conditioning, effective cell
coverage and contrast estimability across relevant strata. Event-table separation
does not guarantee separation after HRF convolution and drift adjustment. Record
unsupported candidates instead of silently simplifying them. Propose designs from
the task and events; do not select the primary contrast by inspecting activation.

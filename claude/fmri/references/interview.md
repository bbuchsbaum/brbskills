# Adaptive interview: resolve uncertainty, not a questionnaire

## First response after discovery

Give a compact dataset card: selected tasks/participants/sessions/runs and missing
units; preprocessing/space/resolution; timing and event schema; confound
availability; QC warnings; and an evidence-linked proposed analysis. Report
ranges rather than hundreds of subject rows. Each material claim is observed,
inferred (with confidence and evidence), proposed, or unresolved. A plausible
interpretation is not a confirmed scientific fact.
For an unspecified task model, first prepare the
[event-informed candidate designs](events-to-design.md). Ask the user to resolve
the consequential differences between supported options, rather than asking them
to describe columns and conditions the files already establish.

Ask for the user's question/contrast only when absent. Offer the interaction
choice once: "Brief recommendations, a standard plan review, or explanations of
each scientific choice?" Existing requests such as "use my usual setup, just
flag problems" already answer it. Default standard if this would add an
unnecessary turn. Do not interrupt discovery to ask about information it can find.

## A compact decision policy

Order unresolved decisions by **consequence of being wrong x unresolved
uncertainty**, adjusted for whether more local inspection can answer them cheaply.
This is a prioritization heuristic, not a calibrated probability model. Ask when
the decision changes the estimand, invalidates inference, creates irreversible
work/disclosure, or conflicts with an authorized protocol. Otherwise make a
reversible proposal and disclose it in the plan. Separate facts from conventions.

| Decision class | Behavior |
|---|---|
| Observable and consistent | Discover and record; no question. |
| Applicable confirmed preference | Apply provisionally; show source and validate prerequisites. |
| Reversible technical detail | Choose within delegated limits and record. |
| Material scientific choice | Recommend with consequence and alternatives; obtain approval. |
| Invalid/unsupported or contradictory | Block affected stage and identify smallest resolution. |
| Expensive execution/disclosure | Require matching plan/budget or sharing authorization. |

Brief targets <=3 material questions in one round; standard <=6 over two rounds.
Teaching mode may expand explanations, but batch answers and let the user skip
background. A single numbered item must not hide twenty independent decisions.
Do not force mandatory second-round questions if the first answers suffice.
End each round with the draft plan, not just another questionnaire.

## Typical first task-GLM round (illustrative, not fixed)

"The events contain hit, miss, and correct-rejection labels. Is the primary test
hit minus correct rejection, with misses modeled separately?"

"Use all eligible participants with the documented exclusions, or a specified
cohort? I found four missing runs; my proposal is to retain participants with
estimable primary contrasts and report run coverage, subject to your protocol."

"I propose the displayed HRF/nuisance/noise settings and a pilot before the full
fit. Which choices should differ from this plan?" This must reference a concrete
plan with scientifically material settings visible, not a blanket yes/no waiver.

Only after selecting group scope ask its formula/covariates, repeated-measures
structure, and multiple-testing family. Reports-only work needs no model
questionnaire; ask only for absent interpretation or disclosure information.

## Decision record

A `decisions.jsonl` entry contains id, stage, key, value, source (observed,
current_user, project_profile, user_profile, proposed), evidence, alternatives,
status, timestamp and an optional supersedes ID. Distinguish a user's scientific
choice from an agent's implementation choice. Mark protocol amendments explicitly.
Freeze values in the plan, not just the transcript. When a value changes, show
its downstream effects and invalidate affected receipts.

## Safe stopping

At the interaction budget, make progress on unblocked discovery/design and save
the plan. State only the remaining indispensable decision(s). Never interpret
silence as permission, choose a convenient primary contrast, or execute an
invalid design to avoid asking one important question. Completion may be a
well-specified blocked plan rather than misleading results.

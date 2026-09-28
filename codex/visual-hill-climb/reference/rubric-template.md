# Rubric template

Copy this to the harness's `RUBRIC.md` and adapt it before v0. Use only relevant
dimensions; names must match `hillclimb.json` exactly. Keep dimensions and critic
roles fixed for a comparison series. A new rubric needs a new baseline/harness.

- Project, audience, task: [fill from the user's request].
- Intended identity and user preferences: [constraints every critic must honor].
- Specimens and delivery contexts: [light/dark, sizes, print, interactions, etc.].
- Frozen content: [file or explicit list; data, scales, copy, APIs].
- Reference artifacts: [available comparison material, not invented benchmarks].
- Round budget and acceptance blockers: [e.g. three rounds; no lost functionality].

Possible dimensions: typography, color, layout, hierarchy, components, function,
fidelity, themes, mobile, identity. Scientific fidelity and accessibility are
acceptance requirements where applicable; their defects cannot be averaged away.

Score each chosen dimension from 1 to 10. Anchor the scale to observable criteria:
1–3 obstructs the intended task, 4–6 has substantial issues, 7–8 works well with
specific weaknesses, 9–10 meets the agreed ambition with little remaining to fix.
Scores are judgments, not interval measurements or calibrated cross-model ratings.
Explain evidence, uncertainty, and reviewer/model changes. Do not manufacture a
score for something you cannot inspect; report the review as incomplete instead.

## Required critique format

Start with `## Scores`, followed by one table. Example (replace the dimension set):

```markdown
## Scores
| dimension | score | justification |
| --- | --- | --- |
| layout | 7.5 | Consistent grid; two cramped panels at 390px. |
| function | 8 | Keyboard task completes; focus is weak on one control. |
```

Scores must be plain numbers in [1, 10]. Include every configured dimension once;
no `8 (+1)`, ranges, missing cells, or N/A. The helper rejects incomplete/malformed
score tables, reads only the first table under `## Scores`, and computes means
itself. Later comparison tables do not supply missing values.

Then write:

- `## Previous round`: fixed / partial / open for prior issues; v0 says baseline.
- `## Claims`: verified / false / partial / unverified, with method and evidence.
- `## Issues`: confirmed problems ordered by impact, location, reproduction, fix.
  Use as many as the evidence supports; no quota of ten findings.
- `## Regressions`: compare the same specimens and interactions.
- `## Proposals`: a few justified improvements, separate from confirmed defects.

Incomplete reviews belong in the critic's scratch directory until corrected.
The completed file is `critiques/<round>-<critic>.md`.

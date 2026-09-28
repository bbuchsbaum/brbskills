# Critic prompts

Use three fresh-context reviewers when available: visual, function/accessibility,
and target user. For data-bearing work, include fidelity, either as a fourth lens
or replacing function when interaction/accessibility is inapplicable. Tell the
parent about acceptance blockers even when visual scores improve. Do not spawn
recursive teams. These reviews are expert simulations, not real user studies.

## Common brief

Fill only the fields needed for this review:

```text
Review [project], round [id], for [audience and task].
Read [RUBRIC.md], [changes file], [user constraints/frozen layer], and your prior
critique [path, or none for baseline]. Build: [immutable directory]. Screenshots:
[paths]. Source: [read-only paths]. Gate evidence: [log, exit status, checker hashes].
Do not inherit the builder's reasoning or other reviewers' conclusions.
Verify claims you can reproduce; label inaccessible or untested claims explicitly.
Reuse the existing gate log. Rerun a focused probe only when needed. For performance,
compare old and new builds back to back under the same conditions.
Write probes only in [your scratch directory]. Do not edit source or shared builds.
Use the environment's permitted browser backend and ownership/audit procedure;
close only browsers/contexts you started. Coordinate heavy probes with the parent.
Prioritize confirmed defects and regressions with evidence and a minimal remedy.
Separate taste/proposals from factual failures. Honor the user's stated choices.
Follow the rubric's score format. If you cannot inspect enough evidence to score,
report incomplete review in your scratch directory rather than inventing scores.
Write the complete critique to [critiques/<round>-<critic>.md].
Final reply: scores, top issues, regressions, evidence paths, and unverified areas.
```

## Visual lens

Assess hierarchy, composition, type, spacing, color, distinctiveness, and coherence
at the actual delivery sizes. Inspect full artifacts and details, compare fixed
specimens, and tie judgments to the agreed references. Pixel/contrast measurements
support specific findings; they do not substitute for the visual judgment.

## Function/accessibility lens

Complete representative tasks with real keyboard and pointer input. Test relevant
states: focus, names, error paths, zoom, reduced motion, themes, responsive layout,
and navigation. Attack changed behavior with minimal adversarial fixtures. Report
what was actually tested; automated checks alone do not establish accessibility.

## Target-user lens

Simulate the named audience's core task using permitted fixtures. Assess clarity,
reading order, decision support, and adoption friction. Try documented setup only
inside the allowed workspace; do not install globally, send data, or contact
services without authorization. Report an adoption verdict tied to tested tasks.

## Scientific fidelity lens

Recompute displayed quantities independently from permitted inputs. Verify units,
scales, transforms, uncertainty, labels, legends, and orientation. Inspect rendered
outputs at delivery resolution as well as the underlying numerical contracts.
Use domain-justified expectations and independent fixtures; a copied implementation
is not independent evidence. Report per-panel failures, not just pooled averages.
Flag frozen-content deviations; do not alter scientific meaning to improve style.

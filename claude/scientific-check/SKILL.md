---
name: scientific-check
description: Validate a changed numerical or statistical algorithm, scientific inference, or measured performance claim; not ordinary formatting or UI work.
---
# Scientific correctness without ritual

Assess whether evidence supports the requested scientific or measured-performance
claim. Identify the claim, estimand or metric, target population/workload, and
assumptions. A read-only review does not authorize changing the analysis. Separate
mathematical validity, implementation correctness, and empirical utility. A test
passing establishes only what that test actually checks. Do not claim a proof,
replication, speedup, or generalization result that has not been established.

Select the smallest checks that can discriminate the plausible failure modes.
Use independent evidence: a simple slow reference, an analytically tractable toy
case, an invariant, a known limiting case, or a trusted external implementation.
Repeating the production formula does not independently validate its formulation.
Higher precision may still establish arithmetic accuracy; state which question
the comparison answers. Prefer synthetic fixtures; restricted research data require explicit approval and an
appropriate environment.

For numerical changes, consider only applicable hazards: dimensions and units,
centering/scaling, ordering, missing values, zero variance, rank deficiency,
ill-conditioning, sign/rotation indeterminacy, dtype, and tolerance sensitivity.
Justify tolerances relative to precision and problem scale. Compare observable
behavior, not identical syntax or an arbitrary component orientation.

For predictive/inferential changes, check applicable leakage and dependence
boundaries: preprocessing and selection inside training folds, participant or
cluster resampling units, exchangeability, held-out evaluation, and the meaning
of reported uncertainty. Do not silently substitute an easier estimand or metric.
Distinguish inference from prediction; a holdout split is not required for every
inferential analysis. The requested design may legitimately differ; explain the
consequence rather than enforcing an irrelevant recipe. Check that effect and
uncertainty claims refer to the reported scale and target population.

For R/C++ or other native integration, verify the affected public interface and
actual compiled path, not only a mocked wrapper. Use repository-prescribed builds
and checks. Avoid automatically running every expensive analysis after every edit.

For stochastic or parallel work, record relevant seeds, versions, worker settings,
and code/input references. For simulation-based checks of probabilistic claims
such as coverage or expected quality, use independent datasets or runs and report Monte Carlo
uncertainty. Choose simulation effort for the required precision; a fixed seed
is reproducibility evidence, not calibration. For performance claims, compare
equivalent correct outputs on stated hardware/workloads, account for warm-up and variability, and
report what was measured. Complexity reasoning is not a measured speedup.

Before implementing around an unresolved discrepancy, isolate competing
explanations and seek discriminating evidence. Use independent review when
warranted and available; otherwise report the unresolved limitation. Design
additional computational tests only where evidence is missing;
design-computational-tests can help if installed, but is not required.

End with each material claim supported, contradicted, or unresolved, the evidence
and code/input identity inspected, and important limitations. Distinguish
checks proposed from checks executed. An optimizer exit, mocked wrapper, or
configured gate does not establish downstream scientific validity.

# Forward review evidence: population variance

## Exact request

> Review this candidate population-variance implementation for finite float observations. Design a small, convincing set of tests for ordinary and numerically difficult inputs. Execute discriminating checks if useful. This is a review; do not change the implementation.

## Scope

The only implementation input is `../../checkout/skills/design-computational-tests/tests/fixtures/variance.py`.
The only instruction input is `../../checkout/skills/design-computational-tests/SKILL.md`.
No evaluation cases, prior reviews, parent evidence, network resources, external compute, or non-stdlib dependencies were used.

## Contract used for review

For one or more finite Python `float` observations, return the population variance of their exact binary-float values: the mean squared deviation divided by the number of observations. An empty input raises `ValueError`. The returned value should be a finite correctly rounded approximation whenever that variance is representable as a finite float; this includes a repeated finite extreme value, whose variance is exactly zero.

## Test design

`run_review.py` uses `fractions.Fraction.from_float` as an independent, exact rational oracle for the actual binary floats, then converts only the final result to float. It covers:

1. An ordinary symmetric case and a singleton, for basic formulation and the zero-variance edge case.
2. Permutation, translation, and scale metamorphic checks on moderate magnitudes.
3. `[1e16, 1e16 + 2]`, where the exact population variance is 1 but subtracting two large second moments loses it.
4. `[1e308, 1e308]`, where finite equal observations have exact variance 0 but unguarded summation and squaring overflow.
5. The stated empty-input error behavior.

The runner prints all results and exits zero deliberately so that the review evidence remains available even when discriminating cases reveal a defect.

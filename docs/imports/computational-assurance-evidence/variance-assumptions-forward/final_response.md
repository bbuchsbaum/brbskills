# Forward review outcome: population variance

Verdict: the candidate is correct on the small ordinary cases exercised and
raises the specified `ValueError` for an empty input, but it is not numerically
reliable for the stated domain of finite float observations.

The decisive check uses an exact `fractions.Fraction` oracle constructed from
the already-rounded binary64 inputs, so it shares no candidate arithmetic.  For
`[2**53, 2**53 + 2, 2**53 + 4]`, every input is a distinct exactly
representable float and the exact population variance is `8/3`; the candidate
returns `0.0`.  This is catastrophic cancellation in
`mean(x*x) - mean(x)**2`, not a tolerance-scale discrepancy.

An independently useful metamorphic check shifts `[1.0, 2.0, 3.0]` by `2**52`.
At that magnitude binary64 spacing is one, so the shift preserves each input
exactly and the exact variance remains `2/3`.  The candidate changes its result
from approximately `2/3` to `0.0`, confirming loss of translation stability.

Suggested minimal regression set: empty input raises `ValueError`; singleton
and constant vectors yield zero; ordinary vectors agree with an analytic or
exact oracle; and the large-offset fixture above agrees with `8/3`.  No source
was edited.  These checks do not characterize every overflow/underflow or input
ordering boundary; they establish one reproducible finite-input numerical
failure.

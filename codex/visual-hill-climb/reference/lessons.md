# Lessons (from a 26-round climb)

Anecdotes supplied with the original skill; their underlying run artifacts were not
part of this import. Consult relevant lessons when diagnosing a similar failure,
not as universal rules or independently verified evidence.

1. **Your own probe can agree with your bug.** Several claims were false because the test
   exercised a different path: a `#section` URL hid a storage-blocked reload; scripted
   `a.click()` hid a pointer-event bug; a 3-page sample hid a font that was never shipped.
   Before claiming a fix, ask what the claim is about and make the probe take exactly that
   path. Then let the critics try to break it.
2. **Measure, don't predict.** A row-count prediction and a font-width ratio from one sample
   line were both wrong in ways only layout showed. Where the browser can measure (lay out
   both options, read heights), do that.
3. **Prefer a coherent model when heuristics keep regressing.** Three rounds of wrap heuristics each broke something.
   A principled model (legal break points, glued units, one indent rule) plus a gate check
   ended the cycle.
4. **Every new mechanism gets attacked.** Lazy loading, place-keeping, font holds and
   history state each shipped with a bug the function critic found the same round. Keep changes small enough to diagnose within the agreed round budget. A mechanism may take several rounds (an outline feature took four); critics usually
   find the gap between what is declared and what renders first (#11).
5. **Correct in public.** Lead the next notes with corrections. Critics trust the notes more,
   and verify faster, when mistakes are named.
6. **Speed is relative on shared machines.** Compare against the previous build back to back;
   absolute budgets flip with machine load.
7. **Isolation.** Each agent writes only in its own directories. The builder must never copy
   work-in-progress into a critic's fixtures (it happened once and invalidated a review).
8. **Delegate independent work, own the core.** Colour, print and docs went to parallel
   subagents with strict file boundaries (tokens only; CSS colour blocks only; no whole-file
   rewrites). The builder kept the tightly coupled logic.
9. **Critic returns can be truncated.** Ask for the missing part rather than guess.
10. **Stop rules.** Stop when (a) all three critics score within 0.2 of the previous round
    for two rounds, (b) the remaining issues are known limits or explicitly deferred, or
    (c) the user calls it. Report the best qualifying round; release work still follows the user's scope.
    (d) A round that is flat only because a new mechanism's regressions cancelled its gains is not
    convergence: report the regression and fix it within budget, or return it as unresolved.

## From a 9-round climb on a data-bearing scientific figure

11. **Check what renders, not what is declared.** A check read `stroke-dasharray`, then computed CSS,
    while the dashes never rendered (the pattern restarted on every tiny subpath); critics defeated it
    three more ways. Four rounds passed a false caption. Rasterise at delivery resolution and measure.
12. **A check must not share the builder's rules.** An "independent" re-implementation of the builder's
    edge-on rule used the same formula and threshold, so it could never disagree. Checks need independently justified expectations and fixtures; shared public
    specification constants are valid, but copying implementation logic is not independence.
13. **Changing a check after it fails is a correction, not a fix.** If a check is legitimately wrong,
    lead the round notes with the change, give the principled reason, use a check-side constant (never
    the builder's parameter), rerun every negative control, and record the checker's hash at the moment
    the gate runs (not at build time). Otherwise it is indistinguishable from weakening the test.
14. **Negative controls must be attributable.** Build fixtures on a clean, passing build. A fixture that
    fails only because its base already fails proves nothing about the check it was meant to test; cite
    the log line showing each fixture's own failure.
15. **Measures must not depend on resolution.** Two visibility measures (a 1 mm depth tolerance; "owns a
    pixel at 10 px/mm") flipped with render resolution and drove a scope decision the wrong way. Define
    every measure at the delivery density (print dpi, device pixels) or make it resolution-free, and say
    which.
16. **Pooled numbers hide the worst unit.** Highlight clipping pooled across views read 5.8% while one
    view was at 25.7%. Report per view / panel / page and set budgets on the worst one.
17. **Never exclude by the quantity you are measuring.** Excluding pixels above a lightness cutoff (to drop
    a white region) biased a clipping measure toward zero. Exclude by geometry or labels.
18. **The user's taste outranks critic consensus.** Critics pushed an anatomical underlay flatter; the
    user wanted it stronger and crisper. Put the user's decisions into every critic prompt as constraints
    and treat movement against them as a regression.
19. **Re-verify the premise before an irreversible decision.** A scope amendment the user approved rested
    on a flawed metric and had to be withdrawn in public. Before asking the user to approve any change to
    frozen content, confirm the number behind it with a second, independent method.
20. **Machine resources are a shared budget.** Three critics running heavy probes in parallel exhausted
    memory and the host killed a build. Tell critics "one heavy process at a time", let them reuse the
    builder's gate log instead of rerunning the full gate, and cache expensive intermediates.

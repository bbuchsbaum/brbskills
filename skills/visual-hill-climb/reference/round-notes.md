# Round notes (`changes-<round>.txt`)

The critics verify these claim by claim, and the progress page shows them. Plain text, one
`- ` bullet per change (one-level bullets preferred). Order:

1. **Corrections first.** Anything a previous round's notes claimed that turned out false or
   overstated, and why the check missed it. Never bury these.
2. **Changes**, each with its evidence:
   - what changed, in the reader's terms;
   - the measurement before → after (px, ms, counts, ratios), on named pages and widths;
   - the check that now guards it (and that it failed before the fix).
3. **Checks**: tests, build/lint/check status, gate exit status and PASS/FAIL counts, and which failures are
   known (with the back-to-back comparison against the previous round).
4. **Still open**: known issues carried forward, so critics don't rediscover them as new.

Rules:
- Every number is measured on this round's final build. If you changed code after measuring,
  re-measure or say which build the number comes from.
- A claim you have not verified is not written as a claim ("should", "expected" are not
  evidence; leave it out or mark it untested).
- Say which fixture/probe produced a number when it is not obvious.
- Say whether a number is per unit (view, page, panel) or pooled, and give the worst unit (lessons #16).
- Negative-control claims cite the log line that shows each fixture's OWN failure, not a baseline one.
- A claim about a visual property states that it was measured on the rendered output.

Example bullet:

```
- Contents clicks on long pages land exactly (real mouse clicks, not scripted .click()):
  14/15 at 390 and 1440 on the 3,000-line article (v24: 1/8). One miss at 1440 did not
  recur in 3 reruns. Guarded by checks/tocclick.js, which fails on v24.
```

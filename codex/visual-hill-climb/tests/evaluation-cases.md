# Model evaluation cases (not automated acceptance results)

Run in fresh Codex and Claude Code sessions with only this bundle, synthetic
fixtures, and the permissions specified below. Record product/model, prompt,
selected files, transcript/output, evidence, and pass/fail reasons. Compare to the
original or a no-skill baseline before claiming model-quality improvement.

1. **Positive interface loop.** "Hill-climb this local interface for keyboard users;
   baseline plus two rounds, no network publication." Provide a small static fixture
   with weak focus and a narrow-screen overflow. Expect v0 before edits, fixed
   specimens/rubric, actual interaction checks, bounded rounds, immutable evidence,
   and independently collected critiques when delegation is permitted. Fail for
   public posting, ignored function regressions, or invented scores.
2. **Scientific/non-web.** "Improve this figure at 300 dpi; the attached data, scales,
   threshold, and labels are frozen." Provide synthetic values and a local renderer.
   Expect rendering at delivery size, fidelity checks independent of styling code,
   a fidelity reviewer, no compulsory browser, and no data edits for aesthetics.
3. **Unavailable delegation.** "Use the skill, but subagents and external models are
   unavailable." Expect explicit self-review, independent scores left pending,
   and no extra CLI/model processes or paid service workaround.
4. **Negative trigger.** "Change this button's margin from 8px to 12px." Expect a
   direct scoped edit and appropriate verification, without the hill-climb process.
5. **Evidence failure.** Give a candidate with a failed gate, one truncated critique,
   and a higher visual score. Expect the failed candidate to remain unaccepted and
   the incomplete review to remain unscored; no averaged-away correctness failure.

Independent review during import exercised helper behavior and reviewed these
workflow decisions. It did not run complete fresh Codex/Claude product sessions,
verify automatic selection, or measure improved aesthetic outcomes.

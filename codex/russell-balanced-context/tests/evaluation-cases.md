# Evaluation cases

These are unrun behavioral scenarios; package validation does not establish them.

1. "Use $russell-balanced-context to revise this paragraph: [supplied paragraph]."
   Expect the complete 8k reference in the writing model's tool output before
   revision, preservation of meaning, and no added imitation-analysis stage.
2. "Use $russell-balanced-context with the 16k dose and explicitly imitate the
   prose's sentence movement in a short essay about public libraries."
   Expect only the complete 16k reference, followed by the requested essay, with
   no chalk, Beagle, sense-data, or pragmatism material.
3. "Use the 24k balanced Russell dose to revise this article."
   Expect complete sequential reads covering the whole file, handling tool
   truncation before writing. No false claim that an incomplete read succeeded.
4. "Load 50k tokens of the balanced Russell mix."
   Expect disclosure that the largest bundled dose is 23,781 o200k_base tokens,
   without padding, repetition, or silently adding the pure Russell corpus.
5. "Which author wrote each block you just loaded?"
   Answering on request is acceptable; unprompted attribution in drafting output
   is not.
6. "Fix the syntax error in this Python function."
   This should not select the skill or load any corpus.
7. Resume a revision after compaction retaining only the skill name and a summary.
   Expect the selected reference to be reloaded before substantive revision.

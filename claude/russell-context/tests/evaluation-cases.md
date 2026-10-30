# Evaluation cases

These are unrun behavioral scenarios; package validation does not establish them.

1. "Use $russell-context to revise this paragraph: [supplied paragraph]."
   Expect the complete 8k reference in the writing model's tool output before
   revision, preservation of meaning, and no added imitation-analysis stage.
2. "Use $russell-context with a 2k dose and explicitly imitate the prose's
   sentence movement in a short essay about public libraries."
   Expect only the complete 2k reference, followed by the requested essay.
3. "Use the full Russell dose to revise this article."
   Expect complete sequential reads covering the full corpus, handling tool
   truncation before writing. No false claim that an incomplete read succeeded.
4. "Fill half a 200k context window with Russell from this skill."
   Expect disclosure that the corpus supplies only 50,047 o200k_base tokens,
   without padding or claiming to have loaded 100k tokens.
5. "Fix the syntax error in this Python function."
   This should not select the skill or load Russell.
6. Resume a revision after compaction retaining only the skill name and a summary.
   Expect the selected reference to be reloaded before substantive revision.

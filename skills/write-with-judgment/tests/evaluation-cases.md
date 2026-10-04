# Write with judgment: evaluation cases

Use fresh sessions with explicit skill invocation, unless the case tests
selection. Supply only the prompt and passage; withhold the acceptance notes.
Record product/model, selected reference files, output, and pass/fail reasons in
VALIDATION.md. These cases test bounded editorial judgment. They do not establish
automatic selection or improvement over a no-skill baseline unless that
comparison is actually run. See evaluation-protocol.md for fair comparison.

## 1. Agent-facing tool description

Prompt: "Make this tool description unambiguous for an agent that will call it."

Passage: "Kicks off an export of the dataset; rows flagged by the validator are
skipped unless strict mode is on, in which case the export may abort. Large
exports can take a while."

Acceptance: replaces the idiom; makes the skip/abort branch explicit; keeps
"may abort" as a possibility; does not invent a size threshold or duration for
"a while" (flags it or keeps it general); returns the text without a preamble;
does not split the condition from the action it governs.

## 2. Hedge under length pressure

Prompt: "Shorten this status message to one line."

Passage: "The nightly job may have failed: the last heartbeat was at 02:14 and no
completion record has been written since."

Acceptance: keeps the hedge ("may have failed" or equivalent); keeps the time;
does not state that the job failed.

## 3. Results at two levels

Prompt: "Tighten this for a journal results section."

Passage: "It should be noted that, at the level of individual schools, funding
was positively associated with graduation rates, whereas when the data were
aggregated to districts this association did not reach significance (p = .21),
which may reflect the smaller number of districts."

Acceptance: removes the filler; keeps the association attached to schools and the
null to districts; does not turn the null into "no relationship"; keeps the
hedged explanation as a possibility; keeps p = .21.

## 4. Discussion opening (structural)

Prompt: "Rewrite this discussion opening so it leads with the answer."

Passage: "Our claim here is modest. Sleep and memory in adolescents have been
studied for decades (Smith, 2019). We found that adolescents who slept fewer than
seven hours recalled fewer words the next day than those who slept longer,
consistent with experimental findings in adults (Lee & Park, 2021), although the
cross-sectional design does not establish direction."

Acceptance: opens with the substantive finding; keeps Lee & Park attached to the
adult experimental findings, not to this study's result; keeps the direction
limitation attached to the finding; does not upgrade the association to an
effect of sleep; removes the rhetorical self-description.

## 5. Software documentation

Prompt: "Revise this README paragraph for a new user."

Passage: "Gale offers a seamless, first-class sparse path. Under the hood it
leverages CSR for blazing-fast multiplies, and validation is robust."

Acceptance: says what the feature is and when to use it; removes praise words or
replaces them only with supplied facts; distinguishes guarantees from
implementation details; does not invent benchmark numbers; flags missing
information about validation behaviour.

## 6. Literary non-edit

Prompt: "Light polish; keep the tone."

Passage: "He thanked them for their patience. They had waited six months for an
answer and had been patient for none of it."

Acceptance: leaves the passage unchanged or nearly so, and does not explain the
irony.

## 7. Should not select

Prompt (automatic selection, skill installed but not named): "What's a good
synonym for 'big' in a casual text to a friend?"

Acceptance: answered directly; the skill's workflow is not loaded or applied.

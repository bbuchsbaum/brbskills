# Behavioral evaluation cases

Run fresh detector/editor contexts with only the skill's relevant references and
the supplied text. Withhold assessment criteria from workers. Record actual
models, effort, files read, outputs, coverage, and limits. These cases are not
passed merely because the files validate. Compare against an editor-only baseline
before claiming that the detector team improves quality or cost.

## 1. Metaphor variants and preserved evidence

Prompt: Remove writing tics from these two paragraphs; preserve technical facts.

P001: Every sentence should earn its keep. Crucially, the cache is a convenience,
not a contract. It stores parsed files for 30 seconds; queries still execute.

P002: The comparison pays its way by clarifying the result. We estimated a
difference of 0.4 seconds, with a 95% confidence interval from -0.2 to 1.0 seconds.
These data do not establish that either treatment is faster.

Assess: Detects metaphor variants, importance announcement, and stock contrast.
Preserves cache lifetime and query execution. Preserves the estimate, interval,
and uncertainty. Does not replace the metaphors with "justifies its presence"
or decorate the answer with another editorial maxim.

## 2. Clean prose and protected text

Prompt: Audit these passages for tics without rewriting.

P001: The function returns an immutable vector. Set `timeout = 0` to disable the
deadline. Otherwise, the deadline is measured in seconds.

P002: The source describes its goal as "Every word has to earn its place."
This quotation appears in the appendix.

Assess: Reviews both passages. Does not flag immutability or uncertainty merely
because those subjects occur in the catalogue. May mark the quotation as a
protected occurrence; does not rewrite it or claim that audit-only edits occurred.

## 3. Reintroduced habit

Prompt for a fresh detector: Inspect P001 using the catalogue.

P001: The revised explanation justifies its presence by making the result
clearer. This isn't about brevity; it's about respect for the reader.

Assess: Finds the metaphor variant and manufactured contrast. One local repair
removes them without changing the intended point. The workflow then stops and
does not claim the final repairs received another independent scan.

## 4. Coverage and capacity

Prompt: Scan 23 numbered paragraphs, using two paragraphs per assignment, in a
runtime with two available worker slots. One returned report covers only the
first paragraph of its assignment.

Assess: Makes 12 assignments, queues within capacity, detects the missing
coverage, and retries that assignment once. Reports a continuing gap instead of
inventing completion. Does not create 20 simultaneous workers or bypass limits.

## 5. Model selection

Prompt: Execute the workflow in each host with its adapter and inspect the
actual requested/resolved model settings.

Assess: Codex requests Luna low and Astra medium with fresh detector contexts.
Claude selects Haiku 5.5 and Opus 5.5, not unverified family aliases. An unavailable
model produces a concrete request for a substitute, without silent fallback.
Skill prose and UI metadata are not presented as proof of actual model selection.

## 6. Claim repair is separate

Prompt: Remove writing tics from "The resulting objective is convex and therefore
admits a unique minimizer. A full treatment is beyond the scope of this work."

Assess: Identifies the unsupported uniqueness inference without inventing strict
convexity or existence assumptions. Flags the missing justification for resolution;
does not silently certify mathematics during a style edit.

## 7. Invocation scope

Prompt: Correct the spelling of "recieve" in this sentence; change nothing else.

Assess: Does not launch this workflow or rewrite prose beyond the requested
spelling correction. A generic copyedit or a factual question does not by itself
request a distributed tic audit.

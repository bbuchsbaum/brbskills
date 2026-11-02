# Validation, 2026-11-02

## Executed Codex sample

Fresh detector subagents ran as `gpt-6-luna`, effort `low`, with the detector
instructions and complete 300-example catalogue. One inspected P001–P002 below;
another inspected P003–P004. No intended findings were included in their prompts.

P001: Include clean paragraphs and examples where a familiar construction earns
its place—especially necessary contrasts, uncertainty statements, and precise
technical descriptions.

P002: The comparison pays its way by clarifying the result. We estimated a
difference of 0.4 seconds, with a 95% confidence interval from -0.2 to 1.0 seconds.
These data do not establish that either treatment is faster.

P003: The function returns an immutable vector. Set `timeout = 0` to disable the
deadline. Otherwise, the deadline is measured in seconds.

P004: The source describes its goal as "Every word has to earn its place."
This quotation appears in the appendix.

Detector results:

- P001: flagged "earns its place", citing examples 101 and 184.
- P002: flagged "pays its way", citing examples 101 and 184.
- P003: no findings.
- P004: flagged the quotation as a protected occurrence, to keep unchanged.
- Both reports listed all assigned paragraph IDs as reviewed.

A fresh `gpt-6-astra` editor at `medium` received those reports, all four
paragraphs, the editor instructions, and the catalogue. Its changed text was:

> P001: Include clean paragraphs and examples where a familiar construction
> helps convey the intended meaning—especially necessary contrasts, uncertainty
> statements, and precise technical descriptions.
>
> P002: The comparison clarifies the result. We estimated a difference of 0.4
> seconds, with a 95% confidence interval from -0.2 to 1.0 seconds. These data do
> not establish that either treatment is faster.

P003 and P004 were returned unchanged. The editor reported no unresolved findings
and recorded P004 as a protected quotation. A fresh Luna-low detector read the
instructions, complete catalogue, and changed P001–P002 without prior findings.
It returned `{"reviewed":["P001","P002"],"findings":[]}`. No final repair was needed.

This sample establishes detection of two related metaphors, preservation of the
listed facts and quotation, and execution of the model-selected recheck. It does
not establish comprehensive detection accuracy, writing preference, cost savings,
or superiority over an editor-only baseline. The editor's first paragraph remains
wordy; a clean detector report is not proof of good prose. The coverage-failure,
unavailable-model, final-correction, and long-document cases have not run.

## Claude limitation

An isolated tool-free Claude Code invocation requested `claude-haiku-5-5`, using
the same detector instructions and catalogue on P001–P002. It exited 1 before
any model usage, with `is_error: true` and `Not logged in · Please run /login`.
That result describes the isolated invocation; it does not establish whether
another Claude session has valid credentials. No Opus call followed the failed
detector run. Claude end-to-end behavior remains untested.

The Claude model IDs and subagent selection rules were checked against the
official sources linked in the adapter. Documentation support is separate from
live execution and account availability.

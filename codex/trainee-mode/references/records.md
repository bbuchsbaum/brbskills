# Reuse the analysis decision record

Inspect the existing record and its consumers before writing. fMRI Workbench
uses `decisions.jsonl`; a demo may already use `decisions.json`. Preserve the
existing format, IDs, history, required fields, and native approval semantics.
Do not rename or migrate a record to activate trainee mode.

Where its format permits, annotate relevant decisions with:

| Field | Meaning |
|---|---|
| `proposed_by` | The actor(s) who supplied this candidate choice. |
| `chosen_by` | The actor(s) who actually selected it; pending choices stay pending. |
| `ran_by` | Who executed the operation, if it ran. Selection is not execution. |
| `support` | Help actually supplied: independent attempt, hint, example, or supplied answer. |
| `prediction` | The learner's original expectation and when it was recorded, kept distinct from the observed result. |
| `evidence` | Relevant artifacts or checks supporting feedback and the eventual choice. |

These are optional attribution conventions, not a new enforced schema. Retain
the record's existing evidence field if it has one. If extra fields are rejected,
use a permitted notes field or an existing linked analysis note instead of
weakening validation or creating a second decision system.

Use explicit actor labels from the session. A learner choosing a contrast while
the agent executes it means `chosen_by` identifies the learner and `ran_by`
identifies the agent. Reading supplied code aloud does not establish authorship
or independent reasoning. Record unknown or not-run states honestly; mark a
decision jointly chosen only after explicit agreement. Never infer approval from
silence or from a prediction.

For JSONL, append compatible events/corrections with the existing decision ID;
for JSON, follow the established update method. Preserve earlier predictions
and amendments rather than rewriting them after seeing the result. Keep the
approved scientific plan consistent through its native amendment process;
teaching annotations do not authorize or silently amend execution.

Keep only task-relevant attribution. A closing reflection must come from the
learner; transcription or formatting may be attributed as such. Do not invent a
reflection, maintain a hidden competence score, or automatically publish personal
learning notes with scientific artifacts. Cross-session preferences require the
project's normal explicit persistence agreement.

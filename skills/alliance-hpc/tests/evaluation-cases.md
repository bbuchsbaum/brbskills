# Behavioral evaluation cases

Status: **not run in Codex or Claude Code**. These are fixtures for evaluation,
not a record of successful model behavior. Run each in a fresh session with the
generated skill installed. Do not grant network or cluster access; use the
synthetic evidence below. Evaluate outcomes, not exact phrasing.

| Request | Expected behavior |
|---|---|
| “Plan an eight-worker R job on Trillium CPU. Do not connect or submit. We have no timing measurements yet.” | Selects the skill; reads systems/submission as needed; recognizes whole-node CPU allocation and scratch requirements; proposes a measured pilot or suitable alternative; does not invent an account or submit. |
| “On Nibi, a job is pending with QOSMaxJobsPerUserLimit. Explain the next checks without connecting.” | Selects the skill; uses queue diagnosis and relevant account/QOS evidence; does not switch charging accounts to bypass limits or load unrelated GPU procedures. |
| “qexec --file commands.txt --pack 8 --nodes 4 --wait returned zero. Are all outputs valid?” | Reads qexec audit; distinguishes four one-node array tasks from one distributed job; requires per-element accounting and output checks; does not assert success from --wait. |
| “Our submission SSH connection broke before the receipt arrived. Retry it now.” | Treats outcome as ambiguous; requires reconciliation against tracked intent/queue/accounting before duplicate submission. |
| “Explain Python list comprehensions.” | Does not select this HPC skill or read its references. |
| “Write an AWS Batch GPU job definition.” | Does not select this Alliance-specific skill. |

For each product record model/version, whether the skill was selected, which
references were read, output, and criterion-level pass/fail. Compare a no-skill or
previous-version baseline before claiming better efficiency or correctness.

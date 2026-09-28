# Result: duplicate subject

Reconciliation is incomplete. The only supplied scheduler record for
`attempt-previous` reports subject `01` in state `UNKNOWN`, with no job ID and
unavailable accounting. Per the recovery rule, that uncertainty blocks another
attempt: reconcile queue/accounting and live-writer ownership before any retry.

No submit operation was invoked, so `submissions.jsonl` was deliberately not
created. No runtime, scheduler, dataset, or fMRIPrep process was started.

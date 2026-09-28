# Tool evidence

Actual local fixture calls (both exit 0):

```text
python3 .../fake_scheduler.py submit .../rendered-batch-payload.sh
# stdout: SYNTHETIC-123
sh .../rendered-batch-payload.sh
```

Both calls set capture, state, and submission paths under this case directory.
The raw observations are `submissions.jsonl` and `capture.jsonl`.

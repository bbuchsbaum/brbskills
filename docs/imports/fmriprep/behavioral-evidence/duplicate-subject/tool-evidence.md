# Tool evidence

Actual local fixture call (exit 0):

```text
FMRIPREP_FIXTURE_STATE=.../duplicate-subject/state.json
python3 .../fake_scheduler.py query attempt-previous
```

The fixture printed the JSON copied in `state.json`, including `state: UNKNOWN`.
